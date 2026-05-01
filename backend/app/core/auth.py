"""JWT authentication utilities — single-admin model."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.config import settings

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

_hashed_password: str | None = None


def _get_hashed_password() -> str:
    global _hashed_password
    if _hashed_password is None:
        _hashed_password = bcrypt.hashpw(
            settings.admin_password.encode(), bcrypt.gensalt()
        ).decode()
    return _hashed_password


def verify_password(plain: str) -> bool:
    return bcrypt.checkpw(plain.encode(), _get_hashed_password().encode())


def create_access_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": "admin", "exp": expire}, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
