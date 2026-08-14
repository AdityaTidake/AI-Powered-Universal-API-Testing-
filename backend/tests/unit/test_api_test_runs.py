"""
API Test Runs integration tests.
Tests for /api/v1/projects/{id}/runs and /api/v1/runs/* endpoints with mocked Beanie/MongoDB interactions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient
from datetime import UTC, datetime

from aitester.api.main import app


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_user():
    from beanie import PydanticObjectId
    user = MagicMock()
    user.id = PydanticObjectId()
    user.email = "tester@example.com"
    user.monthly_run_count = 0
    user.plan = "free"
    user.save = AsyncMock()
    return user


@pytest.fixture
async def client(mock_user):
    from aitester.api.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_project(mock_user):
    from beanie import PydanticObjectId
    proj = MagicMock()
    proj.id = PydanticObjectId()
    proj.owner_id = mock_user.id
    proj.openapi_spec = {"openapi": "3.0.0", "info": {"title": "Test"}}
    return proj


@pytest.fixture
def mock_test_run(mock_project):
    from beanie import PydanticObjectId
    run = MagicMock()
    run.id = PydanticObjectId()
    run.project_id = mock_project.id
    run.status = "COMPLETED"
    run.base_url = "http://example.com"
    run.created_at = datetime.now(UTC)
    run.updated_at = datetime.now(UTC)
    run.started_at = datetime.now(UTC)
    run.completed_at = datetime.now(UTC)
    run.delete = AsyncMock()
    return run


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestTestRunsEndpoints:
    @pytest.mark.asyncio
    @patch("aitester.api.v1.routes.test_runs._dispatch_test_run")
    @patch("aitester.db.models.TestRun.insert")
    @patch("aitester.db.models.Project.get")
    @patch("aitester.db.models.TestResult.find")
    async def test_create_test_run_success(self, mock_result_find, mock_proj_get, mock_insert, mock_dispatch, client: AsyncClient, mock_project):
        mock_proj_get.return_value = mock_project
        
        mock_chain = MagicMock()
        mock_chain.count = AsyncMock(return_value=0)
        mock_result_find.return_value = mock_chain

        payload = {
            "base_url": "http://api.example.com",
            "types": ["functional", "security"],
            "enable_ai": True
        }
        
        response = await client.post(f"/api/v1/projects/{str(mock_project.id)}/runs", json=payload)
        assert response.status_code == 202
        assert mock_dispatch.called
        assert mock_insert.called

    @pytest.mark.asyncio
    @patch("aitester.db.models.Project.get")
    async def test_create_test_run_no_spec_fails(self, mock_proj_get, client: AsyncClient, mock_project):
        mock_project.openapi_spec = None
        mock_proj_get.return_value = mock_project
        
        payload = {"base_url": "http://api.example.com", "types": ["functional"], "enable_ai": False}
        response = await client.post(f"/api/v1/projects/{str(mock_project.id)}/runs", json=payload)
        
        assert response.status_code == 422
        assert "no uploaded OpenAPI spec" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("aitester.db.models.TestRun.find")
    @patch("aitester.db.models.Project.get")
    @patch("aitester.db.models.TestResult.find")
    async def test_list_test_runs(self, mock_result_find, mock_proj_get, mock_run_find, client: AsyncClient, mock_project, mock_test_run):
        mock_proj_get.return_value = mock_project
        
        mock_run_chain = MagicMock()
        mock_run_chain.sort.return_value = mock_run_chain
        mock_run_chain.skip.return_value = mock_run_chain
        mock_run_chain.limit.return_value = mock_run_chain
        mock_run_chain.to_list = AsyncMock(return_value=[mock_test_run])
        mock_run_find.return_value = mock_run_chain

        mock_result_chain = MagicMock()
        mock_result_chain.count = AsyncMock(return_value=5)
        mock_result_find.return_value = mock_result_chain

        response = await client.get(f"/api/v1/projects/{str(mock_project.id)}/runs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "COMPLETED"

    @pytest.mark.asyncio
    @patch("aitester.db.models.TestRun.get")
    @patch("aitester.db.models.Project.get")
    @patch("aitester.db.models.TestResult.find")
    async def test_get_test_run_status(self, mock_result_find, mock_proj_get, mock_run_get, client: AsyncClient, mock_project, mock_test_run):
        mock_run_get.return_value = mock_test_run
        mock_proj_get.return_value = mock_project
        
        mock_result_chain = MagicMock()
        mock_result_chain.count = AsyncMock(return_value=10)
        mock_result_find.return_value = mock_result_chain
        
        response = await client.get(f"/api/v1/runs/{str(mock_test_run.id)}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["progress_pct"] == 100.0

    @pytest.mark.asyncio
    @patch("aitester.db.models.TestRun.get")
    @patch("aitester.db.models.Project.get")
    async def test_delete_test_run_success(self, mock_proj_get, mock_run_get, client: AsyncClient, mock_project, mock_test_run):
        mock_run_get.return_value = mock_test_run
        mock_proj_get.return_value = mock_project
        
        response = await client.delete(f"/api/v1/runs/{str(mock_test_run.id)}")
        assert response.status_code == 204
        assert mock_test_run.delete.called

    @pytest.mark.asyncio
    @patch("aitester.db.models.TestRun.get")
    async def test_delete_test_run_not_found(self, mock_run_get, client: AsyncClient):
        mock_run_get.return_value = None
        from beanie import PydanticObjectId
        response = await client.delete(f"/api/v1/runs/{str(PydanticObjectId())}")
        assert response.status_code == 404
