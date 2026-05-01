"""Domain schemas: EnvSpec, RewardSpec, AlgoSpec, RunSpec.

These are the four unified meta-objects that decouple the platform
from specific library implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EnvSpec:
    env_id: str
    api_standard: str  # "gymnasium"
    single_or_multi: str  # "single" | "multi"
    obs_space: str
    action_space: str  # "discrete" | "continuous"
    seedable: bool = True
    vectorizable: bool = True
    supports_render: bool = True

    def to_dict(self) -> dict:
        return {
            "env_id": self.env_id,
            "api_standard": self.api_standard,
            "single_or_multi": self.single_or_multi,
            "obs_space": self.obs_space,
            "action_space": self.action_space,
            "seedable": self.seedable,
            "vectorizable": self.vectorizable,
            "supports_render": self.supports_render,
        }


@dataclass
class RewardSpecMeta:
    id: str
    name: str
    description: str
    source_type: str  # "handcrafted" | "learned" | "hybrid"
    terms: list[str] = field(default_factory=list)
    requires_history: bool = False
    references: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_type": self.source_type,
            "terms": self.terms,
            "requires_history": self.requires_history,
            "references": self.references,
        }


@dataclass
class AlgoSpec:
    algo_id: str
    name: str
    backend: str  # "sb3"
    policy_type: str  # "MlpPolicy" | "CnnPolicy"
    supports_offpolicy: bool = False
    discrete: bool = False
    continuous: bool = False

    def to_dict(self) -> dict:
        return {
            "algo_id": self.algo_id,
            "name": self.name,
            "backend": self.backend,
            "policy_type": self.policy_type,
            "supports_offpolicy": self.supports_offpolicy,
            "discrete": self.discrete,
            "continuous": self.continuous,
        }
