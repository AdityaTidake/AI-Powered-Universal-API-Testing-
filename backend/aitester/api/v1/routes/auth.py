"""
Auth API routes — /api/v1/auth/*

Endpoints:
  POST /auth/register   → create account + return tokens
  POST /auth/login      → verify credentials + return tokens
  POST /auth/refresh    → rotate refresh token
  POST /auth/logout     → blacklist current access token
  GET  /auth/me         → return authenticated user profile
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from aitester.api.dependencies import get_current_user, get_db
from aitester.core.exceptions import AITesterError
from aitester.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from aitester.services.auth_service import AuthError, AuthService
from aitester.db.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency factory — constructs AuthService with a DB session."""
    return AuthService(db)


# ─── Register ─────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    """
    Creates a new user (and optional organization).
    Returns a JWT access + refresh token pair on success.
    """
    try:
        return await service.register(payload)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Registration failed", "message": exc.message, **exc.details},
        ) from exc


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    """Authenticates a user and returns JWT tokens."""
    try:
        return await service.login(payload)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Authentication failed", "message": exc.message},
        ) from exc


# ─── Token Refresh ────────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate a refresh token",
)
async def refresh_token(
    payload: RefreshRequest,
    service: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    """
    Validates the refresh token, blacklists it, and issues a new token pair.
    Implements refresh token rotation to prevent reuse attacks.
    """
    try:
        return await service.refresh(payload.refresh_token)
    except (AuthError, AITesterError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Token refresh failed", "message": exc.message},
        ) from exc


# ─── Logout ───────────────────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and invalidate current token",
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(_get_auth_service),
) -> None:
    """
    Blacklists the current access token JTI in Redis.
    The client should also discard the refresh token locally.
    """
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    await service.logout(token)


# ─── Me ───────────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Returns the authenticated user's profile."""
    return current_user
