"""Bundle import/export service for ingest runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from whale.ingest.bundle.checksum import compute_bundle_checksum
from whale.ingest.bundle.model import AcquisitionTaskBundleItem, IngestBundle
from whale.ingest.bundle.redaction import redact_bundle
from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.ports.audit import IngestAuditSinkPort
from whale.shared.persistence.orm import (
    AcquisitionTask,
    IngestBundleMetadata,
    IngestRuntimeConfigVersion,
)


@dataclass(frozen=True, slots=True)
class BundleImportResult:
    """Result returned by bundle import."""

    imported_count: int
    dry_run: bool
    config_version: int


class BundleService:
    """Import/export runtime acquisition-task bundles."""

    def __init__(
        self,
        session_factory: sessionmaker[Session] | Callable[[], Session],
        audit_sink: IngestAuditSinkPort | None = None,
        node_id: str | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._audit_sink = audit_sink
        self._node_id = node_id

    def export_bundle(
        self,
        *,
        source: str,
        actor: str | None,
        redacted: bool,
        bundle_version: str | None = None,
    ) -> IngestBundle:
        """Export the current acquisition-task configuration."""

        session = self._session_factory()
        try:
            tasks = list(session.scalars(select(AcquisitionTask).order_by(AcquisitionTask.task_id)))
            resolved_version = bundle_version or datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")
            bundle = IngestBundle(
                bundle_version=resolved_version,
                created_at=datetime.now(tz=UTC),
                source=source,
                checksum="",
                acquisition_tasks=[
                    AcquisitionTaskBundleItem(
                        task_name=task.task_name,
                        ld_instance_id=task.ld_instance_id,
                        acquisition_mode=task.acquisition_mode,
                        poll_interval_ms=task.poll_interval_ms,
                        request_timeout_ms=task.request_timeout_ms,
                        enabled=task.enabled,
                        priority=task.priority,
                        partition_key=task.partition_key,
                        assignment_policy=task.assignment_policy,
                        protocol_params=dict(task.protocol_params),
                        version=task.version,
                    )
                    for task in tasks
                ],
            )
            if redacted:
                bundle = redact_bundle(bundle)
            payload = bundle.model_dump(mode="json")
            checksum = compute_bundle_checksum(payload)
            bundle = bundle.model_copy(update={"checksum": checksum})
            session.add(
                IngestBundleMetadata(
                    bundle_version=bundle.bundle_version,
                    schema_version=bundle.schema_version,
                    checksum=bundle.checksum,
                    signature_status=bundle.signature_status,
                    source=bundle.source,
                    redacted=bundle.redacted,
                    status="EXPORTED",
                )
            )
            session.commit()
            self._emit_audit(
                actor=actor,
                action="bundle.export",
                resource_id=bundle.bundle_version,
                result="SUCCESS",
            )
            return bundle
        finally:
            session.close()

    def import_bundle(
        self,
        bundle: IngestBundle,
        *,
        actor: str | None,
        dry_run: bool,
    ) -> BundleImportResult:
        """Validate and import one bundle."""

        if not bundle.bundle_version.strip():
            raise ValueError("Bundle version is required.")
        if bundle.schema_version != "1.0":
            self._emit_audit(
                actor=actor,
                action="bundle.import",
                resource_id=bundle.bundle_version,
                result="FAILED",
                reason_code="SCHEMA_VERSION_UNSUPPORTED",
            )
            raise ValueError("Bundle schema_version is unsupported.")
        if bundle.redacted:
            self._emit_audit(
                actor=actor,
                action="bundle.import",
                resource_id=bundle.bundle_version,
                result="DENIED",
                reason_code="REDACTED_BUNDLE_DENIED",
            )
            raise ValueError("Redacted bundle cannot be imported as accepted config.")
        payload = bundle.model_dump(mode="json")
        expected_checksum = compute_bundle_checksum(payload)
        if expected_checksum != bundle.checksum:
            self._emit_audit(
                actor=actor,
                action="bundle.import",
                resource_id=bundle.bundle_version,
                result="FAILED",
                reason_code="CHECKSUM_MISMATCH",
            )
            raise ValueError("Bundle checksum mismatch.")

        session = self._session_factory()
        try:
            current_version = (
                session.execute(
                    select(IngestRuntimeConfigVersion).where(
                        IngestRuntimeConfigVersion.scope == "acquisition_tasks"
                    )
                ).scalar_one_or_none()
            )
            next_version = 1 if current_version is None else current_version.current_version + 1
            if dry_run:
                self._emit_audit(
                    actor=actor,
                    action="bundle.import",
                    resource_id=bundle.bundle_version,
                    result="SUCCESS",
                    reason_code="DRY_RUN",
                )
                return BundleImportResult(
                    imported_count=len(bundle.acquisition_tasks),
                    dry_run=True,
                    config_version=next_version,
                )

            try:
                for item in bundle.acquisition_tasks:
                    row = session.execute(
                        select(AcquisitionTask).where(AcquisitionTask.task_name == item.task_name)
                    ).scalar_one_or_none()
                    if row is None:
                        row = AcquisitionTask(
                            task_name=item.task_name,
                            ld_instance_id=item.ld_instance_id,
                            acquisition_mode=item.acquisition_mode,
                            task_status="STOPPED",
                            request_timeout_ms=item.request_timeout_ms,
                            poll_interval_ms=item.poll_interval_ms,
                            enabled=item.enabled,
                            priority=item.priority,
                            partition_key=item.partition_key,
                            assignment_policy=item.assignment_policy,
                            protocol_params=dict(item.protocol_params),
                            version=item.version,
                        )
                        session.add(row)
                    else:
                        row.ld_instance_id = item.ld_instance_id
                        row.acquisition_mode = item.acquisition_mode
                        row.request_timeout_ms = item.request_timeout_ms
                        row.poll_interval_ms = item.poll_interval_ms
                        row.enabled = item.enabled
                        row.priority = item.priority
                        row.partition_key = item.partition_key
                        row.assignment_policy = item.assignment_policy
                        row.protocol_params = dict(item.protocol_params)
                        row.version = item.version

                if current_version is None:
                    current_version = IngestRuntimeConfigVersion(
                        scope="acquisition_tasks",
                        current_version=next_version,
                        accepted_bundle_version=bundle.bundle_version,
                        checksum=bundle.checksum,
                    )
                    session.add(current_version)
                else:
                    current_version.current_version = next_version
                    current_version.accepted_bundle_version = bundle.bundle_version
                    current_version.checksum = bundle.checksum

                metadata = session.execute(
                    select(IngestBundleMetadata).where(
                        IngestBundleMetadata.bundle_version == bundle.bundle_version
                    )
                ).scalar_one_or_none()
                if metadata is None:
                    metadata = IngestBundleMetadata(
                        bundle_version=bundle.bundle_version,
                        schema_version=bundle.schema_version,
                        checksum=bundle.checksum,
                        signature_status=bundle.signature_status,
                        source=bundle.source,
                        redacted=bundle.redacted,
                    )
                    session.add(metadata)
                metadata.status = "IMPORTED"
                metadata.imported_at = datetime.now(tz=UTC)
                session.commit()
            except Exception:
                session.rollback()
                raise

            self._emit_audit(
                actor=actor,
                action="bundle.import",
                resource_id=bundle.bundle_version,
                result="SUCCESS",
            )
            return BundleImportResult(
                imported_count=len(bundle.acquisition_tasks),
                dry_run=False,
                config_version=next_version,
            )
        finally:
            session.close()

    def _emit_audit(
        self,
        *,
        actor: str | None,
        action: str,
        resource_id: str,
        result: str,
        reason_code: str | None = None,
    ) -> None:
        if self._audit_sink is None:
            return
        self._audit_sink.emit(
            IngestAuditEvent(
                request_id=f"bundle-{uuid4()}",
                actor=actor,
                action=action,
                resource_type="bundle",
                resource_id=resource_id,
                decision="ALLOW" if result == "SUCCESS" else "DENY",
                result=result,
                reason_code=reason_code,
                http_status=None,
                trace_id=None,
                client_ip=None,
                node_id=self._node_id,
            )
        )
