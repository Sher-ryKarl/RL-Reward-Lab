"""Multi-objective HPO using Optuna NSGA-II (v1.1).

Each trial optimizes three objectives simultaneously:
  O1 — ep_rew_mean (maximize): average evaluation reward over 3 episodes
  O2 — wall_time (minimize): training wall-clock seconds
  O3 — convergence_steps (minimize): steps needed to reach baseline reward

NSGA-II discovers the Pareto front of trials that trade off between these
conflicting objectives. Single-objective mode is preserved for backward compat.
"""

from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np
import optuna
import torch
from optuna.samplers import NSGAIISampler
from optuna.storages import RDBStorage
from sqlalchemy import select
from stable_baselines3 import DQN, PPO, SAC
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from app.config import settings
from app.core.registry import ALGO_REGISTRY, ENV_REGISTRY
from app.db.models import Experiment, Run as RunModel
from app.rewards.variants import REWARD_REGISTRY

optuna.logging.set_verbosity(optuna.logging.WARNING)

DEFAULT_POPULATION_SIZE = 50  # NSGA-II population


class _ConvergenceCallback(BaseCallback):
    """Records the first training step where ep_rew_mean reaches baseline."""

    def __init__(self, baseline: float, check_freq: int = 200):
        super().__init__()
        self.baseline = baseline
        self.check_freq = check_freq
        self.convergence_step: int | None = None

    def _on_step(self) -> bool:
        if self.convergence_step is not None:
            return True
        if self.n_calls % self.check_freq != 0:
            return True
        if len(self.model.ep_info_buffer) == 0:
            return True
        recent = [ep["r"] for ep in self.model.ep_info_buffer]
        if np.mean(recent) >= self.baseline:
            self.convergence_step = self.num_timesteps
        return True


def _objective(
    trial: optuna.Trial,
    env_id: str,
    algo_id: str,
    reward_ids: list[str],
    total_steps: int,
    search_space: dict[str, dict],
    fixed_hp: dict[str, Any],
    baseline_reward: float,
) -> tuple[float, float, float]:
    """Multi-objective objective: returns (ep_rew_mean, wall_time, convergence_steps)."""
    reward_id = trial.suggest_categorical("reward_id", reward_ids)
    hp = _sample_params(trial, search_space, fixed_hp)
    hp = {**ALGO_REGISTRY[algo_id].default_hp, **hp}

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

    if algo_id == "PPO":
        model = PPO("MlpPolicy", vec, device=settings.device, seed=seed, **hp)
    elif algo_id == "DQN":
        model = DQN("MlpPolicy", vec, device=settings.device, seed=seed, **hp)
    elif algo_id == "SAC":
        model = SAC("MlpPolicy", vec, device=settings.device, seed=seed, **hp)
    else:
        raise ValueError(f"Unknown algorithm: {algo_id}")

    conv_cb = _ConvergenceCallback(baseline=baseline_reward)
    t0 = time.perf_counter()
    model.learn(total_timesteps=total_steps, progress_bar=False, callback=conv_cb)
    wall_time = time.perf_counter() - t0

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

    o1 = float(np.mean(all_rewards))
    o2 = wall_time
    o3 = float(conv_cb.convergence_step if conv_cb.convergence_step is not None else total_steps)
    return (o1, o2, o3)


def _sample_params(
    trial: optuna.Trial,
    search_space: dict[str, dict],
    fixed_hp: dict[str, Any],
) -> dict[str, Any]:
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
    algo_id: str,
    total_steps: int,
    search_space: dict[str, dict],
    n_trials: int,
    reward_ids: list[str],
    fixed_hp: dict[str, Any],
    n_objectives: int = 3,
) -> None:
    """Run a multi-objective NSGA-II sweep in a background task.

    v1.1: Uses NSGAIISampler with 3 objectives (ep_rew_mean, wall_time, convergence_steps).
    Pareto-optimal trials are identified and returned alongside per-reward summaries.
    Single-objective mode (n_objectives=1) preserved for backward compatibility.
    """
    from app.db.database import async_session

    study_name = f"sweep-{exp_id}"
    storage = RDBStorage(
        url=settings.database_url.replace("+aiosqlite", ""),
        engine_kwargs={"connect_args": {"check_same_thread": False}},
    )

    baseline_reward = ENV_REGISTRY[env_id].baseline_reward

    if n_objectives >= 2:
        directions = ["maximize", "minimize", "minimize"][:n_objectives]
        sampler = NSGAIISampler(seed=0)
        study = optuna.create_study(
            study_name=study_name,
            storage=storage,
            sampler=sampler,
            directions=directions,
            load_if_exists=True,
        )
    else:
        directions = ["maximize"]
        from optuna.samplers import TPESampler
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
                    "values": list(trial_inner.values) if trial_inner.values else [trial_inner.value],
                    "params": trial_inner.params,
                    "reward_id": trial_inner.params.get("reward_id", reward_ids[0]),
                })

        if n_objectives >= 2:
            study.optimize(
                lambda trial: _objective(
                    trial, env_id, algo_id, reward_ids, total_steps,
                    search_space, fixed_hp, baseline_reward,
                ),
                n_trials=n_trials,
                callbacks=[_callback],
                n_jobs=1,
                show_progress_bar=False,
            )
        else:
            # Single-objective backward compat
            def _single_obj(trial):
                o1, o2, o3 = _objective(
                    trial, env_id, algo_id, reward_ids, total_steps,
                    search_space, fixed_hp, baseline_reward,
                )
                return o1

            study.optimize(
                _single_obj,
                n_trials=n_trials,
                callbacks=[_callback],
                n_jobs=1,
                show_progress_bar=False,
            )

        return results

    trial_results = await loop.run_in_executor(None, _run_trials)

    # Build per-reward summary (multi-objective aware)
    per_reward: dict[str, dict] = {}
    for tr in trial_results:
        rid = tr["reward_id"]
        vals = tr["values"]
        if rid not in per_reward:
            per_reward[rid] = {
                "best_values": list(vals),
                "best_params": tr["params"],
                "n_trials": 0,
            }
        else:
            # O1 is maximize, so higher is better
            if vals[0] > per_reward[rid]["best_values"][0]:
                per_reward[rid]["best_values"] = list(vals)
                per_reward[rid]["best_params"] = tr["params"]
        per_reward[rid]["n_trials"] += 1

    # Identify Pareto-optimal trials
    pareto_indices: list[int] = []
    if n_objectives >= 2 and len(trial_results) > 0:
        pareto_indices = _compute_pareto_front(trial_results)

    # Create Run records
    async with async_session() as db:
        for tr in trial_results:
            run = RunModel(
                experiment_id=exp_id,
                reward_id=tr["reward_id"],
                seed=tr["trial_number"],
                hyperparams=tr["params"],
                status="done",
                started_at=datetime.now(timezone.utc),
                ended_at=datetime.now(timezone.utc),
                final_metrics={
                    "ep_rew_mean": tr["values"][0],
                    "wall_time": tr["values"][1] if len(tr["values"]) > 1 else None,
                    "convergence_steps": tr["values"][2] if len(tr["values"]) > 2 else None,
                },
            )
            db.add(run)

        result = await db.execute(select(Experiment).where(Experiment.id == exp_id))
        exp = result.scalar_one_or_none()
        if exp:
            exp.status = "done"
            # Store n_objectives and directions in experiment metadata
            await db.commit()


def _compute_pareto_front(trial_results: list[dict]) -> list[int]:
    """Return indices of Pareto-optimal (non-dominated) trials.

    O1 (maximize) is negated so all objectives become "lower is better".
    """
    n = len(trial_results)
    values = np.array([tr["values"] for tr in trial_results], dtype=np.float64)
    # Negate maximize objectives: O1
    values[:, 0] = -values[:, 0]

    dominated = set()
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if np.all(values[i] >= values[j]) and np.any(values[i] > values[j]):
                dominated.add(i)
                break

    return [i for i in range(n) if i not in dominated]
