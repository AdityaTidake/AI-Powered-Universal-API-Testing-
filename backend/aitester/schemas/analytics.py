"""Pydantic schemas for Analytics endpoints."""
from datetime import datetime
from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_projects: int
    total_runs: int
    pass_rate: float          # 0.0 – 100.0
    avg_latency_ms: float
    runs_this_month: int
    plan_limit: int


class TrendPointResponse(BaseModel):
    date: str                 # "Jul 1" etc.
    passed: int
    failed: int


class CoverageProjectResponse(BaseModel):
    project_id: str
    project_name: str
    endpoints_total: int
    endpoints_tested: int
    coverage_pct: float

class OWASPIssue(BaseModel):
    category: str
    severity: str
    description: str

class AIInsightResponse(BaseModel):
    id: str
    run_id: str
    endpoint: str
    root_cause: str
    suggested_fix: str
    confidence: int
    security_score: int
    owasp_issues: list[OWASPIssue]
    created_at: datetime

