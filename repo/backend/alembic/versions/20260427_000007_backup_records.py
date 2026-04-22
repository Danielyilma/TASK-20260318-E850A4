"""backup records for pg_dump + uploads archives

Revision ID: 20260427_000007
Revises: 20260426_000006
Create Date: 2026-04-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260427_000007"
down_revision: Union[str, Sequence[str], None] = "20260426_000006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "backup_records",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("backup_type", sa.String(length=32), nullable=False),
        sa.Column("backup_path", sa.String(length=1024), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_detail", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("restored_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_backup_records_backup_type", "backup_records", ["backup_type"], unique=False)
    op.create_index("ix_backup_records_status", "backup_records", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_backup_records_status", table_name="backup_records")
    op.drop_index("ix_backup_records_backup_type", table_name="backup_records")
    op.drop_table("backup_records")
