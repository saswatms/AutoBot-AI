# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""LATE binary speech provider for Latvian (lv).

LATE is a local ASR binary that exposes an HTTP API on a configurable port.
It is lazily started by the operating system or a separate process manager —
this provider only calls the HTTP API.
"""
import httpx
from autobot_shared.logging_manager import get_logger
from voice_processing.providers import SpeechProvider

logger = get_logger(__name__)


class LATEProvider(SpeechProvider):
    lang = "lv"
    name = "late"
    priority = 10  # Prefer over Tilde (local, no API cost)

    def __init__(self, port: int = 9090) -> None:
        self._base_url = f"http://127.0.0.1:{port}"

    async def transcribe(self, wav_path: str, language: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(wav_path, "rb") as f:
                resp = await client.post(
                    f"{self._base_url}/transcribe",
                    files={"audio": ("audio.wav", f, "audio/wav")},
                    data={"language": language},
                )
            resp.raise_for_status()
            data = await resp.json()
        segments = data.get("segments", [])
        return [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in segments]
