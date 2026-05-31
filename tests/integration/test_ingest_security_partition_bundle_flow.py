"""Security partition one-way bundle flow tests for ingest.

Simulates management zone export → collection zone import without
live API access between the two zones.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from whale.ingest.bundle.checksum import compute_bundle_checksum
from whale.ingest.bundle.model import AcquisitionTaskBundleItem, IngestBundle
from whale.ingest.bundle.redaction import redact_bundle
from whale.ingest.bundle.service import BundleService
from whale.ingest.framework.persistence import create_runtime_session_factory
from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.ports.audit import IngestAuditSinkPort
from sqlalchemy import create_engine
from whale.shared.persistence import Base


class _MemoryAuditSink(IngestAuditSinkPort):
    def __init__(self) -> None:
        self.events: list[IngestAuditEvent] = []

    def emit(self, event: IngestAuditEvent) -> None:
        self.events.append(event)


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(bind=engine)
    return create_runtime_session_factory(engine)


@pytest.fixture
def audit_sink():
    return _MemoryAuditSink()


@pytest.fixture
def service(session_factory, audit_sink):
    return BundleService(session_factory=session_factory, audit_sink=audit_sink, node_id="test-node")


def _make_bundle(**overrides) -> IngestBundle:
    now = datetime.now(tz=UTC)
    b = IngestBundle(
        bundle_version=overrides.get("bundle_version", "test-v1"),
        created_at=now,
        source=overrides.get("source", "test"),
        checksum="",
        acquisition_tasks=[
            AcquisitionTaskBundleItem(
                task_name="task-1",
                ld_instance_id=1,
                acquisition_mode="POLLING",
                poll_interval_ms=1000,
                request_timeout_ms=5000,
                enabled=True,
                priority=100,
                partition_key="p1",
                assignment_policy="active_standby",
                protocol_params={"protocol": "modbus"},
                version=1,
            )
        ],
    )
    payload = b.model_dump(mode="json")
    b.checksum = compute_bundle_checksum(payload)
    return b


class TestOneWayBundleFlow:

    @pytest.mark.integration
    def test_bundle_export_from_management_zone(self, service):
        """Management zone can export a raw bundle with metadata."""
        bundle = service.export_bundle(source="mgmt-zone", actor="admin", redacted=False)
        assert bundle.bundle_version
        assert bundle.checksum
        assert bundle.schema_version == "1.0"
        assert not bundle.redacted

    @pytest.mark.integration
    def test_redacted_bundle_cannot_be_imported(self, service):
        """A redacted bundle must be rejected when importing as accepted config."""
        raw = service.export_bundle(source="mgmt-zone", actor="admin", redacted=False)
        redacted = redact_bundle(raw)
        assert redacted.redacted

        with pytest.raises(ValueError, match="(?i)redacted"):
            service.import_bundle(redacted, actor="admin", dry_run=False)

    @pytest.mark.integration
    def test_raw_bundle_import_dry_run_then_accept(self, service):
        """Dry-run passes, then real import succeeds without corrupting existing config."""
        bundle = _make_bundle(bundle_version="accept-v1")

        dry = service.import_bundle(bundle, actor="admin", dry_run=True)
        assert dry.dry_run
        assert dry.imported_count == 1

        real = service.import_bundle(bundle, actor="admin", dry_run=False)
        assert not real.dry_run
        assert real.imported_count == 1

    @pytest.mark.integration
    def test_bundle_checksum_mismatch_rolls_back(self, service):
        """Checksum mismatch import raises and leaves existing config intact."""
        bundle = _make_bundle(bundle_version="checksum-v1")
        service.import_bundle(bundle, actor="admin", dry_run=False)

        corrupt = bundle.model_copy(update={"checksum": "deadbeef"})
        with pytest.raises(ValueError, match="checksum"):
            service.import_bundle(corrupt, actor="admin", dry_run=False)

        # Existing config should still be importable
        reimport = service.import_bundle(bundle, actor="admin", dry_run=False)
        assert reimport.imported_count == 1

    @pytest.mark.integration
    def test_bundle_import_audited(self, service, audit_sink):
        """Both successful and failed bundle imports produce audit events."""
        bundle = _make_bundle(bundle_version="audit-v1")
        service.import_bundle(bundle, actor="admin", dry_run=False)

        actions = [e.action for e in audit_sink.events]
        assert "bundle.import" in actions

        corrupt = bundle.model_copy(update={"checksum": "bad"})
        with pytest.raises(ValueError):
            service.import_bundle(corrupt, actor="admin", dry_run=False)

        assert any(e.reason_code == "CHECKSUM_MISMATCH" for e in audit_sink.events)
