"""users activities registrations

Revision ID: 20260422_000002
Revises: 20260421_000001
Create Date: 2026-04-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260422_000002"
down_revision: Union[str, Sequence[str], None] = "20260421_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("salt", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("id_number", sa.String(length=50), nullable=True),
        sa.Column("contact_info", sa.String(length=255), nullable=True),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("first_failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    op.create_table(
        "activities",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("budget", sa.Numeric(14, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "registrations",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("applicant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"], name="fk_registrations_activity_id"),
        sa.ForeignKeyConstraint(["applicant_id"], ["users.id"], name="fk_registrations_applicant_id"),
    )
    op.create_index("ix_registrations_activity_id", "registrations", ["activity_id"], unique=False)
    op.create_index("ix_registrations_applicant_id", "registrations", ["applicant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_registrations_applicant_id", table_name="registrations")
    op.drop_index("ix_registrations_activity_id", table_name="registrations")
    op.drop_table("registrations")
    op.drop_table("activities")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
