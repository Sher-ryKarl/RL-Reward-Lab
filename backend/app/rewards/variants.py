"""Five reward variants for v0.1 — all on MountainCar/CartPole.

R0_sparse        – baseline, demonstrate "untrainable without shaping"
R1_dense         – hand-crafted progress signal
R2_pbrs_potential – policy-invariant potential-based shaping
R3_curiosity_rnd  – intrinsic motivation via RND
R4_misleading     – deliberate anti-example (reward hacking demo)
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np

from app.rewards.base import RewardSpec
from app.rewards.wrappers import (
    DenseProgressWrapper,
    MisleadingRewardWrapper,
    PBRSWrapper,
    SparseWrapper,
)


# ── R0: Sparse ────────────────────────────────────────────────────────────────

class SparseReward(RewardSpec):
    id = "R0_sparse"
    name = "Sparse (终局成功)"
    description = "仅成功到达旗子时 +1，其余为 0。演示稀疏奖励在 MountainCar 上训练困难。"
    source_type = "handcrafted"
    terms = ["extrinsic"]
    references = []

    def wrap(self, env: gym.Env) -> gym.Env:
        return SparseWrapper(env)


# ── R1: Dense Progress ───────────────────────────────────────────────────────

class DenseReward(RewardSpec):
    id = "R1_dense"
    name = "Dense (进度信号)"
    description = "r = position - min_position，用位置进度作为稠密代理信号。"
    source_type = "handcrafted"
    terms = ["extrinsic", "progress"]
    references = []

    def wrap(self, env: gym.Env) -> gym.Env:
        return DenseProgressWrapper(
            env,
            progress_fn=lambda obs, r, t, tr: float(obs[0] + 1.2),
        )


# ── R2: PBRS ──────────────────────────────────────────────────────────────────

class PBRSReward(RewardSpec):
    id = "R2_pbrs_potential"
    name = "PBRS (势函数塑形)"
    description = "Φ(s) = position + 0.5·velocity²，理论上不改变最优策略 (Ng & Russell 1999)。"
    source_type = "handcrafted"
    terms = ["extrinsic", "shaping_pbrs"]
    references = ["Ng, Harada & Russell, ICML 1999"]

    def wrap(self, env: gym.Env) -> gym.Env:
        def phi(obs):
            return float(obs[0] + 0.5 * obs[1] ** 2)

        return PBRSWrapper(env, phi, gamma=0.99)


# ── R3: Curiosity (RND) ──────────────────────────────────────────────────────

class CuriosityRNDReward(RewardSpec):
    id = "R3_curiosity_rnd"
    name = "Curiosity (RND 内在动机)"
    description = "r' = r_sparse + β·||f_θ(s) − f̂_φ(s)||²，探索而非奖励塑形。"
    source_type = "handcrafted"
    terms = ["extrinsic", "intrinsic_rnd"]
    references = ["Burda et al., ICLR 2019"]

    def wrap(self, env: gym.Env) -> gym.Env:
        """Wrap with Sparse then attach RND via RLeXplore callback.

        The intrinsic reward injection happens in the training worker
        via the RLeXplore callback, not in the env wrapper, because
        RND needs access to the RL model's internal state.
        """
        return SparseWrapper(env)


# ── R4: Misleading ───────────────────────────────────────────────────────────

class MisleadingReward(RewardSpec):
    id = "R4_misleading"
    name = "⚠ Misleading (教学反例)"
    description = "奖励 |速度| 而非到达终点——agent 学会来回晃动刷分而不完成任务。需在 UI 显式警告。"
    source_type = "handcrafted"
    terms = ["extrinsic", "misleading"]
    references = []

    def wrap(self, env: gym.Env) -> gym.Env:
        return MisleadingRewardWrapper(
            env,
            misleading_fn=lambda obs, r, t, tr: float(abs(obs[1])),
        )


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
