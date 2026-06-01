# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""Stage 6: Align speaker diarization timeline with transcript text segments."""


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def merge_diarization_and_transcript(
    diarization: list[dict], transcript: list[dict]
) -> list[dict]:
    """Assign a speaker to each transcript segment by maximum time overlap.

    Args:
        diarization: [{start, end, speaker}, ...] from diarize()
        transcript:  [{start, end, text}, ...] from transcribe_audio()

    Returns:
        [{start, end, text, speaker, is_overlap}, ...]
    """
    merged = []
    for seg in transcript:
        best_speaker = "UNKNOWN"
        best_overlap = 0.0
        is_overlap = False
        speakers_overlapping = set()
        for d in diarization:
            ov = _overlap(seg["start"], seg["end"], d["start"], d["end"])
            if ov > 0:
                speakers_overlapping.add(d["speaker"])
            if ov > best_overlap:
                best_overlap = ov
                best_speaker = d["speaker"]
        is_overlap = len(speakers_overlapping) > 1
        merged.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
            "speaker": best_speaker,
            "is_overlap": is_overlap,
        })
    return merged
