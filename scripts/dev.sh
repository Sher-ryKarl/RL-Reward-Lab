#!/usr/bin/env bash
# Start both backend and frontend in dev mode (requires two terminals).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Backend:  uv run uvicorn app.main:app --reload --app-dir backend"
echo "Frontend: cd frontend && npm run dev"
