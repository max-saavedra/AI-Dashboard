"""
app/core/security.py

JWT validation utilities.
Supabase Auth issues JWTs; the backend only validates them (stateless, RNF-09).
"""
import requests
from datetime import datetime, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import get_logger
from functools import lru_cache

logger = get_logger(__name__)
settings = get_settings()

JWKS_URL = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"

class TokenPayload(BaseModel):
    """Decoded JWT claims."""

    sub: Optional[str] = None   # user UUID
    email: Optional[str] = None
    exp: Optional[int] = None
    role: Optional[str] = None


# def decode_token(token: str) -> Optional[TokenPayload]:
#     """
#     Decode and validate a Supabase-issued JWT.

#     Returns None if the token is invalid or expired
#     so callers can decide whether to raise 401 or allow
#     anonymous access.
#     """
#     try:
#         payload = jwt.decode(
#             token,
#             settings.supabase_anon_key,
#             algorithms=["HS256"],
#             options={"verify_aud": False},
#         )
#         return TokenPayload(**payload)
#     except JWTError as exc:
#         logger.warning("jwt_decode_failed", error=str(exc))
#         return None

@lru_cache
def get_jwks():
    """Fetch and cache Supabase public keys."""
    response = requests.get(JWKS_URL)
    response.raise_for_status()
    return response.json()


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    Decode and validate a Supabase-issued JWT (ES256 via JWKS).
    """
    logger.info("DEBUG: Starting JWT validation",
                token_length=len(token) if token else 0)

    if not token or token in ("undefined", "null", "None"):
        logger.warning("DEBUG: Invalid token value", token_value=token)
        return None

    if token.count(".") != 2:
        logger.warning("DEBUG: Invalid JWT format",
                       segments=token.count(".") + 1)
        return None

    try:
        # 1. Get public keys (cached)
        jwks = get_jwks()

        # 2. Extract token header
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")

        logger.info("DEBUG: JWT header parsed", kid=kid)

        # 3. Find matching key
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)

        if not key:
            logger.warning("DEBUG: Matching JWKS key not found", kid=kid)
            return None

        # 4. Decode using ES256 public key
        payload = jwt.decode(
            token,
            key,
            algorithms=["ES256"],
            options={"verify_aud": False},
        )

        logger.info("DEBUG: JWT validated successfully",
                    sub=payload.get("sub"),
                    email=payload.get("email"))

        return TokenPayload(**payload)

    except Exception as exc:
        logger.warning("DEBUG: JWT validation failed",
                       error_type=type(exc).__name__,
                       error_message=str(exc))
        return None

def is_token_expired(payload: TokenPayload) -> bool:
    """Return True when the token's expiry has passed."""
    if payload.exp is None:
        return True
    expiry = datetime.fromtimestamp(payload.exp, tz=timezone.utc)
    return datetime.now(tz=timezone.utc) >= expiry
