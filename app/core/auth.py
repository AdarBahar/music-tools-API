"""
Authentication and authorization utilities
"""

import logging
import hashlib
from typing import Optional
from fastapi import HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)


async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> bool:
    """
    Verify API key from header
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        bool: True if authenticated or auth not required
        
    Raises:
        AuthenticationError: If authentication fails
    """
    # If API key authentication is not required, allow all requests
    if not settings.REQUIRE_API_KEY:
        return True
    
    # Check if API key is provided
    if not x_api_key:
        logger.warning("API key authentication required but no key provided")
        raise AuthenticationError("API key required. Provide X-API-Key header.")
    
    # Validate API key against configured keys
    if x_api_key not in settings.valid_api_keys_list:
        logger.warning("Invalid API key attempted")
        raise AuthenticationError("Invalid API key")

    logger.debug("API key authenticated")
    return True


async def log_security_event(request: Request, event_type: str, details: dict):
    """
    Log security-related events
    
    Args:
        request: FastAPI request object
        event_type: Type of security event
        details: Additional event details
    """
    security_logger = logging.getLogger("security")
    
    client_ip = getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
    user_agent = request.headers.get("user-agent", "unknown")
    
    security_logger.info(
        "Security event: %s from %s (UA: %s) - %s",
        event_type,
        client_ip,
        user_agent,
        details
    )


async def get_client_identifier(request: Request) -> str:
    """
    Get a client identifier for rate limiting

    Args:
        request: FastAPI request object

    Returns:
        str: Client identifier (IP or hashed API key)
    """
    # If using API key, use a hash of the key as identifier
    api_key = request.headers.get("X-API-Key")
    if api_key and settings.REQUIRE_API_KEY:
        # Use SHA256 hash of the full key for rate limiting
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        return f"api_key:{key_hash}"

    # Fallback to IP address
    client_ip = getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
    return f"ip:{client_ip}"
