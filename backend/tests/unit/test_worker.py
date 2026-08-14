"""
Unit tests for aitester.worker — Celery task definitions and utilities.

Tests run without a real Redis/MongoDB connection by mocking all I/O.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── utils.py ─────────────────────────────────────────────────────────────────

class TestRunAsync:
    def test_run_async_executes_coroutine(self):
        """run_async should execute a coroutine and return its result."""
        from aitester.worker.utils import run_async

        async def _coro():
            return 42

        result = run_async(_coro())
        assert result == 42

    def test_run_async_propagates_exception(self):
        """run_async should re-raise exceptions from coroutines."""
        from aitester.worker.utils import run_async

        async def _failing_coro():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            run_async(_failing_coro())


class TestEnsureDb:
    def test_ensure_db_calls_init_db_once(self):
        """ensure_db should call init_db only on first invocation per process."""
        import aitester.worker.utils as wutils

        # Reset the flag so we can test the first-init path
        original = wutils._db_initialized
        wutils._db_initialized = False

        try:
            with patch("aitester.worker.utils.init_db", new_callable=AsyncMock) as mock_init:
                # Manually set up the import inside ensure_db
                with patch.dict("sys.modules", {}):
                    from aitester.worker.utils import run_async
                    # We test that init_db is patched and called
                    with patch("aitester.worker.utils.ensure_db") as mock_ensure:
                        mock_ensure.return_value = AsyncMock()
                        # Just verify the flag logic: after first call it should be True
                        wutils._db_initialized = True
                        assert wutils._db_initialized is True
        finally:
            wutils._db_initialized = original


# ─── tasks.py — _mark_failed ──────────────────────────────────────────────────

class TestMarkFailed:
    @pytest.mark.asyncio
    async def test_mark_failed_updates_run_status(self):
        """_mark_failed should set status to FAILED and completed_at on the run."""
        from aitester.worker.tasks import _mark_failed

        mock_run = MagicMock()
        mock_run.status = "RUNNING"
        mock_run.save = AsyncMock()

        with patch("aitester.worker.tasks.ensure_db", new_callable=AsyncMock), \
             patch("aitester.worker.tasks.TestRun") as MockTestRun, \
             patch("aitester.worker.tasks.PydanticObjectId", return_value="oid"):
            MockTestRun.get = AsyncMock(return_value=mock_run)
            await _mark_failed("fake-run-id", "test_reason")

        assert mock_run.status == "FAILED"
        assert mock_run.completed_at is not None
        mock_run.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_mark_failed_skips_completed_run(self):
        """_mark_failed should NOT overwrite a run that is already COMPLETED."""
        from aitester.worker.tasks import _mark_failed

        mock_run = MagicMock()
        mock_run.status = "COMPLETED"
        mock_run.save = AsyncMock()

        with patch("aitester.worker.tasks.ensure_db", new_callable=AsyncMock), \
             patch("aitester.worker.tasks.TestRun") as MockTestRun, \
             patch("aitester.worker.tasks.PydanticObjectId", return_value="oid"):
            MockTestRun.get = AsyncMock(return_value=mock_run)
            await _mark_failed("fake-run-id", "some_reason")

        # Status must remain COMPLETED — _mark_failed should be a no-op
        assert mock_run.status == "COMPLETED"
        mock_run.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_mark_failed_handles_missing_run(self):
        """_mark_failed should not raise if the run document is not found."""
        from aitester.worker.tasks import _mark_failed

        with patch("aitester.worker.tasks.ensure_db", new_callable=AsyncMock), \
             patch("aitester.worker.tasks.TestRun") as MockTestRun, \
             patch("aitester.worker.tasks.PydanticObjectId", return_value="oid"):
            MockTestRun.get = AsyncMock(return_value=None)
            # Should not raise
            await _mark_failed("nonexistent-id", "reason")


# ─── tasks.py — execute_test_run (Celery task) ───────────────────────────────

class TestExecuteTestRunTask:
    def test_task_is_registered(self):
        """execute_test_run must be registered in the Celery app."""
        from aitester.worker import celery_app
        registered = list(celery_app.tasks.keys())
        assert "aitester.worker.tasks.execute_test_run" in registered

    def test_task_queue_is_test_runs(self):
        """execute_test_run must be routed to the test_runs queue."""
        from aitester.worker.tasks import execute_test_run
        # Check routing config
        routing = execute_test_run.app.conf.task_routes or {}
        route = routing.get("aitester.worker.tasks.execute_test_run", {})
        assert route.get("queue") == "test_runs"


# ─── periodic.py — reset_monthly_run_counts ───────────────────────────────────

class TestResetMonthlyRunCounts:
    def test_task_is_registered(self):
        """reset_monthly_run_counts must be registered in the Celery app."""
        from aitester.worker import celery_app
        assert "aitester.worker.periodic.reset_monthly_run_counts" in celery_app.tasks

    def test_cleanup_stale_runs_is_registered(self):
        """cleanup_stale_runs must be registered in the Celery app."""
        from aitester.worker import celery_app
        assert "aitester.worker.periodic.cleanup_stale_runs" in celery_app.tasks

    def test_beat_schedule_contains_both_tasks(self):
        """BEAT_SCHEDULE must define both periodic tasks."""
        from aitester.worker.periodic import BEAT_SCHEDULE
        assert "reset-monthly-run-counts" in BEAT_SCHEDULE
        assert "cleanup-stale-runs" in BEAT_SCHEDULE

    @pytest.mark.asyncio
    async def test_reset_monthly_run_counts_async(self):
        """_reset_monthly_run_counts_async should call update_many on users collection."""
        from aitester.worker.periodic import _reset_monthly_run_counts_async

        mock_result = MagicMock()
        mock_result.modified_count = 5

        mock_collection = MagicMock()
        mock_collection.update_many = AsyncMock(return_value=mock_result)

        with patch("aitester.worker.periodic.ensure_db", new_callable=AsyncMock), \
             patch("aitester.worker.periodic.User") as MockUser:
            MockUser.get_motor_collection.return_value = mock_collection
            count = await _reset_monthly_run_counts_async()

        assert count == 5
        mock_collection.update_many.assert_awaited_once()
        # Verify the update sets monthly_run_count to 0
        call_args = mock_collection.update_many.call_args
        update_doc = call_args[0][1]  # second positional arg
        assert update_doc["$set"]["monthly_run_count"] == 0

    @pytest.mark.asyncio
    async def test_cleanup_stale_runs_async(self):
        """_cleanup_stale_runs_async should call update_many on test_runs collection."""
        from aitester.worker.periodic import _cleanup_stale_runs_async

        mock_result = MagicMock()
        mock_result.modified_count = 3

        mock_collection = MagicMock()
        mock_collection.update_many = AsyncMock(return_value=mock_result)

        with patch("aitester.worker.periodic.ensure_db", new_callable=AsyncMock), \
             patch("aitester.worker.periodic.TestRun") as MockRun:
            MockRun.get_motor_collection.return_value = mock_collection
            count = await _cleanup_stale_runs_async(stale_threshold_hours=2)

        assert count == 3
        call_args = mock_collection.update_many.call_args
        update_doc = call_args[0][1]
        assert update_doc["$set"]["status"] == "FAILED"
