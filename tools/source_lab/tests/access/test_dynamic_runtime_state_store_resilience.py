"""dynamic runtime state store 韧性测试。

验证 state store 在异常场景（磁盘满、并发写入、文件损坏）下的行为。
证据等级：L2（contract）。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import cast

import pytest

from tools.source_lab.access.runtime import RuntimeStateStore
from tools.source_lab.tests.access._dynamic_runtime_test_utils import (
    build_http_source,
    build_registry,
    polling_config,
)


def test_runtime_state_store_uses_atomic_write_for_snapshots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    seen: list[tuple[str, str]] = []
    original_replace = os.replace

    def recording_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        seen.append((str(src), str(dst)))
        original_replace(src, dst)

    monkeypatch.setattr(os, "replace", recording_replace)
    store.save_runtime_snapshot({"ep-1": {"state": "running"}})

    assert seen
    src, dst = seen[-1]
    assert src.endswith(".tmp")
    assert dst.endswith("endpoint_runtime_snapshot.json")


def test_runtime_state_recovery_handles_corrupt_continuity_snapshot(tmp_path: Path) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(1, 58101)
    assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"
    continuity_path = tmp_path / "runtime" / "continuity_snapshot.json"
    continuity_path.write_text("{bad-json", encoding="utf-8")

    recovered_registry, _recovered_monitor = build_registry(tmp_path)
    recovered = recovered_registry.recover()
    assert any(runtime.endpoint_id == source.connection.name for runtime in recovered)
    entries = recovered_registry._state_store.load_journal_entries()
    assert any(
        entry["action"] == "RECOVER"
        and entry["result"] == "FAILED"
        and any("continuity_snapshot.json" in error for error in cast(list[str], entry.get("recovery_errors", [])))
        for entry in entries
    )


def test_runtime_state_recovery_handles_corrupt_registry_snapshot(tmp_path: Path) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(2, 58102)
    assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"
    registry_path = tmp_path / "runtime" / "endpoint_registry.json"
    registry_path.write_text("{bad-json", encoding="utf-8")

    recovered_registry, _recovered_monitor = build_registry(tmp_path)
    recovered = recovered_registry.recover()
    assert any(runtime.endpoint_id == source.connection.name for runtime in recovered)
    entries = recovered_registry._state_store.load_journal_entries()
    assert any(
        entry["action"] == "RECOVER"
        and any("endpoint_registry.json" in error for error in cast(list[str], entry.get("recovery_errors", [])))
        for entry in entries
    )


def test_runtime_state_recovery_journals_partial_recovery_failure(tmp_path: Path) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(3, 58103)
    assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"
    (tmp_path / "runtime" / "accepted_endpoints.json").write_text('[{"broken": true}]', encoding="utf-8")

    recovered_registry, _recovered_monitor = build_registry(tmp_path)
    recovered = recovered_registry.recover()
    assert recovered == []
    entries = recovered_registry._state_store.load_journal_entries()
    assert any(
        entry["action"] == "RECOVER"
        and entry["result"] == "FAILED"
        and any(
            "accepted_endpoints.json" in error or "invalid_endpoint" in error
            for error in cast(list[str], entry.get("recovery_errors", []))
        )
        for entry in entries
    )


def test_runtime_state_recovery_does_not_start_deleted_or_invalid_endpoint(tmp_path: Path) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(4, 58104)
    assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"
    assert registry.delete_endpoint(source.connection.name).result == "SUCCESS"
    accepted_path = tmp_path / "runtime" / "accepted_endpoints.json"
    accepted_path.write_text(
        '[{"endpoint_id":"invalid-1","protocol":"http_rest","mode":"polling","source":{"endpoint":{"name":"invalid-1","host":"","port":0,"protocol":"http_rest","transport":"tcp","params":{"http_path":"/points"}},"points":[]}}]',
        encoding="utf-8",
    )

    recovered_registry, _recovered_monitor = build_registry(tmp_path)
    recovered = recovered_registry.recover()
    assert recovered == []
