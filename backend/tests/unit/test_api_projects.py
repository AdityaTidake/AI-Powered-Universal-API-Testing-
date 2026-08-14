"""
API Projects integration tests — Beanie/MongoDB edition.

These tests verify route structure, auth protection, and schema correctness
using FastAPI's TestClient without a live database (mocked Beanie).
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
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.plan = "free"
    user.monthly_run_count = 0
    user.is_active = True
    return user


@pytest.fixture
def auth_headers():
    """Return a fake Authorization header. Auth is overridden via dependency injection."""
    return {"Authorization": "Bearer fake-token"}


@pytest.fixture
async def client(mock_user):
    """Provide an AsyncClient with get_current_user mocked out."""
    from aitester.api.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ─── Health ───────────────────────────────────────────────────────────────────

class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


# ─── Projects (mocked Beanie) ─────────────────────────────────────────────────

class TestProjectsAuth:
    @pytest.mark.asyncio
    async def test_list_projects_requires_auth(self):
        """Without the dependency override, the endpoint must reject unauthenticated requests."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.get("/api/v1/projects")
        assert response.status_code == 401  # HTTPBearer raises 401 when no token

    @pytest.mark.asyncio
    async def test_create_project_requires_auth(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.post("/api/v1/projects", json={"name": "Test"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    @patch("aitester.db.models.Project.find")
    async def test_list_projects_returns_list(self, mock_find, client: AsyncClient):
        """list_projects should return a JSON array."""
        mock_chain = MagicMock()
        mock_chain.sort.return_value = mock_chain
        mock_chain.skip.return_value = mock_chain
        mock_chain.limit.return_value = mock_chain
        mock_chain.to_list = AsyncMock(return_value=[])
        mock_find.return_value = mock_chain

        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ─── Orgs Auth ────────────────────────────────────────────────────────────────

class TestOrgsAuth:
    @pytest.mark.asyncio
    async def test_list_orgs_requires_auth(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.get("/api/v1/orgs")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_org_requires_auth(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            response = await c.post("/api/v1/orgs", json={"name": "Acme"})
        assert response.status_code == 401


# ─── Schema Validation ────────────────────────────────────────────────────────

class TestSchemaValidation:
    @pytest.mark.asyncio
    @patch("aitester.db.models.Project.insert")
    async def test_create_project_missing_name_returns_422(self, mock_insert, client: AsyncClient):
        """Missing required 'name' field must return 422."""
        response = await client.post("/api/v1/projects", json={"description": "no name"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_org_missing_name_returns_422(self, client: AsyncClient):
        """Missing required 'name' field for org must return 422."""
        response = await client.post("/api/v1/orgs", json={})
        assert response.status_code == 422
