"""RL-Reward-Lab API Server.

Start with: uv run uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import algos, demos, envs, experiments, rewards, runs, stream
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="RL-Reward-Lab",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(algos.router)
app.include_router(demos.router)
app.include_router(envs.router)
app.include_router(rewards.router)
app.include_router(experiments.router)
app.include_router(runs.router)
app.include_router(stream.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
