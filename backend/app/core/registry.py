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
    baseline_reward: float = 0.0  # reasonable threshold for convergence tracking
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
        baseline_reward=-110,
    ),
    "CartPole-v1": EnvMeta(
        env_id="CartPole-v1",
        name="CartPole",
        action_space="discrete",
        baseline_reward=195,
    ),
    "LunarLander-v2": EnvMeta(
        env_id="LunarLander-v2",
        name="Lunar Lander",
        action_space="discrete",
        baseline_reward=200,
    ),
    "Acrobot-v1": EnvMeta(
        env_id="Acrobot-v1",
        name="Acrobot",
        action_space="discrete",
        baseline_reward=-100,
    ),
    "Pendulum-v1": EnvMeta(
        env_id="Pendulum-v1",
        name="Pendulum",
        action_space="continuous",
        baseline_reward=-500,
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
    "DQN": AlgoMeta(
        algo_id="DQN",
        name="Deep Q-Network",
        discrete=True,
        continuous=False,
        default_hp={
            "learning_rate": 1e-4,
            "buffer_size": 100_000,
            "learning_starts": 1_000,
            "batch_size": 32,
            "tau": 1.0,
            "gamma": 0.99,
            "train_freq": 4,
            "gradient_steps": 1,
            "exploration_fraction": 0.1,
            "exploration_initial_eps": 1.0,
            "exploration_final_eps": 0.02,
        },
    ),
    "SAC": AlgoMeta(
        algo_id="SAC",
        name="Soft Actor-Critic",
        discrete=False,
        continuous=True,
        default_hp={
            "learning_rate": 3e-4,
            "buffer_size": 100_000,
            "learning_starts": 100,
            "batch_size": 256,
            "tau": 0.005,
            "gamma": 0.99,
            "train_freq": 1,
            "gradient_steps": 1,
            "ent_coef": "auto",
            "use_sde": False,
        },
    ),
    "BC": AlgoMeta(
        algo_id="BC",
        name="Behavioral Cloning",
        discrete=True,
        continuous=True,
        default_hp={
            "batch_size": 32,
            "l2_weight": 1e-4,
            "optimizer_kwargs": {"lr": 1e-3},
        },
    ),
}


def algo_supports_env(algo_id: str, env_id: str) -> bool:
    a = ALGO_REGISTRY[algo_id]
    e = ENV_REGISTRY[env_id]
    if e.action_space == "discrete":
        return a.discrete
    return a.continuous
