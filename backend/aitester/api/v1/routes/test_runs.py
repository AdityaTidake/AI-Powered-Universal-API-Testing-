"""
Test Runs API routes — /api/v1/projects/{project_id}/runs/*

All endpoints require a valid JWT and enforce ownership.
Runs are executed as background tasks using the spec stored on the project.
"""

import logging
from datetime import UTC, datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from aitester.api.dependencies import get_current_user
from aitester.db.models import Project, TestCase, TestResult, TestRun, User
from aitester.schemas.test_run import (
    TestResultResponse,
    TestRunCreate,
    TestRunResponse,
    TestRunStatusResponse,
)

router = APIRouter(tags=["Test Runs"])
logger = logging.getLogger("aitester.api")


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_owned_project(project_id: str, current_user: User) -> Project:
    try:
        project = await Project.get(PydanticObjectId(project_id))
    except Exception:
        project = None
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


async def _attach_counts(run: TestRun) -> TestRunResponse:
    """Build TestRunResponse with aggregated pass/fail counts from MongoDB."""
    total  = await TestResult.find(TestResult.test_run_id == run.id).count()
    passed = await TestResult.find(
        TestResult.test_run_id == run.id,
        TestResult.passed == True,  # noqa: E712
    ).count()
    failed = total - passed

    resp = TestRunResponse(
        id=str(run.id),
        project_id=str(run.project_id),
        base_url=run.base_url,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        total_cases=total,
        passed_cases=passed,
        failed_cases=failed,
    )
    return resp


# ─── Background Executor ──────────────────────────────────────────────────────

async def _execute_test_run(
    test_run_id: str,
    base_url: str,
    spec_dict: dict,
    types: list[str],
    enable_ai: bool,
) -> None:
    """Background task: generate + execute test cases then persist results."""
    from aitester.db.init import init_db  # ensure connection is initialised
    from aitester.parser.parser import parse_spec_dict

    try:
        run = await TestRun.get(PydanticObjectId(test_run_id))
        if run:
            run.status = "RUNNING"
            run.started_at = datetime.now(UTC)
            await run.save()

        spec = parse_spec_dict(spec_dict)

        from aitester.generators.coordinator import TestGenerationCoordinator
        coordinator = TestGenerationCoordinator(enable_ai=enable_ai, types=types)
        test_cases  = await coordinator.generate_async(spec, test_run_id)

        if not test_cases:
            run = await TestRun.get(PydanticObjectId(test_run_id))
            if run:
                run.status = "COMPLETED"
                run.completed_at = datetime.now(UTC)
                await run.save()
            return

        await TestCase.insert_many(test_cases)  # type: ignore

        from aitester.executor.runner import AsyncTestRunner
        runner  = AsyncTestRunner(base_url=base_url, enable_ai=enable_ai)
        results = await runner.execute_all(test_cases)

        if results:
            await TestResult.insert_many(results)  # type: ignore

        run = await TestRun.get(PydanticObjectId(test_run_id))
        if run:
            run.status = "COMPLETED"
            run.completed_at = datetime.now(UTC)
            await run.save()

    except Exception as exc:
        logger.error(f"Test run {test_run_id} failed: {exc}", exc_info=True)
        run = await TestRun.get(PydanticObjectId(test_run_id))
        if run:
            run.status = "FAILED"
            run.completed_at = datetime.now(UTC)
            await run.save()


# ─── Create Run ───────────────────────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/runs",
    response_model=TestRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Launch a new test run for a project",
)
async def create_test_run(
    project_id: str,
    run_create: TestRunCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> TestRunResponse:
    project = await _get_owned_project(project_id, current_user)

    if not project.openapi_spec:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Project has no uploaded OpenAPI spec. Upload one via POST /projects/{id}/upload-spec first.",
        )

    new_run = TestRun(
        project_id=project.id,  # type: ignore
        base_url=run_create.base_url,
        status="PENDING",
    )
    await new_run.insert()

    background_tasks.add_task(
        _execute_test_run,
        test_run_id=str(new_run.id),
        base_url=run_create.base_url,
        spec_dict=project.openapi_spec,
        types=list(run_create.types),
        enable_ai=run_create.enable_ai,
    )

    return await _attach_counts(new_run)


# ─── List Runs ─────────────────────────────────────────────────────────────────

@router.get(
    "/projects/{project_id}/runs",
    response_model=list[TestRunResponse],
    summary="List test runs for a project",
)
async def list_test_runs(
    project_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
) -> list[TestRunResponse]:
    await _get_owned_project(project_id, current_user)

    try:
        pid = PydanticObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project_id.")

    runs = await (
        TestRun.find(TestRun.project_id == pid)
        .sort("-created_at")
        .skip(skip)
        .limit(limit)
        .to_list()
    )
    return [await _attach_counts(r) for r in runs]


# ─── Get Single Run ────────────────────────────────────────────────────────────

@router.get(
    "/runs/{run_id}",
    response_model=TestRunResponse,
    summary="Get a single test run",
)
async def get_test_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
) -> TestRunResponse:
    try:
        run = await TestRun.get(PydanticObjectId(run_id))
    except Exception:
        run = None
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found.")
    await _get_owned_project(str(run.project_id), current_user)
    return await _attach_counts(run)


# ─── Status Poll ──────────────────────────────────────────────────────────────

@router.get(
    "/runs/{run_id}/status",
    response_model=TestRunStatusResponse,
    summary="Poll status of a test run",
)
async def get_test_run_status(
    run_id: str,
    current_user: User = Depends(get_current_user),
) -> TestRunStatusResponse:
    try:
        run = await TestRun.get(PydanticObjectId(run_id))
    except Exception:
        run = None
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found.")
    await _get_owned_project(str(run.project_id), current_user)

    total  = await TestResult.find(TestResult.test_run_id == run.id).count()
    passed = await TestResult.find(
        TestResult.test_run_id == run.id, TestResult.passed == True  # noqa: E712
    ).count()
    failed = total - passed

    return TestRunStatusResponse(
        status=run.status,
        total_cases=total,
        completed_cases=total,
        passed_cases=passed,
        failed_cases=failed,
        progress_pct=100.0 if total > 0 else 0.0,
    )


# ─── Results ──────────────────────────────────────────────────────────────────

@router.get(
    "/runs/{run_id}/results",
    response_model=list[TestResultResponse],
    summary="Get all test results for a run",
)
async def get_test_run_results(
    run_id: str,
    current_user: User = Depends(get_current_user),
) -> list[TestResult]:
    try:
        run = await TestRun.get(PydanticObjectId(run_id))
    except Exception:
        run = None
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found.")
    await _get_owned_project(str(run.project_id), current_user)

    return await TestResult.find(TestResult.test_run_id == run.id).to_list()


# ─── Delete Run ───────────────────────────────────────────────────────────────

@router.delete(
    "/runs/{run_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a test run",
)
async def delete_test_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        run = await TestRun.get(PydanticObjectId(run_id))
    except Exception:
        run = None
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found.")
    await _get_owned_project(str(run.project_id), current_user)
    await run.delete()


# ─── Cancel Run ───────────────────────────────────────────────────────────────

@router.patch(
    "/runs/{run_id}/cancel",
    response_model=TestRunResponse,
    summary="Cancel an active (RUNNING or PENDING) test run",
)
async def cancel_test_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
) -> TestRunResponse:
    try:
        run = await TestRun.get(PydanticObjectId(run_id))
    except Exception:
        run = None
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found.")
    await _get_owned_project(str(run.project_id), current_user)

    if run.status not in ("RUNNING", "PENDING"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel a run with status '{run.status}'.",
        )

    run.status = "CANCELLED"
    run.completed_at = datetime.now(UTC)
    await run.save()
    logger.info("Run %s cancelled by user %s", run_id, current_user.id)

    return await _attach_counts(run)

