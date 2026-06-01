# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
import pytest
from unittest.mock import AsyncMock, patch
from transcriber.pipeline.transcribe import transcribe_audio


@pytest.mark.asyncio
async def test_transcribe_uses_provider(tmp_path):
    wav = tmp_path / "audio.wav"
    wav.write_bytes(b"\x00" * 100)
    mock_provider = AsyncMock()
    mock_provider.transcribe = AsyncMock(return_value=[
        {"start": 0.0, "end": 1.0, "text": "Hello world"}
    ])
    with patch("transcriber.pipeline.transcribe._get_provider", return_value=mock_provider):
        result = await transcribe_audio(str(wav), "en")
    assert len(result) == 1
    assert result[0]["text"] == "Hello world"
    mock_provider.transcribe.assert_awaited_once_with(str(wav), "en")


@pytest.mark.asyncio
async def test_transcribe_raises_when_no_provider(tmp_path):
    wav = tmp_path / "audio.wav"
    wav.write_bytes(b"\x00" * 100)
    with patch("transcriber.pipeline.transcribe._get_provider", return_value=None):
        with pytest.raises(RuntimeError, match="No speech provider"):
            await transcribe_audio(str(wav), "zz")
