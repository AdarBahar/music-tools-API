"""
Shared rate limiter.

One Limiter instance is used by the whole application. The route modules import
`limit` and put it BELOW the router decorator. The router decorator registers
the function it receives, so the limit must wrap the function first.
"""

import ipaddress
import logging
from typing import Callable, Optional

from fastapi import Request
from slowapi import Limiter

from app.core.config import settings

logger = logging.getLogger(__name__)

def _parse_networks(value: str) -> list:
    """Parse a comma-separated list of IP addresses and networks."""
    networks = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            networks.append(ipaddress.ip_network(item, strict=False))
        except ValueError:
            logger.warning(f"Ignored invalid TRUSTED_PROXIES entry: {item!r}")
    return networks


_TRUSTED_NETWORKS = _parse_networks(settings.TRUSTED_PROXIES)


def _is_trusted(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return any(ip in network for network in _TRUSTED_NETWORKS)


def get_client_ip(request: Request) -> str:
    """Return the client IP address.

    A client can send any X-Forwarded-For header, so the header counts only
    when the direct peer is a trusted proxy (TRUSTED_PROXIES). Each trusted
    proxy appends the address it saw to the end of the header. The code reads
    the header from the right and returns the first address that is not a
    trusted proxy. The part of the header on the left of that address is
    client input, and the code never uses it.
    """
    peer = request.client.host if request.client else "unknown"
    if not _is_trusted(peer):
        return peer
    forwarded = request.headers.get("x-forwarded-for", "")
    for entry in reversed([e.strip() for e in forwarded.split(",") if e.strip()]):
        if not _is_trusted(entry):
            return entry
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
