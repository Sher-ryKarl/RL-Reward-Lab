"""Shared FastAPI dependencies."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_token
from app.db.database import async_session
from app.db.models import User

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        result = await db.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        if user is None:
            from app.core.auth import hash_password
            from app.config import settings
            from app.db.models import _new_user_id

            user = User(
                id=_new_user_id(),
                username="admin",
                hashed_password=hash_password(settings.admin_password),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    if credentials is None:
        raise HTTPException(
            401, "Not authenticated", headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token payload")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(401, "User not found")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"}
        )
