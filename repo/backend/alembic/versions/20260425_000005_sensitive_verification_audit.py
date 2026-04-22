"""sensitive verification audit log

Revision ID: 20260425_000005
Revises: 20260424_000004
Create Date: 2026-04-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260425_000005"
down_revision: Union[str, Sequence[str], None] = "20260424_000004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sensitive_verification_audits",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_sensitive_verification_audits_registration_id",
        "sensitive_verification_audits",
        ["registration_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sensitive_verification_audits_registration_id", table_name="sensitive_verification_audits")
    op.drop_table("sensitive_verification_audits")
