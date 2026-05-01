from __future__ import annotations

from pathlib import Path

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
    mlflow_tracking_uri: str = f"file:///{project_root / 'data' / 'mlruns'}"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # RL
    default_total_steps: int = 50_000
    max_total_steps: int = 2_000_000
    max_concurrent_runs: int = 4
    device: str = "cpu"


settings = Settings()
