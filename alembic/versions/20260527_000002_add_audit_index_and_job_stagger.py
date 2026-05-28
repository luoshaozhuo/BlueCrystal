"""Add audit_event action/timestamp index and scheduler job stagger column

Revision ID: 20260527_000002
Revises: 20260527_000001
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260527_000002"
down_revision = "20260527_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add index on audit event action + event_timestamp for fast queries
    op.create_index(
        "ix_ingest_audit_event_action_ts",
        "ingest_audit_event",
        ["action", "event_timestamp"],
        postgresql_using="btree",
    )
    # Add stagger_offset_ms column to ingest_runtime_job
    op.add_column(
        "ingest_runtime_job",
        sa.Column("stagger_offset_ms", sa.Integer(), nullable=True, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("ingest_runtime_job", "stagger_offset_ms")
    op.drop_index("ix_ingest_audit_event_action_ts", table_name="ingest_audit_event")
