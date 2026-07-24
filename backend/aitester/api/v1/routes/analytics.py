"""
Analytics API routes — /api/v1/analytics/*

Aggregates live data from the DB for the authenticated user's projects.
All endpoints require a valid JWT.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aitester.api.dependencies import get_current_user, get_db
from aitester.db.models.project import Project
from aitester.db.models.test_result import TestResult
from aitester.db.models.test_run import TestRun
from aitester.db.models.user import User
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardStatsResponse:
    from aitester.core.config import settings as cfg

    # ── Project count ─────────────────────────────────────────────────────────
    proj_q = await db.execute(
        select(func.count(Project.id)).where(Project.owner_id == current_user.id)
    )
    total_projects: int = proj_q.scalar_one() or 0

    # ── All run IDs for this user ─────────────────────────────────────────────
    user_project_ids_q = await db.execute(
        select(Project.id).where(Project.owner_id == current_user.id)
    )
    user_project_ids = [r for r in user_project_ids_q.scalars().all()]

    if not user_project_ids:
        return DashboardStatsResponse(
            total_projects=total_projects,
            total_runs=0,
            pass_rate=0.0,
            avg_latency_ms=0.0,
            runs_this_month=current_user.monthly_run_count,
            plan_limit=cfg.FREE_PLAN_MONTHLY_RUNS if current_user.plan == "free" else cfg.PRO_PLAN_MONTHLY_RUNS,
        )

    # ── Total runs ────────────────────────────────────────────────────────────
    runs_q = await db.execute(
        select(func.count(TestRun.id)).where(
            TestRun.project_id.in_(user_project_ids)
        )
    )
    total_runs: int = runs_q.scalar_one() or 0

    # ── Pass rate + avg latency across all results ────────────────────────────
    run_ids_q = await db.execute(
        select(TestRun.id).where(TestRun.project_id.in_(user_project_ids))
    )
    run_ids = [r for r in run_ids_q.scalars().all()]

    pass_rate = 0.0
    avg_latency_ms = 0.0

    if run_ids:
        agg_q = await db.execute(
            select(
                func.count(TestResult.id).label("total"),
                func.sum(case((TestResult.passed.is_(True), 1), else_=0)).label("passed"),
                func.avg(TestResult.latency_ms).label("avg_latency"),
            ).where(TestResult.test_run_id.in_(run_ids))
        )
        row = agg_q.one()
        if row.total and row.total > 0:
            pass_rate = round((row.passed or 0) / row.total * 100, 1)
        avg_latency_ms = round(float(row.avg_latency or 0), 1)

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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TrendPointResponse]:
    # Build date range
    today = datetime.now(UTC).date()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]

    user_project_ids_q = await db.execute(
        select(Project.id).where(Project.owner_id == current_user.id)
    )
    user_project_ids = list(user_project_ids_q.scalars().all())

    if not user_project_ids:
        return [TrendPointResponse(date=d.strftime("%-d %b") if hasattr(d, 'strftime') else str(d), passed=0, failed=0) for d in days]

    run_ids_q = await db.execute(
        select(TestRun.id).where(TestRun.project_id.in_(user_project_ids))
    )
    run_ids = list(run_ids_q.scalars().all())

    # Default bucket: {date_str: {passed: 0, failed: 0}}
    buckets: dict[str, dict[str, int]] = {}
    for d in days:
        label = d.strftime("%b %-d") if hasattr(d, 'strftime') else str(d)
        buckets[d.isoformat()] = {"label": label, "passed": 0, "failed": 0}

    if run_ids:
        results_q = await db.execute(
            select(
                func.date(TestResult.created_at).label("day"),
                func.sum(case((TestResult.passed.is_(True), 1), else_=0)).label("passed"),
                func.sum(case((TestResult.passed.is_(False), 1), else_=0)).label("failed"),
            )
            .where(
                TestResult.test_run_id.in_(run_ids),
                TestResult.created_at >= datetime.now(UTC) - timedelta(days=14),
            )
            .group_by(func.date(TestResult.created_at))
        )
        for row in results_q.all():
            key = str(row.day)
            if key in buckets:
                buckets[key]["passed"] = int(row.passed or 0)
                buckets[key]["failed"] = int(row.failed or 0)

    return [
        TrendPointResponse(date=v["label"], passed=v["passed"], failed=v["failed"])
        for v in buckets.values()
    ]


# ─── Coverage ─────────────────────────────────────────────────────────────────

@router.get(
    "/coverage",
    response_model=list[CoverageProjectResponse],
    summary="Endpoint coverage per project",
)
async def get_coverage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CoverageProjectResponse]:
    result = await db.execute(
        select(Project).where(Project.owner_id == current_user.id)
    )
    projects = result.scalars().all()

    coverage_list = []
    for proj in projects:
        spec = proj.openapi_spec or {}
        paths = spec.get("paths", {})
        # Count total operation entries in the spec
        endpoints_total = sum(len(methods) for methods in paths.values()) if paths else 0

        # Count distinct endpoints actually tested
        tested_q = await db.execute(
            select(func.count(func.distinct(
                func.concat(
                    TestResult.test_run_id.cast("text"),
                    TestResult.test_case_id.cast("text"),
                )
            ))).select_from(TestResult)
            .join(TestRun, TestResult.test_run_id == TestRun.id)
            .where(TestRun.project_id == proj.id)
        )
        endpoints_tested = min(tested_q.scalar_one() or 0, endpoints_total)
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
