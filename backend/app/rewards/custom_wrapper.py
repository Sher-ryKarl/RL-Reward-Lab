"""Wrapper that replaces reward with a user-defined function."""

from __future__ import annotations

import gymnasium as gym

from app.core.reward_editor import get as _get_custom_reward


class CustomRewardWrapper(gym.Wrapper):
    """Replaces step reward with user_fn(obs, reward, terminated, truncated)."""

    def __init__(self, env: gym.Env, reward_id: str):
        super().__init__(env)
        entry = _get_custom_reward(reward_id)
        if not entry:
            raise ValueError(f"Custom reward '{reward_id}' not found in registry")
        code = entry["code"]
        namespace: dict = {}
        exec(compile(code, "<reward_fn>", "exec"), namespace)
        self._fn = namespace["reward_fn"]

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        try:
            custom = self._fn(obs, reward, terminated, truncated)
            return obs, float(custom), terminated, truncated, info
        except Exception:
            # Fallback to original reward on user-code error
            return obs, float(reward), terminated, truncated, info
