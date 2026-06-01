# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
import pytest
from voice_processing.providers import SpeechProviderRegistry, SpeechProvider


class DummyProvider(SpeechProvider):
    lang = "xx"
    name = "dummy"

    async def transcribe(self, wav_path: str, language: str) -> list[dict]:
        return [{"start": 0.0, "end": 1.0, "text": "hello"}]


def test_register_and_get():
    reg = SpeechProviderRegistry()
    reg.register(DummyProvider())
    providers = reg.get("xx")
    assert len(providers) == 1
    assert providers[0].name == "dummy"


def test_get_unknown_lang_returns_empty():
    reg = SpeechProviderRegistry()
    assert reg.get("zz") == []


def test_get_best_provider():
    reg = SpeechProviderRegistry()
    reg.register(DummyProvider())
    best = reg.get_best("xx")
    assert best is not None
    assert best.name == "dummy"
