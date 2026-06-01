# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""SSE progress endpoint — streams pipeline stage progress to the frontend."""
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from transcriber.database import Database
from transcriber.deps import get_db
from autobot_shared.logging_manager import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["transcriber-sse"])


@router.get("/recordings/{recording_id}/progress")
async def recording_progress(recording_id: int, db: Database = Depends(get_db)):
    """Stream pipeline progress as Server-Sent Events.

    Polls async_work ProgressTracker every 500ms and forwards updates.
    Closes when status reaches 100% or error.
    """
    rec = await db.get_recording(recording_id)
    if not rec:
        raise HTTPException(404, "Recording not found")

    async def event_stream():
        task_id = f"transcriber:{recording_id}"
        last_percent = -1
        max_polls = 600  # 5 minutes max (600 × 500ms)
        polls = 0
        while polls < max_polls:
            polls += 1
            try:
                from async_work import get_progress_tracker
                progress = await get_progress_tracker().get(task_id)
                if progress is not None:
                    if progress.percent != last_percent:
                        last_percent = progress.percent
                        data = json.dumps({
                            "percent": progress.percent,
                            "step": progress.current_step or "",
                        })
                        yield f"data: {data}\n\n"
                    if progress.percent >= 100:
                        break
            except Exception:
                pass
            # Also check DB status directly in case progress tracker is unavailable
            current = await db.get_recording(recording_id)
            if current and current["status"] in ("complete", "error"):
                pct = 100 if current["status"] == "complete" else -1
                yield f"data: {json.dumps({'percent': pct, 'step': current['status']})}\n\n"
                break
            await asyncio.sleep(0.5)
        yield "data: {\"percent\": 100, \"step\": \"done\"}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/recordings/{recording_id}/retry")
async def retry_recording(recording_id: int, db: Database = Depends(get_db)):
    """Retry a failed recording from the beginning."""
    rec = await db.get_recording(recording_id)
    if not rec:
        raise HTTPException(404, "Recording not found")
    if rec["status"] != "error":
        raise HTTPException(400, "Only failed recordings can be retried")
    import asyncio as _asyncio
    from transcriber.pipeline.queue import run_pipeline
    processed_dir = str(__import__('pathlib').Path(rec["filepath"]).parent.parent / "processed")
    await db.update_recording_status(recording_id, "pending",
                                     failure_stage=None, failure_reason=None)
    _asyncio.create_task(run_pipeline(recording_id, db, processed_dir))
    return {"status": "retrying"}
