"""ingest runtime initial revision"""

from __future__ import annotations

from alembic import op

from whale.shared.persistence import Base
import whale.shared.persistence.orm  # noqa: F401
import whale.ingest.framework.persistence.orm  # noqa: F401

revision = "20260527_000001"
down_revision = None
branch_labels = None
depends_on = None

_TABLE_NAMES = (
    "asset_type",
    "asset_model",
    "org_unit",
    "asset_instance",
    "scada_data_type",
    "scada_ied",
    "scada_communication_endpoint",
    "scada_signal_profile",
    "scada_ld_instance",
    "scada_signal_profile_item",
    "acq_task",
    "acq_signal_state",
    "acq_signal_sample",
    "ingest_runtime_node",
    "ingest_runtime_job",
    "ingest_job_assignment",
    "ingest_job_lease",
    "ingest_fencing_token",
    "ingest_bundle_metadata",
    "ingest_audit_event",
    "ingest_runtime_config_version",
)


def upgrade() -> None:
    bind = op.get_bind()
    for table_name in _TABLE_NAMES:
        Base.metadata.tables[table_name].create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for table_name in reversed(_TABLE_NAMES):
        Base.metadata.tables[table_name].drop(bind=bind, checkfirst=True)
