from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


class Experiment(Base):
    __tablename__ = "experiment"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    env_id: Mapped[str] = mapped_column(String(64), nullable=False)
    algo_id: Mapped[str] = mapped_column(String(16), nullable=False)
    total_steps: Mapped[int] = mapped_column(default=50_000)
    status: Mapped[str] = mapped_column(
        String(16), default="pending"
    )  # pending|running|done|failed|cancelled

    runs: Mapped[list["Run"]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )


class Run(Base):
    __tablename__ = "run"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=_new_id)
    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("experiment.id"), nullable=False
    )
    reward_id: Mapped[str] = mapped_column(String(32), nullable=False)
    seed: Mapped[int] = mapped_column(default=0)
    hyperparams: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(64), default=None)
    final_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    artifact_path: Mapped[str | None] = mapped_column(String(512), default=None)

    experiment: Mapped["Experiment"] = relationship(back_populates="runs")


class Demo(Base):
    __tablename__ = "demo"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    env_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reward_id: Mapped[str | None] = mapped_column(String(32), default=None)
    source_run_id: Mapped[str | None] = mapped_column(String(12), default=None)
    n_episodes: Mapped[int] = mapped_column(default=0)
    n_steps: Mapped[int] = mapped_column(default=0)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
