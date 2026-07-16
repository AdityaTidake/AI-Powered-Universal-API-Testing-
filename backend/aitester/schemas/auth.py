"""
Pydantic schemas for Authentication endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ─── Request Schemas ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Body for POST /auth/register"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=1, max_length=255)
    org_name: str | None = Field(None, max_length=255, description="Optional org workspace to create")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if v.isdigit():
            raise ValueError("Password must contain at least one non-numeric character.")
        return v


class LoginRequest(BaseModel):
    """Body for POST /auth/login"""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Body for POST /auth/refresh"""
    refresh_token: str


# ─── Response Schemas ─────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """Returned on successful login or register."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public representation of an authenticated user."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    plan: str
    monthly_run_count: int
    created_at: datetime
