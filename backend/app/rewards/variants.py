"""Reward variants — env-aware for MountainCar, CartPole, LunarLander, Acrobot.

R0_sparse          – baseline, demonstrate "untrainable without shaping"
R1_dense           – hand-crafted progress signal (varies per env)
R2_pbrs_potential  – policy-invariant potential-based shaping (varies per env)
R3_curiosity_rnd   – intrinsic motivation via RND
R4_misleading      – deliberate anti-example (reward hacking demo)
"""

from __future__ import annotations

import gymnasium as gym

from app.rewards.base import RewardSpec
from app.rewards.wrappers import (
    DenseProgressWrapper,
    MisleadingRewardWrapper,
    PBRSWrapper,
    SparseWrapper,
)


def _progress_fn(env_id: str):
    """Return a progress function for DenseProgressWrapper."""
    if env_id == "LunarLander-v2":
        return lambda obs, r, t, tr: float(obs[1])  # altitude
    if env_id == "Acrobot-v1":
        # tip height = -cos(θ1) - cos(θ1+θ2)
        return lambda obs, r, t, tr: float(
            -obs[0] - (obs[0] * obs[2] - obs[1] * obs[3])
        )
    # MountainCar-v0 / CartPole-v1: position
    return lambda obs, r, t, tr: float(obs[0] + 1.2)


def _phi_fn(env_id: str):
    """Return a potential function Phi(s) for PBRSWrapper."""
    if env_id == "LunarLander-v2":
        def phi(obs):
            return float(obs[1] + 0.3 * (1.0 - abs(obs[4])))

        return phi
    if env_id == "Acrobot-v1":
        # tip height = -cos(θ1) - cos(θ1+θ2)
        def phi(obs):
            return float(-obs[0] - (obs[0] * obs[2] - obs[1] * obs[3]))

        return phi
    # MountainCar-v0 / CartPole-v1: position + kinetic energy
    def phi(obs):
        return float(obs[0] + 0.5 * obs[1] ** 2)

    return phi


def _misleading_fn(env_id: str):
    """Return a misleading reward function."""
    if env_id == "LunarLander-v2":
        # reward total speed → encourages crashing instead of careful landing
        return lambda obs, r, t, tr: float(abs(obs[2]) + abs(obs[3]))
    if env_id == "Acrobot-v1":
        # reward angular velocity magnitude → encourages spastic motion
        return lambda obs, r, t, tr: float(abs(obs[4]) + abs(obs[5]))
    # MountainCar-v0 / CartPole-v1: reward |velocity|
    return lambda obs, r, t, tr: float(abs(obs[1]))


# ── R0: Sparse ────────────────────────────────────────────────────────────────

class SparseReward(RewardSpec):
    id = "R0_sparse"
    name = "Sparse (终局成功)"
    description = "仅成功到达目标时 +1，其余为 0。演示稀疏奖励训练困难。"
    source_type = "handcrafted"
    terms = ["extrinsic"]
    references = []

    def wrap(self, env: gym.Env, env_id: str = "") -> gym.Env:
        return SparseWrapper(env)


# ── R1: Dense Progress ───────────────────────────────────────────────────────

class DenseReward(RewardSpec):
    id = "R1_dense"
    name = "Dense (进度信号)"
    description = "MC: r = position + 1.2; LL: r = altitude。用位置/高度作为稠密代理信号。"
    source_type = "handcrafted"
    terms = ["extrinsic", "progress"]
    references = []

    def wrap(self, env: gym.Env, env_id: str = "") -> gym.Env:
        return DenseProgressWrapper(env, _progress_fn(env_id))


# ── R2: PBRS ──────────────────────────────────────────────────────────────────

class PBRSReward(RewardSpec):
    id = "R2_pbrs_potential"
    name = "PBRS (势函数塑形)"
    description = "MC: Φ(s)=position+0.5v²; LL: Φ(s)=altitude+0.3·uprightness。策略不变性塑形。"
    source_type = "handcrafted"
    terms = ["extrinsic", "shaping_pbrs"]
    references = ["Ng, Harada & Russell, ICML 1999"]

    def wrap(self, env: gym.Env, env_id: str = "") -> gym.Env:
        return PBRSWrapper(env, _phi_fn(env_id), gamma=0.99)


# ── R3: Curiosity (RND) ──────────────────────────────────────────────────────

class CuriosityRNDReward(RewardSpec):
    id = "R3_curiosity_rnd"
    name = "Curiosity (RND 内在动机)"
    description = "r' = r_sparse + β·||f_θ(s) − f̂_φ(s)||²，探索而非奖励塑形。"
    source_type = "handcrafted"
    terms = ["extrinsic", "intrinsic_rnd"]
    references = ["Burda et al., ICLR 2019"]

    def wrap(self, env: gym.Env, env_id: str = "") -> gym.Env:
        return SparseWrapper(env)


# ── R4: Misleading ───────────────────────────────────────────────────────────

class MisleadingReward(RewardSpec):
    id = "R4_misleading"
    name = "⚠ Misleading (教学反例)"
    description = "MC: 奖励|速度|; LL: 奖励总速率。agent 学到刷分而非完成任务。需在 UI 显式警告。"
    source_type = "handcrafted"
    terms = ["extrinsic", "misleading"]
    references = []

    def wrap(self, env: gym.Env, env_id: str = "") -> gym.Env:
        return MisleadingRewardWrapper(env, _misleading_fn(env_id))


# ── Registry ──────────────────────────────────────────────────────────────────

REWARD_REGISTRY: dict[str, RewardSpec] = {
    s.id: s
    for s in [
        SparseReward(),
        DenseReward(),
        PBRSReward(),
        CuriosityRNDReward(),
        MisleadingReward(),
    ]
}

REWARD_REGISTRY_V1 = REWARD_REGISTRY  # alias for future versioning
