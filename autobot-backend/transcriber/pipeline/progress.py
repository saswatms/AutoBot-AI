# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""Fire SSE progress events via AutoBot's async_work ProgressTracker."""
from autobot_shared.logging_manager import get_logger

logger = get_logger(__name__)


async def report_progress(recording_id: int, percent: int, step: str) -> None:
    """Report pipeline progress. Fails silently if async_work unavailable."""
    try:
        from async_work import get_progress_tracker
        tracker = get_progress_tracker()
        await tracker.report(
            task_id=f"transcriber:{recording_id}",
            percent=percent,
            current_step=step,
        )
    except Exception:
        logger.debug("Progress report skipped for recording=%s step=%s", recording_id, step)
