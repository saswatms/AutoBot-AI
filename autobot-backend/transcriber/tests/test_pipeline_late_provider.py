# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
import pytest
from unittest.mock import AsyncMock, patch
from voice_processing.providers.lv.late_provider import LATEProvider


@pytest.mark.asyncio
async def test_late_provider_lang():
    p = LATEProvider()
    assert p.lang == "lv"
    assert p.name == "late"


@pytest.mark.asyncio
async def test_late_transcribe_calls_endpoint(tmp_path):
    wav = tmp_path / "test.wav"
    wav.write_bytes(b"RIFF" + b"\x00" * 44)
    p = LATEProvider(port=9090)
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={
        "segments": [{"start": 0.0, "end": 1.5, "text": "Sveiki"}]
    })
    mock_response.raise_for_status = AsyncMock()
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await p.transcribe(str(wav), "lv")
    assert len(result) == 1
    assert result[0]["text"] == "Sveiki"
