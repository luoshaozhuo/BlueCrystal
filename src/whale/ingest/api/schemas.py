"""Pydantic schemas for ingest runtime CRUD APIs."""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field


AcquisitionModeLiteral = Literal["READ_ONCE", "POLLING", "SUBSCRIBE", "REPORT"]

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Small pagination envelope shared by runtime-config lists."""

    items: list[T]
    total: int
    limit: int
    offset: int


class AcquisitionTaskCreate(BaseModel):
    task_name: str
    ld_instance_id: int
    acquisition_mode: AcquisitionModeLiteral = "POLLING"
    poll_interval_ms: int = 100
    request_timeout_ms: int = 500
    enabled: bool = True
    priority: int = 100
    partition_key: str | None = None
    assignment_policy: str = "AUTO"
    protocol_params: dict[str, Any] = Field(default_factory=dict)


class AcquisitionTaskPatch(BaseModel):
    expected_version: int
    task_name: str | None = None
    acquisition_mode: AcquisitionModeLiteral | None = None
    poll_interval_ms: int | None = None
    request_timeout_ms: int | None = None
    enabled: bool | None = None
    priority: int | None = None
    partition_key: str | None = None
    assignment_policy: str | None = None
    protocol_params: dict[str, Any] | None = None


class AcquisitionTaskResponse(BaseModel):
    task_id: int
    task_name: str
    ld_instance_id: int
    acquisition_mode: str
    poll_interval_ms: int
    request_timeout_ms: int
    enabled: bool
    priority: int
    partition_key: str | None
    assignment_policy: str
    protocol_params: dict[str, Any]
    version: int

    @classmethod
    def from_orm_row(cls, row: object) -> "AcquisitionTaskResponse":
        return cls(
            task_id=row.task_id,
            task_name=row.task_name,
            ld_instance_id=row.ld_instance_id,
            acquisition_mode=row.acquisition_mode,
            poll_interval_ms=row.poll_interval_ms,
            request_timeout_ms=row.request_timeout_ms,
            enabled=row.enabled,
            priority=row.priority,
            partition_key=row.partition_key,
            assignment_policy=row.assignment_policy,
            protocol_params=dict(row.protocol_params),
            version=row.version,
        )


class SourceCreate(BaseModel):
    ied_name: str
    asset_code: str
    asset_name: str
    ied_type: str | None = None
    standard_family: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class SourcePatch(BaseModel):
    expected_version: int
    ied_name: str | None = None
    asset_name: str | None = None
    ied_type: str | None = None
    standard_family: str | None = None
    metadata_json: dict[str, Any] | None = None


class SourceResponse(BaseModel):
    source_id: int
    ied_name: str
    asset_instance_id: int
    asset_code: str
    asset_name: str
    ied_type: str | None
    standard_family: str | None
    version: int


class ConnectionCreate(BaseModel):
    source_id: int
    access_point_name: str
    application_protocol: str
    transport: str
    service_type: str | None = None
    host: str | None = None
    port: int | None = None
    namespace_uri: str | None = None
    endpoint_name: str | None = None
    credential_ref: str | None = None
    service_capabilities_json: dict[str, Any] = Field(default_factory=dict)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ConnectionPatch(BaseModel):
    expected_version: int
    access_point_name: str | None = None
    application_protocol: str | None = None
    transport: str | None = None
    service_type: str | None = None
    host: str | None = None
    port: int | None = None
    namespace_uri: str | None = None
    endpoint_name: str | None = None
    credential_ref: str | None = None
    service_capabilities_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None


class ConnectionResponse(BaseModel):
    connection_id: int
    source_id: int
    access_point_name: str
    application_protocol: str
    transport: str
    service_type: str | None
    host: str | None
    port: int | None
    namespace_uri: str | None
    endpoint_name: str | None
    credential_ref: str | None
    service_capabilities_json: dict[str, Any]
    metadata_json: dict[str, Any]
    version: int


class SignalProfileCreate(BaseModel):
    profile_code: str
    profile_name: str
    standard_family: str | None = None
    vendor: str | None = None
    version_label: str | None = None
    description: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class SignalProfilePatch(BaseModel):
    expected_version: int
    profile_code: str | None = None
    profile_name: str | None = None
    standard_family: str | None = None
    vendor: str | None = None
    version_label: str | None = None
    description: str | None = None
    metadata_json: dict[str, Any] | None = None


class SignalProfileResponse(BaseModel):
    signal_profile_id: int
    profile_code: str
    profile_name: str
    standard_family: str | None
    vendor: str | None
    version_label: str | None
    description: str | None
    metadata_json: dict[str, Any]
    version: int


class PointCreate(BaseModel):
    signal_profile_id: int
    relative_path: str
    do_name: str
    data_type_name: str
    ln_class: str | None = None
    ln_name: str | None = None
    da_name: str | None = None
    fc: str | None = None
    cdc: str | None = None
    default_unit: str | None = None
    writable: bool = False
    display_name: str | None = None
    description: str | None = None


class PointPatch(BaseModel):
    expected_version: int
    relative_path: str | None = None
    do_name: str | None = None
    data_type_name: str | None = None
    ln_class: str | None = None
    ln_name: str | None = None
    da_name: str | None = None
    fc: str | None = None
    cdc: str | None = None
    default_unit: str | None = None
    writable: bool | None = None
    display_name: str | None = None
    description: str | None = None


class PointResponse(BaseModel):
    point_id: int
    signal_profile_id: int
    relative_path: str
    do_name: str
    data_type_name: str
    ln_class: str | None
    ln_name: str | None
    da_name: str | None
    fc: str | None
    cdc: str | None
    default_unit: str | None
    writable: bool
    display_name: str | None
    description: str | None
    version: int


# ── Scheduler Job ──────────────────────────────────────────────────────────

class SchedulerJobCreate(BaseModel):
    job_id: str
    job_type: str = "acquisition"
    task_id: int | None = None
    partition_key: str | None = None
    enabled: bool = True
    priority: int = 100
    schedule_kind: str = "manual"
    schedule_expr: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    stagger_offset_ms: int | None = None


class SchedulerJobPatch(BaseModel):
    expected_version: int
    job_type: str | None = None
    enabled: bool | None = None
    priority: int | None = None
    partition_key: str | None = None
    schedule_kind: str | None = None
    schedule_expr: str | None = None
    config: dict[str, Any] | None = None
    stagger_offset_ms: int | None = None


class SchedulerJobResponse(BaseModel):
    job_id: str
    job_type: str
    task_id: int | None
    partition_key: str | None
    enabled: bool
    priority: int
    schedule_kind: str
    schedule_expr: str | None
    version: int
    config: dict[str, Any]
    stagger_offset_ms: int | None = None


# ── Security Partition ─────────────────────────────────────────────────────

class SecurityPartitionCreate(BaseModel):
    partition_code: str
    partition_name: str
    security_zone: str = "UNCLASSIFIED"
    direction: str = "READ_ONLY"
    description: str | None = None
    rules_json: dict[str, Any] = Field(default_factory=dict)


class SecurityPartitionPatch(BaseModel):
    expected_version: int
    partition_name: str | None = None
    security_zone: str | None = None
    direction: str | None = None
    description: str | None = None
    rules_json: dict[str, Any] | None = None


class SecurityPartitionResponse(BaseModel):
    partition_id: int
    partition_code: str
    partition_name: str
    security_zone: str
    direction: str
    description: str | None
    rules_json: dict[str, Any]
    version: int


# ── Bundle Metadata ────────────────────────────────────────────────────────

class BundleMetadataResponse(BaseModel):
    bundle_id: int
    bundle_version: str
    schema_version: str
    checksum: str
    signature_status: str
    source: str
    redacted: bool
    status: str
    created_at: str
    imported_at: str | None


# ── Node ───────────────────────────────────────────────────────────────────

class NodeResponse(BaseModel):
    node_key: str
    runtime_mode: str
    status: str
    hostname: str | None
    heartbeat_at: str
    last_seen_at: str
    created_at: str
    updated_at: str


# ── Lease ──────────────────────────────────────────────────────────────────

class LeaseResponse(BaseModel):
    lease_id: int
    lease_name: str
    lease_scope: str
    resource_id: str
    holder_key: str
    status: str
    fencing_token: int
    acquired_at: str
    renewed_at: str
    expires_at: str
    released_at: str | None
    version: int


# ── Audit Event ────────────────────────────────────────────────────────────

class AuditEventResponse(BaseModel):
    audit_id: int
    request_id: str
    actor: str | None
    action: str
    resource_type: str
    resource_id: str | None
    decision: str
    result: str
    reason_code: str | None
    http_status: int | None
    trace_id: str | None
    client_ip: str | None
    node_id: str | None
    event_timestamp: str
