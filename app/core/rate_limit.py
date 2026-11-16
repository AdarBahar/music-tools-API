"""
Shared rate limiter.

One Limiter instance is used by the whole application. The route modules import
`limit` and put it BELOW the router decorator. The router decorator registers
the function it receives, so the limit must wrap the function first.
"""

import logging
from typing import Callable, Optional

from fastapi import Request
from slowapi import Limiter

from app.core.config import settings

logger = logging.getLogger(__name__)

_LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def get_client_ip(request: Request) -> str:
    """Return the client IP address.

    Behind the local Nginx proxy, the direct peer is the loopback address.
    Nginx appends the real client address at the end of X-Forwarded-For,
    so the last entry is the only entry the client cannot forge.
    """
    peer = request.client.host if request.client else "unknown"
    if peer in _LOOPBACK:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[-1].strip()
    return peer


limiter: Optional[Limiter] = None
if settings.ENABLE_RATE_LIMITING:
    try:
        limiter = Limiter(
            key_func=get_client_ip,
            storage_uri=settings.RATE_LIMIT_STORAGE_URI,
            in_memory_fallback_enabled=True,
        )
        logger.info("Rate limiting enabled")
    except Exception as e:
        logger.warning(f"Failed to initialize rate limiter: {type(e).__name__}. Rate limiting disabled.")
        limiter = None
else:
    logger.info("Rate limiting disabled in configuration")


def limit(rate: str) -> Callable:
    """Return a decorator that applies `rate`, or a no-op when limiting is off."""
    if limiter is None:
        return lambda f: f
    return limiter.limit(rate)
