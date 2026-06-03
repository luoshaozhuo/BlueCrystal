"""native runner 隔离测试。

验证不同协议 native runner 之间的进程和资源隔离。
测试阶段：开发期验证 (contract)。
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from tools.source_lab.access.runtime.endpoint_runtime import EndpointRuntimeState
from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import UpdateConfig
from tools.source_lab.tests.access._dynamic_runtime_test_utils import (
    build_native_registry,
    build_opcua_source,
    choose_port,
    polling_config,
    shutdown_registry,
    subscribe_config,
)


def _require_native(build_names: tuple[str, ...]) -> None:
    build_dir = Path(__file__).resolve().parents[2] / "native" / "build"
    missing = [str(build_dir / name) for name in build_names if not (build_dir / name).exists()]
    if missing:
        pytest.skip(
            "dependency_missing: "
            + ",".join(missing)
            + " not compiled. CI hint: cmake -S tools/source_lab/native -B tools/source_lab/native/build && cmake --build tools/source_lab/native/build"
        )


def test_dynamic_native_polling_process_is_endpoint_scoped_when_replacement_required(tmp_path: Path) -> None:
    _require_native(("open62541_client_runner", "open62541_source_simulator"))
    sources = tuple(build_opcua_source(index, choose_port(54201, 54700)) for index in range(3))
    spare = build_opcua_source(98, choose_port(54701, 54900))
    registry, _monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources + (spare,), update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=2.0)).result == "SUCCESS"
        time.sleep(1.4)
        before = {runtime.endpoint_id: runtime.last_started_at for runtime in registry.list_status()}

        assert registry.update_endpoint(
            sources[0].connection.name,
            {"host": "127.0.0.1", "port": spare.connection.port},
            expected_version=1,
        ).result == "SUCCESS"
        time.sleep(0.8)
        after = {runtime.endpoint_id: runtime.last_started_at for runtime in registry.list_status()}

        assert after[sources[0].connection.name] != before[sources[0].connection.name]
        for source in sources[1:]:
            assert after[source.connection.name] == before[source.connection.name]
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_native_subscription_process_is_endpoint_scoped_when_replacement_required(tmp_path: Path) -> None:
    _require_native(("open62541_subscription_runner", "open62541_source_simulator"))
    sources = tuple(build_opcua_source(index, choose_port(54901, 55400)) for index in range(3))
    spare = build_opcua_source(97, choose_port(55401, 55600))
    registry, _monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources + (spare,), update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(subscribe_config(source, interval_ms=200.0)).result == "SUCCESS"
        time.sleep(1.4)
        before = {runtime.endpoint_id: runtime.last_started_at for runtime in registry.list_status()}

        assert registry.update_endpoint(
            sources[0].connection.name,
            {"host": "127.0.0.1", "port": spare.connection.port},
            expected_version=1,
        ).result == "SUCCESS"
        time.sleep(0.8)
        after = {runtime.endpoint_id: runtime.last_started_at for runtime in registry.list_status()}

        assert after[sources[0].connection.name] != before[sources[0].connection.name]
        for source in sources[1:]:
            assert after[source.connection.name] == before[source.connection.name]
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_native_runner_failure_marks_only_target_endpoint_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _require_native(("open62541_client_runner", "open62541_source_simulator"))
    sources = tuple(build_opcua_source(index, choose_port(55601, 56100)) for index in range(3))
    registry, _monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    original = registry._session_manager._run_native_polling_loop
    try:
        fleet.start()

        def fail_target(runtime, *args, **kwargs):
            if runtime.endpoint_id == sources[0].connection.name:
                raise RuntimeError("forced native polling crash")
            return original(runtime, *args, **kwargs)

        monkeypatch.setattr(registry._session_manager, "_run_native_polling_loop", fail_target)
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=2.0)).result == "SUCCESS"
        time.sleep(1.0)

        states = {runtime.endpoint_id: runtime.state for runtime in registry.list_status()}
        assert states[sources[0].connection.name] == EndpointRuntimeState.FAILED
        for source in sources[1:]:
            assert states[source.connection.name] in {EndpointRuntimeState.RUNNING, EndpointRuntimeState.STARTING}
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_native_runner_stop_cleans_only_target_process(tmp_path: Path) -> None:
    _require_native(("open62541_client_runner", "open62541_source_simulator"))
    sources = tuple(build_opcua_source(index, choose_port(56101, 56600)) for index in range(3))
    registry, _monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=2.0)).result == "SUCCESS"
        time.sleep(1.2)
        before = {runtime.endpoint_id: runtime.last_started_at for runtime in registry.list_status()}

        assert registry.stop_endpoint(sources[0].connection.name).result == "SUCCESS"
        time.sleep(0.8)
        runtimes = {runtime.endpoint_id: runtime for runtime in registry.list_status()}

        assert runtimes[sources[0].connection.name].state == EndpointRuntimeState.STOPPED
        for source in sources[1:]:
            assert runtimes[source.connection.name].state in {EndpointRuntimeState.RUNNING, EndpointRuntimeState.STARTING}
            assert runtimes[source.connection.name].last_started_at == before[source.connection.name]
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_native_unaffected_runner_process_ids_stable(tmp_path: Path) -> None:
    _require_native(("open62541_subscription_runner", "open62541_source_simulator"))
    sources = tuple(build_opcua_source(index, choose_port(56601, 57100)) for index in range(3))
    spare = build_opcua_source(96, choose_port(57101, 57300))
    registry, _monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources + (spare,), update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(subscribe_config(source, interval_ms=200.0)).result == "SUCCESS"
        time.sleep(1.4)
        before = {
            runtime.endpoint_id: getattr(runtime.runner_handle, "last_cycle_started_at", None)
            for runtime in registry._runtimes.values()
        }

        assert registry.update_endpoint(
            sources[0].connection.name,
            {"host": "127.0.0.1", "port": spare.connection.port},
            expected_version=1,
        ).result == "SUCCESS"
        time.sleep(0.8)
        after_runtimes = dict(registry._runtimes)

        for source in sources[1:]:
            assert getattr(after_runtimes[source.connection.name].runner_handle, "last_cycle_started_at", None) != before[source.connection.name]
            assert after_runtimes[source.connection.name].config_version == 1
    finally:
        shutdown_registry(registry)
        fleet.stop()
