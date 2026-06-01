# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""Stage 1: Convert any audio format to 16kHz mono WAV using FFmpeg."""
import asyncio
from pathlib import Path
from autobot_shared.logging_manager import get_logger

logger = get_logger(__name__)


async def convert_to_wav(input_path: str, output_dir: str) -> str:
    """Convert audio file to 16kHz mono PCM WAV.

    Returns absolute path to the output WAV file.
    Raises RuntimeError if FFmpeg exits non-zero.
    """
    stem = Path(input_path).stem
    output_path = str(Path(output_dir) / f"{stem}.wav")
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000", "-ac", "1", "-f", "wav", output_path,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed: {stderr.decode(errors='replace')}")
    logger.debug("Converted %s → %s", input_path, output_path)
    return output_path
