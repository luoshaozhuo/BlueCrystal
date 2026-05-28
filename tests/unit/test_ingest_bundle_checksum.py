"""Bundle checksum tests."""

from __future__ import annotations

from whale.ingest.bundle.checksum import compute_bundle_checksum


def test_bundle_checksum_ignores_existing_checksum_field() -> None:
    payload = {
        "schema_version": "1.0",
        "bundle_version": "v1",
        "checksum": "old",
        "acquisition_tasks": [{"task_name": "task-1"}],
    }
    first = compute_bundle_checksum(payload)
    payload["checksum"] = "another"
    second = compute_bundle_checksum(payload)
    assert first == second
