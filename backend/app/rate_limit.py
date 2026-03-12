from __future__ import annotations

import time
from typing import Callable

from fastapi import HTTPException, Request, status

from .queue import get_redis


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int, prefix: str) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.prefix = prefix

    def _key(self, identifier: str) -> str:
        current_window = int(time.time()) // self.window_seconds
        return f"rl:{self.prefix}:{identifier}:{current_window}"

    def __call__(self, identifier: str) -> None:
        client = get_redis()
        key = self._key(identifier)
        try:
            current = client.incr(key)
            if current == 1:
                client.expire(key, self.window_seconds)
        except Exception:
            # If Redis is unavailable, fail open rather than blocking all traffic.
            return

        if current > self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )


def rate_limit_dependency(
    request: Request,
    limiter: RateLimiter,
) -> None:
    client_ip = request.client.host if request.client else "unknown"
    limiter(client_ip)


def auth_rate_limiter() -> Callable[[Request], None]:
    """
    Returns a dependency function that rate-limits based on client IP for auth endpoints.
    """
    limiter = RateLimiter(limit=10, window_seconds=60, prefix="auth")

    def dependency(request: Request) -> None:
        rate_limit_dependency(request, limiter)

    return dependency

