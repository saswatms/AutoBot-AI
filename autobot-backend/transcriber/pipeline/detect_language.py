# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""Stage 2: Detect spoken language from transcript sample text.

Uses lingua-language-detector. Detector is lazy-loaded and cached.
"""
from __future__ import annotations
from autobot_shared.logging_manager import get_logger

logger = get_logger(__name__)
_detector = None


def _get_detector():
    global _detector
    if _detector is None:
        from lingua import LanguageDetectorBuilder
        _detector = LanguageDetectorBuilder.from_all_languages().build()
    return _detector


def detect_language(sample_text: str) -> str | None:
    """Return BCP-47 language code (e.g. 'lv', 'en') or None if undetected."""
    if not sample_text.strip():
        return None
    detector = _get_detector()
    lang = detector.detect_language_of(sample_text)
    if lang is None:
        return None
    code = lang.iso_code_639_1.name.lower()
    logger.debug("Detected language: %s", code)
    return code
