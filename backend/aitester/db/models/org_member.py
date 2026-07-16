"""
OrgMember DB model — join table between User and Organization with RBAC role.

SOLID: Single Responsibility — only models the membership relationship + role.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aitester.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from aitester.db.models.organization import Organization
    from aitester.db.models.user import User


class OrgMember(TimestampMixin, Base):
    """
    Join table: User ↔ Organization with a role.
    Roles: 'owner' | 'admin' | 'viewer'
    A User can belong to multiple Organizations with different roles.
    """

    __tablename__ = "org_members"
    __table_args__ = (
        UniqueConstraint("org_id", "user_id", name="uq_org_member"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="viewer",
        comment="owner | admin | viewer"
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="members"
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="org_memberships"
    )

    def __repr__(self) -> str:
        return f"<OrgMember user={self.user_id} org={self.org_id} role={self.role}>"
