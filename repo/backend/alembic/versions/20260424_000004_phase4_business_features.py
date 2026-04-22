"""phase 4: registrations expansion, materials, reviews, funding

Revision ID: 20260424_000004
Revises: 20260423_000003
Create Date: 2026-04-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260424_000004"
down_revision: Union[str, Sequence[str], None] = "20260423_000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    json_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")

    op.add_column("registrations", sa.Column("form_data", json_type, nullable=True))
    op.add_column("registrations", sa.Column("requested_funding", sa.Numeric(12, 2), nullable=True))
    op.add_column("registrations", sa.Column("status", sa.String(length=32), nullable=True))
    op.add_column("registrations", sa.Column("deadline", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "registrations",
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("registrations", sa.Column("supplementary_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("registrations", sa.Column("supplementary_deadline", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "registrations",
        sa.Column("supplementary_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("registrations", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("registrations", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    if dialect == "sqlite":
        op.execute(
            sa.text(
                "UPDATE registrations SET deadline = "
                "(SELECT deadline FROM activities WHERE activities.id = registrations.activity_id), "
                "form_data = '{}', requested_funding = 1, status = 'draft', "
                "created_at = datetime('now'), updated_at = datetime('now') "
                "WHERE deadline IS NULL"
            )
        )
    else:
        op.execute(
            sa.text(
                "UPDATE registrations AS r SET "
                "deadline = a.deadline, "
                "form_data = '{}'::jsonb, "
                "requested_funding = 1, "
                "status = 'draft', "
                "created_at = timezone('utc', now()), "
                "updated_at = timezone('utc', now()) "
                "FROM activities AS a WHERE r.activity_id = a.id AND r.deadline IS NULL"
            )
        )

    op.alter_column("registrations", "form_data", nullable=False)
    op.alter_column("registrations", "requested_funding", nullable=False)
    op.alter_column("registrations", "status", nullable=False)
    op.alter_column("registrations", "deadline", nullable=False)
    op.alter_column("registrations", "created_at", nullable=False)
    op.alter_column("registrations", "updated_at", nullable=False)

    op.create_table(
        "material_checklists",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("item_name", sa.String(length=255), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("allowed_types", json_type, nullable=False),
        sa.Column("max_file_size_mb", sa.Integer(), nullable=False, server_default=sa.text("20")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_material_checklists_registration_id", "material_checklists", ["registration_id"])

    op.create_table(
        "material_versions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("checklist_item_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("file_type", sa.String(length=20), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=32), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["checklist_item_id"], ["material_checklists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("sha256_hash", name="uq_material_versions_sha256_hash"),
    )
    op.create_index("ix_material_versions_checklist_item_id", "material_versions", ["checklist_item_id"])
    op.create_index("ix_material_versions_sha256_hash", "material_versions", ["sha256_hash"])

    op.create_table(
        "review_records",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("previous_status", sa.String(length=32), nullable=False),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("correction_reason", sa.Text(), nullable=True),
        sa.Column("batch_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_review_records_registration_id", "review_records", ["registration_id"])
    op.create_index("ix_review_records_batch_id", "review_records", ["batch_id"])

    op.create_table(
        "funding_accounts",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("approved_budget", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_income", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("total_expenses", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("registration_id", name="uq_funding_accounts_registration_id"),
    )
    op.create_index("ix_funding_accounts_registration_id", "funding_accounts", ["registration_id"])

    op.create_table(
        "transaction_records",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("funding_account_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("invoice_file_path", sa.String(length=500), nullable=True),
        sa.Column("recorded_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["funding_account_id"], ["funding_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_transaction_records_funding_account_id", "transaction_records", ["funding_account_id"])


def downgrade() -> None:
    op.drop_index("ix_transaction_records_funding_account_id", table_name="transaction_records")
    op.drop_table("transaction_records")
    op.drop_index("ix_funding_accounts_registration_id", table_name="funding_accounts")
    op.drop_table("funding_accounts")
    op.drop_index("ix_review_records_batch_id", table_name="review_records")
    op.drop_index("ix_review_records_registration_id", table_name="review_records")
    op.drop_table("review_records")
    op.drop_index("ix_material_versions_sha256_hash", table_name="material_versions")
    op.drop_index("ix_material_versions_checklist_item_id", table_name="material_versions")
    op.drop_table("material_versions")
    op.drop_index("ix_material_checklists_registration_id", table_name="material_checklists")
    op.drop_table("material_checklists")

    op.drop_column("registrations", "updated_at")
    op.drop_column("registrations", "created_at")
    op.drop_column("registrations", "supplementary_used")
    op.drop_column("registrations", "supplementary_deadline")
    op.drop_column("registrations", "supplementary_requested_at")
    op.drop_column("registrations", "is_locked")
    op.drop_column("registrations", "deadline")
    op.drop_column("registrations", "status")
    op.drop_column("registrations", "requested_funding")
    op.drop_column("registrations", "form_data")
