from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.core.registry import algo_supports_env
from app.db.models import Experiment, Run as RunModel
from app.schemas.api import (
    ExperimentCreate,
    ExperimentList,
    ExperimentSummary,
    OptimizationResult,
    RunSummary,
    TrialResult,
)
from app.workers.hpo import run_sweep
from app.workers.scheduler import RUN_QUEUES, schedule_run

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


@router.post("", status_code=202, response_model=ExperimentSummary)
async def create_experiment(
    body: ExperimentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    if not algo_supports_env(body.algo_id, body.env_id):
        from app.core.registry import ENV_REGISTRY
        env_meta = ENV_REGISTRY.get(body.env_id)
        action = env_meta.action_space if env_meta else "unknown"
        raise HTTPException(
            400,
            f"Algorithm '{body.algo_id}' does not support '{body.env_id}' "
            f"({action} action space).",
        )

    # BC requires a demo
    hp = dict(body.hyperparams)
    if body.algo_id == "BC":
        if not body.demo_id:
            raise HTTPException(400, "BC requires a demo_id (clone source)")
        from app.db.models import Demo
        demo_result = await db.execute(select(Demo).where(Demo.id == body.demo_id))
        demo = demo_result.scalar_one_or_none()
        if not demo:
            raise HTTPException(404, f"Demo '{body.demo_id}' not found")
        if demo.env_id != body.env_id:
            raise HTTPException(
                400,
                f"Demo env '{demo.env_id}' does not match experiment env '{body.env_id}'",
            )
        hp["demo_path"] = demo.file_path

    exp = Experiment(
        name=body.name,
        env_id=body.env_id,
        algo_id=body.algo_id,
        total_steps=body.total_steps,
        status="pending",
    )
    db.add(exp)
    await db.flush()

    if body.optimize:
        # HPO mode: trials create Run records as they complete
        await db.commit()
        result = await db.execute(
            select(Experiment).options(selectinload(Experiment.runs)).where(Experiment.id == exp.id)
        )
        exp = result.scalar_one()

        reward_id = body.reward_ids[0]
        background_tasks.add_task(
            _execute_optimization,
            exp.id,
            body.search_space,
            body.n_trials,
            reward_id,
            hp,
        )
        return _exp_to_summary(exp)

    for reward_id in body.reward_ids:
        for seed in body.seeds:
            run = RunModel(
                experiment_id=exp.id,
                reward_id=reward_id,
                seed=seed,
                hyperparams=hp,
                status="pending",
            )
            db.add(run)

    await db.commit()
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


@router.get("/{exp_id}/optimization", response_model=OptimizationResult)
async def get_optimization(exp_id: str, db: AsyncSession = Depends(get_db)):
    q = (
        select(Experiment)
        .options(selectinload(Experiment.runs))
        .where(Experiment.id == exp_id)
    )
    result = await db.execute(q)
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(404, "Experiment not found")

    trials: list[TrialResult] = []
    best_value: float | None = None
    best_params: dict = {}
    for run in exp.runs:
        value = run.final_metrics.get("ep_rew_mean") if run.final_metrics else None
        trial = TrialResult(
            number=run.seed,
            value=value or 0.0,
            params=run.hyperparams or {},
        )
        trials.append(trial)
        if value is not None and (best_value is None or value > best_value):
            best_value = value
            best_params = run.hyperparams or {}

    return OptimizationResult(
        experiment_id=exp.id,
        n_trials=len(trials),
        best_value=best_value,
        best_params=best_params,
        trials=trials,
        status=exp.status,
    )


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
            except Exception as exc:
                import traceback
                print(f"[ERROR] Run {run_model.id} failed: {exc}")
                traceback.print_exc()
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


async def _execute_optimization(
    exp_id: str,
    search_space: dict,
    n_trials: int,
    reward_id: str,
    fixed_hp: dict,
) -> None:
    """Background task: run Optuna HPO sweep. run_sweep handles Run records and status."""
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

        env_id = exp.env_id
        algo_id = exp.algo_id
        total_steps = exp.total_steps

        exp.status = "running"
        await db.commit()

        try:
            await run_sweep(
                exp_id=exp_id,
                env_id=env_id,
                algo_id=algo_id,
                total_steps=total_steps,
                search_space=search_space,
                n_trials=n_trials,
                reward_id=reward_id,
                fixed_hp=fixed_hp,
            )
        except Exception as exc:
            import traceback

            print(f"[ERROR] Optimization {exp_id} failed: {exc}")
            traceback.print_exc()
            result = await db.execute(
                select(Experiment).where(Experiment.id == exp_id)
            )
            exp = result.scalar_one_or_none()
            if exp:
                exp.status = "failed"
                await db.commit()
