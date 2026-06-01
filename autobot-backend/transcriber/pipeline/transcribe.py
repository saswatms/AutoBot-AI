# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""Stage 5: ASR transcription via AutoBot speech provider registry.

The transcriber never imports any specific provider — it only calls
voice_processing.providers.get_registry().get_best(lang).
"""
from autobot_shared.logging_manager import get_logger
from voice_processing.providers import get_registry, SpeechProvider

logger = get_logger(__name__)


def _get_provider(lang: str) -> SpeechProvider | None:
    return get_registry().get_best(lang)


async def transcribe_audio(wav_path: str, language: str) -> list[dict]:
    """Transcribe audio using the best registered provider for the language.

    Returns list of dicts: [{start, end, text}, ...]
    Raises RuntimeError if no provider is registered for the language.
    """
    provider = _get_provider(language)
    if provider is None:
        raise RuntimeError(f"No speech provider registered for language='{language}'")
    logger.info("Transcribing with provider='%s' lang='%s'", provider.name, language)
    return await provider.transcribe(wav_path, language)
