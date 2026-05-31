"""polling endpoint 动态调整测试。

验证 polling endpoint 在 runtime 的创建、修改和移除行为。
证据等级：L2（contract）。
"""
from __future__ import annotations

import random
import socket
import time
from pathlib import Path

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.http_rest_polling import HttpRestPollingRunner
from tools.source_lab.access.runners.modbus_tcp_polling import ModbusTcpPollingRunner
from tools.source_lab.access.runtime import (
    ContinuityMonitor,
    EndpointMode,
    EndpointRuntimeConfig,
    EndpointRuntimeRegistry,
    EndpointSessionManager,
    RuntimeStateStore,
    StaggerCoordinator,
)
from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection, UpdateConfig


def _choose_port() -> int:
    rng = random.SystemRandom()
    for _ in range(100):
        port = rng.randint(60001, 63000)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("no available port")


def _build_modbus_source(index: int, port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"modbus-dyn-{index}",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="modbus_tcp",
            ied_name="",
            ld_name="",
            namespace_uri=None,
        ),
        points=(
            SimulatedPoint(ln_name="holding", do_name="0", unit=None, data_type="INT32"),
            SimulatedPoint(ln_name="holding", do_name="1", unit=None, data_type="INT32"),
            SimulatedPoint(ln_name="holding", do_name="2", unit=None, data_type="INT32"),
        ),
    )


def _build_http_source(index: int, port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"http-dyn-{index}",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="http_rest",
            ied_name="",
            ld_name="",
            namespace_uri=None,
        ),
        points=(
            SimulatedPoint(ln_name="WPP", do_name="TotW", unit="kW", data_type="FLOAT64"),
            SimulatedPoint(ln_name="WPP", do_name="DevSt", unit=None, data_type="BOOLEAN"),
            SimulatedPoint(ln_name="WPP", do_name="OpCnt", unit=None, data_type="INT32"),
        ),
    )


def _runtime_spec(source: SimulatedSource) -> SourceRuntimeSpec:
    params: dict[str, object] = {}
    if source.connection.protocol == "modbus_tcp":
        params["modbus_start_address"] = 0
    if source.connection.protocol == "http_rest":
        params["http_path"] = "/points"
    return SourceRuntimeSpec(
        endpoint=SourceEndpointSpec(
            name=source.connection.name,
            host=source.connection.host,
            port=source.connection.port,
            protocol=source.connection.protocol,
            transport=source.connection.transport,
            params=params,  # type: ignore[arg-type]
        ),
        points=tuple(
            SourcePointSpec(
                address=point.key,
                name=point.key,
                data_type=point.data_type,
                ln_name=point.ln_name,
                do_name=point.do_name,
                unit=point.unit,
            )
            for point in source.points
        ),
    )


def _build_registry(tmp_path: Path) -> tuple[EndpointRuntimeRegistry, ContinuityMonitor]:
    monitor = ContinuityMonitor()
    stagger = StaggerCoordinator()
    session_manager = EndpointSessionManager(
        continuity_monitor=monitor,
        stagger_coordinator=stagger,
        polling_runner_factory=lambda protocol: (
            ModbusTcpPollingRunner() if protocol == "modbus_tcp" else HttpRestPollingRunner()
        ),
    )
    registry = EndpointRuntimeRegistry(
        session_manager=session_manager,
        continuity_monitor=monitor,
        stagger_coordinator=stagger,
        state_store=RuntimeStateStore(str(tmp_path / "runtime")),
    )
    return registry, monitor


def _polling_config(source: SimulatedSource, *, hz: float = 6.0) -> EndpointRuntimeConfig:
    spec = _runtime_spec(source)
    return EndpointRuntimeConfig(
        endpoint_id=spec.endpoint.name,
        protocol=spec.endpoint.protocol,
        mode=EndpointMode.POLLING,
        source=spec,
        target_hz=hz,
        read_timeout_s=1.0,
    )


def _shutdown_registry(registry: EndpointRuntimeRegistry) -> None:
    for runtime in registry.list_status():
        if runtime.state.value != "deleted":
            registry.stop_endpoint(runtime.endpoint_id)


def test_dynamic_polling_stop_one_modbus_endpoint_keeps_others_running(tmp_path: Path) -> None:
    sources = tuple(_build_modbus_source(index, _choose_port()) for index in range(3))
    registry, monitor = _build_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(_polling_config(source)).result == "SUCCESS"
        time.sleep(0.8)
        before = monitor.snapshot()

        assert registry.stop_endpoint(sources[0].connection.name).result == "SUCCESS"
        time.sleep(0.6)
        after = monitor.snapshot()

        for source in sources[1:]:
            metrics_before = before[source.connection.name]
            metrics_after = after[source.connection.name]
            assert metrics_after.endpoint_actual_samples > metrics_before.endpoint_actual_samples
            assert metrics_after.endpoint_restart_count == metrics_before.endpoint_restart_count
            assert metrics_after.unaffected_endpoint_continuity_breaks == 0
    finally:
        _shutdown_registry(registry)
        fleet.stop()


def test_dynamic_polling_update_one_http_endpoint_points_keeps_others_running(tmp_path: Path) -> None:
    sources = tuple(_build_http_source(index, _choose_port()) for index in range(3))
    registry, monitor = _build_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(_polling_config(source)).result == "SUCCESS"
        time.sleep(0.8)
        before = monitor.snapshot()

        updated_points = _runtime_spec(sources[0]).points[:1]
        result = registry.replace_points(sources[0].connection.name, updated_points, expected_version=1)
        assert result.result == "SUCCESS"
        time.sleep(0.6)
        after = monitor.snapshot()

        for source in sources[1:]:
            metrics_before = before[source.connection.name]
            metrics_after = after[source.connection.name]
            assert metrics_after.endpoint_actual_samples > metrics_before.endpoint_actual_samples
            assert metrics_after.endpoint_restart_count == metrics_before.endpoint_restart_count
            assert metrics_after.unaffected_endpoint_continuity_breaks == 0
    finally:
        _shutdown_registry(registry)
        fleet.stop()


def test_dynamic_polling_stagger_offset_preserved_for_unaffected_endpoints(tmp_path: Path) -> None:
    sources = tuple(_build_modbus_source(index, _choose_port()) for index in range(3))
    registry, monitor = _build_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    try:
        fleet.start()
        for source in sources:
            registry.add_endpoint(_polling_config(source))
        time.sleep(0.5)
        before_offsets = {
            runtime.endpoint_id: runtime.stagger_offset_ns for runtime in registry.list_status()
        }

        result = registry.update_endpoint(
            sources[0].connection.name,
            {"host": "127.0.0.1"},
            expected_version=1,
        )
        assert result.result == "SUCCESS"
        after_offsets = {
            runtime.endpoint_id: runtime.stagger_offset_ns for runtime in registry.list_status()
        }
        snapshot = monitor.snapshot()

        for source in sources[1:]:
            assert after_offsets[source.connection.name] == before_offsets[source.connection.name]
            assert snapshot[source.connection.name].stagger_offset_changed is False
    finally:
        _shutdown_registry(registry)
        fleet.stop()


def test_dynamic_polling_continuity_metrics_for_unaffected_endpoint(tmp_path: Path) -> None:
    sources = tuple(_build_http_source(index, _choose_port()) for index in range(3))
    registry, monitor = _build_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    try:
        fleet.start()
        for source in sources:
            registry.add_endpoint(_polling_config(source, hz=8.0))
        time.sleep(0.8)
        registry.stop_endpoint(sources[0].connection.name)
        time.sleep(0.5)
        metrics = monitor.snapshot()[sources[1].connection.name]

        assert metrics.unaffected_endpoint_samples > 0
        assert metrics.unaffected_endpoint_continuity_breaks == 0
        assert metrics.endpoint_missed_tick_count == 0
    finally:
        _shutdown_registry(registry)
        fleet.stop()
