"""
FastAPI dependency providers for SpecGuard AI — MongoDB / Beanie edition.

SOLID:
- Interface Segregation: Callers import only what they need.
- Dependency Inversion: Routes depend on these injected interfaces, not DB/JWT directly.

Note: With Beanie there is no session / connection to inject — documents use the
globally initialised Motor client. The only injected dependency is the current user.
"""

import uuid

from beanie import PydanticObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aitester.core.jwt import TokenError, decode_token, is_token_blacklisted, TokenType
from aitester.db.models import User

__all__ = ["get_current_user", "require_active_user", "require_pro_plan", "require_run_quota"]

# Bearer scheme — auto-extracts "Authorization: Bearer <token>"
_bearer = HTTPBearer(auto_error=True)


# ─── Core Auth Dependency ─────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> User:
    """
    Decodes the JWT, checks the Redis blacklist, and returns the active User.
    Raises HTTP 401 on any failure.
    """
    _401 = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = decode_token(token, expected_type=TokenType.ACCESS)
        jti     = payload.get("jti", "")
        # sub is stored as str(uuid) but MongoDB IDs are ObjectId strings
        user_id_str = payload["sub"]
    except (TokenError, Exception):
        raise _401

    if await is_token_blacklisted(jti):
        raise _401

    # Look up by the _id stored as string in JWT sub
    try:
        user = await User.get(PydanticObjectId(user_id_str))
    except Exception:
        raise _401

    if not user or not user.is_active:
        raise _401

    return user


# ─── Role / Plan Checks ───────────────────────────────────────────────────────

async def require_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Alias for get_current_user — use in routes that just need auth."""
    return current_user


async def require_pro_plan(
    current_user: User = Depends(get_current_user),
) -> User:
    """Blocks access if the user is on the free plan."""
    if current_user.plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Plan limit reached",
                "message": "This feature requires a Pro plan. Please upgrade.",
                "upgrade_url": "/settings/billing",
            },
        )
    return current_user


async def require_run_quota(
    current_user: User = Depends(get_current_user),
) -> User:
    """Checks whether the user has remaining monthly test runs."""
    from aitester.core.config import settings as cfg

    limit = cfg.FREE_PLAN_MONTHLY_RUNS if current_user.plan == "free" else cfg.PRO_PLAN_MONTHLY_RUNS
    if current_user.monthly_run_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Monthly run limit reached",
                "message": f"You've used all {limit} runs for this month.",
                "used": current_user.monthly_run_count,
                "limit": limit,
            },
        )
    return current_user
