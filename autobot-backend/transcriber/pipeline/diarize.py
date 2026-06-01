# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""Stage 4: Speaker diarization using Pyannote 3.1 (CPU, lazy-loaded)."""
from __future__ import annotations
import asyncio
from autobot_shared.logging_manager import get_logger

logger = get_logger(__name__)
_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        import os
        from pyannote.audio import Pipeline
        import torch
        token = os.getenv("HUGGINGFACE_TOKEN", "")
        _pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token or None,
        )
        _pipeline.to(torch.device("cpu"))
        logger.info("Pyannote diarization pipeline loaded")
    return _pipeline


async def diarize(wav_path: str) -> list[dict]:
    """Run speaker diarization on a WAV file.

    Returns list of dicts: [{start, end, speaker}, ...]
    Runs in a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run_diarize, wav_path)


def _run_diarize(wav_path: str) -> list[dict]:
    pipeline = _get_pipeline()
    diarization = pipeline(wav_path)
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({"start": round(turn.start, 3), "end": round(turn.end, 3), "speaker": speaker})
    return segments
