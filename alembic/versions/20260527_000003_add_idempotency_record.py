"""Add ingest_idempotency_record table

Revision ID: 20260527_000003
Revises: 20260527_000002
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260527_000003"
down_revision = "20260527_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingest_idempotency_record",
        sa.Column("record_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_fingerprint", sa.String(128), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("record_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_ingest_idempotency_record_key"),
    )


def downgrade() -> None:
    op.drop_table("ingest_idempotency_record")
