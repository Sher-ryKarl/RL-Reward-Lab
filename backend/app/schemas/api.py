"""Pydantic v2 request/response schemas for the REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Experiment ────────────────────────────────────────────────────────────────

class ExperimentCreate(BaseModel):
    name: str = Field(default="Untitled")
    env_id: Literal["MountainCar-v0", "CartPole-v1", "LunarLander-v2", "Acrobot-v1", "Pendulum-v1"] = "MountainCar-v0"
    algo_id: Literal["PPO", "DQN", "SAC", "BC"] = "PPO"
    reward_ids: list[str] = Field(min_length=1, max_length=8)
    hyperparams: dict[str, Any] = Field(default_factory=dict)
    total_steps: int = Field(50_000, ge=100, le=2_000_000)
    seeds: list[int] = Field(default_factory=lambda: [0])
    # v0.5: BC cloning source
    demo_id: str | None = None
    # v0.2: Optional Optuna search
    optimize: bool = False
    search_space: dict = Field(default_factory=dict)
    n_trials: int = Field(30, ge=2, le=500)


# ── Demo (v0.5) ────────────────────────────────────────────────────────────────

class DemoCreate(BaseModel):
    name: str = Field(default="Untitled Demo")
    env_id: Literal["MountainCar-v0", "CartPole-v1", "LunarLander-v2", "Acrobot-v1", "Pendulum-v1"] = "MountainCar-v0"
    source_run_id: str | None = None
    n_episodes: int = Field(10, ge=1, le=100)
    min_timesteps: int = Field(10_000, ge=100, le=500_000)


class DemoSummary(BaseModel):
    id: str
    name: str
    env_id: str
    reward_id: str | None
    source_run_id: str | None
    n_episodes: int
    n_steps: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Optimization / HPO (v0.2) ─────────────────────────────────────────────────

class TrialResult(BaseModel):
    number: int
    value: float
    params: dict
    reward_id: str = ""


class PerRewardResult(BaseModel):
    best_value: float
    best_params: dict
    n_trials: int
    trials: list[TrialResult] = Field(default_factory=list)


class OptimizationResult(BaseModel):
    experiment_id: str
    n_trials: int
    best_value: float | None
    best_params: dict
    trials: list[TrialResult]
    status: str
    per_reward: dict[str, PerRewardResult] = Field(default_factory=dict)


class RunSummary(BaseModel):
    id: str
    reward_id: str
    seed: int
    status: str
    hyperparams: dict
    final_metrics: dict
    artifact_path: str | None = None
    started_at: datetime | None
    ended_at: datetime | None

    model_config = {"from_attributes": True}


class ExperimentSummary(BaseModel):
    id: str
    name: str
    env_id: str
    algo_id: str
    total_steps: int
    status: str
    created_at: datetime
    runs: list[RunSummary] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ExperimentList(BaseModel):
    items: list[ExperimentSummary]
    total: int
    page: int
    size: int


# ── SSE Event ─────────────────────────────────────────────────────────────────

class MetricEvent(BaseModel):
    run_id: str
    step: int
    wall_time: float
    metrics: dict[str, float]
    components: dict[str, float] | None = None
