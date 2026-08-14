"""aitester.schemas — all Pydantic request/response models."""

from aitester.schemas.analytics import (
    AIInsightResponse,
    CoverageProjectResponse,
    DashboardStatsResponse,
    OWASPIssue,
    TrendPointResponse,
)
from aitester.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from aitester.schemas.org import OrgCreate, OrgMemberAdd, OrgResponse, OrgUpdate
from aitester.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
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
    "ProjectUpdate",
    "ProjectResponse",
    # Organizations
    "OrgCreate",
    "OrgUpdate",
    "OrgMemberAdd",
    "OrgResponse",
    # Test Runs
    "TestRunCreate",
    "TestRunResponse",
    "TestRunStatusResponse",
    "TestResultResponse",
    # Analytics
    "DashboardStatsResponse",
    "TrendPointResponse",
    "CoverageProjectResponse",
    "AIInsightResponse",
    "OWASPIssue",
]
