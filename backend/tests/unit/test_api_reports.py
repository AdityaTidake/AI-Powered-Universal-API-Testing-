"""
API Reports integration tests.
Tests for /api/v1/runs/{run_id}/report/* endpoints.
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
    user.email = "reporter@example.com"
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
    proj.name = "Reporter API"
    return proj


@pytest.fixture
def mock_test_run(mock_project):
    from beanie import PydanticObjectId
    run = MagicMock()
    run.id = PydanticObjectId()
    run.project_id = mock_project.id
    run.status = "COMPLETED"
    run.base_url = "http://api.reporter.com"
    run.created_at = datetime.now(UTC)
    run.completed_at = datetime.now(UTC)
    return run


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestReportsEndpoints:
    @pytest.mark.asyncio
    @patch("aitester.db.models.TestRun.get")
    @patch("aitester.db.models.Project.get")
    @patch("aitester.db.models.TestResult.find")
    async def test_get_report_json(self, mock_result_find, mock_proj_get, mock_run_get, client: AsyncClient, mock_project, mock_test_run):
        mock_run_get.return_value = mock_test_run
        mock_proj_get.return_value = mock_project
        
        mock_result_chain = MagicMock()
        mock_result_chain.to_list = AsyncMock(return_value=[])
        mock_result_find.return_value = mock_result_chain

        response = await client.get(f"/api/v1/runs/{str(mock_test_run.id)}/report/json")
        assert response.status_code == 200
        data = response.json()
        assert data["test_run_id"] == str(mock_test_run.id)
        assert data["project_name"] == "Reporter API"

    @pytest.mark.asyncio
    @patch("aitester.db.models.TestRun.get")
    @patch("aitester.db.models.Project.get")
    @patch("aitester.db.models.TestResult.find")
    @patch("aitester.api.v1.routes.reports.generate_html_report")
    async def test_get_report_html(self, mock_generate_html, mock_result_find, mock_proj_get, mock_run_get, client: AsyncClient, mock_project, mock_test_run):
        mock_run_get.return_value = mock_test_run
        mock_proj_get.return_value = mock_project
        
        mock_result_chain = MagicMock()
        mock_result_chain.to_list = AsyncMock(return_value=[])
        mock_result_find.return_value = mock_result_chain
        
        mock_generate_html.return_value = "<html><body>Report</body></html>"

        response = await client.get(f"/api/v1/runs/{str(mock_test_run.id)}/report/html")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert response.text == "<html><body>Report</body></html>"
