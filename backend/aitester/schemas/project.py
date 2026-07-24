"""Pydantic schemas for the Project resource."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """Body for POST /projects"""
    name: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=2000)


class ProjectResponse(BaseModel):
    """Returned by project endpoints."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    openapi_spec: dict[str, Any] | None
    owner_id: str
    org_id: str | None
    created_at: datetime
    updated_at: datetime
