"""dynamic runtime state store 保留策略测试。

验证 state store 的保留/清理策略行为。
测试阶段：开发期验证 (contract)。
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.source_lab.access.runtime import RuntimeStateStore


def test_runtime_state_store_retains_recent_versioned_backups(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_LAB_RUNTIME_SNAPSHOT_RETENTION", "3")
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    for index in range(6):
        store.save_registry({"ep-1": {"value": index}})
    backups = sorted(store.base_dir.glob("endpoint_registry.json.*.bak"))
    assert len(backups) == 3


def test_runtime_state_store_recovery_prefers_recent_valid_backup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_LAB_RUNTIME_SNAPSHOT_RETENTION", "4")
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    store.save_registry({"ep-1": {"value": 1}})
    store.save_registry({"ep-1": {"value": 2}})
    store.save_registry({"ep-1": {"value": 3}})
    store.registry_path.write_text('{"checksum":"broken","payload":{"oops":1}}', encoding="utf-8")

    bundle = store.load_recovery_bundle()
    assert bundle.registry.used_backup is True
    assert bundle.registry.selected_backup is not None
    assert bundle.registry.payload == {"ep-1": {"value": 2}}


def test_runtime_state_store_inspect_reports_backup_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_LAB_RUNTIME_SNAPSHOT_RETENTION", "2")
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    store.save_continuity_snapshot({"ep-1": {"endpoint_actual_samples": 1}})
    store.save_continuity_snapshot({"ep-1": {"endpoint_actual_samples": 2}})

    summary = store.inspect_state_store()
    continuity = summary["continuity_snapshot"]
    assert isinstance(continuity["backup_count"], int)
    assert continuity["backup_count"] >= 1
    assert isinstance(continuity["retention"], int)
    assert continuity["retention"] == 2
    assert continuity["latest_backup"] is not None


def test_runtime_state_store_repair_restores_primary_from_backup(tmp_path: Path) -> None:
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    store.save_runtime_snapshot({"ep-1": {"state": "running"}})
    store.save_runtime_snapshot({"ep-1": {"state": "paused"}})
    store.runtime_snapshot_path.write_text("{bad", encoding="utf-8")

    result = store.repair_state_store()
    assert result["runtime_snapshot"]["status"] == "SUCCESS"
    restored = store.load_runtime_snapshot()
    assert restored == {"ep-1": {"state": "running"}}


def test_runtime_state_store_repair_reports_failure_without_backup(tmp_path: Path) -> None:
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    store.registry_path.write_text("{bad", encoding="utf-8")

    result = store.repair_state_store()
    assert result["registry"]["status"] == "FAILED"
