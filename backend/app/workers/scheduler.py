"""Lightweight async scheduler using asyncio.Semaphore + ProcessPoolExecutor.

Architecture (避坑 #4 from 技术栈选型.md):
- Training runs in a subprocess (ProcessPoolExecutor)
- Subprocess writes metrics via a Manager-based Queue (picklable on Windows spawn)
- A background asyncio task drains the mp.Queue → asyncio.Queue
- SSE endpoint reads from asyncio.Queue

Windows note: mp.Queue() is NOT picklable under "spawn" start method.
mp.Manager().Queue() proxies ARE picklable, solving the cross-process issue.
"""

from __future__ import annotations

import asyncio
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

from app.config import settings
from app.db.models import Experiment, Run as RunModel

MAX_CPU_WORKERS = max(1, (mp.cpu_count() or 4) - 2)
executor = ProcessPoolExecutor(max_workers=MAX_CPU_WORKERS)

# Shared manager — lives for the lifetime of the process
_manager = mp.Manager()

# Per-run asyncio queues that the SSE route consumes
RUN_QUEUES: dict[str, asyncio.Queue] = {}

# Semaphore to limit concurrent training runs
_run_semaphore = asyncio.Semaphore(
    min(settings.max_concurrent_runs, MAX_CPU_WORKERS)
)

# Background task that bridges Manager.Queue → asyncio.Queue
_bridge_tasks: dict[str, asyncio.Task] = {}


async def _bridge(mp_queue, async_queue: asyncio.Queue, run_id: str) -> None:
    """Drain a Manager().Queue into an asyncio.Queue."""
    loop = asyncio.get_running_loop()
    while True:
        try:
            msg = await loop.run_in_executor(
                None,
                lambda: mp_queue.get(timeout=1.0),
            )
            if msg is None:  # sentinel
                break
            await async_queue.put(msg)
        except Exception:
            # Timeout or empty — keep polling
            continue


async def schedule_run(
    run_model: RunModel,
    experiment: Experiment,
    queue: asyncio.Queue,
) -> None:
    """Submit a single training run; blocks until the semaphore is available."""
    from app.workers.run_one import run_one

    mp_queue = _manager.Queue(maxsize=500)

    async with _run_semaphore:
        run_model.status = "running"

        bridge_task = asyncio.create_task(_bridge(mp_queue, queue, run_model.id))
        _bridge_tasks[run_model.id] = bridge_task

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                executor,
                run_one,
                run_model.id,
                experiment.env_id,
                run_model.reward_id,
                experiment.algo_id,
                run_model.hyperparams,
                experiment.total_steps,
                run_model.seed,
                mp_queue,
            )
        except Exception:
            run_model.status = "failed"
            raise
        finally:
            try:
                mp_queue.put(None, timeout=1.0)
            except Exception:
                pass
            bridge_task.cancel()
            _bridge_tasks.pop(run_model.id, None)
