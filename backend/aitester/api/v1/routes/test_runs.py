"""
Test Runs API routes — /api/v1/projects/{project_id}/runs/*

All endpoints require a valid JWT and enforce ownership:
- The project must belong to the authenticated user.
- Test runs are executed as background tasks using the spec stored on the project.
"""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aitester.api.dependencies import get_current_user, get_db
from aitester.db.models.project import Project
from aitester.db.models.test_case import TestCase
from aitester.db.models.test_result import TestResult
from aitester.db.models.test_run import TestRun
from aitester.db.models.user import User
from aitester.executor.runner import AsyncTestRunner
from aitester.generators.coordinator import TestGenerationCoordinator
from aitester.schemas.test_run import (
    TestResultResponse,
    TestRunCreate,
    TestRunResponse,
    TestRunStatusResponse,
)

router = APIRouter(tags=["Test Runs"])
logger = logging.getLogger("aitester.api")


# ─── Helper: resolve project + assert ownership ────────────────────────────────

async def _get_owned_project(
    project_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Project:
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


# ─── Aggregate counts helper ──────────────────────────────────────────────────

async def _attach_counts(run: TestRun, db: AsyncSession) -> TestRunResponse:
    """Build a TestRunResponse with aggregated pass/fail counts."""
    total_q = await db.execute(
        select(func.count()).where(TestResult.test_run_id == run.id)
    )
    passed_q = await db.execute(
        select(func.count()).where(
            TestResult.test_run_id == run.id, TestResult.passed.is_(True)
        )
    )
    total = total_q.scalar_one()
    passed = passed_q.scalar_one()
    failed = total - passed

    resp = TestRunResponse.model_validate(run)
    resp.total_cases = total
    resp.passed_cases = passed
    resp.failed_cases = failed
    return resp


# ─── Background executor ───────────────────────────────────────────────────────

async def _execute_test_run(
    test_run_id: uuid.UUID,
    base_url: str,
    spec_dict: dict,
    types: list[str],
    enable_ai: bool,
) -> None:
    """
    Background task: generate + execute test cases.
    Uses a fresh DB session since this runs outside the request lifecycle.
    """
    from aitester.db.session import AsyncSessionLocal
    from aitester.parser.parser import parse_spec_dict

    try:
        # Mark as RUNNING
        async with AsyncSessionLocal() as db:
            run = await db.get(TestRun, test_run_id)
            if run:
                run.status = "RUNNING"
                run.started_at = datetime.now(UTC)
                await db.commit()

        # Parse spec from the project's stored JSON
        spec = parse_spec_dict(spec_dict)

        # Generate test cases
        coordinator = TestGenerationCoordinator(enable_ai=enable_ai, types=types)
        test_cases = await coordinator.generate_async(spec, str(test_run_id))

        if not test_cases:
            async with AsyncSessionLocal() as db:
                run = await db.get(TestRun, test_run_id)
                if run:
                    run.status = "COMPLETED"
                    run.completed_at = datetime.now(UTC)
                    await db.commit()
            return

        # Persist generated test cases
        async with AsyncSessionLocal() as db:
            db.add_all(test_cases)
            await db.commit()

        # Execute
        runner = AsyncTestRunner(base_url=base_url)
        results = await runner.execute_all(test_cases)

        async with AsyncSessionLocal() as db:
            run = await db.get(TestRun, test_run_id)
            if run:
                db.add_all(results)
                run.status = "COMPLETED"
                run.completed_at = datetime.now(UTC)
                await db.commit()

    except Exception as exc:
        logger.error(f"Test run {test_run_id} failed: {exc}", exc_info=True)
        async with AsyncSessionLocal() as db:
            run = await db.get(TestRun, test_run_id)
            if run:
                run.status = "FAILED"
                run.completed_at = datetime.now(UTC)
                await db.commit()


# ─── Create Test Run ───────────────────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/runs",
    response_model=TestRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Launch a new test run for a project",
)
async def create_test_run(
    project_id: uuid.UUID,
    run_create: TestRunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestRunResponse:
    """
    Creates a TestRun record and dispatches execution as a background task.
    Uses the OpenAPI spec stored on the project (uploaded via /upload-spec).
    """
    project = await _get_owned_project(project_id, current_user, db)

    if not project.openapi_spec:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project has no uploaded OpenAPI spec. Upload one via POST /projects/{id}/upload-spec first.",
        )

    new_run = TestRun(
        project_id=project_id,
        base_url=run_create.base_url,
        status="PENDING",
    )
    db.add(new_run)
    await db.commit()
    await db.refresh(new_run)

    background_tasks.add_task(
        _execute_test_run,
        test_run_id=new_run.id,
        base_url=run_create.base_url,
        spec_dict=project.openapi_spec,
        types=list(run_create.types),
        enable_ai=run_create.enable_ai,
    )

    return await _attach_counts(new_run, db)


# ─── List Test Runs ────────────────────────────────────────────────────────────

@router.get(
    "/projects/{project_id}/runs",
    response_model=list[TestRunResponse],
    summary="List test runs for a project",
)
async def list_test_runs(
    project_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TestRunResponse]:
    await _get_owned_project(project_id, current_user, db)

    result = await db.execute(
        select(TestRun)
        .where(TestRun.project_id == project_id)
        .order_by(TestRun.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    runs = result.scalars().all()
    return [await _attach_counts(r, db) for r in runs]


# ─── Get Single Test Run ───────────────────────────────────────────────────────

@router.get(
    "/runs/{run_id}",
    response_model=TestRunResponse,
    summary="Get a single test run",
)
async def get_test_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestRunResponse:
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found.")
    # Verify ownership via the project
    await _get_owned_project(run.project_id, current_user, db)
    return await _attach_counts(run, db)


# ─── Get Run Status (lightweight poll endpoint) ────────────────────────────────

@router.get(
    "/runs/{run_id}/status",
    response_model=TestRunStatusResponse,
    summary="Poll status of a test run",
)
async def get_test_run_status(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestRunStatusResponse:
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found.")
    await _get_owned_project(run.project_id, current_user, db)

    total_q = await db.execute(
        select(func.count()).where(TestResult.test_run_id == run_id)
    )
    passed_q = await db.execute(
        select(func.count()).where(
            TestResult.test_run_id == run_id, TestResult.passed.is_(True)
        )
    )
    total = total_q.scalar_one()
    passed = passed_q.scalar_one()
    failed = total - passed
    progress = round(total / max(total, 1) * 100, 1) if total else 0

    return TestRunStatusResponse(
        status=run.status,
        total_cases=total,
        completed_cases=total,
        passed_cases=passed,
        failed_cases=failed,
        progress_pct=progress,
    )


# ─── Get Run Results ───────────────────────────────────────────────────────────

@router.get(
    "/runs/{run_id}/results",
    response_model=list[TestResultResponse],
    summary="Get all test results for a run",
)
async def get_test_run_results(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TestResultResponse]:
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found.")
    await _get_owned_project(run.project_id, current_user, db)

    result = await db.execute(
        select(TestResult).where(TestResult.test_run_id == run_id)
    )
    return list(result.scalars().all())


# ─── Delete Test Run ───────────────────────────────────────────────────────────

@router.delete(
    "/runs/{run_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a test run",
)
async def delete_test_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found.")
    await _get_owned_project(run.project_id, current_user, db)
    await db.delete(run)
    await db.commit()
