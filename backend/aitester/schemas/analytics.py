"""Pydantic schemas for Analytics endpoints."""

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
