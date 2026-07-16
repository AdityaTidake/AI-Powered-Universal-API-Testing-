"""aitester.schemas — all Pydantic request/response models."""

from aitester.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from aitester.schemas.project import ProjectCreate, ProjectResponse
from aitester.schemas.test_run import TestRunCreate, TestRunResponse, TestRunStatusResponse

__all__ = [
    "LoginRequest",
    "RefreshRequest",
    "RegisterRequest",
    "TokenResponse",
    "UserResponse",
    "ProjectCreate",
    "ProjectResponse",
    "TestRunCreate",
    "TestRunResponse",
    "TestRunStatusResponse",
]
