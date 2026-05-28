"""Bundle redaction tests."""

from __future__ import annotations

from datetime import UTC, datetime

from whale.ingest.bundle.model import AcquisitionTaskBundleItem, IngestBundle
from whale.ingest.bundle.redaction import redact_bundle


def test_redacted_bundle_masks_sensitive_protocol_params() -> None:
    bundle = IngestBundle(
        bundle_version="v1",
        created_at=datetime.now(tz=UTC),
        source="test",
        checksum="c1",
        acquisition_tasks=[
            AcquisitionTaskBundleItem(
                task_name="task-1",
                ld_instance_id=1,
                acquisition_mode="POLLING",
                poll_interval_ms=100,
                request_timeout_ms=500,
                enabled=True,
                priority=100,
                assignment_policy="AUTO",
                protocol_params={"password": "secret", "endpoint": "127.0.0.1"},
                version=1,
            )
        ],
    )

    redacted = redact_bundle(bundle)
    assert redacted.redacted is True
    assert redacted.acquisition_tasks[0].protocol_params["password"] == "***REDACTED***"
    assert redacted.acquisition_tasks[0].protocol_params["endpoint"] == "127.0.0.1"
