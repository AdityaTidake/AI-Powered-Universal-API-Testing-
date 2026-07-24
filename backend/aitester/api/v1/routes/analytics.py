"""
Analytics API routes — /api/v1/analytics/*
Aggregates live data from MongoDB for the authenticated user's projects.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends

from aitester.api.dependencies import get_current_user
from aitester.db.models import Project, TestResult, TestRun, User
from aitester.schemas.analytics import (
    CoverageProjectResponse,
    DashboardStatsResponse,
    TrendPointResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger("aitester.api")


# ─── Dashboard Stats ──────────────────────────────────────────────────────────

@router.get(
    "/dashboard",
    response_model=DashboardStatsResponse,
    summary="Aggregate stats for the authenticated user's dashboard",
)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
) -> DashboardStatsResponse:
    from aitester.core.config import settings as cfg

    # Project count
    total_projects = await Project.find(Project.owner_id == current_user.id).count()

    if total_projects == 0:
        return DashboardStatsResponse(
            total_projects=0,
            total_runs=0,
            pass_rate=0.0,
            avg_latency_ms=0.0,
            runs_this_month=current_user.monthly_run_count,
            plan_limit=cfg.FREE_PLAN_MONTHLY_RUNS if current_user.plan == "free" else cfg.PRO_PLAN_MONTHLY_RUNS,
        )

    # All project IDs for this user
    projects = await Project.find(Project.owner_id == current_user.id).to_list()
    project_ids = [p.id for p in projects]

    # Total runs
    total_runs = await TestRun.find({"project_id": {"$in": project_ids}}).count()

    # All run IDs
    runs = await TestRun.find({"project_id": {"$in": project_ids}}).to_list()
    run_ids = [r.id for r in runs]

    pass_rate = 0.0
    avg_latency_ms = 0.0

    if run_ids:
        total_results  = await TestResult.find({"test_run_id": {"$in": run_ids}}).count()
        passed_results = await TestResult.find(
            {"test_run_id": {"$in": run_ids}, "passed": True}
        ).count()

        if total_results > 0:
            pass_rate = round(passed_results / total_results * 100, 1)

        # Average latency using aggregation pipeline
        pipeline = [
            {"$match": {"test_run_id": {"$in": run_ids}}},
            {"$group": {"_id": None, "avg_lat": {"$avg": "$latency_ms"}}},
        ]
        agg = await TestResult.aggregate(pipeline).to_list()
        if agg:
            avg_latency_ms = round(float(agg[0].get("avg_lat") or 0), 1)

    plan_limit = (
        cfg.FREE_PLAN_MONTHLY_RUNS if current_user.plan == "free"
        else cfg.PRO_PLAN_MONTHLY_RUNS
    )

    return DashboardStatsResponse(
        total_projects=total_projects,
        total_runs=total_runs,
        pass_rate=pass_rate,
        avg_latency_ms=avg_latency_ms,
        runs_this_month=current_user.monthly_run_count,
        plan_limit=plan_limit,
    )


# ─── Trends ───────────────────────────────────────────────────────────────────

@router.get(
    "/trends",
    response_model=list[TrendPointResponse],
    summary="Daily pass/fail counts for the last 14 days",
)
async def get_trends(
    current_user: User = Depends(get_current_user),
) -> list[TrendPointResponse]:
    today = datetime.now(UTC).date()
    days  = [today - timedelta(days=i) for i in range(13, -1, -1)]

    projects   = await Project.find(Project.owner_id == current_user.id).to_list()
    project_ids = [p.id for p in projects]

    if not project_ids:
        return [TrendPointResponse(date=d.strftime("%b %-d"), passed=0, failed=0) for d in days]

    runs   = await TestRun.find({"project_id": {"$in": project_ids}}).to_list()
    run_ids = [r.id for r in runs]

    cutoff = datetime.now(UTC) - timedelta(days=14)

    # Aggregation pipeline for daily bucketing
    pipeline = [
        {"$match": {
            "test_run_id": {"$in": run_ids},
            "created_at": {"$gte": cutoff},
        }},
        {"$group": {
            "_id": {
                "y": {"$year": "$created_at"},
                "m": {"$month": "$created_at"},
                "d": {"$dayOfMonth": "$created_at"},
            },
            "passed": {"$sum": {"$cond": ["$passed", 1, 0]}},
            "failed": {"$sum": {"$cond": ["$passed", 0, 1]}},
        }},
    ]
    agg = await TestResult.aggregate(pipeline).to_list()

    # Map aggregation results to date keys
    buckets: dict[str, dict] = {}
    for item in agg:
        key = f"{item['_id']['y']:04d}-{item['_id']['m']:02d}-{item['_id']['d']:02d}"
        buckets[key] = {"passed": item["passed"], "failed": item["failed"]}

    result = []
    for d in days:
        key   = d.isoformat()
        label = d.strftime("%b %d").lstrip("0") if hasattr(d, "strftime") else str(d)
        b     = buckets.get(key, {"passed": 0, "failed": 0})
        result.append(TrendPointResponse(date=label, passed=b["passed"], failed=b["failed"]))

    return result


# ─── Coverage ─────────────────────────────────────────────────────────────────

@router.get(
    "/coverage",
    response_model=list[CoverageProjectResponse],
    summary="Endpoint coverage per project",
)
async def get_coverage(
    current_user: User = Depends(get_current_user),
) -> list[CoverageProjectResponse]:
    projects = await Project.find(Project.owner_id == current_user.id).to_list()

    coverage_list = []
    for proj in projects:
        spec = proj.openapi_spec or {}
        paths = spec.get("paths", {})
        endpoints_total = sum(len(methods) for methods in paths.values()) if paths else 0

        # Count distinct test cases created for runs under this project
        runs = await TestRun.find(TestRun.project_id == proj.id).to_list()
        run_ids = [r.id for r in runs]

        endpoints_tested = 0
        if run_ids:
            endpoints_tested = await TestResult.find(
                {"test_run_id": {"$in": run_ids}}
            ).count()
            endpoints_tested = min(endpoints_tested, endpoints_total)

        coverage_pct = (
            round(endpoints_tested / endpoints_total * 100, 1) if endpoints_total else 0.0
        )

        coverage_list.append(CoverageProjectResponse(
            project_id=str(proj.id),
            project_name=proj.name,
            endpoints_total=endpoints_total,
            endpoints_tested=endpoints_tested,
            coverage_pct=coverage_pct,
        ))

    return coverage_list
