"""Callbacks for streaming metrics during training."""

from __future__ import annotations

import time
import uuid
from multiprocessing import Queue

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback


class StreamCallback(BaseCallback):
    """Push per-episode metrics to an mp.Queue every N steps."""

    def __init__(
        self,
        queue: Queue,
        run_id: str,
        reward_id: str,
        every: int = 1000,
        verbose: int = 0,
    ):
        super().__init__(verbose)
        self.q = queue
        self.run_id = run_id
        self.reward_id = reward_id
        self.every = every

    def _on_step(self) -> bool:
        if self.num_timesteps % self.every != 0:
            return True
        ep_info = self.model.ep_info_buffer
        if not ep_info:
            return True

        r_vals = [e["r"] for e in ep_info]
        l_vals = [e["l"] for e in ep_info]
        metrics = {
            "ep_rew_mean": float(np.mean(r_vals)),
            "ep_rew_std": float(np.std(r_vals)) if len(r_vals) > 1 else 0.0,
            "ep_len_mean": float(np.mean(l_vals)),
            "ep_len_std": float(np.std(l_vals)) if len(l_vals) > 1 else 0.0,
        }

        # PPO-specific training health
        if hasattr(self.model, "logger") and hasattr(self.model.logger, "name_to_value"):
            n2v = self.model.logger.name_to_value
            for key in ("train/approx_kl", "train/entropy_loss", "train/value_loss", "train/explained_variance"):
                if key in n2v:
                    metrics[key.replace("train/", "")] = float(n2v[key])

        self.q.put({
            "run_id": self.run_id,
            "reward_id": self.reward_id,
            "step": self.num_timesteps,
            "wall_time": time.time(),
            "metrics": metrics,
            "components": None,  # filled by env info
        })
        return True
