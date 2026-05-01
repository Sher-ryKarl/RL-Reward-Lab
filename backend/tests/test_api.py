"""Integration tests for REST API endpoints.

Uses httpx.AsyncClient against the FastAPI app directly (no server needed).
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(autouse=True)
def _cleanup_custom_rewards():
    """Remove custom rewards added during a test."""
    from app.core.reward_editor import list_custom, remove
    from app.rewards.variants import REWARD_REGISTRY

    yield
    for entry in list_custom():
        rid = entry["reward_id"]
        remove(rid)
        REWARD_REGISTRY.pop(rid, None)


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
    assert len(data) == 5
    env_ids = {e["env_id"] for e in data}
    assert "MountainCar-v0" in env_ids
    assert "CartPole-v1" in env_ids
    assert "Pendulum-v1" in env_ids


@pytest.mark.asyncio
async def test_list_rewards(client: AsyncClient):
    r = await client.get("/api/v1/rewards")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 5
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
        "env_id": "NonExistentEnv-v0",  # not in registry
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
    assert len(data) == 4
    ids = {a["algo_id"] for a in data}
    assert ids == {"PPO", "DQN", "SAC", "BC"}
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
async def test_algo_env_compatibility(client: AsyncClient):
    """Verify continuous/discrete compatibility matrix."""
    from app.core.registry import algo_supports_env
    # SAC is continuous-only
    assert algo_supports_env("SAC", "MountainCar-v0") is False
    assert algo_supports_env("SAC", "Pendulum-v1") is True
    # DQN is discrete-only
    assert algo_supports_env("DQN", "MountainCar-v0") is True
    assert algo_supports_env("DQN", "Pendulum-v1") is False
    # PPO works on both
    assert algo_supports_env("PPO", "MountainCar-v0") is True
    assert algo_supports_env("PPO", "Pendulum-v1") is True


@pytest.mark.asyncio
async def test_create_sac_pendulum_experiment(client: AsyncClient):
    """SAC should be accepted for continuous Pendulum-v1."""
    body = {
        "name": "SAC Pendulum",
        "env_id": "Pendulum-v1",
        "algo_id": "SAC",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {"learning_rate": 1e-4},
        "total_steps": 300,
        "seeds": [0],
    }
    r = await client.post("/api/v1/experiments", json=body)
    assert r.status_code == 202, r.text


@pytest.mark.asyncio
async def test_create_dqn_rejected_for_continuous_env(client: AsyncClient):
    """DQN is discrete-only, should be rejected for continuous Pendulum."""
    body = {
        "name": "DQN Pendulum (should fail)",
        "env_id": "Pendulum-v1",
        "algo_id": "DQN",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {},
        "total_steps": 300,
        "seeds": [0],
    }
    r = await client.post("/api/v1/experiments", json=body)
    assert r.status_code == 400
    assert "does not support" in r.text


# ── BC & Demo tests (v0.5) ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_bc_experiment_requires_demo(client: AsyncClient):
    body = {
        "name": "BC No Demo",
        "env_id": "MountainCar-v0",
        "algo_id": "BC",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {},
        "total_steps": 500,
        "seeds": [0],
    }
    r = await client.post("/api/v1/experiments", json=body)
    assert r.status_code == 400
    assert "demo_id" in r.text


@pytest.mark.asyncio
async def test_list_demos(client: AsyncClient):
    r = await client.get("/api/v1/demos")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_create_demo_missing_source(client: AsyncClient):
    body = {
        "name": "Bad Demo",
        "env_id": "MountainCar-v0",
        "n_episodes": 10,
        "min_timesteps": 1000,
    }
    r = await client.post("/api/v1/demos", json=body)
    assert r.status_code == 400
    assert "source_run_id" in r.text


@pytest.mark.asyncio
async def test_get_demo_nonexistent(client: AsyncClient):
    r = await client.get("/api/v1/demos/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_demo_nonexistent(client: AsyncClient):
    r = await client.delete("/api/v1/demos/nonexistent")
    assert r.status_code == 404


# ── Custom Reward tests (v0.6) ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_valid_custom_reward(client: AsyncClient):
    code = (
        "def reward_fn(obs, reward, terminated, truncated):\n"
        "    return obs[0] + 0.5 * abs(obs[1])\n"
    )
    body = {"name": "Position+Velocity", "code": code}
    r = await client.post("/api/v1/rewards/custom", json=body)
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["reward_id"].startswith("C_")
    assert "Position+Velocity" in data["name"]


@pytest.mark.asyncio
async def test_create_custom_reward_bad_syntax(client: AsyncClient):
    body = {"name": "Bad", "code": "def reward_fn(): pass"}
    r = await client.post("/api/v1/rewards/custom", json=body)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_create_custom_reward_wrong_name(client: AsyncClient):
    code = "def not_reward_fn(obs, reward, terminated, truncated):\n    return 1.0\n"
    body = {"name": "Wrong Name", "code": code}
    r = await client.post("/api/v1/rewards/custom", json=body)
    assert r.status_code == 400
    assert "reward_fn" in r.text


@pytest.mark.asyncio
async def test_create_custom_reward_disallowed_import(client: AsyncClient):
    code = (
        "def reward_fn(obs, reward, terminated, truncated):\n"
        "    import os\n"
        "    return 0.0\n"
    )
    body = {"name": "Bad Import", "code": code}
    r = await client.post("/api/v1/rewards/custom", json=body)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_create_custom_reward_disallowed_builtin(client: AsyncClient):
    code = (
        "def reward_fn(obs, reward, terminated, truncated):\n"
        "    exec('print(1)')\n"
        "    return 0.0\n"
    )
    body = {"name": "Bad Builtin", "code": code}
    r = await client.post("/api/v1/rewards/custom", json=body)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_custom_reward_in_list(client: AsyncClient):
    code = (
        "def reward_fn(obs, reward, terminated, truncated):\n"
        "    return 1.0\n"
    )
    body = {"name": "AlwaysOne", "code": code}
    r = await client.post("/api/v1/rewards/custom", json=body)
    assert r.status_code == 201
    rid = r.json()["reward_id"]

    r2 = await client.get("/api/v1/rewards")
    ids = {rw["id"] for rw in r2.json()}
    assert rid in ids


@pytest.mark.asyncio
async def test_delete_custom_reward(client: AsyncClient):
    code = (
        "def reward_fn(obs, reward, terminated, truncated):\n"
        "    return 2.0\n"
    )
    body = {"name": "ToDelete", "code": code}
    r = await client.post("/api/v1/rewards/custom", json=body)
    rid = r.json()["reward_id"]

    r2 = await client.delete(f"/api/v1/rewards/custom/{rid}")
    assert r2.status_code == 204

    r3 = await client.delete(f"/api/v1/rewards/custom/{rid}")
    assert r3.status_code == 404


# ── Auth tests ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_auth_login_success(client: AsyncClient):
    r = await client.post("/api/v1/auth/login", json={"password": "admin"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_auth_login_wrong_password(client: AsyncClient):
    r = await client.post("/api/v1/auth/login", json={"password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_me(client: AsyncClient):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json() == {"user": "admin"}


@pytest.mark.asyncio
async def test_auth_write_rejected_without_token(client: AsyncClient):
    _disable_auth_bypass()
    try:
        r = await client.post(
            "/api/v1/experiments",
            json={
                "name": "No Auth",
                "env_id": "MountainCar-v0",
                "algo_id": "PPO",
                "reward_ids": ["R0_sparse"],
                "hyperparams": {},
                "total_steps": 1000,
                "seeds": [0],
            },
        )
        assert r.status_code == 401
    finally:
        _enable_auth_bypass()


@pytest.mark.asyncio
async def test_auth_custom_reward_rejected_without_token(client: AsyncClient):
    _disable_auth_bypass()
    try:
        code = (
            "import math\n"
            "def reward_fn(obs, reward, terminated, truncated):\n"
            "    return 1.0\n"
        )
        r = await client.post(
            "/api/v1/rewards/custom",
            json={"name": "Blocked", "code": code},
        )
        assert r.status_code == 401
    finally:
        _enable_auth_bypass()


@pytest.mark.asyncio
async def test_replay_status_no_video(client: AsyncClient):
    r = await client.get("/api/v1/runs/nonexistent-replay-status/replay/status")
    assert r.status_code == 404


# ── helpers ──────────────────────────────────────────────────────────────────


def _disable_auth_bypass():
    import os
    os.environ.pop("PYTEST_CURRENT_TEST", None)


def _enable_auth_bypass():
    import os
    os.environ["PYTEST_CURRENT_TEST"] = "1"


# ── Multi-objective (v1.1) ────────────────────────────────────────────────────


def test_pareto_front_computation():
    """Unit test: _compute_pareto_front correctly identifies non-dominated trials."""
    from app.workers.hpo import _compute_pareto_front

    # 4 trials with 2 objectives (O1=maximize→negated, O2=minimize)
    # Trial A: reward=100, time=10s  — Pareto
    # Trial B: reward=50,  time=5s   — Pareto (faster but worse reward)
    # Trial C: reward=40,  time=12s  — Dominated by B (worse on both)
    # Trial D: reward=80,  time=8s   — Pareto
    results = [
        {"values": [100.0, 10.0]},
        {"values": [50.0, 5.0]},
        {"values": [40.0, 12.0]},
        {"values": [80.0, 8.0]},
    ]
    pareto = _compute_pareto_front(results)
    assert set(pareto) == {0, 1, 3}, f"Expected Pareto {0,1,3}, got {set(pareto)}"


def test_pareto_front_single_trial():
    """Single trial is always Pareto-optimal."""
    from app.workers.hpo import _compute_pareto_front

    results = [{"values": [50.0, 10.0]}]
    pareto = _compute_pareto_front(results)
    assert pareto == [0]


def test_pareto_front_all_equal():
    """Trials with identical objectives: all are Pareto-optimal."""
    from app.workers.hpo import _compute_pareto_front

    results = [{"values": [10.0, 10.0]}, {"values": [10.0, 10.0]}]
    pareto = _compute_pareto_front(results)
    assert len(pareto) == 2


@pytest.mark.asyncio
async def test_envs_include_baseline_reward(client: AsyncClient):
    r = await client.get("/api/v1/envs")
    assert r.status_code == 200
    data = r.json()
    for env in data:
        assert "baseline_reward" in env, f"{env['env_id']} missing baseline_reward"
        assert isinstance(env["baseline_reward"], (int, float))


@pytest.mark.asyncio
async def test_single_objective_backward_compat(client: AsyncClient):
    """Single-objective experiment returns n_objectives=1, empty pareto_front."""
    body = {
        "name": "Single Obj Compat",
        "env_id": "MountainCar-v0",
        "algo_id": "PPO",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {},
        "total_steps": 100,
        "seeds": [9999],
    }
    r = await client.post("/api/v1/experiments", json=body)
    assert r.status_code == 202
    exp_id = r.json()["id"]

    # The experiment is "pending" → get_optimization returns empty trials
    r2 = await client.get(f"/api/v1/experiments/{exp_id}/optimization")
    assert r2.status_code == 200
    data = r2.json()
    assert data["n_objectives"] == 1
    assert data["directions"] == ["maximize"] or data["directions"] == ["maximize", "minimize", "minimize"]
    assert isinstance(data["pareto_front"], list)
