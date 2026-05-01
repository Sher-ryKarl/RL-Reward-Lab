"""Token-bucket rate limiter ASGI middleware (v1.3).

Simple per-IP token bucket. Default 30 req/min on write endpoints.
GET/HEAD/OPTIONS are exempt. Exceeded limit returns 429 with Retry-After.

Configure via RL_LAB_RATE_LIMIT env var (format: "30/minute").
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Callable

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings

_WRITE_METHODS = {"POST", "PUT", "DELETE", "PATCH"}


class _TokenBucket:
    """Fixed-window counter (simpler than leaky bucket, sufficient for admin tool)."""

    def __init__(self, max_tokens: int, window_seconds: float):
        self.max_tokens = max_tokens
        self.window = window_seconds
        self._buckets: dict[str, tuple[int, float]] = {}  # ip -> (tokens, window_start)
        self._lock = asyncio.Lock()

    async def consume(self, client_ip: str) -> bool:
        now = time.monotonic()
        async with self._lock:
            tokens, window_start = self._buckets.get(client_ip, (self.max_tokens, now))
            if now - window_start >= self.window:
                tokens = self.max_tokens
                window_start = now
            if tokens > 0:
                self._buckets[client_ip] = (tokens - 1, window_start)
                return True
            self._buckets[client_ip] = (tokens, window_start)
            return False


def _parse_rate_limit(raw: str) -> tuple[int, float]:
    """Parse '30/minute' → (30, 60.0)."""
    parts = raw.strip().split("/")
    count = int(parts[0])
    unit = parts[1].lower() if len(parts) > 1 else "minute"
    if unit in ("s", "sec", "second"):
        return count, float(count)
    if unit in ("m", "min", "minute"):
        return count, 60.0
    if unit in ("h", "hr", "hour"):
        return count, 3600.0
    return count, 60.0  # default


_rate_config = _parse_rate_limit(settings.rate_limit)
_bucket = _TokenBucket(max_tokens=_rate_config[0], window_seconds=_rate_config[1])


class RateLimitMiddleware:
    """ASGI middleware that rate-limits write requests per client IP."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        if method not in _WRITE_METHODS:
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        client_ip = request.client.host if request.client else "unknown"

        if await _bucket.consume(client_ip):
            await self.app(scope, receive, send)
        else:
            response = Response(
                content='{"detail":"Rate limit exceeded. Try again later."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(int(_rate_config[1]))},
            )
            await response(scope, receive, send)
