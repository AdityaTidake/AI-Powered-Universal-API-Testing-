"""
FastAPI dependency providers for SpecGuard AI.

SOLID:
- Interface Segregation: Callers import only what they need (get_db, get_current_user, etc.)
- Dependency Inversion: Routes depend on these injected interfaces, not DB/JWT directly.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aitester.core.jwt import TokenError, get_user_id_from_token, is_token_blacklisted, decode_token, TokenType
from aitester.db.models.user import User
from aitester.db.session import get_db

# ── Re-export for backwards compat ────────────────────────────────────────────
__all__ = ["get_db", "get_current_user", "require_active_user", "require_pro_plan"]

# Bearer scheme — auto-extracts "Authorization: Bearer <token>"
_bearer = HTTPBearer(auto_error=True)


# ─── Core Auth Dependency ─────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
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
        jti = payload.get("jti", "")
        user_id = uuid.UUID(payload["sub"])
    except (TokenError, Exception):
        raise _401

    if await is_token_blacklisted(jti):
        raise _401

    user = await db.get(User, user_id)
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
    """
    Blocks access if the user is on the free plan.
    Raises HTTP 403 with an upgrade prompt.
    """
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
    """
    Checks whether the user has remaining monthly test runs.
    Free: 10/month. Pro: 500/month.
    """
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
