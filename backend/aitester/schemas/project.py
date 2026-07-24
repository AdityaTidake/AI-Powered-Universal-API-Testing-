"""Pydantic schemas for the Project resource."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from aitester.schemas.base import MongoBaseResponse, PyObjectIdStr


class ProjectCreate(BaseModel):
    """Body for POST /projects"""
    name: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=2000)


class ProjectResponse(MongoBaseResponse):
    """Returned by project endpoints."""
    id: PyObjectIdStr
    name: str
    description: str | None
    openapi_spec: dict[str, Any] | None
    owner_id: PyObjectIdStr
    org_id: PyObjectIdStr | None = None
    created_at: datetime
    updated_at: datetime
