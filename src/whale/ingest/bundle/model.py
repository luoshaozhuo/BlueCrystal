"""Bundle model for ingest runtime configuration export/import."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AcquisitionTaskBundleItem(BaseModel):
    """Serializable acquisition-task record stored inside one bundle."""

    task_name: str
    ld_instance_id: int
    acquisition_mode: str
    poll_interval_ms: int
    request_timeout_ms: int
    enabled: bool
    priority: int
    partition_key: str | None = None
    assignment_policy: str
    protocol_params: dict[str, object] = Field(default_factory=dict)
    version: int


class IngestBundle(BaseModel):
    """Serializable ingest bundle envelope."""

    schema_version: str = "1.0"
    bundle_version: str
    created_at: datetime
    source: str
    checksum: str
    signature_status: str = "UNSIGNED"
    redacted: bool = False
    acquisition_tasks: list[AcquisitionTaskBundleItem] = Field(default_factory=list)
