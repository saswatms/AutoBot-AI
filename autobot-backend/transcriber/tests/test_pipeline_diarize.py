# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
import pytest
from unittest.mock import patch, MagicMock
from transcriber.pipeline.diarize import diarize


@pytest.mark.asyncio
async def test_diarize_returns_speaker_segments(tmp_path):
    wav = tmp_path / "audio.wav"
    wav.write_bytes(b"\x00" * 1000)

    mock_pipeline = MagicMock()
    mock_turn1 = MagicMock(start=0.0, end=2.5)
    mock_turn2 = MagicMock(start=2.5, end=5.0)
    mock_pipeline.return_value.itertracks.return_value = [
        (mock_turn1, None, "SPEAKER_00"),
        (mock_turn2, None, "SPEAKER_01"),
    ]
    with patch("transcriber.pipeline.diarize._get_pipeline", return_value=mock_pipeline):
        result = await diarize(str(wav))
    assert len(result) == 2
    assert result[0] == {"start": 0.0, "end": 2.5, "speaker": "SPEAKER_00"}
    assert result[1] == {"start": 2.5, "end": 5.0, "speaker": "SPEAKER_01"}
