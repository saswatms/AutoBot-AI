# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""Language-keyed speech provider registry for AutoBot.

Providers register themselves by language code (BCP-47, e.g. 'lv', 'en').
The transcriber pipeline calls get_best(lang) to get the highest-priority
available provider for the detected language.
"""
from __future__ import annotations
import abc
from autobot_shared.logging_manager import get_logger

logger = get_logger(__name__)


class SpeechProvider(abc.ABC):
    """Base class for all AutoBot speech providers."""

    lang: str       # BCP-47 language code this provider handles
    name: str       # Unique provider identifier
    priority: int = 50  # Lower = higher priority (0 = best)

    @abc.abstractmethod
    async def transcribe(self, wav_path: str, language: str) -> list[dict]:
        """Transcribe audio file.

        Args:
            wav_path: Absolute path to normalized 16kHz mono WAV.
            language: BCP-47 language code.

        Returns:
            List of dicts: [{start: float, end: float, text: str}, ...]
        """


class SpeechProviderRegistry:
    """Thread-safe singleton registry of speech providers keyed by language."""

    def __init__(self) -> None:
        self._providers: dict[str, list[SpeechProvider]] = {}

    def register(self, provider: SpeechProvider) -> None:
        lang = provider.lang
        self._providers.setdefault(lang, [])
        self._providers[lang].append(provider)
        self._providers[lang].sort(key=lambda p: p.priority)
        logger.info("Registered speech provider '%s' for lang='%s'", provider.name, lang)

    def get(self, lang: str) -> list[SpeechProvider]:
        return self._providers.get(lang, [])

    def get_best(self, lang: str) -> SpeechProvider | None:
        providers = self.get(lang)
        return providers[0] if providers else None

    def available_languages(self) -> list[str]:
        return list(self._providers.keys())


# Module-level singleton — import and use directly
_registry = SpeechProviderRegistry()


def get_registry() -> SpeechProviderRegistry:
    return _registry
