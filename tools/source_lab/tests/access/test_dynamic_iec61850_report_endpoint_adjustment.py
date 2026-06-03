"""IEC 61850 Report endpoint 动态调整测试。

验证 Report endpoint 在 runtime 的创建、修改和移除行为。
测试阶段：开发期验证 (contract)。
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import UpdateConfig
from tools.source_lab.tests.access._dynamic_runtime_test_utils import (
    build_iec61850_report_source,
    build_native_registry,
    choose_port,
    report_config,
    runtime_spec,
    shutdown_registry,
)


def _require_report_runtime() -> None:
    build_dir = Path(__file__).resolve().parents[2] / "native" / "build"
    required = ("iec61850_report_runner", "iec61850_simulator_server")
    missing = [str(build_dir / name) for name in required if not (build_dir / name).exists()]
    if missing:
        pytest.skip(
            "dependency_missing: "
            + ",".join(missing)
            + " not compiled. CI hint: cmake -S tools/source_lab/native -B tools/source_lab/native/build && cmake --build tools/source_lab/native/build"
        )


def test_dynamic_report_stop_one_rcb_keeps_other_rcb_receiving(tmp_path: Path) -> None:
    _require_report_runtime()
    sources = tuple(build_iec61850_report_source(index, choose_port(57301, 57800)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(report_config(source, interval_ms=500.0)).result == "SUCCESS"
        time.sleep(1.5)
        before = monitor.snapshot()
        assert registry.stop_endpoint(sources[0].connection.name).result == "SUCCESS"
        time.sleep(1.0)
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_event_count > before[source.connection.name].endpoint_event_count
            assert after[source.connection.name].endpoint_restart_count == before[source.connection.name].endpoint_restart_count
            assert after[source.connection.name].endpoint_config_version == before[source.connection.name].endpoint_config_version
            assert after[source.connection.name].stagger_offset_changed is False
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_report_pause_one_rcb_keeps_other_rcb_receiving(tmp_path: Path) -> None:
    _require_report_runtime()
    sources = tuple(build_iec61850_report_source(index, choose_port(57801, 58300)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(report_config(source, interval_ms=500.0)).result == "SUCCESS"
        time.sleep(1.5)
        before = monitor.snapshot()
        assert registry.pause_endpoint(sources[0].connection.name).result == "SUCCESS"
        time.sleep(1.0)
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_event_count > before[source.connection.name].endpoint_event_count
            assert after[source.connection.name].endpoint_callback_gap_count == 0
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_report_replace_points_keeps_unaffected_rcb_receiving(tmp_path: Path) -> None:
    _require_report_runtime()
    sources = tuple(build_iec61850_report_source(index, choose_port(58301, 58800)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(report_config(source, interval_ms=500.0)).result == "SUCCESS"
        time.sleep(1.5)
        before = monitor.snapshot()
        updated_points = runtime_spec(sources[0]).points[:1]
        assert registry.replace_points(sources[0].connection.name, updated_points, expected_version=1).result == "SUCCESS"
        time.sleep(1.0)
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_event_count > before[source.connection.name].endpoint_event_count
            assert after[source.connection.name].endpoint_restart_count == before[source.connection.name].endpoint_restart_count
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_report_host_port_patch_rolls_back_without_affecting_others(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_report_runtime()
    sources = tuple(build_iec61850_report_source(index, choose_port(58801, 59300)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    original_start = registry._session_manager.start_endpoint
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(report_config(source, interval_ms=500.0)).result == "SUCCESS"
        time.sleep(1.5)
        before = monitor.snapshot()

        injected = {"done": False}

        def fail_once(runtime, config):
            if runtime.endpoint_id == sources[0].connection.name and config.config_version == 2 and not injected["done"]:
                injected["done"] = True
                raise RuntimeError("report replacement failed")
            return original_start(runtime, config)

        monkeypatch.setattr(registry._session_manager, "start_endpoint", fail_once)
        result = registry.update_endpoint(
            sources[0].connection.name,
            {"host": "127.0.0.1", "port": choose_port(59301, 59450)},
            expected_version=1,
        )
        assert result.result == "ROLLBACK"
        time.sleep(0.8)
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_event_count > before[source.connection.name].endpoint_event_count
            assert after[source.connection.name].endpoint_restart_count == before[source.connection.name].endpoint_restart_count
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_report_continuity_metrics_for_unaffected_endpoint(tmp_path: Path) -> None:
    _require_report_runtime()
    sources = tuple(build_iec61850_report_source(index, choose_port(59451, 59900)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(report_config(source, interval_ms=500.0)).result == "SUCCESS"
        time.sleep(1.5)
        assert registry.pause_endpoint(sources[0].connection.name).result == "SUCCESS"
        time.sleep(0.8)
        metrics = monitor.snapshot()[sources[1].connection.name]
        assert metrics.unaffected_endpoint_samples > 0
        assert metrics.unaffected_endpoint_continuity_breaks == 0
        assert metrics.endpoint_callback_gap_count == 0
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_report_journal_records_success_failed_rollback(tmp_path: Path) -> None:
    _require_report_runtime()
    source = build_iec61850_report_source(9, choose_port(59901, 60100))
    registry, _monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create((source,), update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    original_start = registry._session_manager.start_endpoint
    try:
        fleet.start()
        assert registry.add_endpoint(report_config(source, interval_ms=500.0)).result == "SUCCESS"
        injected = {"done": False}

        def fail_once(runtime, config):
            if config.config_version == 2 and not injected["done"]:
                injected["done"] = True
                raise RuntimeError("report replacement failed")
            return original_start(runtime, config)

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(registry._session_manager, "start_endpoint", fail_once)
        try:
            assert registry.update_endpoint(source.connection.name, {"host": "127.0.0.2"}, expected_version=1).result == "ROLLBACK"
        finally:
            monkeypatch.undo()
        assert registry.update_endpoint(source.connection.name, {"unsupported": True}, expected_version=1).result == "VALIDATION_ERROR"
        entries = registry._state_store.load_journal_entries()
        results = {entry["result"] for entry in entries}
        assert {"SUCCESS", "ROLLBACK", "VALIDATION_ERROR"} <= results
    finally:
        shutdown_registry(registry)
        fleet.stop()
