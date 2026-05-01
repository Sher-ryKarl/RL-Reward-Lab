from __future__ import annotations

from pathlib import Path

import torch
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RL_LAB_", env_file=".env")

    # Project
    project_root: Path = Path(__file__).resolve().parents[2]
    backend_dir: Path = Path(__file__).resolve().parent
    data_dir: Path = project_root / "data"

    # Database
    database_url: str = f"sqlite+aiosqlite:///{project_root / 'data' / 'rl_lab.db'}"

    # MLflow
    mlflow_tracking_uri: str = f"sqlite:///{project_root / 'data' / 'mlflow.db'}"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    test_mode: bool = False  # Bypass auth in tests

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost"

    # Auth
    secret_key: str = "rl-lab-dev-secret-change-in-production"
    admin_password: str = "admin"

    # RL
    default_total_steps: int = 50_000
    max_total_steps: int = 2_000_000
    max_concurrent_runs: int = 4
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


settings = Settings()
