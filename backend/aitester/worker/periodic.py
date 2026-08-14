"""
aitester.worker.periodic — Celery Beat periodic (scheduled) tasks.

Schedule
────────
Task                      Cron              Description
─────────────────────────────────────────────────────────────────────
reset_monthly_run_counts  0 0 1 * *         Reset all user run quotas on the
                                            1st of every month at 00:00 UTC.
cleanup_stale_runs        0 * * * *         Hourly: find TestRuns stuck in
                                            PENDING/RUNNING for >2 h and mark
                                            them FAILED (catches crashed workers).

Running Beat:
    celery -A aitester.worker beat --loglevel=info --schedule=/tmp/celerybeat-schedule

Note: Run exactly ONE beat instance per deployment. Multiple instances cause
duplicate task submissions.
"""

import logging
from datetime import UTC, datetime, timedelta

from celery import shared_task
from celery.schedules import crontab

from aitester.worker.utils import ensure_db, run_async

logger = logging.getLogger("aitester.worker.periodic")


# ─── Beat Schedule ────────────────────────────────────────────────────────────
# Defined here and consumed by celery_app in __init__.py via the `include` list.
# Do NOT import celery_app here — that creates a circular import.
# Instead, the schedule is registered on the app after all modules are loaded.

BEAT_SCHEDULE = {
    # ── Monthly quota reset — 1st of every month at 00:00 UTC ─────────────────
    "reset-monthly-run-counts": {
        "task": "aitester.worker.periodic.reset_monthly_run_counts",
        "schedule": crontab(minute=0, hour=0, day_of_month=1),
        # Discard the beat message if not consumed within 1 hour
        "options": {"expires": 3600, "queue": "maintenance"},
    },
    # ── Stale-run cleanup — every hour ────────────────────────────────────────
    "cleanup-stale-runs": {
        "task": "aitester.worker.periodic.cleanup_stale_runs",
        "schedule": crontab(minute=0),   # top of every hour
        "options": {"expires": 3600, "queue": "maintenance"},
    },
}


# ─── Task 1: Monthly quota reset ──────────────────────────────────────────────

async def _reset_monthly_run_counts_async() -> int:
    """
    Reset monthly_run_count to 0 for every user using a single bulk update.
    Returns the number of users updated.
    """
    from aitester.db.models import User

    await ensure_db()

    now = datetime.now(UTC)
    result = await User.get_motor_collection().update_many(
        {},   # match ALL users
        {
            "$set": {
                "monthly_run_count": 0,
                "monthly_run_reset_at": now,
                "updated_at": now,
            }
        },
    )
    updated_count: int = result.modified_count
    logger.info("Monthly quota reset: %d users updated at %s", updated_count, now.isoformat())
    return updated_count


@shared_task(
    name="aitester.worker.periodic.reset_monthly_run_counts",
    bind=True,
    max_retries=3,
    default_retry_delay=300,   # 5-minute delay between retries
    queue="maintenance",
)
def reset_monthly_run_counts(self) -> dict:
    """
    Celery Beat task — resets all users' monthly run quota to 0.

    Scheduled: 00:00 UTC on the 1st of every month.
    Safe to re-run: idempotent (count is set to 0, not decremented).
    """
    logger.info("Executing scheduled task: reset_monthly_run_counts")
    try:
        updated_count = run_async(_reset_monthly_run_counts_async())
        result = {
            "task": "reset_monthly_run_counts",
            "users_reset": updated_count,
            "reset_at": datetime.now(UTC).isoformat(),
        }
        logger.info("Scheduled task succeeded: %s", result)
        return result
    except Exception as exc:
        logger.error("reset_monthly_run_counts failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)


# ─── Task 2: Stale run cleanup ────────────────────────────────────────────────

async def _cleanup_stale_runs_async(stale_threshold_hours: int = 2) -> int:
    """
    Find test runs stuck in PENDING or RUNNING for longer than `stale_threshold_hours`
    and mark them as FAILED.

    This handles cases where a Celery worker crashed without updating the run status,
    leaving it perpetually in RUNNING state.

    Returns the number of runs cleaned up.
    """
    from aitester.db.models import TestRun

    await ensure_db()

    cutoff = datetime.now(UTC) - timedelta(hours=stale_threshold_hours)
    now = datetime.now(UTC)

    # Find all runs in a non-terminal state that started (or were created) before cutoff
    result = await TestRun.get_motor_collection().update_many(
        {
            "status": {"$in": ["PENDING", "RUNNING"]},
            # Use created_at as the stale anchor — a run stuck in PENDING
            # means the worker never picked it up
            "created_at": {"$lt": cutoff},
        },
        {
            "$set": {
                "status": "FAILED",
                "completed_at": now,
                "updated_at": now,
            }
        },
    )
    cleaned_count: int = result.modified_count
    if cleaned_count:
        logger.warning(
            "Stale run cleanup: marked %d runs as FAILED (threshold=%dh)",
            cleaned_count,
            stale_threshold_hours,
        )
    else:
        logger.debug("Stale run cleanup: no stale runs found")
    return cleaned_count


@shared_task(
    name="aitester.worker.periodic.cleanup_stale_runs",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    queue="maintenance",
)
def cleanup_stale_runs(self, stale_threshold_hours: int = 2) -> dict:
    """
    Celery Beat task — finds and fails runs stuck in PENDING/RUNNING.

    Scheduled: every hour.

    Args:
        stale_threshold_hours: Runs older than this many hours in a non-terminal
                               state are marked FAILED. Defaults to 2 hours.
    """
    logger.info("Executing scheduled task: cleanup_stale_runs (threshold=%dh)", stale_threshold_hours)
    try:
        cleaned_count = run_async(_cleanup_stale_runs_async(stale_threshold_hours))
        result = {
            "task": "cleanup_stale_runs",
            "runs_cleaned": cleaned_count,
            "checked_at": datetime.now(UTC).isoformat(),
        }
        logger.info("Scheduled task succeeded: %s", result)
        return result
    except Exception as exc:
        logger.error("cleanup_stale_runs failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)
