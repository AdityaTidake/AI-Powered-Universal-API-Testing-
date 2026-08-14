"""
aitester.worker.tasks — Core Celery task definitions for SpecGuard AI.

Tasks
─────
execute_test_run
    Runs the full test pipeline for a single TestRun document:
    1. Parse the uploaded OpenAPI spec.
    2. Generate functional, edge-case, security, and AI test cases.
    3. Execute all test cases concurrently against the target API.
    4. Persist TestCase and TestResult documents to MongoDB.
    5. Update the TestRun status (RUNNING → COMPLETED | FAILED).

Dispatch from the API layer:
    from aitester.worker.tasks import execute_test_run
    execute_test_run.apply_async(
        kwargs=dict(
            test_run_id=str(new_run.id),
            base_url=run_create.base_url,
            spec_dict=project.openapi_spec,
            types=list(run_create.types),
            enable_ai=run_create.enable_ai,
        ),
        queue="test_runs",
    )
"""

import logging
from datetime import UTC, datetime

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from aitester.worker.utils import ensure_db, run_async

logger = logging.getLogger("aitester.worker.tasks")


# ─── Async Pipeline ───────────────────────────────────────────────────────────

async def _run_pipeline(
    test_run_id: str,
    base_url: str,
    spec_dict: dict,
    types: list[str],
    enable_ai: bool,
) -> dict:
    """
    Full async test-run pipeline.

    Returns a summary dict on completion or raises on fatal error.
    The caller (execute_test_run) is responsible for FAILED status writes.
    """
    from beanie import PydanticObjectId

    from aitester.db.models import TestCase, TestResult, TestRun
    from aitester.executor.runner import AsyncTestRunner
    from aitester.generators.coordinator import TestGenerationCoordinator
    from aitester.parser.parser import parse_spec_dict

    await ensure_db()

    run_oid = PydanticObjectId(test_run_id)

    # ── Step 1: Mark RUNNING ──────────────────────────────────────────────────
    run = await TestRun.get(run_oid)
    if not run:
        raise ValueError(f"TestRun {test_run_id} not found in database")

    run.status = "RUNNING"
    run.started_at = datetime.now(UTC)
    await run.save()
    logger.info("[%s] Status → RUNNING", test_run_id)

    # ── Step 2: Parse spec ────────────────────────────────────────────────────
    spec = parse_spec_dict(spec_dict)
    logger.info("[%s] Spec parsed: %d endpoints", test_run_id, len(spec.endpoints))

    # ── Step 3: Generate test cases ───────────────────────────────────────────
    coordinator = TestGenerationCoordinator(enable_ai=enable_ai, types=types)
    test_cases = await coordinator.generate_async(spec, test_run_id)
    logger.info("[%s] Generated %d test cases", test_run_id, len(test_cases))

    if not test_cases:
        run = await TestRun.get(run_oid)
        if run:
            run.status = "COMPLETED"
            run.completed_at = datetime.now(UTC)
            await run.save()
        logger.warning("[%s] No test cases generated — marking COMPLETED", test_run_id)
        return {"test_run_id": test_run_id, "total_cases": 0, "passed": 0, "failed": 0}

    # ── Step 4: Persist test cases ────────────────────────────────────────────
    await TestCase.insert_many(test_cases)  # type: ignore[arg-type]

    # ── Step 5: Execute concurrently ──────────────────────────────────────────
    runner = AsyncTestRunner(base_url=base_url, enable_ai=enable_ai)
    results = await runner.execute_all(test_cases)
    logger.info("[%s] Executed %d tests", test_run_id, len(results))

    # ── Step 6: Persist results ───────────────────────────────────────────────
    if results:
        await TestResult.insert_many(results)  # type: ignore[arg-type]

    # ── Step 7: Mark COMPLETED ────────────────────────────────────────────────
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count

    run = await TestRun.get(run_oid)
    if run:
        run.status = "COMPLETED"
        run.completed_at = datetime.now(UTC)
        await run.save()

        # Send Email Notification
        try:
            from aitester.db.models import Project, User
            from aitester.core.email import send_run_completion_email
            
            project = await Project.get(run.project_id)
            if project:
                user = await User.get(project.owner_id)
                if user:
                    total_cases = len(results)
                    pass_rate = round(passed_count / total_cases * 100, 1) if total_cases > 0 else 0.0
                    sec_fails = sum(1 for r in results if not r.passed and r.ai_failure_analysis and r.ai_failure_analysis.get("is_security_concern"))
                    sec_score = round(max(0.0, 100.0 - (sec_fails / total_cases) * 100), 1) if total_cases > 0 else 100.0
                    
                    # Offload to asyncio threadpool to avoid blocking event loop during SMTP sending
                    import asyncio
                    await asyncio.to_thread(send_run_completion_email, user.email, run, project.name, total_cases, pass_rate, sec_score)
        except Exception as e:
            logger.error("Failed to send completion email: %s", e)

        # Publish final completion to WebSocket
        try:
            import redis.asyncio as aioredis
            import json
            from aitester.core.config import settings
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await r.publish(f"run_progress:{test_run_id}", json.dumps({"run_finished": True}))
            await r.close()
        except Exception as e:
            logger.error(f"Failed to publish run_finished: {e}")

    logger.info(
        "[%s] Status → COMPLETED (passed=%d failed=%d)",
        test_run_id,
        passed_count,
        failed_count,
    )
    return {
        "test_run_id": test_run_id,
        "total_cases": len(results),
        "passed": passed_count,
        "failed": failed_count,
    }


async def _mark_failed(test_run_id: str, reason: str) -> None:
    """Best-effort: write FAILED status to the database."""
    try:
        from beanie import PydanticObjectId
        from aitester.db.models import TestRun, Project, User
        from aitester.core.email import send_run_failure_email

        await ensure_db()
        run = await TestRun.get(PydanticObjectId(test_run_id))
        if run and run.status not in ("COMPLETED", "FAILED"):
            run.status = "FAILED"
            run.completed_at = datetime.now(UTC)
            await run.save()
            
            # Send Failure Email Notification
            try:
                project = await Project.get(run.project_id)
                if project:
                    user = await User.get(project.owner_id)
                    if user:
                        import asyncio
                        await asyncio.to_thread(send_run_failure_email, user.email, test_run_id, reason)
            except Exception as e:
                logger.error("Failed to send failure email: %s", e)
                
            logger.info("[%s] Status → FAILED (reason: %s)", test_run_id, reason)
    except Exception:
        logger.exception("[%s] Could not write FAILED status to DB", test_run_id)


# ─── Celery Task ──────────────────────────────────────────────────────────────

@shared_task(
    name="aitester.worker.tasks.execute_test_run",
    bind=True,
    # No auto-retry — run status is persisted in MongoDB regardless
    max_retries=0,
    # Hard kill after 30 min (SIGKILL)
    time_limit=1800,
    # Soft warning at 25 min (SIGTERM) — allows graceful cleanup
    soft_time_limit=1500,
    # Acknowledge only after task completes (re-queue on crash)
    acks_late=True,
    queue="test_runs",
)
def execute_test_run(
    self,
    test_run_id: str,
    base_url: str,
    spec_dict: dict,
    types: list[str],
    enable_ai: bool = True,
) -> dict:
    """
    Celery task — runs the full test pipeline for a TestRun.

    Args:
        test_run_id: MongoDB ObjectId string of the TestRun document.
        base_url:    Target API base URL (e.g. "https://api.example.com").
        spec_dict:   OpenAPI spec as a plain Python dict (JSON-serialisable).
        types:       Generator types to run (e.g. ["functional", "edge", "security"]).
        enable_ai:   Whether to run AI failure analysis and AI test generation.

    Returns:
        Summary dict with test_run_id, total_cases, passed, failed counts.
    """
    logger.info("[%s] Task started (worker pid=%d)", test_run_id, __import__("os").getpid())

    # Update Celery task state so Flower / monitoring can show progress
    self.update_state(
        state="RUNNING",
        meta={"test_run_id": test_run_id, "stage": "starting"},
    )

    try:
        result = run_async(
            _run_pipeline(
                test_run_id=test_run_id,
                base_url=base_url,
                spec_dict=spec_dict,
                types=types,
                enable_ai=enable_ai,
            )
        )
        logger.info("[%s] Task completed successfully", test_run_id)
        return result

    except SoftTimeLimitExceeded:
        # Worker received SIGTERM — 5 minutes before hard kill
        logger.error("[%s] Soft time limit exceeded — cleaning up", test_run_id)
        run_async(_mark_failed(test_run_id, "soft_time_limit_exceeded"))
        raise  # Re-raise so Celery marks task as FAILED

    except Exception as exc:
        logger.error("[%s] Task failed: %s", test_run_id, exc, exc_info=True)
        run_async(_mark_failed(test_run_id, str(exc)))
        raise  # Re-raise so Celery records correct FAILURE state


# ─── Cancel / Revoke helper (used by API if needed) ──────────────────────────

def cancel_test_run(task_id: str) -> None:
    """
    Revoke a queued or running test run Celery task.

    Args:
        task_id: The Celery task ID returned by .apply_async().

    Note:
        This sends a SIGTERM to the worker process. The SoftTimeLimitExceeded
        handler in execute_test_run will mark the TestRun as FAILED.
    """
    from aitester.worker import celery_app

    celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")
    logger.info("Revoked Celery task %s", task_id)
