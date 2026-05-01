"""Minimal RND (Random Network Distillation) for curiosity-driven exploration.

Based on Burda et al., ICLR 2019.
Integrates as an SB3 callback — no external rlexplore dependency needed for v0.1.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import VecEnv


class RNDNetwork(nn.Module):
    """Tiny MLP: target (fixed, random) and predictor (trainable)."""

    def __init__(self, input_dim: int, hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class RNDCallback(BaseCallback):
    """SB3 callback that adds RND intrinsic reward to VecEnv step returns.

    Architecture:
    - target_net: randomly initialized, NEVER trained
    - predictor_net: trained via MSE to match target_net output
    - intrinsic_reward = ||target(s) - predictor(s)||²
    """

    def __init__(
        self,
        env: VecEnv,
        lr: float = 1e-4,
        intrinsic_coef: float = 0.1,
        update_normalize: bool = True,
        verbose: int = 0,
    ):
        super().__init__(verbose)
        obs_shape = env.observation_space.shape
        input_dim = int(np.prod(obs_shape))

        self.target_net = RNDNetwork(input_dim)
        self.predictor_net = RNDNetwork(input_dim)
        # Freeze target
        for p in self.target_net.parameters():
            p.requires_grad = False

        self.optimizer = torch.optim.Adam(self.predictor_net.parameters(), lr=lr)
        self.intrinsic_coef = intrinsic_coef
        self.update_normalize = update_normalize

        # Running stats for normalization
        self._running_mean: float = 0.0
        self._running_std: float = 1.0
        self._ema = 0.99

    def _on_step(self) -> bool:
        # Get latest observations from the VecEnv
        obs = self.model.env.get_attr("last_obs")[0]
        if obs is None:
            return True

        obs_t = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            target = self.target_net(obs_t)
        pred = self.predictor_net(obs_t)
        intr = (target - pred).pow(2).mean(dim=-1).item()

        # Normalize
        if self.update_normalize:
            self._running_mean = self._ema * self._running_mean + (1 - self._ema) * intr
            self._running_std = self._ema * self._running_std + (1 - self._ema) * abs(
                intr - self._running_mean
            )
            intr_norm = (intr - self._running_mean) / max(self._running_std, 1e-8)
        else:
            intr_norm = intr

        # Inject into env's reward buffer for this step
        intrinsic = self.intrinsic_coef * intr_norm
        buf = self.model.env.get_attr("buf_rews")[0]
        if buf is not None:
            idx = getattr(self.model.env, "step_idx", 0) % len(buf)
            buf[idx] += intrinsic

        # Train predictor
        self.optimizer.zero_grad()
        pred2 = self.predictor_net(obs_t)
        loss = nn.functional.mse_loss(pred2, target)
        loss.backward()
        self.optimizer.step()

        return True
