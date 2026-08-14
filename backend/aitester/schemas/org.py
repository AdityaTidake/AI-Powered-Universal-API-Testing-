"""Pydantic schemas for the Organization resource."""

from datetime import datetime

from pydantic import BaseModel, Field

from aitester.schemas.base import MongoBaseResponse, PyObjectIdStr


class OrgCreate(BaseModel):
    """Body for POST /orgs"""
    name: str = Field(..., max_length=255)


class OrgUpdate(BaseModel):
    """Body for PATCH /orgs/{id} — all fields optional."""
    name: str | None = Field(None, max_length=255)


class OrgMemberAdd(BaseModel):
    """Body for POST /orgs/{id}/members"""
    user_id: str = Field(..., description="MongoDB ObjectId of the user to add")


class OrgResponse(MongoBaseResponse):
    """Returned by org endpoints."""
    id: PyObjectIdStr
    name: str
    slug: str
    owner_id: PyObjectIdStr
    member_ids: list[PyObjectIdStr]
    created_at: datetime
    updated_at: datetime
