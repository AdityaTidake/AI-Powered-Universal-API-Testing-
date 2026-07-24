"""
Beanie Document models for SpecGuard AI — MongoDB.

All models inherit from beanie.Document.
Timestamps (created_at, updated_at) are added automatically where needed.
"""

from datetime import UTC, datetime
from typing import Any

import pymongo
from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


# ─── User ──────────────────────────────────────────────────────────────────────

class User(Document):
    """Platform user. Owns projects and belongs to organisations."""

    email: Indexed(str, unique=True)  # type: ignore[valid-type]
    hashed_password: str
    full_name: str
    is_active: bool = True
    is_verified: bool = False

    plan: str = "free"               # "free" | "pro" | "enterprise"
    monthly_run_count: int = 0
    monthly_run_reset_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "users"
        indexes = [
            pymongo.IndexModel([("email", pymongo.ASCENDING)], unique=True),
        ]


# ─── Organisation ──────────────────────────────────────────────────────────────

class Organization(Document):
    name: str
    slug: str
    owner_id: PydanticObjectId
    member_ids: list[PydanticObjectId] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "organizations"


# ─── Project ───────────────────────────────────────────────────────────────────

class Project(Document):
    name: str
    description: str | None = None
    openapi_spec: dict[str, Any] | None = None

    owner_id: PydanticObjectId
    org_id: PydanticObjectId | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "projects"
        indexes = [
            pymongo.IndexModel([("owner_id", pymongo.ASCENDING)]),
        ]


# ─── TestRun ───────────────────────────────────────────────────────────────────

class TestRun(Document):
    project_id: PydanticObjectId
    base_url: str
    status: str = "PENDING"          # PENDING | RUNNING | COMPLETED | FAILED

    started_at: datetime | None = None
    completed_at: datetime | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "test_runs"
        indexes = [
            pymongo.IndexModel([("project_id", pymongo.ASCENDING)]),
        ]


# ─── TestCase ──────────────────────────────────────────────────────────────────

class TestCase(Document):
    test_run_id: PydanticObjectId
    category: str                    # FUNCTIONAL | EDGE | AI | SECURITY
    endpoint: str
    method: str

    headers: dict[str, Any] | None = None
    query_params: dict[str, Any] | None = None
    body: dict[str, Any] | None = None
    expected_status_code: int | None = None
    expected_schema: dict[str, Any] | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "test_cases"
        indexes = [
            pymongo.IndexModel([("test_run_id", pymongo.ASCENDING)]),
        ]


# ─── TestResult ────────────────────────────────────────────────────────────────

class TestResult(Document):
    test_run_id: PydanticObjectId
    test_case_id: PydanticObjectId

    passed: bool = False
    status: str = "passed"

    actual_status_code: int | None = None
    actual_body: str | None = None
    latency_ms: float = 0.0
    response_time_ms: float = 0.0

    ai_failure_analysis: dict[str, Any] | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "test_results"
        indexes = [
            pymongo.IndexModel([("test_run_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("test_case_id", pymongo.ASCENDING)]),
        ]
