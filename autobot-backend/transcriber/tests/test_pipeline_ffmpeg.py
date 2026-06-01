# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
import pytest
from unittest.mock import AsyncMock, patch
from transcriber.pipeline.ffmpeg_convert import convert_to_wav


@pytest.mark.asyncio
async def test_convert_returns_wav_path(tmp_path):
    input_path = str(tmp_path / "input.mp3")
    output_dir = str(tmp_path / "processed")
    import os; os.makedirs(output_dir)
    expected_output = str(tmp_path / "processed" / "input.wav")

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_proc:
        mock_proc.return_value.returncode = 0
        mock_proc.return_value.communicate = AsyncMock(return_value=(b"", b""))
        result = await convert_to_wav(input_path, output_dir)
    assert result == expected_output


@pytest.mark.asyncio
async def test_convert_raises_on_ffmpeg_failure(tmp_path):
    output_dir = str(tmp_path / "processed")
    import os; os.makedirs(output_dir)
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_proc:
        mock_proc.return_value.returncode = 1
        mock_proc.return_value.communicate = AsyncMock(return_value=(b"", b"ffmpeg error"))
        with pytest.raises(RuntimeError, match="FFmpeg conversion failed"):
            await convert_to_wav(str(tmp_path / "bad.mp3"), output_dir)
