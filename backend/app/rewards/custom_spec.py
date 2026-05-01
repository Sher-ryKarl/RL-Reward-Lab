"""CustomRewardSpec — a RewardSpec backed by user-submitted code."""

from __future__ import annotations

import gymnasium as gym

from app.rewards.base import RewardSpec
from app.rewards.custom_wrapper import CustomRewardWrapper


class CustomRewardSpec(RewardSpec):
    """Thin spec that wraps env with the user-defined reward function."""

    def __init__(self, reward_id: str, name: str, code: str):
        self.id = reward_id
        self.name = name
        self.description = f"Custom reward: {name}"
        self.source_type = "custom"
        self.terms = ["extrinsic"]
        self.references = []
        self._code = code

    def wrap(self, env: gym.Env, env_id: str = "") -> gym.Env:
        return CustomRewardWrapper(env, self.id)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["code"] = self._code
        return d
