"""RewardSpec abstract base — the unified reward interface.

Every reward variant is a RewardSpec subclass that knows:
1. How to wrap an environment to modify the step() return reward
2. How to expose per-term components in info["reward_components"]
3. Its own metadata (id, description, references)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import gymnasium as gym


class RewardSpec(ABC):
    id: str
    name: str
    description: str
    source_type: str = "handcrafted"
    terms: list[str] = []
    references: list[str] = []

    @abstractmethod
    def wrap(self, env: gym.Env) -> gym.Env:
        """Wrap the env so step() returns the modified reward."""
        ...

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_type": self.source_type,
            "terms": self.terms,
            "references": self.references,
        }
