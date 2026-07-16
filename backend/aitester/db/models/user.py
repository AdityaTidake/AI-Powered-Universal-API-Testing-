"""
User DB model.

SOLID: Single Responsibility — represents only the user entity and its DB columns.
OCP: New fields added without modifying service logic.
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aitester.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from aitester.db.models.org_member import OrgMember
    from aitester.db.models.project import Project


class User(TimestampMixin, Base):
    """
    Represents an authenticated platform user.
    Every user may own projects directly or via an Organization.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Plan / Billing ────────────────────────────────────────────────────────
    plan: Mapped[str] = mapped_column(
        String(50), default="free", nullable=False,
        comment="free | pro | enterprise"
    )
    monthly_run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_run_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    org_memberships: Mapped[list["OrgMember"]] = relationship(
        "OrgMember", back_populates="user", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} plan={self.plan}>"
