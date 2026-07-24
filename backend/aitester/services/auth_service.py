"""
Authentication Service — Beanie/MongoDB edition.

SOLID:
- Single Responsibility: Only handles register/login/refresh/logout.
- Open/Closed: New OAuth providers can be added without touching this service.
"""

import re
import uuid
from datetime import UTC, datetime

from beanie import PydanticObjectId

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
from aitester.db.models import Organization, User
from aitester.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthError(AITesterError):
    """Domain error for authentication failures."""


def _make_slug(name: str) -> str:
    """Convert an org name to a URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:80] + "-" + str(uuid.uuid4())[:8]


class AuthService:
    """
    Stateless auth service — no DB session needed (Beanie uses a global connection).
    All methods are async.
    """

    # ── Register ──────────────────────────────────────────────────────────────

    @staticmethod
    async def register(payload: RegisterRequest) -> TokenResponse:
        """
        Create a new user account.
        Raises AuthError if the email is already registered.
        """
        existing = await User.find_one(User.email == payload.email)
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
        await user.insert()

        if payload.org_name:
            org = Organization(
                name=payload.org_name,
                slug=_make_slug(payload.org_name),
                owner_id=user.id,
                member_ids=[user.id],
            )
            await org.insert()

        return AuthService._issue_tokens(user.id)

    # ── Login ─────────────────────────────────────────────────────────────────

    @staticmethod
    async def login(payload: LoginRequest) -> TokenResponse:
        """
        Authenticate a user by email + password.
        Raises AuthError with a generic message (no user enumeration).
        """
        _generic_error = AuthError(
            "Invalid email or password.",
            details={"hint": "Check credentials and try again."},
        )

        user = await User.find_one(User.email == payload.email)
        if not user or not user.is_active:
            raise _generic_error

        if not verify_password(payload.password, user.hashed_password):
            raise _generic_error

        return AuthService._issue_tokens(user.id)

    # ── Refresh ───────────────────────────────────────────────────────────────

    @staticmethod
    async def refresh(refresh_token: str) -> TokenResponse:
        """
        Rotate tokens: validate the refresh token, blacklist it,
        and issue a fresh access + refresh pair.
        """
        from aitester.core.jwt import TokenError

        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        jti = payload["jti"]

        if await is_token_blacklisted(jti):
            raise AuthError("Refresh token has been revoked.", details={"reason": "blacklisted"})

        user_id_str = payload["sub"]
        try:
            user = await User.get(PydanticObjectId(user_id_str))
        except Exception:
            user = None

        if not user or not user.is_active:
            raise AuthError("User account is inactive or deleted.")

        import time
        ttl = max(0, int(payload["exp"] - time.time()))
        await blacklist_token(jti, ttl)

        return AuthService._issue_tokens(user.id)

    # ── Logout ────────────────────────────────────────────────────────────────

    @staticmethod
    async def logout(access_token: str) -> None:
        """Blacklist the current access token JTI."""
        try:
            import time
            payload = decode_token(access_token, expected_type=TokenType.ACCESS)
            jti = payload["jti"]
            ttl = max(0, int(payload["exp"] - time.time()))
            await blacklist_token(jti, ttl)
        except Exception:
            pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _issue_tokens(user_id: PydanticObjectId) -> TokenResponse:
        # Convert ObjectId → str for JWT subject
        return TokenResponse(
            access_token=create_access_token(str(user_id)),
            refresh_token=create_refresh_token(str(user_id)),
        )
