"""
aitester.worker.signals — Celery signal handlers for SpecGuard AI.

Provides structured logging and observability hooks that fire automatically
on task lifecycle events. This gives visibility into worker health without
requiring an external APM tool.

Signals connected:
  - task_prerun:    Logs task start with worker info.
  - task_postrun:   Logs task completion and duration.
  - task_failure:   Logs failures with exception details.
  - task_retry:     Logs retry attempts.
  - worker_ready:   Logs worker startup.
  - worker_shutdown: Logs worker shutdown.

This module is imported in worker/__init__.py via the `include` list,
which means signal handlers are connected automatically when the worker starts.
"""

import logging
import time
from typing import Any

from celery.signals import (
    task_failure,
    task_postrun,
    task_prerun,
    task_retry,
    worker_ready,
    worker_shutdown,
)

logger = logging.getLogger("aitester.worker.signals")

# In-process store for task start times (used to compute duration in postrun)
_task_start_times: dict[str, float] = {}


# ─── Task Lifecycle Signals ───────────────────────────────────────────────────

@task_prerun.connect
def on_task_prerun(
    task_id: str,
    task: Any,
    args: tuple,
    kwargs: dict,
    **_: Any,
) -> None:
    """Fires before a task is executed. Records start time for duration tracking."""
    _task_start_times[task_id] = time.monotonic()
    logger.info(
        "TASK_START | task_id=%s name=%s",
        task_id,
        task.name,
    )


@task_postrun.connect
def on_task_postrun(
    task_id: str,
    task: Any,
    args: tuple,
    kwargs: dict,
    retval: Any,
    state: str,
    **_: Any,
) -> None:
    """Fires after a task is executed (regardless of success/failure)."""
    start = _task_start_times.pop(task_id, None)
    duration_ms = round((time.monotonic() - start) * 1000) if start is not None else -1

    logger.info(
        "TASK_DONE  | task_id=%s name=%s state=%s duration_ms=%d",
        task_id,
        task.name,
        state,
        duration_ms,
    )


@task_failure.connect
def on_task_failure(
    task_id: str,
    exception: Exception,
    traceback: Any,
    sender: Any,
    **_: Any,
) -> None:
    """Fires when a task raises an unhandled exception."""
    logger.error(
        "TASK_FAIL  | task_id=%s name=%s error=%s: %s",
        task_id,
        sender.name if sender else "unknown",
        type(exception).__name__,
        exception,
        exc_info=(type(exception), exception, traceback),
    )


@task_retry.connect
def on_task_retry(
    request: Any,
    reason: Any,
    einfo: Any,
    **_: Any,
) -> None:
    """Fires when a task is about to be retried."""
    logger.warning(
        "TASK_RETRY | task_id=%s reason=%s",
        request.id,
        reason,
    )


# ─── Worker Lifecycle Signals ─────────────────────────────────────────────────

@worker_ready.connect
def on_worker_ready(sender: Any, **_: Any) -> None:
    """Fires when the Celery worker has finished booting and is ready to receive tasks."""
    import os

    logger.info(
        "WORKER_UP  | hostname=%s pid=%d",
        getattr(sender, "hostname", "unknown"),
        os.getpid(),
    )


@worker_shutdown.connect
def on_worker_shutdown(sender: Any, **_: Any) -> None:
    """Fires when the Celery worker begins its shutdown sequence."""
    logger.info(
        "WORKER_DOWN | hostname=%s",
        getattr(sender, "hostname", "unknown"),
    )
