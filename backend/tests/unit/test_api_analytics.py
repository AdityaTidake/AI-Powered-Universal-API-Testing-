"""
API Analytics integration tests.
Tests for /api/v1/analytics/* endpoints with mocked Beanie/MongoDB aggregations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient

from aitester.api.main import app


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_user():
    from beanie import PydanticObjectId
    user = MagicMock()
    user.id = PydanticObjectId()
    return user


@pytest.fixture
async def client(mock_user):
    from aitester.api.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestAnalyticsEndpoints:
    @pytest.mark.asyncio
    @patch("aitester.db.models.Project.find")
    @patch("aitester.db.models.TestRun.find")
    async def test_dashboard_analytics(self, mock_run_find, mock_proj_find, client: AsyncClient):
        mock_proj_chain = MagicMock()
        mock_proj_chain.count = AsyncMock(return_value=3)
        mock_proj_find.return_value = mock_proj_chain
        
        mock_run_chain = MagicMock()
        mock_run_chain.count = AsyncMock(return_value=10)
        mock_run_find.return_value = mock_run_chain
        
        response = await client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["total_projects"] == 3
        assert data["total_runs"] == 10

    @pytest.mark.asyncio
    @patch("aitester.db.models.TestRun.aggregate")
    async def test_analytics_trends(self, mock_aggregate, client: AsyncClient):
        mock_aggregate.return_value.to_list = AsyncMock(return_value=[
            {"_id": "2024-01-01", "total_runs": 5, "passed_runs": 4, "failed_runs": 1}
        ])
        
        response = await client.get("/api/v1/analytics/trends")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["date"] == "2024-01-01"

    @pytest.mark.asyncio
    @patch("aitester.db.models.TestResult.aggregate")
    async def test_analytics_coverage(self, mock_aggregate, client: AsyncClient):
        mock_aggregate.return_value.to_list = AsyncMock(return_value=[
            {"_id": "GET /api/users", "count": 10, "passed": 8, "failed": 2}
        ])
        
        response = await client.get("/api/v1/analytics/coverage")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["endpoint"] == "GET /api/users"

    @pytest.mark.asyncio
    @patch("aitester.db.models.TestResult.aggregate")
    async def test_analytics_insights(self, mock_aggregate, client: AsyncClient):
        mock_aggregate.return_value.to_list = AsyncMock(return_value=[
            {
                "_id": "60d5ecb8b392d2b51c8a4c10",
                "test_case_id": "TC-001",
                "endpoint": "GET /auth",
                "ai_failure_analysis": {
                    "is_security_concern": True,
                    "root_cause": "SQL Injection vulnerability",
                    "suggested_fix": "Use parameterized queries"
                }
            }
        ])
        
        response = await client.get("/api/v1/analytics/insights")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["endpoint"] == "GET /auth"
        assert data[0]["root_cause"] == "SQL Injection vulnerability"
