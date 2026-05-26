from __future__ import annotations

import json
import threading
from pathlib import Path

from tools.source_lab.access.runtime import RuntimeStateStore


def _read_raw(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_state_store_writes_checksum(tmp_path: Path) -> None:
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    store.save_registry({"ep-1": {"state": "running"}})
    payload = _read_raw(store.registry_path)
    assert "checksum" in payload
    assert "payload" in payload


def test_state_store_recovers_from_backup_when_primary_checksum_fails(tmp_path: Path) -> None:
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    store.save_runtime_snapshot({"ep-1": {"state": "running"}})
    store.save_runtime_snapshot({"ep-1": {"state": "paused"}})
    raw = _read_raw(store.runtime_snapshot_path)
    raw["checksum"] = "broken"
    store.runtime_snapshot_path.write_text(json.dumps(raw), encoding="utf-8")

    bundle = store.load_recovery_bundle()
    assert bundle.runtime_snapshot.used_backup is True
    assert bundle.runtime_snapshot.payload == {"ep-1": {"state": "running"}}


def test_state_store_reports_error_when_primary_and_backup_corrupt(tmp_path: Path) -> None:
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    store.save_continuity_snapshot({"ep-1": {"endpoint_actual_samples": 1}})
    store.save_continuity_snapshot({"ep-1": {"endpoint_actual_samples": 2}})
    store.continuity_path.write_text("{bad", encoding="utf-8")
    store.continuity_path.with_suffix(".json.bak").write_text("{bad", encoding="utf-8")
    for candidate in store.base_dir.glob("continuity_snapshot.json.*.bak"):
        candidate.write_text("{bad", encoding="utf-8")

    bundle = store.load_recovery_bundle()
    assert bundle.continuity_snapshot.error is not None
    assert "backup_failed" in bundle.continuity_snapshot.error


def test_state_store_lock_prevents_interleaved_writes(tmp_path: Path) -> None:
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    barrier = threading.Barrier(2)

    def writer(value: int) -> None:
        barrier.wait()
        for _ in range(10):
            store.save_registry({"ep-1": {"value": value}})

    left = threading.Thread(target=writer, args=(1,))
    right = threading.Thread(target=writer, args=(2,))
    left.start()
    right.start()
    left.join()
    right.join()

    loaded = store.load_registry()
    assert loaded["ep-1"]["value"] in {1, 2}


def test_state_store_recovery_journal_records_checksum_failure(tmp_path: Path) -> None:
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    store.save_registry({"ep-1": {"state": "running"}})
    raw = _read_raw(store.registry_path)
    raw["checksum"] = "broken"
    store.registry_path.write_text(json.dumps(raw), encoding="utf-8")

    bundle = store.load_recovery_bundle()
    store.append_journal_entry(
        {
            "operation_id": "recover-1",
            "action": "RECOVER",
            "endpoint_id": "*",
            "decision": "ALLOW",
            "result": "FAILED" if bundle.registry.error else "SUCCESS",
            "reason_code": "checksum_failure" if bundle.registry.error else "ok",
            "recovery_errors": [bundle.registry.error] if bundle.registry.error else [],
            "timestamp": "2026-05-26T00:00:00+00:00",
        }
    )
    entries = store.load_journal_entries()
    assert any("checksum" in json.dumps(entry) for entry in entries)


def test_state_store_does_not_leak_sensitive_values_in_errors(tmp_path: Path) -> None:
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    store.accepted_endpoints_path.write_text(
        '{"payload":{"password":"secret","token":"abc","username":"alice"},"checksum":"broken"}',
        encoding="utf-8",
    )
    bundle = store.load_recovery_bundle()
    assert bundle.accepted_endpoints.error is not None
    assert "secret" not in bundle.accepted_endpoints.error
    assert "alice" not in bundle.accepted_endpoints.error
    assert "abc" not in bundle.accepted_endpoints.error
