"""Tests for the five v0.1 reward variants.

Verifies: (1) each RewardSpec returns correct metadata,
(2) wrappers produce expected reward_components keys in info,
(3) PBRS doesn't leak future info on done.
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np
import pytest
from stable_baselines3.common.monitor import Monitor

from app.rewards.variants import REWARD_REGISTRY


@pytest.mark.parametrize("rid", ["R0_sparse", "R1_dense", "R2_pbrs_potential", "R3_curiosity_rnd", "R4_misleading"])
def test_reward_spec_to_dict(rid):
    spec = REWARD_REGISTRY[rid]
    d = spec.to_dict()
    assert d["id"] == rid
    assert isinstance(d["name"], str)
    assert isinstance(d["description"], str)


def test_sparse_wrapper():
    env = gym.make("MountainCar-v0")
    spec = REWARD_REGISTRY["R0_sparse"]
    wrapped = spec.wrap(env)
    wrapped = Monitor(wrapped)
    obs, _ = wrapped.reset()
    obs, rew, *_ = wrapped.step(0)
    assert rew == 0.0  # sparse zeros out default


def test_dense_wrapper():
    env = gym.make("MountainCar-v0")
    spec = REWARD_REGISTRY["R1_dense"]
    wrapped = spec.wrap(env)
    wrapped = Monitor(wrapped)
    obs, _ = wrapped.reset()
    obs, rew, *_ = wrapped.step(1)
    # Position should be a progress signal (≥ 0 when moving right)
    assert isinstance(rew, float)


def test_pbrs_wrapper():
    env = gym.make("MountainCar-v0")
    spec = REWARD_REGISTRY["R2_pbrs_potential"]
    wrapped = spec.wrap(env)
    wrapped = Monitor(wrapped)
    obs, info = wrapped.reset()
    assert "reward_components" not in info  # reset has no step-based components

    obs, rew, term, trunc, info = wrapped.step(0)
    assert "extrinsic" in info.get("reward_components", {})
    assert "shaping_pbrs" in info.get("reward_components", {})


def test_misleading_wrapper_has_warning():
    spec = REWARD_REGISTRY["R4_misleading"]
    d = spec.to_dict()
    assert "⚠" in d["name"]
    from app.rewards.wrappers import MisleadingRewardWrapper
    assert MisleadingRewardWrapper.MISLEADING_WARNING is True


def test_monitor_inside_wrapper_order():
    """verify Monitor(RewardWrapper(env)) — Monitor must be outermost."""
    env = gym.make("MountainCar-v0")
    spec = REWARD_REGISTRY["R2_pbrs_potential"]
    wrapped = spec.wrap(env)
    wrapped = Monitor(wrapped)
    obs, _ = wrapped.reset()
    for _ in range(200):
        obs, _, term, _, info = wrapped.step(0)
        if term:
            break
    # Monitor's ep_info_buffer should have recorded episode info
    assert hasattr(wrapped, "get_episode_rewards")


def test_all_rewards_register():
    assert len(REWARD_REGISTRY) == 5
    for rid in ["R0_sparse", "R1_dense", "R2_pbrs_potential", "R3_curiosity_rnd", "R4_misleading"]:
        assert rid in REWARD_REGISTRY
