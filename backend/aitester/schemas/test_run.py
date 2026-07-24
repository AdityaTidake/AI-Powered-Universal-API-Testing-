"""Pydantic schemas for TestRun and TestResult resources."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from aitester.schemas.base import MongoBaseResponse, PyObjectIdStr


# ── Test Run ──────────────────────────────────────────────────────────────────

class TestRunCreate(BaseModel):
    """Body for POST /projects/{project_id}/runs."""
    base_url: str
    types: list[Literal["functional", "edge", "security", "ai"]] = ["functional"]
    enable_ai: bool = False


class TestRunResponse(MongoBaseResponse):
    """Returned by all test run endpoints."""
    id: PyObjectIdStr
    project_id: PyObjectIdStr
    status: str
    base_url: str
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_cases: int | None = None
    passed_cases: int | None = None
    failed_cases: int | None = None


class TestRunStatusResponse(BaseModel):
    status: str
    total_cases: int | None = None
    completed_cases: int | None = None
    passed_cases: int | None = None
    failed_cases: int | None = None
    progress_pct: float | None = None


# ── Test Result ───────────────────────────────────────────────────────────────

class TestResultResponse(MongoBaseResponse):
    """Returned by GET /runs/{run_id}/results."""
    id: PyObjectIdStr
    test_run_id: PyObjectIdStr
    test_case_id: PyObjectIdStr
    passed: bool
    status: str
    actual_status_code: int | None = None
    latency_ms: float
    response_time_ms: float
    ai_failure_analysis: dict[str, Any] | None = None
