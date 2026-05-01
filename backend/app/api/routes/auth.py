"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.auth import create_access_token, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginBody(BaseModel):
    password: str


@router.post("/login")
async def login(body: LoginBody):
    if not verify_password(body.password):
        raise HTTPException(401, "Invalid password")
    return {"access_token": create_access_token(), "token_type": "bearer"}


@router.get("/me")
async def me():
    return {"user": "admin"}
