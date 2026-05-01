from __future__ import annotations

from fastapi import APIRouter

from app.core.registry import ENV_REGISTRY

router = APIRouter(prefix="/api/v1", tags=["envs"])


@router.get("/envs")
async def list_envs():
    return [{"env_id": e.env_id, "name": e.name, "action_space": e.action_space}
            for e in ENV_REGISTRY.values()]
