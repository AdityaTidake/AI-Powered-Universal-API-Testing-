"""
Phase 2: JWT Auth + Multi-Tenant DB Schema

Revision ID: 46c79b1f906f
Revises: a3c9e1f52b08
Create Date: 2026-07-16 20:39:53.120480

Changes:
  - CREATE TABLE users
  - CREATE TABLE organizations
  - CREATE TABLE org_members
  - ALTER TABLE projects  ADD COLUMNS owner_id, org_id
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "46c79b1f906f"
down_revision: str | None = "a3c9e1f52b08"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",                    postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email",                 sa.String(255),  nullable=False),
        sa.Column("hashed_password",       sa.String(255),  nullable=False),
        sa.Column("full_name",             sa.String(255),  nullable=False),
        sa.Column("is_active",             sa.Boolean(),    nullable=False, server_default=sa.true()),
        sa.Column("is_verified",           sa.Boolean(),    nullable=False, server_default=sa.false()),
        sa.Column("plan",                  sa.String(50),   nullable=False, server_default="free"),
        sa.Column("monthly_run_count",     sa.Integer(),    nullable=False, server_default="0"),
        sa.Column("monthly_run_reset_at",  sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at",            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── organizations ──────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name",       sa.String(255), nullable=False),
        sa.Column("slug",       sa.String(100), nullable=False),
        sa.Column("plan",       sa.String(50),  nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    # ── org_members ───────────────────────────────────────────────────────────
    op.create_table(
        "org_members",
        sa.Column("id",         postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id",     postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id",    postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id",         ondelete="CASCADE"), nullable=False),
        sa.Column("role",       sa.String(50),  nullable=False, server_default="viewer"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_org_members_org_id",  "org_members", ["org_id"])
    op.create_index("ix_org_members_user_id", "org_members", ["user_id"])
    op.create_unique_constraint("uq_org_member", "org_members", ["org_id", "user_id"])

    # ── projects — add owner_id + org_id ─────────────────────────────────────
    # Add columns as nullable first to avoid failing on existing rows
    op.add_column("projects", sa.Column(
        "owner_id", postgresql.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    ))
    op.add_column("projects", sa.Column(
        "org_id", postgresql.UUID(as_uuid=True),
        sa.ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    ))
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])
    op.create_index("ix_projects_org_id",   "projects", ["org_id"])


def downgrade() -> None:
    # Projects
    op.drop_index("ix_projects_org_id",   table_name="projects")
    op.drop_index("ix_projects_owner_id", table_name="projects")
    op.drop_column("projects", "org_id")
    op.drop_column("projects", "owner_id")

    # Org members
    op.drop_table("org_members")

    # Organizations
    op.drop_table("organizations")

    # Users
    op.drop_table("users")
