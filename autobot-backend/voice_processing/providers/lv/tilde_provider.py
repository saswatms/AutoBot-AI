# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""Tilde cloud ASR provider for Latvian (lv).

Requires TILDE_API_KEY environment variable.
Falls back gracefully if key is not set.
"""
import os
import httpx
from autobot_shared.logging_manager import get_logger
from voice_processing.providers import SpeechProvider

logger = get_logger(__name__)

_TILDE_URL = "https://api.tilde.lv/asr/v1/transcribe"


class TildeProvider(SpeechProvider):
    lang = "lv"
    name = "tilde"
    priority = 20  # Lower priority than LATE

    def __init__(self) -> None:
        self._api_key = os.getenv("TILDE_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def transcribe(self, wav_path: str, language: str) -> list[dict]:
        if not self._api_key:
            raise RuntimeError("TILDE_API_KEY not configured")
        async with httpx.AsyncClient(timeout=600.0) as client:
            with open(wav_path, "rb") as f:
                resp = await client.post(
                    _TILDE_URL,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    files={"audio": ("audio.wav", f, "audio/wav")},
                    data={"language": language},
                )
            resp.raise_for_status()
            data = await resp.json()
        return [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in data.get("segments", [])]
