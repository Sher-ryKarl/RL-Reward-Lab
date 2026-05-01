"""Integration tests for REST API endpoints.

Uses httpx.AsyncClient against the FastAPI app directly (no server needed).
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": "0.1.0"}


@pytest.mark.asyncio
async def test_list_envs(client: AsyncClient):
    r = await client.get("/api/v1/envs")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 4
    env_ids = {e["env_id"] for e in data}
    assert "MountainCar-v0" in env_ids
    assert "CartPole-v1" in env_ids


@pytest.mark.asyncio
async def test_list_rewards(client: AsyncClient):
    r = await client.get("/api/v1/rewards")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 5
    ids = {rw["id"] for rw in data}
    assert "R0_sparse" in ids
    assert "R4_misleading" in ids


@pytest.mark.asyncio
async def test_create_experiment(client: AsyncClient):
    body = {
        "name": "API Test",
        "env_id": "MountainCar-v0",
        "algo_id": "PPO",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {
            "learning_rate": 3e-4,
            "n_steps": 128,
            "batch_size": 32,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "ent_coef": 0.0,
            "clip_range": 0.2,
        },
        "total_steps": 5000,
        "seeds": [0],
    }
    r = await client.post("/api/v1/experiments", json=body)
    assert r.status_code == 202
    data = r.json()
    assert data["env_id"] == "MountainCar-v0"
    assert len(data["runs"]) == 1
    assert data["runs"][0]["reward_id"] == "R0_sparse"
    assert data["runs"][0]["status"] == "pending"


@pytest.mark.asyncio
async def test_create_validation_fails_on_bad_env(client: AsyncClient):
    body = {
        "name": "Bad Env",
        "env_id": "Pendulum-v1",  # not in v0.1
        "algo_id": "PPO",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {},
        "total_steps": 1000,
        "seeds": [0],
    }
    # Pydantic Literal validation should reject this
    r = await client.post("/api/v1/experiments", json=body)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_experiments(client: AsyncClient):
    r = await client.get("/api/v1/experiments")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_nonexistent_experiment(client: AsyncClient):
    r = await client.get("/api/v1/experiments/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_run(client: AsyncClient):
    r = await client.get("/api/v1/runs/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_stream_nonexistent_run(client: AsyncClient):
    r = await client.get("/api/v1/runs/nonexistent/stream")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_optimize_experiment(client: AsyncClient):
    body = {
        "name": "HPO Test",
        "env_id": "MountainCar-v0",
        "algo_id": "PPO",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {
            "learning_rate": 3e-4,
            "n_steps": 128,
            "batch_size": 32,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "ent_coef": 0.0,
            "clip_range": 0.2,
        },
        "total_steps": 100,
        "seeds": [0],
        "optimize": True,
        "search_space": {"learning_rate": {"type": "loguniform", "low": 1e-6, "high": 1.0}},
        "n_trials": 5,
    }
    r = await client.post("/api/v1/experiments", json=body)
    assert r.status_code == 202
    data = r.json()
    assert data["status"] in ("pending", "running")


@pytest.mark.asyncio
async def test_get_optimization_nonexistent(client: AsyncClient):
    r = await client.get("/api/v1/experiments/nonexistent/optimization")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_algos(client: AsyncClient):
    r = await client.get("/api/v1/algos")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    ids = {a["algo_id"] for a in data}
    assert ids == {"PPO", "DQN", "SAC"}
    # Check DQN fields
    dqn = [a for a in data if a["algo_id"] == "DQN"][0]
    assert dqn["discrete"] is True
    assert dqn["continuous"] is False
    assert "buffer_size" in dqn["default_hp"]


@pytest.mark.asyncio
async def test_create_dqn_experiment(client: AsyncClient):
    body = {
        "name": "DQN Test",
        "env_id": "MountainCar-v0",
        "algo_id": "DQN",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {
            "learning_rate": 1e-4,
            "buffer_size": 10000,
            "batch_size": 32,
        },
        "total_steps": 500,
        "seeds": [0],
    }
    r = await client.post("/api/v1/experiments", json=body)
    assert r.status_code == 202
    data = r.json()
    assert data["algo_id"] == "DQN"


@pytest.mark.asyncio
async def test_create_sac_rejected_for_discrete_env(client: AsyncClient):
    """SAC is continuous-only, should be rejected for discrete MountainCar."""
    # The API itself accepts the POST (schema validation passes),
    # but validation should happen before training. For now just verify
    # it's in the valid algo_id list.
    from app.core.registry import algo_supports_env
    assert algo_supports_env("SAC", "MountainCar-v0") is False
    assert algo_supports_env("DQN", "MountainCar-v0") is True
    assert algo_supports_env("PPO", "MountainCar-v0") is True
