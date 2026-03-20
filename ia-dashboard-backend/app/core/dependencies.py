"""
app/core/dependencies.py

FastAPI dependency injection helpers:
- optional_current_user: resolves JWT if present; returns None for anonymous sessions
- require_current_user: enforces authentication
"""

from typing import Optional
from fastapi import Depends, Header, HTTPException, status

from app.core.security import TokenPayload, decode_token, is_token_expired
from app.core.logging import get_logger

logger = get_logger(__name__)


def optional_current_user(
    authorization: Optional[str] = Header(default=None),
) -> Optional[TokenPayload]:
    """
    Try to resolve the calling user from the Authorization header.
    Returns None for anonymous sessions (no token provided).
    Raises 401 only when an invalid token is explicitly sent.
    """
    # Anonymous access is expected - debug only
    if authorization is None:
        logger.debug("anon_request_allowed")
        return None

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        logger.debug("invalid_auth_header", scheme=scheme)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format.",
        )

    payload = decode_token(token)

    if payload is None:
        logger.debug("invalid_or_expired_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired.",
        )

    if is_token_expired(payload):
        logger.debug("token_expired", exp=payload.exp)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired.",
        )

    logger.debug("token_valid", user_sub=payload.sub)
    return payload


def require_current_user(
    user: Optional[TokenPayload] = Depends(optional_current_user),
) -> TokenPayload:
    """
    Enforce authentication. Used on endpoints that require persistence (RF-04).
    Raises 401 when no valid token is present.
    """
    if user is None:
        logger.debug("auth_required_missing_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required for this operation.",
        )

    return user
