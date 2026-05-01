"""Unified registry for environments, algorithms, and reward variants.

All capability matrices and compatibility checks live here so the API
layer never needs to hard-code env/algo/reward relationships.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EnvMeta:
    env_id: str
    name: str
    action_space: str  # "discrete" | "continuous"
    single_or_multi: str = "single"
    supports_render: bool = True


@dataclass
class AlgoMeta:
    algo_id: str
    name: str
    discrete: bool = False
    continuous: bool = False
    supports_multiagent: bool = False
    supports_offpolicy: bool = False
    default_hp: dict = field(default_factory=dict)


ENV_REGISTRY: dict[str, EnvMeta] = {
    "MountainCar-v0": EnvMeta(
        env_id="MountainCar-v0",
        name="Mountain Car",
        action_space="discrete",
    ),
    "CartPole-v1": EnvMeta(
        env_id="CartPole-v1",
        name="CartPole",
        action_space="discrete",
    ),
}

ALGO_REGISTRY: dict[str, AlgoMeta] = {
    "PPO": AlgoMeta(
        algo_id="PPO",
        name="Proximal Policy Optimization",
        discrete=True,
        continuous=True,
        default_hp={
            "learning_rate": 3e-4,
            "n_steps": 2048,
            "batch_size": 64,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "ent_coef": 0.0,
            "clip_range": 0.2,
        },
    ),
}


def algo_supports_env(algo_id: str, env_id: str) -> bool:
    a = ALGO_REGISTRY[algo_id]
    e = ENV_REGISTRY[env_id]
    if e.action_space == "discrete":
        return a.discrete
    return a.continuous
