"""Pydantic v2 request/response schemas for the REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── PPO Hyperparameters ──────────────────────────────────────────────────────

class PPOHyper(BaseModel):
    learning_rate: float = Field(3e-4, ge=1e-6, le=1.0)
    n_steps: int = Field(2048, ge=16, le=8192)
    batch_size: int = Field(64, ge=8, le=2048)
    gamma: float = Field(0.99, ge=0.0, le=1.0)
    gae_lambda: float = Field(0.95, ge=0.0, le=1.0)
    ent_coef: float = Field(0.0, ge=0.0, le=1.0)
    clip_range: float = Field(0.2, ge=0.01, le=1.0)


# ── Experiment ────────────────────────────────────────────────────────────────

class ExperimentCreate(BaseModel):
    name: str = Field(default="Untitled")
    env_id: Literal["MountainCar-v0", "CartPole-v1"] = "MountainCar-v0"
    algo_id: Literal["PPO"] = "PPO"
    reward_ids: list[str] = Field(min_length=1, max_length=8)
    hyperparams: PPOHyper = PPOHyper()
    total_steps: int = Field(50_000, ge=1_000, le=2_000_000)
    seeds: list[int] = Field(default_factory=lambda: [0])


class RunSummary(BaseModel):
    id: str
    reward_id: str
    seed: int
    status: str
    hyperparams: dict
    final_metrics: dict
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
