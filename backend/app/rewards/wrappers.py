"""Gymnasium wrappers for reward shaping.

All wrappers follow the rule: Monitor(RewardWrapper(env))
so that SB3's Monitor captures the *extrinsic* reward in ep_rew_mean.
"""

from __future__ import annotations

from collections.abc import Callable

import gymnasium as gym
import numpy as np


class PBRSWrapper(gym.Wrapper):
    """Potential-based reward shaping (Ng, Harada & Russell, 1999).

    r' = r + gamma * Phi(s') - Phi(s)

    Policy-invariant under standard discount MDP conditions.
    """

    def __init__(self, env: gym.Env, potential_fn: Callable, gamma: float = 0.99):
        super().__init__(env)
        self.phi = potential_fn
        self.gamma = gamma
        self._prev_phi: float = 0.0

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self._prev_phi = float(self.phi(obs))
        return obs, info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        phi_next = float(self.phi(obs))
        # Setting shaping to 0 on done avoids "peeking" at the next episode's state.
        # The terminal_observation in info is available for evaluation.
        if terminated or truncated:
            shaping = 0.0
        else:
            shaping = self.gamma * phi_next - self._prev_phi
        self._prev_phi = phi_next

        components = info.setdefault("reward_components", {})
        components["extrinsic"] = float(reward)
        components["shaping_pbrs"] = float(shaping)
        return obs, reward + shaping, terminated, truncated, info


class SparseWrapper(gym.Wrapper):
    """Zero out the default dense reward; only keep the extrinsic at done."""

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        components = info.setdefault("reward_components", {})
        components["extrinsic"] = float(reward)
        return obs, 0.0, terminated, truncated, info


class DenseProgressWrapper(gym.Wrapper):
    """Replace reward with a custom progress signal."""

    def __init__(self, env: gym.Env, progress_fn: Callable):
        super().__init__(env)
        self.progress_fn = progress_fn

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        r = self.progress_fn(obs, reward, terminated, truncated)
        components = info.setdefault("reward_components", {})
        components["extrinsic"] = float(reward)
        components["progress"] = float(r)
        return obs, r, terminated, truncated, info


class MisleadingRewardWrapper(gym.Wrapper):
    """Intentionally wrong reward — for demonstrating reward hacking."""

    MISLEADING_WARNING = True  # checked by the API layer

    def __init__(self, env: gym.Env, misleading_fn: Callable):
        super().__init__(env)
        self.misleading_fn = misleading_fn

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        r = self.misleading_fn(obs, reward, terminated, truncated)
        components = info.setdefault("reward_components", {})
        components["extrinsic"] = float(reward)
        components["misleading"] = float(r)
        return obs, r, terminated, truncated, info
