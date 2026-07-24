"""
Shared base for all API response schemas.

Uses a custom PyObjectIdStr annotated type that coerces MongoDB ObjectId
to plain str at the field level — works reliably with Pydantic v2 + Beanie.
"""

from typing import Annotated, Any

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict


def _objectid_to_str(v: Any) -> str:
    """Coerce an ObjectId (or any value) to str."""
    if isinstance(v, ObjectId):
        return str(v)
    return str(v) if v is not None else ""


# Annotated str type that coerces ObjectId → str before validation
PyObjectIdStr = Annotated[str, BeforeValidator(_objectid_to_str)]


class MongoBaseResponse(BaseModel):
    """
    Base response model for all Beanie-backed endpoints.
    Use PyObjectIdStr for any id fields that come from MongoDB ObjectId.
    """
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
