"""Optuna-based hyperparameter optimization for v0.2.

Each trial = one training run. The study runs in-process via study.optimize().
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import optuna
import torch
from optuna.samplers import TPESampler
from optuna.storages import RDBStorage
from sqlalchemy import select
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from app.config import settings
from app.db.models import Experiment, Run as RunModel
from app.rewards.variants import REWARD_REGISTRY

optuna.logging.set_verbosity(optuna.logging.WARNING)


def _objective(
    trial: optuna.Trial,
    env_id: str,
    reward_id: str,
    total_steps: int,
    search_space: dict[str, dict],
    fixed_hp: dict[str, Any],
) -> float:
    """Optuna objective: sample → train → return eval reward."""
    hp = _sample_params(trial, search_space, fixed_hp)

    spec = REWARD_REGISTRY[reward_id]

    import gymnasium

    def make():
        e = gymnasium.make(env_id)
        e = spec.wrap(e, env_id=env_id)
        e = Monitor(e)
        return e

    vec = DummyVecEnv([make])
    seed = trial.number
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    model = PPO(
        "MlpPolicy",
        vec,
        device=settings.device,
        seed=seed,
        learning_rate=hp.get("learning_rate", 3e-4),
        n_steps=hp.get("n_steps", 2048),
        batch_size=hp.get("batch_size", 64),
        gamma=hp.get("gamma", 0.99),
        gae_lambda=hp.get("gae_lambda", 0.95),
        ent_coef=hp.get("ent_coef", 0.0),
        clip_range=hp.get("clip_range", 0.2),
    )

    model.learn(total_timesteps=total_steps, progress_bar=False)

    # Evaluate with 3 episodes
    eval_env = DummyVecEnv([make])
    all_rewards = []
    for _ in range(3):
        obs = eval_env.reset()
        ep_rew = 0.0
        while True:
            action, _ = model.predict(obs, deterministic=True)
            obs, rew, done, _ = eval_env.step(action)
            ep_rew += rew[0]
            if done.any():
                break
        all_rewards.append(ep_rew)

    return float(np.mean(all_rewards))


def _sample_params(
    trial: optuna.Trial,
    search_space: dict[str, dict],
    fixed_hp: dict[str, Any],
) -> dict[str, Any]:
    """Sample hyperparameters from the Optuna search space."""
    hp: dict[str, Any] = {}
    for name, spec in search_space.items():
        dist = spec.get("type", "float")
        if dist == "loguniform":
            hp[name] = trial.suggest_float(name, spec["low"], spec["high"], log=True)
        elif dist == "uniform":
            hp[name] = trial.suggest_float(name, spec["low"], spec["high"])
        elif dist == "int":
            hp[name] = trial.suggest_int(name, spec["low"], spec["high"])
        elif dist == "categorical":
            hp[name] = trial.suggest_categorical(name, spec["choices"])
        elif dist == "discrete_uniform":
            hp[name] = trial.suggest_discrete_uniform(name, spec["low"], spec["high"], spec.get("q", 1.0))
    for name, val in fixed_hp.items():
        hp.setdefault(name, val)
    return hp


async def run_sweep(
    exp_id: str,
    env_id: str,
    total_steps: int,
    search_space: dict[str, dict],
    n_trials: int,
    reward_id: str,
    fixed_hp: dict[str, Any],
) -> None:
    """Run an Optuna sweep in a background task. Updates Run models as trials complete."""
    from app.db.database import async_session

    study_name = f"sweep-{exp_id}"
    storage = RDBStorage(
        url=settings.database_url.replace("+aiosqlite", ""),
        engine_kwargs={"connect_args": {"check_same_thread": False}},
    )

    study = optuna.create_study(
        study_name=study_name,
        storage=storage,
        sampler=TPESampler(seed=0, multivariate=True),
        direction="maximize",
        load_if_exists=True,
    )

    loop = asyncio.get_running_loop()

    def _run_trials() -> list[dict]:
        results = []

        def _callback(study_inner, trial_inner):
            if trial_inner.state == optuna.trial.TrialState.COMPLETE:
                results.append({
                    "trial_number": trial_inner.number,
                    "value": trial_inner.value,
                    "params": trial_inner.params,
                })

        study.optimize(
            lambda trial: _objective(
                trial,
                env_id,
                reward_id,
                total_steps,
                search_space,
                fixed_hp,
            ),
            n_trials=n_trials,
            callbacks=[_callback],
            n_jobs=1,
            show_progress_bar=False,
        )
        return results

    # Run in thread pool (Optuna's RDBStorage + sqlite3 is synchronous)
    trial_results = await loop.run_in_executor(None, _run_trials)

    # Create Run records for each completed trial
    async with async_session() as db:
        for tr in trial_results:
            run = RunModel(
                experiment_id=exp_id,
                reward_id=reward_id,
                seed=tr["trial_number"],
                hyperparams=tr["params"],
                status="done",
                started_at=datetime.now(timezone.utc),
                ended_at=datetime.now(timezone.utc),
                final_metrics={"ep_rew_mean": tr["value"]},
            )
            db.add(run)

        # Update experiment status
        result = await db.execute(
            select(Experiment).where(Experiment.id == exp_id)
        )
        exp = result.scalar_one_or_none()
        if exp:
            exp.status = "done"
            await db.commit()
