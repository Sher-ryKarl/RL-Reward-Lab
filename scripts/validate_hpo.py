"""End-to-end validation: Optuna HPO sweep with minimal settings.

Run with: python scripts/validate_hpo.py
Requires the backend server to be running on localhost:8000.
"""

import httpx
import time
import sys

BASE = "http://localhost:8000"


def main():
    # 1. Health check
    r = httpx.get(f"{BASE}/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    print(f"[OK] Health: {r.json()}")

    # 2. Check envs
    r = httpx.get(f"{BASE}/api/v1/envs")
    assert r.status_code == 200
    envs = r.json()
    env_ids = [e["env_id"] for e in envs]
    assert len(envs) == 4, f"Expected 4 envs, got {len(envs)}"
    print(f"[OK] Envs ({len(envs)}): {env_ids}")

    # 3. Create optimization experiment
    body = {
        "name": "E2E HPO Validation",
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
        "total_steps": 1000,
        "seeds": [0],
        "optimize": True,
        "search_space": {
            "learning_rate": {"type": "loguniform", "low": 1e-5, "high": 1e-2},
            "batch_size": {"type": "int", "low": 16, "high": 128},
        },
        "n_trials": 3,
    }
    r = httpx.post(f"{BASE}/api/v1/experiments", json=body)
    assert r.status_code == 202, f"Create failed: {r.status_code} {r.text}"
    exp = r.json()
    exp_id = exp["id"]
    print(f"[OK] Experiment created: {exp_id}, status={exp['status']}")

    # 4. Poll optimization endpoint until done or timeout
    timeout = 180  # 3 minutes max
    start = time.time()
    while time.time() - start < timeout:
        r = httpx.get(f"{BASE}/api/v1/experiments/{exp_id}/optimization")
        if r.status_code == 200:
            result = r.json()
            n = len(result["trials"])
            status = result["status"]
            best = result.get("best_value")
            print(
                f"  [{time.time() - start:.0f}s] trials={n}, status={status}, best={best}"
            )
            if status in ("done", "failed", "partial"):
                break
        else:
            print(f"  [{time.time() - start:.0f}s] optimization endpoint: {r.status_code}")
        time.sleep(3)

    elapsed = time.time() - start

    # 5. Final assertions
    r = httpx.get(f"{BASE}/api/v1/experiments/{exp_id}/optimization")
    assert r.status_code == 200, f"Final get failed: {r.status_code}"
    result = r.json()

    assert result["status"] == "done", f"Expected 'done', got '{result['status']}'"
    assert len(result["trials"]) == 3, f"Expected 3 trials, got {len(result['trials'])}"
    assert result["best_value"] is not None, "best_value should not be None"
    print(f"\n[OK] Sweep completed in {elapsed:.0f}s")
    print(f"[OK] Best trial: value={result['best_value']:.4f}")
    print(f"[OK] Trials: {len(result['trials'])}")
    for t in result["trials"]:
        print(f"  Trial {t['number']}: value={t['value']:.4f}")

    # 6. Verify experiment summary
    r = httpx.get(f"{BASE}/api/v1/experiments/{exp_id}")
    assert r.status_code == 200
    exp = r.json()
    print(f"[OK] Experiment runs: {len(exp['runs'])}")
    assert len(exp["runs"]) == 3, f"Expected 3 runs, got {len(exp['runs'])}"

    print("\n=== ALL VALIDATION CHECKS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
