"""Demo (expert trajectories) CRUD API."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models import Demo
from app.schemas.api import DemoCreate, DemoSummary
from app.workers.collect_demo import collect_demo

router = APIRouter(prefix="/api/v1/demos", tags=["demos"])


@router.get("", response_model=list[DemoSummary])
async def list_demos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Demo).order_by(Demo.created_at.desc()))
    return [DemoSummary.model_validate(d) for d in result.scalars().all()]


@router.post("", status_code=202, response_model=DemoSummary)
async def create_demo(body: DemoCreate, db: AsyncSession = Depends(get_db)):
    if not body.source_run_id:
        raise HTTPException(400, "source_run_id is required to collect a demo")

    from app.db.models import Run as RunModel

    run_result = await db.execute(
        select(RunModel).where(RunModel.id == body.source_run_id)
    )
    source_run = run_result.scalar_one_or_none()
    if not source_run:
        raise HTTPException(404, f"Source run '{body.source_run_id}' not found")
    if source_run.status != "done":
        raise HTTPException(400, f"Source run must be 'done', got '{source_run.status}'")

    reward_id = source_run.reward_id
    checkpoint = source_run.artifact_path
    if not checkpoint:
        raise HTTPException(400, "Source run has no saved artifact")

    demo = Demo(
        name=body.name,
        env_id=body.env_id,
        reward_id=reward_id,
        source_run_id=body.source_run_id,
        n_episodes=0,
        n_steps=0,
        file_path="",
    )
    db.add(demo)
    await db.commit()
    await db.refresh(demo)

    try:
        file_path, n_eps, n_steps = await asyncio.to_thread(
            collect_demo,
            run_id=body.source_run_id,
            env_id=body.env_id,
            reward_id=reward_id,
            n_episodes=body.n_episodes,
            min_timesteps=body.min_timesteps,
        )
        demo.file_path = str(file_path)
        demo.n_episodes = n_eps
        demo.n_steps = n_steps
        await db.commit()
        await db.refresh(demo)
    except Exception as exc:
        demo.n_episodes = 0
        demo.n_steps = 0
        demo.file_path = ""
        await db.commit()
        raise HTTPException(500, f"Demo collection failed: {exc}")

    return DemoSummary.model_validate(demo)


@router.get("/{demo_id}", response_model=DemoSummary)
async def get_demo(demo_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Demo).where(Demo.id == demo_id))
    demo = result.scalar_one_or_none()
    if not demo:
        raise HTTPException(404, "Demo not found")
    return DemoSummary.model_validate(demo)


@router.delete("/{demo_id}", status_code=204)
async def delete_demo(demo_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Demo).where(Demo.id == demo_id))
    demo = result.scalar_one_or_none()
    if not demo:
        raise HTTPException(404, "Demo not found")
    await db.delete(demo)
    await db.commit()
    return None
