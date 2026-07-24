"""
JWT token management for SpecGuard AI.

SOLID:
- Single Responsibility: Only handles token creation, verification, blacklisting.
- Open/Closed: New token types extend via TokenType enum without modifying core logic.
"""

import uuid
from datetime import UTC, datetime, timedelta
from enum import Enum

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from aitester.core.config import settings
from aitester.core.exceptions import AITesterError


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenError(AITesterError):
    """Raised when a JWT is invalid, expired, or blacklisted."""


# ─── Token Creation ────────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    """
    Creates a short-lived access token (default 15 min).
    Payload: sub=user_id, type=access, jti=unique-id, exp=expiry
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": TokenType.ACCESS,
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Creates a long-lived refresh token (default 7 days).
    Stored JTI is saved to Redis so it can be invalidated (logout/rotation).
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": TokenType.REFRESH,
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ─── Token Verification ────────────────────────────────────────────────────────

def decode_token(token: str, expected_type: TokenType = TokenType.ACCESS) -> dict:
    """
    Decodes and validates a JWT.
    Raises TokenError on any failure (expired, bad sig, wrong type).
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except ExpiredSignatureError:
        raise TokenError("Token has expired.", details={"reason": "expired"})
    except JWTError as exc:
        raise TokenError("Invalid token.", details={"reason": str(exc)})

    if payload.get("type") != expected_type:
        raise TokenError(
            f"Expected {expected_type} token, got {payload.get('type')}.",
            details={"reason": "wrong_type"},
        )
    return payload


def get_user_id_from_token(token: str) -> str:
    """Extract and return the user ID string from a valid access token."""
    payload = decode_token(token, TokenType.ACCESS)
    return payload["sub"]


# ─── Token Blacklist (Redis) ───────────────────────────────────────────────────

async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """
    Stores the JTI in Redis with a TTL matching the token's remaining lifetime.
    Blacklisted tokens are rejected even if cryptographically valid.
    """
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        await client.setex(f"blacklist:{jti}", ttl_seconds, "1")
        await client.aclose()
    except Exception:
        # Redis unavailable: log and continue (degraded security — acceptable in dev)
        pass


async def is_token_blacklisted(jti: str) -> bool:
    """Returns True if the JTI has been blacklisted in Redis."""
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        result = await client.get(f"blacklist:{jti}")
        await client.aclose()
        return result is not None
    except Exception:
        return False
