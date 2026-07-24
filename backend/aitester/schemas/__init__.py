"""aitester.schemas — all Pydantic request/response models."""

from aitester.schemas.analytics import (
    CoverageProjectResponse,
    DashboardStatsResponse,
    TrendPointResponse,
)
from aitester.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from aitester.schemas.project import ProjectCreate, ProjectResponse
from aitester.schemas.test_run import (
    TestResultResponse,
    TestRunCreate,
    TestRunResponse,
    TestRunStatusResponse,
)

__all__ = [
    # Auth
    "LoginRequest",
    "RefreshRequest",
    "RegisterRequest",
    "TokenResponse",
    "UserResponse",
    # Projects
    "ProjectCreate",
    "ProjectResponse",
    # Test Runs
    "TestRunCreate",
    "TestRunResponse",
    "TestRunStatusResponse",
    "TestResultResponse",
    # Analytics
    "DashboardStatsResponse",
    "TrendPointResponse",
    "CoverageProjectResponse",
]
