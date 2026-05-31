"""OPC UA subscription endpoint 动态调整测试。

验证 OPC UA subscription endpoint 的创建、修改和移除行为。
证据等级：L2（contract）。
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import UpdateConfig
from tools.source_lab.protocols.opcua.open62541_source_simulator import resolve_runner_path as resolve_simulator_path
from tools.source_lab.tests.access._dynamic_runtime_test_utils import (
    build_native_registry,
    build_opcua_source,
    choose_port,
    runtime_spec,
    shutdown_registry,
    subscribe_config,
    wait_for_metric_growth,
)


def _require_opcua_native() -> None:
    build_dir = Path(__file__).resolve().parents[2] / "native" / "build"
    missing = [
        str(path)
        for path in (
            build_dir / "open62541_subscription_runner",
            build_dir / "open62541_source_simulator",
        )
        if not path.exists()
    ]
    if missing:
        pytest.skip(
            "dependency_missing: "
            + ",".join(missing)
            + " not compiled. CI hint: cmake -S tools/source_lab/native -B tools/source_lab/native/build && cmake --build tools/source_lab/native/build"
        )
    if not resolve_simulator_path().exists():
        pytest.skip("dependency_missing: open62541_source_simulator path unresolved")


def test_dynamic_opcua_subscription_pause_one_endpoint_keeps_others_receiving(tmp_path: Path) -> None:
    _require_opcua_native()
    sources = tuple(build_opcua_source(index, choose_port(51301, 51800)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(subscribe_config(source, interval_ms=200.0)).result == "SUCCESS"
        time.sleep(1.6)
        for source in sources[1:]:
            wait_for_metric_growth(monitor, source.connection.name, timeout_s=6.0)
        before = monitor.snapshot()

        assert registry.pause_endpoint(sources[0].connection.name).result == "SUCCESS"
        for source in sources[1:]:
            wait_for_metric_growth(
                monitor,
                source.connection.name,
                baseline_samples=before[source.connection.name].endpoint_actual_samples,
                timeout_s=6.0,
            )
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_actual_samples > before[source.connection.name].endpoint_actual_samples
            assert after[source.connection.name].endpoint_restart_count == before[source.connection.name].endpoint_restart_count
            assert after[source.connection.name].unaffected_endpoint_continuity_breaks == 0
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_opcua_subscription_replace_points_keeps_others_receiving(tmp_path: Path) -> None:
    _require_opcua_native()
    sources = tuple(build_opcua_source(index, choose_port(51801, 52300)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(subscribe_config(source, interval_ms=200.0)).result == "SUCCESS"
        time.sleep(1.6)
        before = monitor.snapshot()

        updated_points = runtime_spec(sources[0]).points[:1]
        assert registry.replace_points(sources[0].connection.name, updated_points, expected_version=1).result == "SUCCESS"
        time.sleep(1.0)
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_actual_samples > before[source.connection.name].endpoint_actual_samples
            assert after[source.connection.name].endpoint_restart_count == before[source.connection.name].endpoint_restart_count
            assert after[source.connection.name].endpoint_config_version == before[source.connection.name].endpoint_config_version
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_opcua_subscription_patch_host_port_replaces_only_target_endpoint(tmp_path: Path) -> None:
    _require_opcua_native()
    sources = tuple(build_opcua_source(index, choose_port(52301, 52800)) for index in range(3))
    spare = build_opcua_source(99, choose_port(52801, 53000))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources + (spare,), update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(subscribe_config(source, interval_ms=200.0)).result == "SUCCESS"
        time.sleep(1.6)
        before = monitor.snapshot()

        result = registry.update_endpoint(
            sources[0].connection.name,
            {"host": "127.0.0.1", "port": spare.connection.port},
            expected_version=1,
        )
        assert result.result == "SUCCESS"
        time.sleep(1.0)
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_actual_samples > before[source.connection.name].endpoint_actual_samples
            assert after[source.connection.name].endpoint_restart_count == before[source.connection.name].endpoint_restart_count
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_opcua_subscription_replacement_failure_does_not_restart_unaffected_endpoints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_opcua_native()
    sources = tuple(build_opcua_source(index, choose_port(53001, 53500)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    original_start = registry._session_manager.start_endpoint
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(subscribe_config(source, interval_ms=200.0)).result == "SUCCESS"
        time.sleep(1.6)
        before = monitor.snapshot()

        failure_injected = {"done": False}

        def fail_target(runtime, config):
            if (
                runtime.endpoint_id == sources[0].connection.name
                and getattr(config, "config_version", 0) == 2
                and not failure_injected["done"]
            ):
                failure_injected["done"] = True
                raise RuntimeError("forced native replacement failure")
            return original_start(runtime, config)

        monkeypatch.setattr(registry._session_manager, "start_endpoint", fail_target)
        result = registry.update_endpoint(
            sources[0].connection.name,
            {"params": {"subscription_name": "replaced"}},
            expected_version=1,
        )
        assert result.result == "ROLLBACK"
        time.sleep(0.8)
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_restart_count == before[source.connection.name].endpoint_restart_count
            assert after[source.connection.name].endpoint_actual_samples > before[source.connection.name].endpoint_actual_samples
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_opcua_subscription_callback_gap_metrics_for_unaffected_endpoints(tmp_path: Path) -> None:
    _require_opcua_native()
    sources = tuple(build_opcua_source(index, choose_port(53501, 54000)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(subscribe_config(source, interval_ms=180.0)).result == "SUCCESS"
        time.sleep(1.6)
        assert registry.pause_endpoint(sources[0].connection.name).result == "SUCCESS"
        time.sleep(0.8)
        metrics = monitor.snapshot()[sources[1].connection.name]

        assert metrics.unaffected_endpoint_samples > 0
        assert metrics.unaffected_endpoint_continuity_breaks == 0
        assert metrics.endpoint_missed_tick_count == 0
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_opcua_subscription_journal_records_success_failed_conflict_denied(
    tmp_path: Path,
) -> None:
    _require_opcua_native()

    def deny_resume(action: str, endpoint_id: str, _context: dict[str, object]) -> tuple[bool, str]:
        if action == "RESUME_ENDPOINT":
            return False, "resume_denied"
        return True, "ok"

    source = build_opcua_source(77, choose_port(54001, 54200))
    registry, _monitor = build_native_registry(tmp_path, decision_hook=deny_resume)
    fleet = SourceSimulatorFleet.create((source,), update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    try:
        fleet.start()
        assert registry.add_endpoint(subscribe_config(source, interval_ms=200.0)).result == "SUCCESS"
        assert registry.pause_endpoint(source.connection.name).result == "SUCCESS"
        assert registry.resume_endpoint(source.connection.name).result == "DENY"
        assert registry.update_endpoint(source.connection.name, {"host": "127.0.0.2"}, expected_version=99).result == "CONFLICT"
        assert registry.update_endpoint(source.connection.name, {"unsupported": True}, expected_version=1).result == "VALIDATION_ERROR"
        entries = registry._state_store.load_journal_entries()
        results = {entry["result"] for entry in entries}
        assert {"SUCCESS", "DENY", "CONFLICT", "VALIDATION_ERROR"} <= results
    finally:
        shutdown_registry(registry)
        fleet.stop()
