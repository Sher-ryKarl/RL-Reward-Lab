"""Single training run — executed in a subprocess.

mlflow must NOT be initialized in the main process before fork;
each subprocess starts its own MLflow run.
"""

from __future__ import annotations

import random
from multiprocessing import Queue
from pathlib import Path

import gymnasium as gym
import mlflow
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecVideoRecorder
from app.config import settings
from app.rewards.variants import REWARD_REGISTRY
from app.rewards.rnd import RNDCallback
from app.workers.callbacks import StreamCallback


def run_one(
    run_id: str,
    env_id: str,
    reward_id: str,
    algo: str,
    hp: dict,
    total_steps: int,
    seed: int,
    queue: Queue,
) -> None:
    spec = REWARD_REGISTRY[reward_id]

    def make_env():
        e = gym.make(env_id, render_mode="rgb_array")
        e = spec.wrap(e)
        e = Monitor(e)
        return e

    # Seed everything
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if not torch.cuda.is_available():
        torch.use_deterministic_algorithms(True)

    vec = DummyVecEnv([make_env])

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    with mlflow.start_run(run_name=run_id):
        mlflow.log_params({
            "env": env_id,
            "algo": algo,
            "reward": reward_id,
            "total_steps": total_steps,
            "seed": seed,
            **hp,
        })
        mlflow.log_dict(spec.to_dict(), "reward_spec.json")

        model = PPO(
            "MlpPolicy",
            vec,
            device=settings.device,
            tensorboard_log=str(settings.data_dir / "tb" / run_id),
            seed=seed,
            **hp,
        )

        callback = StreamCallback(
            queue, run_id=run_id, reward_id=reward_id, every=1000
        )

        # R3_curiosity_rnd: wire up RND intrinsic reward callback
        cb_list = [callback]
        if reward_id == "R3_curiosity_rnd":
            rnd_cb = RNDCallback(
                env=vec,
                intrinsic_coef=0.1,
                update_normalize=True,
                verbose=1,
            )
            cb_list.insert(0, rnd_cb)

        model.learn(total_timesteps=total_steps, callback=cb_list)

        # Save model
        model_path = Path(settings.data_dir) / "checkpoints" / f"{run_id}.zip"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save(str(model_path))
        mlflow.log_artifact(str(model_path))

        # Record replay video
        video_path = _record_replay(env_id, spec, model, run_id)
        if video_path:
            mlflow.log_artifact(str(video_path))

        queue.put({
            "run_id": run_id,
            "reward_id": reward_id,
            "step": total_steps,
            "wall_time": 0,
            "metrics": {"status": "done", "artifact": str(model_path)},
            "components": None,
        })


def _record_replay(env_id: str, spec, model: PPO, run_id: str) -> Path | None:
    """Record a 30s replay video using VecVideoRecorder."""
    try:
        eval_env = DummyVecEnv([
            lambda: Monitor(spec.wrap(gym.make(env_id, render_mode="rgb_array")))
        ])
        video_dir = Path(settings.data_dir) / "videos"
        video_dir.mkdir(parents=True, exist_ok=True)
        eval_env = VecVideoRecorder(
            eval_env,
            str(video_dir / run_id),
            record_video_trigger=lambda x: x == 0,
            video_length=600,  # frames
        )
        obs = eval_env.reset()
        for _ in range(600):
            action, _ = model.predict(obs, deterministic=True)
            obs, _, done, _ = eval_env.step(action)
            if done.any():
                break
        eval_env.close()

        video_file = video_dir / run_id / "step-0-to-step-600.mp4"
        if video_file.exists():
            return video_file
        return None
    except Exception:
        return None
