from __future__ import annotations

import logging

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # ── Idempotent migrations (SQLite-safe) ──────────────────────────────
        _migrations = [
            ("experiment", "user_id", "VARCHAR(12) REFERENCES \"user\"(id)"),
            ("demo", "user_id", "VARCHAR(12) REFERENCES \"user\"(id)"),
        ]
        for tbl, col, col_def in _migrations:
            try:
                await conn.execute(
                    text(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}")
                )
                logger.info("Migration: added %s.%s", tbl, col)
            except Exception:
                pass  # Column already exists

        # ── Seed admin user ──────────────────────────────────────────────────
        from app.db.models import User  # noqa: F811

        result = await conn.execute(
            text("SELECT id FROM \"user\" WHERE username = 'admin'")
        )
        admin_row = result.fetchone()
        if admin_row is None:
            hashed = bcrypt.hashpw(
                settings.admin_password.encode(), bcrypt.gensalt()
            ).decode()
            import secrets

            uid = secrets.token_hex(6)
            await conn.execute(
                text(
                    "INSERT INTO \"user\" (id, username, hashed_password, created_at) "
                    "VALUES (:id, 'admin', :pw, datetime('now'))"
                ),
                {"id": uid, "pw": hashed},
            )
            admin_id = uid
            logger.info("Seeded admin user (id=%s)", admin_id)
        else:
            admin_id = admin_row[0]

        # ── Assign legacy rows to admin ──────────────────────────────────────
        for tbl in ("experiment", "demo"):
            result = await conn.execute(
                text(f"SELECT COUNT(*) FROM {tbl} WHERE user_id IS NULL")
            )
            count = result.scalar_one()
            if count > 0:
                await conn.execute(
                    text(f"UPDATE {tbl} SET user_id = :uid WHERE user_id IS NULL"),
                    {"uid": admin_id},
                )
                logger.info(
                    "Migration: assigned %d orphan %s rows to admin", count, tbl
                )
