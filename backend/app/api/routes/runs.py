from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import settings
from app.db.models import Run as RunModel
from app.schemas.api import RunSummary
from app.workers.scheduler import RUN_QUEUES

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.get("/{run_id}", response_model=RunSummary)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RunModel).where(RunModel.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "Run not found")
    return RunSummary(
        id=run.id,
        reward_id=run.reward_id,
        seed=run.seed,
        status=run.status,
        hyperparams=run.hyperparams,
        final_metrics=run.final_metrics,
        artifact_path=run.artifact_path,
        started_at=run.started_at,
        ended_at=run.ended_at,
    )


@router.delete("/{run_id}")
async def cancel_run(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RunModel).where(RunModel.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status not in ("pending", "running"):
        raise HTTPException(409, f"Run already {run.status}")

    run.status = "cancelled"
    await db.commit()

    q = RUN_QUEUES.pop(run_id, None)
    if q:
        await q.put({"run_id": run_id, "metrics": {"status": "cancelled"}, "step": 0, "wall_time": 0})

    return {"status": "cancelled"}


@router.get("/{run_id}/replay")
async def get_replay_video(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RunModel).where(RunModel.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "Run not found")

    video_dir = Path(settings.data_dir) / "videos" / run_id
    if not video_dir.exists():
        raise HTTPException(404, "No replay video recorded for this run")

    # Match VecVideoRecorder naming: step-0-to-step-600.mp4
    for candidate in video_dir.iterdir():
        if candidate.suffix == ".mp4":
            return FileResponse(candidate, media_type="video/mp4")

    raise HTTPException(404, "Video file not found")
