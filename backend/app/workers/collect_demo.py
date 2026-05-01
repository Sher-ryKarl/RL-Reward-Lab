"""Collect expert demonstration trajectories from a trained PPO agent."""

from __future__ import annotations

import random
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
from imitation.data import rollout, serialize, types
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from app.config import settings
from app.rewards.variants import REWARD_REGISTRY


def collect_demo(
    run_id: str,
    env_id: str,
    reward_id: str,
    n_episodes: int = 10,
    min_timesteps: int = 10_000,
) -> tuple[Path, int, int]:
    """Collect expert trajectories from a trained PPO checkpoint.

    Returns (file_path, n_episodes_recorded, total_steps).
    """
    checkpoint = Path(settings.data_dir) / "checkpoints" / f"{run_id}.zip"
    if not checkpoint.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint}")

    spec = REWARD_REGISTRY[reward_id]

    def make_env():
        e = gym.make(env_id)
        e = spec.wrap(e, env_id=env_id)
        e = Monitor(e)
        return e

    # Seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)

    venv = DummyVecEnv([make_env])

    # Load PPO model to extract policy
    model = PPO.load(str(checkpoint), device="cpu")
    policy = model.policy

    # Collect trajectories
    trajectories = rollout.rollout(
        policy,
        venv,
        rollout.make_sample_until(min_timesteps=min_timesteps, min_episodes=n_episodes),
        rng=np.random.default_rng(42),
        unwrap=False,
    )

    venv.close()

    # Serialize
    demo_dir = Path(settings.data_dir) / "demos"
    demo_dir.mkdir(parents=True, exist_ok=True)
    file_path = demo_dir / f"{run_id}.npz"
    serialize.save(str(file_path), trajectories)

    return file_path, len(trajectories), sum(len(t.obs) for t in trajectories)
