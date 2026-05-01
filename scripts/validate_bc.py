"""End-to-end validation: BC training from a collected demo.

Run with: python scripts/validate_bc.py
Requires the backend server to be running on localhost:8000.
"""

import httpx
import time
import sys

BASE = "http://localhost:8000"


def main():
    # 1. Create a short PPO experiment to generate an expert
    body_ppo = {
        "name": "BC Demo Source",
        "env_id": "MountainCar-v0",
        "algo_id": "PPO",
        "reward_ids": ["R1_dense"],
        "hyperparams": {
            "learning_rate": 3e-4,
            "n_steps": 128,
            "batch_size": 32,
            "gamma": 0.99,
            "gae_lambda": 0.95,
        },
        "total_steps": 1000,
        "seeds": [0],
    }
    r = httpx.post(f"{BASE}/api/v1/experiments", json=body_ppo)
    assert r.status_code == 202, f"PPO create failed: {r.status_code} {r.text}"
    exp = r.json()
    exp_id = exp["id"]
    run_id = exp["runs"][0]["id"]
    print(f"[OK] PPO experiment created: {exp_id}, run: {run_id}")

    # 2. Wait for PPO run to finish
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

    r = httpx.get(f"{BASE}/api/v1/experiments/{exp_id}")
    exp = r.json()
    run = exp["runs"][0]
    assert run["status"] == "done", f"PPO training failed: {run['status']}"
    print(f"[OK] PPO training done in {time.time() - start:.0f}s")

    # 3. Collect demo from the PPO run
    body_demo = {
        "name": "BC Demo from PPO",
        "env_id": "MountainCar-v0",
        "source_run_id": run_id,
        "n_episodes": 5,
        "min_timesteps": 500,
    }
    r = httpx.post(f"{BASE}/api/v1/demos", json=body_demo)
    assert r.status_code == 202, f"Demo collect failed: {r.status_code} {r.text}"
    demo = r.json()
    demo_id = demo["id"]
    print(f"[OK] Demo collected: {demo_id} ({demo['n_episodes']} eps, {demo['n_steps']} steps)")

    # 4. Verify demo appears in list
    r = httpx.get(f"{BASE}/api/v1/demos")
    assert r.status_code == 200
    demos = r.json()
    assert any(d["id"] == demo_id for d in demos)
    print(f"[OK] Demo listed ({len(demos)} total)")

    # 5. Create BC experiment using the demo
    body_bc = {
        "name": "BC Clone Test",
        "env_id": "MountainCar-v0",
        "algo_id": "BC",
        "reward_ids": ["R1_dense"],
        "hyperparams": {"batch_size": 32, "l2_weight": 1e-4},
        "total_steps": 100,
        "seeds": [0],
        "demo_id": demo_id,
    }
    r = httpx.post(f"{BASE}/api/v1/experiments", json=body_bc)
    assert r.status_code == 202, f"BC create failed: {r.status_code} {r.text}"
    bc_exp = r.json()
    bc_exp_id = bc_exp["id"]
    bc_run_id = bc_exp["runs"][0]["id"]
    print(f"[OK] BC experiment created: {bc_exp_id}")

    # 6. Wait for BC training to finish
    start = time.time()
    while time.time() - start < 60:
        r = httpx.get(f"{BASE}/api/v1/experiments/{bc_exp_id}")
        if r.status_code == 200:
            exp = r.json()
            runs = exp["runs"]
            statuses = [run["status"] for run in runs]
            print(f"  [{time.time() - start:.0f}s] statuses={statuses}")
            if all(s in ("done", "failed") for s in statuses):
                break
        time.sleep(1)

    r = httpx.get(f"{BASE}/api/v1/experiments/{bc_exp_id}")
    bc_exp = r.json()
    bc_run = bc_exp["runs"][0]
    assert bc_run["status"] == "done", f"BC training failed: {bc_run['status']}"
    print(f"[OK] BC training done in {time.time() - start:.0f}s")
    print(f"[OK] Final metrics: {bc_run.get('final_metrics', 'N/A')}")

    # 7. Verify BC experiment is in experiment list with correct algo
    r = httpx.get(f"{BASE}/api/v1/experiments/{bc_exp_id}")
    assert r.json()["algo_id"] == "BC"

    # 8. BC without demo should be rejected
    r = httpx.post(f"{BASE}/api/v1/experiments", json={
        "name": "BC No Demo",
        "env_id": "MountainCar-v0",
        "algo_id": "BC",
        "reward_ids": ["R0_sparse"],
        "hyperparams": {},
        "total_steps": 100,
        "seeds": [0],
    })
    assert r.status_code == 400
    assert "demo_id" in r.text
    print("[OK] BC without demo correctly rejected")

    print("\n=== ALL BC VALIDATION CHECKS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
