"""
Project DB model — now multi-tenant with owner_id and optional org_id.
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aitester.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from aitester.db.models.organization import Organization
    from aitester.db.models.test_run import TestRun
    from aitester.db.models.user import User


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    openapi_spec: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Parsed OpenAPI spec stored as JSON"
    )

    # ── Multi-tenant ownership ────────────────────────────────────────────────
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional organization this project belongs to",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    organization: Mapped["Organization | None"] = relationship(
        "Organization", back_populates="projects"
    )
    test_runs: Mapped[list["TestRun"]] = relationship(
        "TestRun", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r} owner={self.owner_id}>"
