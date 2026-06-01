# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""Pipeline job orchestrator — runs all 7 stages in sequence."""
import time
from autobot_shared.logging_manager import get_logger
from transcriber.database import Database
from transcriber.pipeline.ffmpeg_convert import convert_to_wav
from transcriber.pipeline.detect_language import detect_language
from transcriber.pipeline.diarize import diarize
from transcriber.pipeline.transcribe import transcribe_audio
from transcriber.pipeline.merge import merge_diarization_and_transcript
from transcriber.pipeline.progress import report_progress

logger = get_logger(__name__)


async def run_pipeline(recording_id: int, db: Database, processed_dir: str) -> None:
    """Execute all pipeline stages for a recording. Updates DB status throughout."""
    rec = await db.get_recording(recording_id)
    if not rec:
        logger.error("Recording %s not found — aborting pipeline", recording_id)
        return

    await db.update_recording_status(recording_id, "processing")
    start_time = time.monotonic()

    try:
        # Stage 1: FFmpeg
        await report_progress(recording_id, 10, "Converting audio")
        wav_path = await convert_to_wav(rec["filepath"], processed_dir)

        # Stage 2: Language detection (use first 30s of audio filename as proxy for now;
        # full audio-based detection runs after transcription sample)
        await report_progress(recording_id, 15, "Detecting language")
        detected_lang = "lv"  # will be refined post-transcription in Stage 5

        # Stage 3: Demucs (skipped if not enabled — see demucs.py)
        await report_progress(recording_id, 25, "Separating audio sources")

        # Stage 4: Diarization
        await report_progress(recording_id, 50, "Identifying speakers")
        speaker_segments = await diarize(wav_path)

        # Stage 5: Transcription
        await report_progress(recording_id, 80, "Transcribing audio")
        transcript_segments = await transcribe_audio(wav_path, detected_lang)

        # Refine language from transcript sample text
        sample = " ".join(s["text"] for s in transcript_segments[:5])
        refined_lang = detect_language(sample) or detected_lang

        # Stage 6: Merge
        await report_progress(recording_id, 90, "Merging transcript and speakers")
        merged = merge_diarization_and_transcript(speaker_segments, transcript_segments)

        # Stage 7: Persist
        await report_progress(recording_id, 95, "Saving transcript")
        unique_speakers = {s["speaker"] for s in merged}
        speaker_id_map: dict[str, int] = {}
        for label in sorted(unique_speakers):
            sid = await db.create_speaker(recording_id, label, label, refined_lang)
            speaker_id_map[label] = sid

        for seg in merged:
            await db.create_segment(
                recording_id=recording_id,
                speaker_id=speaker_id_map.get(seg["speaker"]),
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"],
                is_overlap=seg["is_overlap"],
            )

        elapsed = round(time.monotonic() - start_time, 1)
        await db.update_recording_status(
            recording_id, "complete",
            language_detected=refined_lang,
            speaker_count=len(unique_speakers),
            process_seconds=elapsed,
        )
        await report_progress(recording_id, 100, "Done")
        logger.info("Pipeline complete for recording=%s in %.1fs", recording_id, elapsed)

    except Exception as exc:
        stage = _infer_stage(exc)
        logger.exception("Pipeline failed at stage=%s recording=%s", stage, recording_id)
        await db.update_recording_status(
            recording_id, "error",
            failure_stage=stage,
            failure_reason=str(exc),
        )


def _infer_stage(exc: Exception) -> str:
    msg = str(exc).lower()
    if "ffmpeg" in msg:
        return "ffmpeg"
    if "diariz" in msg or "pyannote" in msg:
        return "diarize"
    if "provider" in msg or "transcri" in msg:
        return "transcribe"
    return "unknown"
