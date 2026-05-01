"""SSE endpoint for real-time training metrics streaming.

FastAPI 0.135+ EventSourceResponse provides:
- Auto Content-Type: text/event-stream
- Auto Cache-Control: no-cache, X-Accel-Buffering: no
- Auto keep-alive pings
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import EventSourceResponse

from app.workers.scheduler import RUN_QUEUES

router = APIRouter(prefix="/api/v1", tags=["stream"])


@router.get("/runs/{run_id}/stream")
async def stream_run(run_id: str):
    queue = RUN_QUEUES.get(run_id)
    if queue is None:
        raise HTTPException(404, "Run not found or not running")

    async def event_generator():
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield {"event": "metric", "data": json.dumps(msg, default=str)}
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": ""}

    return EventSourceResponse(event_generator())
