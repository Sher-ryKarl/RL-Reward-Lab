from __future__ import annotations

from fastapi import APIRouter

from app.core.registry import ALGO_REGISTRY

router = APIRouter(prefix="/api/v1", tags=["algos"])


@router.get("/algos")
async def list_algos():
    return [
        {
            "algo_id": a.algo_id,
            "name": a.name,
            "discrete": a.discrete,
            "continuous": a.continuous,
            "supports_multiagent": a.supports_multiagent,
            "default_hp": a.default_hp,
        }
        for a in ALGO_REGISTRY.values()
    ]
