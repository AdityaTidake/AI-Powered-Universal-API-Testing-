"""
API Organizations integration tests.
Tests for /api/v1/orgs/* endpoints with mocked Beanie/MongoDB interactions.
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
    user.email = "orgowner@example.com"
    user.full_name = "Org Owner"
    user.plan = "free"
    user.monthly_run_count = 0
    user.is_active = True
    return user


@pytest.fixture
async def client(mock_user):
    from aitester.api.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_org(mock_user):
    from beanie import PydanticObjectId
    org = MagicMock()
    org.id = PydanticObjectId()
    org.name = "Acme Corp"
    org.slug = "acme-corp-1234"
    org.owner_id = mock_user.id
    org.member_ids = [mock_user.id]
    org.created_at = datetime.now(UTC)
    org.updated_at = datetime.now(UTC)
    # Beanie mock helpers
    org.save = AsyncMock()
    org.delete = AsyncMock()
    return org


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestOrgsEndpoints:
    @pytest.mark.asyncio
    @patch("aitester.db.models.Organization.insert")
    async def test_create_org(self, mock_insert, client: AsyncClient):
        response = await client.post("/api/v1/orgs", json={"name": "New Org"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Org"
        assert mock_insert.called

    @pytest.mark.asyncio
    @patch("aitester.db.models.Organization.find")
    async def test_list_orgs(self, mock_find, client: AsyncClient, mock_org):
        mock_chain = MagicMock()
        mock_chain.sort.return_value = mock_chain
        mock_chain.skip.return_value = mock_chain
        mock_chain.limit.return_value = mock_chain
        mock_chain.to_list = AsyncMock(return_value=[mock_org])
        mock_find.return_value = mock_chain

        response = await client.get("/api/v1/orgs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Acme Corp"

    @pytest.mark.asyncio
    @patch("aitester.db.models.Organization.get")
    async def test_get_org_success(self, mock_get, client: AsyncClient, mock_org):
        mock_get.return_value = mock_org
        response = await client.get(f"/api/v1/orgs/{str(mock_org.id)}")
        assert response.status_code == 200
        assert response.json()["name"] == "Acme Corp"

    @pytest.mark.asyncio
    @patch("aitester.db.models.Organization.get")
    async def test_get_org_not_found(self, mock_get, client: AsyncClient):
        mock_get.return_value = None
        from beanie import PydanticObjectId
        response = await client.get(f"/api/v1/orgs/{str(PydanticObjectId())}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("aitester.db.models.Organization.get")
    @patch("aitester.db.models.User.get")
    async def test_add_member_success(self, mock_user_get, mock_org_get, client: AsyncClient, mock_org):
        mock_org_get.return_value = mock_org
        
        from beanie import PydanticObjectId
        new_member_id = PydanticObjectId()
        
        target_user = MagicMock()
        target_user.id = new_member_id
        mock_user_get.return_value = target_user

        response = await client.post(f"/api/v1/orgs/{str(mock_org.id)}/members", json={"user_id": str(new_member_id)})
        assert response.status_code == 200
        assert mock_org.save.called

    @pytest.mark.asyncio
    @patch("aitester.db.models.Organization.get")
    async def test_add_member_invalid_id(self, mock_org_get, client: AsyncClient, mock_org):
        mock_org_get.return_value = mock_org
        response = await client.post(f"/api/v1/orgs/{str(mock_org.id)}/members", json={"user_id": "not-an-objectid"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    @patch("aitester.db.models.Organization.get")
    async def test_remove_member_success(self, mock_org_get, client: AsyncClient, mock_org):
        mock_org_get.return_value = mock_org
        
        from beanie import PydanticObjectId
        member_to_remove = PydanticObjectId()
        mock_org.member_ids.append(member_to_remove)

        response = await client.delete(f"/api/v1/orgs/{str(mock_org.id)}/members/{str(member_to_remove)}")
        assert response.status_code == 200
        assert mock_org.save.called

    @pytest.mark.asyncio
    @patch("aitester.db.models.Organization.get")
    async def test_remove_member_owner_fails(self, mock_org_get, client: AsyncClient, mock_org):
        mock_org_get.return_value = mock_org
        
        response = await client.delete(f"/api/v1/orgs/{str(mock_org.id)}/members/{str(mock_org.owner_id)}")
        assert response.status_code == 400
        assert "owner cannot be removed" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("aitester.db.models.Organization.get")
    async def test_delete_org_success(self, mock_org_get, client: AsyncClient, mock_org):
        mock_org_get.return_value = mock_org
        response = await client.delete(f"/api/v1/orgs/{str(mock_org.id)}")
        assert response.status_code == 204
        assert mock_org.delete.called
