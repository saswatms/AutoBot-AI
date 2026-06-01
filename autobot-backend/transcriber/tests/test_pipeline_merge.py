# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
from transcriber.pipeline.merge import merge_diarization_and_transcript


def test_merge_assigns_speaker_to_segment():
    diarization = [
        {"start": 0.0, "end": 3.0, "speaker": "SPEAKER_00"},
        {"start": 3.0, "end": 6.0, "speaker": "SPEAKER_01"},
    ]
    transcript = [
        {"start": 0.5, "end": 2.5, "text": "Hello"},
        {"start": 3.5, "end": 5.5, "text": "World"},
    ]
    segments = merge_diarization_and_transcript(diarization, transcript)
    assert segments[0]["speaker"] == "SPEAKER_00"
    assert segments[0]["text"] == "Hello"
    assert segments[1]["speaker"] == "SPEAKER_01"
    assert segments[1]["text"] == "World"


def test_merge_unknown_speaker_when_no_overlap():
    diarization = [{"start": 0.0, "end": 1.0, "speaker": "SPEAKER_00"}]
    transcript = [{"start": 5.0, "end": 6.0, "text": "Orphan"}]
    segments = merge_diarization_and_transcript(diarization, transcript)
    assert segments[0]["speaker"] == "UNKNOWN"


def test_merge_empty_inputs():
    assert merge_diarization_and_transcript([], []) == []
