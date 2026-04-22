"""phase 5: audit logs, alerts, data collection, reports

Revision ID: 20260426_000006
Revises: 20260425_000005
Create Date: 2026-04-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260426_000006"
down_revision: Union[str, Sequence[str], None] = "20260425_000005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"], unique=False)
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"], unique=False)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)

    op.create_table(
        "alert_records",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("alert_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("acknowledged_by", sa.Uuid(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_alert_records_alert_type", "alert_records", ["alert_type"], unique=False)
    op.create_index("ix_alert_records_acknowledged", "alert_records", ["acknowledged"], unique=False)
    op.create_index("ix_alert_records_created_at", "alert_records", ["created_at"], unique=False)

    op.create_table(
        "data_collection_batches",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("scope_whitelist", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "quality_validation_results",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("registration_id", sa.Uuid(), nullable=False),
        sa.Column("validation_type", sa.String(length=100), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["data_collection_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_qvr_batch_id", "quality_validation_results", ["batch_id"], unique=False)
    op.create_index("ix_qvr_registration_id", "quality_validation_results", ["registration_id"], unique=False)

    op.create_table(
        "generated_reports",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("report_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'completed'")),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("file_format", sa.String(length=16), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("activity_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_generated_reports_report_type", "generated_reports", ["report_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_generated_reports_report_type", table_name="generated_reports")
    op.drop_table("generated_reports")
    op.drop_index("ix_qvr_registration_id", table_name="quality_validation_results")
    op.drop_index("ix_qvr_batch_id", table_name="quality_validation_results")
    op.drop_table("quality_validation_results")
    op.drop_table("data_collection_batches")
    op.drop_index("ix_alert_records_created_at", table_name="alert_records")
    op.drop_index("ix_alert_records_acknowledged", table_name="alert_records")
    op.drop_index("ix_alert_records_alert_type", table_name="alert_records")
    op.drop_table("alert_records")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
