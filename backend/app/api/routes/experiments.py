from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.db.models import Experiment, Run as RunModel
from app.schemas.api import (
    ExperimentCreate,
    ExperimentList,
    ExperimentSummary,
    RunSummary,
)
from app.workers.scheduler import RUN_QUEUES, schedule_run

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


@router.post("", status_code=202, response_model=ExperimentSummary)
async def create_experiment(
    body: ExperimentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    exp = Experiment(
        name=body.name,
        env_id=body.env_id,
        algo_id=body.algo_id,
        total_steps=body.total_steps,
        status="pending",
    )
    db.add(exp)
    await db.flush()

    for reward_id in body.reward_ids:
        for seed in body.seeds:
            run = RunModel(
                experiment_id=exp.id,
                reward_id=reward_id,
                seed=seed,
                hyperparams=body.hyperparams.model_dump(),
                status="pending",
            )
            db.add(run)

    await db.commit()
    # Reload with runs eagerly loaded
    result = await db.execute(
        select(Experiment).options(selectinload(Experiment.runs)).where(Experiment.id == exp.id)
    )
    exp = result.scalar_one()

    background_tasks.add_task(_execute_experiment, exp.id)

    return _exp_to_summary(exp)


@router.get("", response_model=ExperimentList)
async def list_experiments(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    count_q = await db.execute(select(Experiment))
    total = len(count_q.scalars().all())

    q = (
        select(Experiment)
        .options(selectinload(Experiment.runs))
        .order_by(Experiment.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    exps = (await db.execute(q)).scalars().unique().all()
    return ExperimentList(
        items=[_exp_to_summary(e) for e in exps],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{exp_id}", response_model=ExperimentSummary)
async def get_experiment(exp_id: str, db: AsyncSession = Depends(get_db)):
    q = (
        select(Experiment)
        .options(selectinload(Experiment.runs))
        .where(Experiment.id == exp_id)
    )
    result = await db.execute(q)
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(404, "Experiment not found")
    return _exp_to_summary(exp)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _exp_to_summary(e: Experiment) -> ExperimentSummary:
    return ExperimentSummary(
        id=e.id,
        name=e.name,
        env_id=e.env_id,
        algo_id=e.algo_id,
        total_steps=e.total_steps,
        status=e.status,
        created_at=e.created_at,
        runs=[_run_to_summary(r) for r in e.runs],
    )


def _run_to_summary(r: RunModel) -> RunSummary:
    return RunSummary(
        id=r.id,
        reward_id=r.reward_id,
        seed=r.seed,
        status=r.status,
        hyperparams=r.hyperparams,
        final_metrics=r.final_metrics,
        started_at=r.started_at,
        ended_at=r.ended_at,
    )


async def _execute_experiment(exp_id: str) -> None:
    """Background task: grab pending runs and schedule them."""
    from app.db.database import async_session

    async with async_session() as db:
        result = await db.execute(
            select(Experiment)
            .options(selectinload(Experiment.runs))
            .where(Experiment.id == exp_id)
        )
        exp = result.scalar_one_or_none()
        if not exp:
            return

        exp.status = "running"
        await db.commit()

        for run_model in exp.runs:
            if run_model.status != "pending":
                continue
            queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
            RUN_QUEUES[run_model.id] = queue

            run_model.status = "running"
            run_model.started_at = datetime.now(timezone.utc)
            await db.commit()

            try:
                await schedule_run(run_model, exp, queue)
                run_model.status = "done"
                run_model.ended_at = datetime.now(timezone.utc)
            except Exception:
                run_model.status = "failed"
                run_model.ended_at = datetime.now(timezone.utc)
            finally:
                await db.commit()
                RUN_QUEUES.pop(run_model.id, None)

        # Check if all runs are finished
        result = await db.execute(
            select(Experiment)
            .options(selectinload(Experiment.runs))
            .where(Experiment.id == exp_id)
        )
        exp = result.scalar_one()
        statuses = {r.status for r in exp.runs}
        if statuses <= {"done", "failed", "cancelled"}:
            exp.status = "done" if "failed" not in statuses else "partial"
            await db.commit()
