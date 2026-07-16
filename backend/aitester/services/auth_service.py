"""
Authentication Service — encapsulates all auth business logic.

SOLID:
- Single Responsibility: Only handles register/login/refresh/logout logic.
- Dependency Inversion: Depends on DB session interface, not concretions.
- Open/Closed: New OAuth providers can be added without touching this service.
"""

import uuid
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aitester.core.exceptions import AITesterError
from aitester.core.jwt import (
    TokenType,
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    is_token_blacklisted,
)
from aitester.core.password import hash_password, verify_password
from aitester.db.models.organization import Organization
from aitester.db.models.org_member import OrgMember
from aitester.db.models.user import User
from aitester.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthError(AITesterError):
    """Domain error for authentication failures."""


def _make_slug(name: str) -> str:
    """Convert an org name to a URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:80] + "-" + str(uuid.uuid4())[:8]


class AuthService:
    """
    Stateless service — receives a DB session per call.
    All methods are async to align with the async DB layer.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Register ──────────────────────────────────────────────────────────────

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        """
        Create a new user account.
        Optionally creates an Organization and makes the user its owner.
        Raises AuthError if the email is already registered.
        """
        existing = await self._db.scalar(
            select(User).where(User.email == payload.email)
        )
        if existing:
            raise AuthError(
                "An account with this email already exists.",
                details={"field": "email"},
            )

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            is_active=True,
        )
        self._db.add(user)
        await self._db.flush()  # Get user.id before creating org

        if payload.org_name:
            org = Organization(
                name=payload.org_name,
                slug=_make_slug(payload.org_name),
            )
            self._db.add(org)
            await self._db.flush()

            membership = OrgMember(
                org_id=org.id,
                user_id=user.id,
                role="owner",
            )
            self._db.add(membership)

        await self._db.commit()
        await self._db.refresh(user)

        return self._issue_tokens(user.id)

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """
        Authenticate a user by email + password.
        Raises AuthError with a generic message on any failure (no user enumeration).
        """
        _generic_error = AuthError(
            "Invalid email or password.",
            details={"hint": "Check credentials and try again."},
        )

        user = await self._db.scalar(
            select(User).where(User.email == payload.email)
        )
        if not user or not user.is_active:
            raise _generic_error

        if not verify_password(payload.password, user.hashed_password):
            raise _generic_error

        return self._issue_tokens(user.id)

    # ── Refresh ───────────────────────────────────────────────────────────────

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """
        Rotate tokens: validate the refresh token, blacklist it,
        and issue a fresh access + refresh pair.
        """
        from aitester.core.jwt import TokenError

        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        jti = payload["jti"]

        if await is_token_blacklisted(jti):
            raise AuthError("Refresh token has been revoked.", details={"reason": "blacklisted"})

        # Verify user still exists and is active
        user_id = uuid.UUID(payload["sub"])
        user = await self._db.get(User, user_id)
        if not user or not user.is_active:
            raise AuthError("User account is inactive or deleted.")

        # Rotate: blacklist old refresh token
        import time
        ttl = max(0, int(payload["exp"] - time.time()))
        await blacklist_token(jti, ttl)

        return self._issue_tokens(user.id)

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(self, access_token: str) -> None:
        """
        Blacklist the current access token JTI so it cannot be reused.
        This is a best-effort operation — Redis failures are silently swallowed.
        """
        try:
            import time
            payload = decode_token(access_token, expected_type=TokenType.ACCESS)
            jti = payload["jti"]
            ttl = max(0, int(payload["exp"] - time.time()))
            await blacklist_token(jti, ttl)
        except Exception:
            pass  # Already expired tokens needn't be blacklisted

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _issue_tokens(user_id: uuid.UUID) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )
