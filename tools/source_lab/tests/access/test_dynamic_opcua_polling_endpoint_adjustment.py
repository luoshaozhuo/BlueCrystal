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
    polling_config,
    runtime_spec,
    shutdown_registry,
)


def _require_opcua_native() -> None:
    build_dir = Path(__file__).resolve().parents[2] / "native" / "build"
    missing = [
        str(path)
        for path in (
            build_dir / "open62541_client_runner",
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


def test_dynamic_opcua_polling_stop_one_endpoint_keeps_others_running(tmp_path: Path) -> None:
    _require_opcua_native()
    sources = tuple(build_opcua_source(index, choose_port(48101, 48600)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=2.0)).result == "SUCCESS"
        time.sleep(1.6)
        before = monitor.snapshot()

        assert registry.stop_endpoint(sources[0].connection.name).result == "SUCCESS"
        time.sleep(1.0)
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_actual_samples > before[source.connection.name].endpoint_actual_samples
            assert after[source.connection.name].endpoint_restart_count == before[source.connection.name].endpoint_restart_count
            assert after[source.connection.name].stagger_offset_changed is False
            assert after[source.connection.name].unaffected_endpoint_continuity_breaks == 0
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_opcua_polling_replace_points_keeps_others_running(tmp_path: Path) -> None:
    _require_opcua_native()
    sources = tuple(build_opcua_source(index, choose_port(48601, 49100)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=2.0)).result == "SUCCESS"
        time.sleep(1.6)
        before = monitor.snapshot()

        updated_points = runtime_spec(sources[0]).points[:1]
        assert registry.replace_points(sources[0].connection.name, updated_points, expected_version=1).result == "SUCCESS"
        time.sleep(1.0)
        after = monitor.snapshot()

        assert after[sources[0].connection.name].endpoint_config_version == 2
        for source in sources[1:]:
            assert after[source.connection.name].endpoint_actual_samples > before[source.connection.name].endpoint_actual_samples
            assert after[source.connection.name].endpoint_restart_count == before[source.connection.name].endpoint_restart_count
            assert after[source.connection.name].endpoint_config_version == before[source.connection.name].endpoint_config_version
            assert after[source.connection.name].unaffected_endpoint_continuity_breaks == 0
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_opcua_polling_patch_host_port_replaces_only_target_endpoint(tmp_path: Path) -> None:
    _require_opcua_native()
    sources = tuple(build_opcua_source(index, choose_port(49101, 49600)) for index in range(3))
    spare = build_opcua_source(99, choose_port(49601, 49800))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources + (spare,), update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=2.0)).result == "SUCCESS"
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


def test_dynamic_opcua_polling_replacement_failure_does_not_restart_unaffected_endpoints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_opcua_native()
    sources = tuple(build_opcua_source(index, choose_port(49801, 50300)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    original_start = registry._session_manager.start_endpoint
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=2.0)).result == "SUCCESS"
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
        result = registry.update_endpoint(sources[0].connection.name, {"host": "127.0.0.2"}, expected_version=1)
        assert result.result == "ROLLBACK"
        time.sleep(0.8)
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_restart_count == before[source.connection.name].endpoint_restart_count
            assert after[source.connection.name].endpoint_actual_samples > before[source.connection.name].endpoint_actual_samples
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_opcua_polling_stagger_offset_preserved_for_unaffected_endpoints(tmp_path: Path) -> None:
    _require_opcua_native()
    sources = tuple(build_opcua_source(index, choose_port(50301, 50800)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=2.0)).result == "SUCCESS"
        time.sleep(1.2)
        before_offsets = {runtime.endpoint_id: runtime.stagger_offset_ns for runtime in registry.list_status()}
        assert registry.update_endpoint(sources[0].connection.name, {"host": "127.0.0.1"}, expected_version=1).result == "SUCCESS"
        time.sleep(0.8)
        after_offsets = {runtime.endpoint_id: runtime.stagger_offset_ns for runtime in registry.list_status()}
        snapshot = monitor.snapshot()

        for source in sources[1:]:
            assert after_offsets[source.connection.name] == before_offsets[source.connection.name]
            assert snapshot[source.connection.name].stagger_offset_changed is False
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_opcua_polling_continuity_metrics_for_unaffected_endpoints(tmp_path: Path) -> None:
    _require_opcua_native()
    sources = tuple(build_opcua_source(index, choose_port(50801, 51300)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=3.0)).result == "SUCCESS"
        time.sleep(1.6)
        assert registry.stop_endpoint(sources[0].connection.name).result == "SUCCESS"
        time.sleep(0.8)
        metrics = monitor.snapshot()[sources[1].connection.name]

        assert metrics.unaffected_endpoint_samples > 0
        assert metrics.unaffected_endpoint_continuity_breaks == 0
        assert metrics.endpoint_missed_tick_count == 0
    finally:
        shutdown_registry(registry)
        fleet.stop()
