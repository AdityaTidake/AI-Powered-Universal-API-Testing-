"""
Organizations API routes — /api/v1/orgs/*

Endpoints:
  POST   /orgs                       → create a new org (caller becomes owner)
  GET    /orgs                       → list orgs the current user belongs to
  GET    /orgs/{org_id}              → get a single org (member only)
  PATCH  /orgs/{org_id}             → update org name (owner only)
  DELETE /orgs/{org_id}             → delete an org (owner only)
  POST   /orgs/{org_id}/members     → add a member by user_id (owner only)
  DELETE /orgs/{org_id}/members/{user_id} → remove a member (owner only)
  GET    /orgs/{org_id}/projects    → list all projects belonging to this org
"""

import re
import uuid
from datetime import UTC, datetime

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from aitester.api.dependencies import get_current_user
from aitester.db.models import Organization, Project, User
from aitester.schemas.org import OrgCreate, OrgMemberAdd, OrgResponse, OrgUpdate
from aitester.schemas.project import ProjectResponse

router = APIRouter(prefix="/orgs", tags=["Organizations"])


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_slug(name: str) -> str:
    """Convert an org name to a URL-safe slug with a short random suffix."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:72] + "-" + str(uuid.uuid4())[:8]


async def _get_member_org(org_id: str, current_user: User) -> Organization:
    """Return the org if the current user is a member; raise 404 otherwise."""
    try:
        org = await Organization.get(PydanticObjectId(org_id))
    except Exception:
        org = None
    if not org or current_user.id not in org.member_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    return org


async def _get_owner_org(org_id: str, current_user: User) -> Organization:
    """Return the org only if the current user is the owner; raise 403 otherwise."""
    try:
        org = await Organization.get(PydanticObjectId(org_id))
    except Exception:
        org = None
    if not org or current_user.id not in org.member_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    if org.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the organization owner can perform this action.",
        )
    return org


# ─── Create ───────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=OrgResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
async def create_org(
    org_in: OrgCreate,
    current_user: User = Depends(get_current_user),
) -> Organization:
    """Creates an org. The caller becomes the owner and first member."""
    org = Organization(
        name=org_in.name,
        slug=_make_slug(org_in.name),
        owner_id=current_user.id,
        member_ids=[current_user.id],
    )
    await org.insert()
    return org


# ─── List ─────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[OrgResponse],
    summary="List organizations the current user belongs to",
)
async def list_orgs(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
) -> list[Organization]:
    """Returns all orgs where the current user is a member."""
    return await (
        Organization.find({"member_ids": current_user.id})
        .sort("-created_at")
        .skip(skip)
        .limit(limit)
        .to_list()
    )


# ─── Get Single ───────────────────────────────────────────────────────────────

@router.get(
    "/{org_id}",
    response_model=OrgResponse,
    summary="Get a single organization",
)
async def get_org(
    org_id: str,
    current_user: User = Depends(get_current_user),
) -> Organization:
    return await _get_member_org(org_id, current_user)


# ─── Update ───────────────────────────────────────────────────────────────────

@router.patch(
    "/{org_id}",
    response_model=OrgResponse,
    summary="Update an organization (owner only)",
)
async def update_org(
    org_id: str,
    update_in: OrgUpdate,
    current_user: User = Depends(get_current_user),
) -> Organization:
    org = await _get_owner_org(org_id, current_user)
    if update_in.name is not None:
        org.name = update_in.name
        org.updated_at = datetime.now(UTC)
        await org.save()
    return org


# ─── Delete ───────────────────────────────────────────────────────────────────

@router.delete(
    "/{org_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an organization (owner only)",
)
async def delete_org(
    org_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    org = await _get_owner_org(org_id, current_user)
    await org.delete()


# ─── Add Member ───────────────────────────────────────────────────────────────

@router.post(
    "/{org_id}/members",
    response_model=OrgResponse,
    summary="Add a member to an organization (owner only)",
)
async def add_member(
    org_id: str,
    body: OrgMemberAdd,
    current_user: User = Depends(get_current_user),
) -> Organization:
    """Adds a user (by their ObjectId) to the org's member_ids list."""
    org = await _get_owner_org(org_id, current_user)

    try:
        member_oid = PydanticObjectId(body.user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid user_id format.")

    # Verify the user exists
    target_user = await User.get(member_oid)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if member_oid not in org.member_ids:
        org.member_ids.append(member_oid)
        org.updated_at = datetime.now(UTC)
        await org.save()
    return org


# ─── Remove Member ────────────────────────────────────────────────────────────

@router.delete(
    "/{org_id}/members/{user_id}",
    response_model=OrgResponse,
    summary="Remove a member from an organization (owner only)",
)
async def remove_member(
    org_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
) -> Organization:
    """Removes a member from the org. The owner cannot remove themselves."""
    org = await _get_owner_org(org_id, current_user)

    try:
        member_oid = PydanticObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid user_id format.")

    if member_oid == org.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The owner cannot be removed from the organization.",
        )

    org.member_ids = [mid for mid in org.member_ids if mid != member_oid]
    org.updated_at = datetime.now(UTC)
    await org.save()
    return org


# ─── List Org Projects ────────────────────────────────────────────────────────

@router.get(
    "/{org_id}/projects",
    response_model=list[ProjectResponse],
    summary="List all projects belonging to an organization (member only)",
)
async def list_org_projects(
    org_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
) -> list[Project]:
    org = await _get_member_org(org_id, current_user)
    return await (
        Project.find(Project.org_id == org.id)
        .sort("-created_at")
        .skip(skip)
        .limit(limit)
        .to_list()
    )
