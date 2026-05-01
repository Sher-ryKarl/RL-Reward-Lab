#!/usr/bin/env bash
# One-shot environment setup for RL-Reward-Lab.
# Prerequisites: Python 3.10+, pip, node 18+
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Installing Python dependencies with uv..."
pip install uv
uv pip install -e ".[dev]"

echo "==> Setting up data directories..."
mkdir -p data/checkpoints data/expert_trajs

echo "==> Setup complete. Start backend with:"
echo "    uv run uvicorn app.main:app --reload --app-dir backend"
