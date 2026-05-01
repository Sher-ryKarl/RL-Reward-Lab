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
