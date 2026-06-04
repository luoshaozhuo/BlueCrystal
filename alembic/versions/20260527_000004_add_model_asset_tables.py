"""Add model_asset, simulation_case, simulation_result, simulation_artifact tables

Revision ID: 20260527_000004
Revises: 20260527_000003
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260527_000004"
down_revision = "20260527_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # model_asset
    op.create_table(
        "model_asset",
        sa.Column("model_asset_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_code", sa.String(128), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("model_type", sa.String(32), nullable=False),
        sa.Column("asset_scope", sa.String(32), nullable=False),
        sa.Column("owner_asset_instance_id", sa.Integer(), nullable=True),
        sa.Column("parent_model_asset_id", sa.Integer(), nullable=True),
        sa.Column("source_file_uri", sa.String(1024), nullable=True),
        sa.Column("raw_archive_batch_id", sa.String(128), nullable=True),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("parser_status", sa.String(32), nullable=False, server_default="IMPORTED"),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("model_asset_id"),
        sa.UniqueConstraint("model_code", name="uq_model_asset_code"),
        sa.ForeignKeyConstraint(
            ["owner_asset_instance_id"], ["asset_instance.asset_instance_id"],
            name="fk_model_asset_owner",
        ),
        sa.ForeignKeyConstraint(
            ["parent_model_asset_id"], ["model_asset.model_asset_id"],
            name="fk_model_asset_parent",
        ),
    )

    # simulation_case
    op.create_table(
        "simulation_case",
        sa.Column("simulation_case_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_code", sa.String(128), nullable=False),
        sa.Column("case_name", sa.String(255), nullable=False),
        sa.Column("model_asset_id", sa.Integer(), nullable=False),
        sa.Column("case_type", sa.String(32), nullable=False),
        sa.Column("input_file_uri", sa.String(1024), nullable=True),
        sa.Column("raw_archive_batch_id", sa.String(128), nullable=True),
        sa.Column("parameter_json", sa.JSON(), nullable=False),
        sa.Column("scenario_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="CREATED"),
        sa.Column("created_by", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("simulation_case_id"),
        sa.UniqueConstraint("case_code", name="uq_simulation_case_code"),
        sa.ForeignKeyConstraint(
            ["model_asset_id"], ["model_asset.model_asset_id"],
            name="fk_simulation_case_model_asset",
        ),
    )

    # simulation_result
    op.create_table(
        "simulation_result",
        sa.Column("simulation_result_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("simulation_case_id", sa.Integer(), nullable=False),
        sa.Column("result_code", sa.String(128), nullable=False),
        sa.Column("result_type", sa.String(32), nullable=False),
        sa.Column("result_file_uri", sa.String(1024), nullable=True),
        sa.Column("raw_archive_batch_id", sa.String(128), nullable=True),
        sa.Column("time_series_backend", sa.String(32), nullable=True),
        sa.Column("time_series_ref", sa.String(512), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("metric_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="IMPORTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("simulation_result_id"),
        sa.UniqueConstraint("result_code", name="uq_simulation_result_code"),
        sa.ForeignKeyConstraint(
            ["simulation_case_id"], ["simulation_case.simulation_case_id"],
            name="fk_simulation_result_case",
        ),
    )

    # simulation_artifact
    op.create_table(
        "simulation_artifact",
        sa.Column("simulation_artifact_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_type", sa.String(32), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("artifact_type", sa.String(32), nullable=False),
        sa.Column("file_uri", sa.String(1024), nullable=False),
        sa.Column("raw_archive_batch_id", sa.String(128), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("simulation_artifact_id"),
    )


def downgrade() -> None:
    op.drop_table("simulation_artifact")
    op.drop_table("simulation_result")
    op.drop_table("simulation_case")
    op.drop_table("model_asset")
