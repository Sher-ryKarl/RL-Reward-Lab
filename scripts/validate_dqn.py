"""End-to-end validation: DQN training + SAC rejection on discrete env.

Run with: python scripts/validate_dqn.py
Requires the backend server to be running on localhost:8000.
"""

import httpx
import time
import sys

BASE = "http://localhost:8000"


def main():
    # 1. Verify SAC is rejected
    body_sac = {
        "name": "SAC Reject Test",
        "env_id": "MountainCar-v0",
        "algo_id": "SAC",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {},
        "total_steps": 100,
        "seeds": [0],
    }
    r = httpx.post(f"{BASE}/api/v1/experiments", json=body_sac)
    assert r.status_code == 400, f"SAC should be 400, got {r.status_code}: {r.text}"
    assert "does not support" in r.text
    print("[OK] SAC correctly rejected for MountainCar (discrete)")

    # 2. Create DQN experiment
    body_dqn = {
        "name": "E2E DQN Validation",
        "env_id": "MountainCar-v0",
        "algo_id": "DQN",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {
            "learning_rate": 1e-4,
            "buffer_size": 1000,
            "learning_starts": 100,
            "batch_size": 32,
            "tau": 1.0,
            "gamma": 0.99,
            "exploration_fraction": 0.1,
            "exploration_initial_eps": 1.0,
            "exploration_final_eps": 0.02,
        },
        "total_steps": 500,
        "seeds": [0],
    }
    r = httpx.post(f"{BASE}/api/v1/experiments", json=body_dqn)
    assert r.status_code == 202, f"DQN create failed: {r.status_code} {r.text}"
    exp = r.json()
    exp_id = exp["id"]
    print(f"[OK] DQN experiment created: {exp_id}")

    # 3. Poll until done
    timeout = 120
    start = time.time()
    while time.time() - start < timeout:
        r = httpx.get(f"{BASE}/api/v1/experiments/{exp_id}")
        if r.status_code == 200:
            exp = r.json()
            runs = exp["runs"]
            statuses = [run["status"] for run in runs]
            print(f"  [{time.time() - start:.0f}s] statuses={statuses}")
            if all(s in ("done", "failed") for s in statuses):
                break
        time.sleep(2)

    elapsed = time.time() - start

    # 4. Verify
    r = httpx.get(f"{BASE}/api/v1/experiments/{exp_id}")
    exp = r.json()
    assert exp["algo_id"] == "DQN"
    assert len(exp["runs"]) == 1
    run = exp["runs"][0]
    assert run["status"] == "done", f"Expected done, got {run['status']}"
    assert run["final_metrics"] is not None
    print(f"\n[OK] DQN training completed in {elapsed:.0f}s")
    print(f"[OK] Final metrics: {run['final_metrics']}")
    print(f"[OK] Hyperparams stored: {len(run['hyperparams'])} keys")

    # 5. Test DQN on LunarLander (also discrete)
    body_ll = {
        "name": "DQN LunarLander",
        "env_id": "LunarLander-v2",
        "algo_id": "DQN",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {"learning_rate": 1e-4, "buffer_size": 1000, "batch_size": 32},
        "total_steps": 500,
        "seeds": [0],
    }
    r = httpx.post(f"{BASE}/api/v1/experiments", json=body_ll)
    assert r.status_code == 202, f"DQN LunarLander create failed: {r.status_code}"

    print("\n=== ALL DQN VALIDATION CHECKS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
