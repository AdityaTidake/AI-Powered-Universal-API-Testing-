"""Pydantic schemas for TestRun and TestResult resources."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


# ── Test Run ──────────────────────────────────────────────────────────────────

class TestRunCreate(BaseModel):
    """Body for POST /projects/{project_id}/runs.
    spec_path removed — runs now use the spec already stored on the project.
    """
    base_url: str
    types: list[Literal["functional", "edge", "security", "ai"]] = ["functional"]
    enable_ai: bool = False


class TestRunResponse(BaseModel):
    """Returned by all test run endpoints."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    status: str
    base_url: str
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    # Aggregate counts (computed by the route, not stored columns)
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

class TestResultResponse(BaseModel):
    """Returned by GET /runs/{run_id}/results."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_run_id: uuid.UUID
    test_case_id: uuid.UUID
    passed: bool
    status: str
    actual_status_code: int | None = None
    latency_ms: float
    response_time_ms: float
    ai_failure_analysis: dict[str, Any] | None = None
