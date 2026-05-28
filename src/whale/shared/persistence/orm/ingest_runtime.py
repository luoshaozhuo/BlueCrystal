"""Runtime persistence models for ingest API, scheduler, lease, and audit."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from whale.shared.persistence import Base


class IngestRuntimeNode(Base):
    """One runtime node participating in ingest scheduling."""

    __tablename__ = "ingest_runtime_node"

    node_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    runtime_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ALIVE")
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class IngestRuntimeJob(Base):
    """One scheduler-visible runtime job."""

    __tablename__ = "ingest_runtime_job"

    job_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False, default="acquisition")
    task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("acq_task.task_id"),
        nullable=True,
        index=True,
    )
    partition_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    schedule_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    schedule_expr: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class IngestJobAssignment(Base):
    """DB-backed assignment of one runtime job to one node."""

    __tablename__ = "ingest_job_assignment"
    __table_args__ = (
        UniqueConstraint("job_id", "node_key", name="uq_ingest_job_assignment_job_node"),
    )

    assignment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("ingest_runtime_job.job_id"), nullable=False, index=True)
    node_key: Mapped[str] = mapped_column(
        ForeignKey("ingest_runtime_node.node_key"),
        nullable=False,
        index=True,
    )
    assignment_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class IngestJobLease(Base):
    """Lease table shared by scheduler job leases and write leases."""

    __tablename__ = "ingest_job_lease"
    __table_args__ = (
        UniqueConstraint("lease_name", name="uq_ingest_job_lease_name"),
    )

    lease_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lease_name: Mapped[str] = mapped_column(String(255), nullable=False)
    lease_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    holder_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    fencing_token: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    renewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class IngestFencingToken(Base):
    """Monotonic fencing counter for one leased resource."""

    __tablename__ = "ingest_fencing_token"

    token_name: Mapped[str] = mapped_column(String(255), primary_key=True)
    current_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class IngestBundleMetadata(Base):
    """Bundle export/import bookkeeping."""

    __tablename__ = "ingest_bundle_metadata"

    bundle_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bundle_version: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    signature_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNSIGNED")
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    redacted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="EXPORTED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    imported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class IngestAuditEventOrm(Base):
    """Structured ingest audit event persisted into the runtime DB."""

    __tablename__ = "ingest_audit_event"

    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    actor: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    trace_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    node_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    before_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    after_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    changed_fields_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    attributes_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class IngestRuntimeConfigVersion(Base):
    """Accepted runtime configuration version tracker."""

    __tablename__ = "ingest_runtime_config_version"
    __table_args__ = (
        UniqueConstraint("scope", name="uq_ingest_runtime_config_version_scope"),
    )

    config_version_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    accepted_bundle_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class IngestIdempotencyRecord(Base):
    """Idempotency key tracking for CRUD API requests."""

    __tablename__ = "ingest_idempotency_record"

    record_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True, unique=True)
    request_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
