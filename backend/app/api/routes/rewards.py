from __future__ import annotations

from fastapi import APIRouter

from app.rewards.variants import REWARD_REGISTRY

router = APIRouter(prefix="/api/v1", tags=["rewards"])


@router.get("/rewards")
async def list_rewards():
    return [s.to_dict() for s in REWARD_REGISTRY.values()]
