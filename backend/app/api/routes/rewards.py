"""Reward variant listing + custom reward registration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from pydantic import BaseModel, Field

from app.core import reward_editor
from app.db.models import User
from app.rewards.custom_spec import CustomRewardSpec
from app.rewards.variants import REWARD_REGISTRY

router = APIRouter(prefix="/api/v1", tags=["rewards"])


class CustomRewardBody(BaseModel):
    name: str = Field(default="Untitled Reward")
    code: str = Field(min_length=1, max_length=4096)


@router.get("/rewards")
async def list_rewards(_user: User = Depends(get_current_user)):
    builtins = [s.to_dict() for s in REWARD_REGISTRY.values()]
    customs = [
        {
            "id": r["reward_id"],
            "name": r["name"],
            "description": f"Custom reward: {r['name']}",
            "source_type": "custom",
            "terms": ["extrinsic"],
            "references": [],
            "code": r["code"],
        }
        for r in reward_editor.list_custom(_user.id)
    ]
    return builtins + customs


@router.post("/rewards/custom", status_code=201)
async def create_custom_reward(body: CustomRewardBody, _user: User = Depends(get_current_user)):
    try:
        rid = reward_editor.register(body.code, body.name, _user.id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    # Register as a RewardSpec so experiments can use it
    if rid not in REWARD_REGISTRY:
        REWARD_REGISTRY[rid] = CustomRewardSpec(rid, body.name, body.code)

    entry = reward_editor.get(rid)
    return {
        "reward_id": rid,
        "name": entry["name"] if entry else body.name,
        "code": body.code,
    }


@router.delete("/rewards/custom/{reward_id}", status_code=204)
async def delete_custom_reward(reward_id: str, _user: User = Depends(get_current_user)):
    if not reward_editor.remove(reward_id, _user.id):
        raise HTTPException(404, f"Custom reward '{reward_id}' not found")
    REWARD_REGISTRY.pop(reward_id, None)
    return None
