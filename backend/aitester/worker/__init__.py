"""
aitester.worker — Celery application factory for SpecGuard AI.

Creates and configures the Celery application that powers asynchronous
test execution and scheduled maintenance tasks.

Starting workers:
    # Development (single worker, verbose logging):
    celery -A aitester.worker worker --loglevel=debug --concurrency=2

    # Production (multiple workers with autoscale):
    celery -A aitester.worker worker --loglevel=info --autoscale=8,2

    # Beat scheduler (periodic tasks — run ONE instance only):
    celery -A aitester.worker beat --loglevel=info --schedule=/tmp/celerybeat-schedule

    # Combined worker + beat (dev only — do not use in production):
    celery -A aitester.worker worker --beat --loglevel=info

Importing:
    from aitester.worker import celery_app
"""

from celery import Celery

from aitester.core.config import settings

# ─── Application ──────────────────────────────────────────────────────────────
celery_app = Celery(
    "specguard",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    # Eagerly import these modules so tasks are registered at startup
    include=[
        "aitester.worker.tasks",
        "aitester.worker.periodic",
        "aitester.worker.signals",
    ],
)

# ─── Configuration ────────────────────────────────────────────────────────────
celery_app.conf.update(
    # ── Serialisation ─────────────────────────────────────────────────────────
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # ── Timezone ──────────────────────────────────────────────────────────────
    timezone="UTC",
    enable_utc=True,

    # ── Reliability ───────────────────────────────────────────────────────────
    # Acknowledge tasks only AFTER they complete (re-queue on worker crash)
    task_acks_late=True,
    # Reject the task back to the queue if the worker process is lost
    task_reject_on_worker_lost=True,
    # Each worker fetches one task at a time — fair dispatch for long-running jobs
    worker_prefetch_multiplier=1,

    # ── Visibility ────────────────────────────────────────────────────────────
    # Publish STARTED state when a task begins (visible via Flower / result backend)
    task_track_started=True,
    # Store result even when the task succeeds (default False)
    task_ignore_result=False,

    # ── Result TTL ────────────────────────────────────────────────────────────
    # Keep results in Redis for 24 h, then expire automatically
    result_expires=86_400,

    # ── Routing ───────────────────────────────────────────────────────────────
    # Named queues so workers can be scaled independently per workload type
    task_routes={
        "aitester.worker.tasks.execute_test_run": {"queue": "test_runs"},
        "aitester.worker.periodic.*": {"queue": "maintenance"},
    },
    task_default_queue="celery",

    # ── Beat ──────────────────────────────────────────────────────────────────
    # Persistent schedule file used by celery beat
    beat_schedule_filename="/tmp/celerybeat-schedule",

    # ── Worker ────────────────────────────────────────────────────────────────
    # Maximum number of tasks a single worker process can execute before
    # recycling (guards against memory leaks in long-running processes)
    worker_max_tasks_per_child=200,
)

__all__ = ["celery_app"]

# ─── Beat Schedule (wired after app creation to avoid circular imports) ────────
# periodic.py defines BEAT_SCHEDULE as a plain dict; we register it on the app
# here so there is a single source of truth for the schedule.
def _register_beat_schedule() -> None:
    from aitester.worker.periodic import BEAT_SCHEDULE  # noqa: PLC0415
    celery_app.conf.beat_schedule = BEAT_SCHEDULE


_register_beat_schedule()
