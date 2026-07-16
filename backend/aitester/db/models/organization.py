"""
Organization DB model.

Multi-tenant design: each Organization owns Projects.
Users belong to Organizations via OrgMember (RBAC).
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aitester.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from aitester.db.models.org_member import OrgMember
    from aitester.db.models.project import Project


class Organization(TimestampMixin, Base):
    """
    Represents a team workspace.
    One owner (User) + many members via OrgMember join table.
    """

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="URL-safe identifier, e.g. 'my-company'"
    )
    plan: Mapped[str] = mapped_column(
        String(50), default="free", nullable=False,
        comment="free | pro | enterprise"
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    members: Mapped[list["OrgMember"]] = relationship(
        "OrgMember", back_populates="organization", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization id={self.id} slug={self.slug}>"
