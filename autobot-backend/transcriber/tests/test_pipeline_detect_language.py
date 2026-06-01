# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
import pytest
from unittest.mock import patch, MagicMock
from transcriber.pipeline.detect_language import detect_language


def test_detect_language_returns_bcp47():
    mock_detector = MagicMock()
    mock_lang = MagicMock()
    mock_lang.iso_code_639_1.name.lower.return_value = "lv"
    mock_detector.detect_language_of.return_value = mock_lang
    with patch("transcriber.pipeline.detect_language._get_detector", return_value=mock_detector):
        result = detect_language("Šis ir teksts latviešu valodā")
    assert result == "lv"


def test_detect_language_unknown_returns_none():
    mock_detector = MagicMock()
    mock_detector.detect_language_of.return_value = None
    with patch("transcriber.pipeline.detect_language._get_detector", return_value=mock_detector):
        result = detect_language("")
    assert result is None
