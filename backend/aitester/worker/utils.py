"""
aitester.worker.utils — Shared helpers for Celery worker tasks.

Provides a safe way to run asyncio coroutines from within synchronous
Celery task context, compatible with Python 3.10+.
"""

import asyncio
import logging
from typing import Any, Coroutine, TypeVar

logger = logging.getLogger("aitester.worker.utils")

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Execute an async coroutine from a synchronous Celery task.

    Strategy:
      - Celery workers are synchronous (no running loop) — use asyncio.run().
      - asyncio.run() always creates a fresh loop, tears it down cleanly,
        and is the only safe approach in Python 3.10+ (get_event_loop()
        raises DeprecationWarning in non-async contexts).

    Args:
        coro: An awaitable coroutine to execute.

    Returns:
        The coroutine's return value.
    """
    return asyncio.run(coro)


_db_initialized: bool = False
_db_lock: asyncio.Lock | None = None


async def ensure_db() -> None:
    """
    Idempotent DB initialisation guard for worker processes.

    Celery workers are long-lived processes — calling init_db() on every
    task invocation creates a new Motor client each time. This guard ensures
    Beanie is only initialised once per worker process lifetime.

    Note: Uses a module-level flag rather than a lock because each asyncio.run()
    call creates a fresh event loop, meaning asyncio.Lock instances don't survive
    across task boundaries. The flag is process-local and thus safe.
    """
    global _db_initialized  # noqa: PLW0603

    if not _db_initialized:
        from aitester.db.init import init_db

        await init_db()
        _db_initialized = True
        logger.debug("Worker DB connection initialised (pid=%d)", __import__("os").getpid())
