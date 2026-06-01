# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""
Transcriber builtin extension.

Mounts all transcriber routes under /api/transcriber and manages
DB lifecycle (connect on app startup, close on shutdown).
Enabled via TRANSCRIBER_ENABLED=true in environment.
"""
import os
from pathlib import Path
from fastapi import APIRouter, FastAPI
from extensions.base import Extension, HookContext
from autobot_shared.logging_manager import get_logger

logger = get_logger(__name__)

_ENABLED = os.getenv("TRANSCRIBER_ENABLED", "true").lower() == "true"
_DATA_DIR = Path(os.getenv("TRANSCRIBER_DATA_DIR", "data/transcriber"))


def get_transcriber_router() -> APIRouter:
    from transcriber.routes.projects import router as projects_router
    from transcriber.routes.recordings import router as recordings_router
    from transcriber.routes.recordings_sse import router as sse_router
    combined = APIRouter(prefix="/api/transcriber")
    combined.include_router(projects_router)
    combined.include_router(recordings_router)
    combined.include_router(sse_router)
    return combined


# Module-level router for feature_routers.py loader
router = get_transcriber_router()


class TranscriberExtension(Extension):
    name = "transcriber"
    priority = 10

    async def on_app_startup(self, app: FastAPI) -> None:
        if not _ENABLED:
            logger.info("Transcriber extension disabled (TRANSCRIBER_ENABLED != true)")
            return
        from transcriber.database import Database
        from voice_processing.providers import get_registry
        from voice_processing.providers.lv.late_provider import LATEProvider
        from voice_processing.providers.lv.tilde_provider import TildeProvider

        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR := _DATA_DIR / "uploads").mkdir(exist_ok=True)
        (_DATA_DIR / "processed").mkdir(exist_ok=True)
        (_DATA_DIR / "exports").mkdir(exist_ok=True)

        db = Database(str(_DATA_DIR / "transcriber.db"))
        await db.connect()
        app.state.transcriber_db = db
        app.state.transcriber_upload_dir = str(_DATA_DIR / "uploads")
        app.state.transcriber_export_dir = str(_DATA_DIR / "exports")

        registry = get_registry()
        registry.register(LATEProvider())
        tilde = TildeProvider()
        if tilde.is_available():
            registry.register(tilde)
            logger.info("Tilde provider registered (API key present)")
        else:
            logger.info("Tilde provider skipped (TILDE_API_KEY not set)")
        logger.info("Transcriber extension started")

    async def on_app_shutdown(self, app: FastAPI) -> None:
        db = getattr(app.state, "transcriber_db", None)
        if db:
            await db.close()
            logger.info("Transcriber DB closed")
