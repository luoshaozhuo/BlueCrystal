"""dynamic runtime state 恢复测试。

验证 state store 在进程重启后的状态恢复能力。
测试阶段：开发期验证 (contract)。
"""
from __future__ import annotations

import random
import socket
import time
from pathlib import Path

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.http_rest_polling import HttpRestPollingRunner
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
        port = rng.randint(56001, 59000)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("no available port")


def _build_http_source(index: int, port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"http-rec-{index}",
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
        ),
    )


def _runtime_spec(source: SimulatedSource) -> SourceRuntimeSpec:
    return SourceRuntimeSpec(
        endpoint=SourceEndpointSpec(
            name=source.connection.name,
            host=source.connection.host,
            port=source.connection.port,
            protocol=source.connection.protocol,
            transport=source.connection.transport,
            params={"http_path": "/points"},
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


def _build_registry(state_dir: Path) -> EndpointRuntimeRegistry:
    monitor = ContinuityMonitor()
    stagger = StaggerCoordinator()
    session_manager = EndpointSessionManager(
        continuity_monitor=monitor,
        stagger_coordinator=stagger,
        polling_runner_factory=lambda _protocol: HttpRestPollingRunner(),
    )
    return EndpointRuntimeRegistry(
        session_manager=session_manager,
        continuity_monitor=monitor,
        stagger_coordinator=stagger,
        state_store=RuntimeStateStore(str(state_dir)),
    )


def _config(source: SimulatedSource) -> EndpointRuntimeConfig:
    spec = _runtime_spec(source)
    return EndpointRuntimeConfig(
        endpoint_id=spec.endpoint.name,
        protocol="http_rest",
        mode=EndpointMode.POLLING,
        source=spec,
        target_hz=5.0,
        read_timeout_s=1.0,
    )


def _shutdown_registry(registry: EndpointRuntimeRegistry) -> None:
    for runtime in registry.list_status():
        if runtime.state.value != "deleted":
            registry.stop_endpoint(runtime.endpoint_id)


def _prepare_registry(state_dir: Path, sources: tuple[SimulatedSource, ...]) -> EndpointRuntimeRegistry:
    registry = _build_registry(state_dir)
    for source in sources:
        assert registry.add_endpoint(_config(source)).result == "SUCCESS"
    time.sleep(0.5)
    assert registry.pause_endpoint(sources[1].connection.name).result == "SUCCESS"
    assert registry.update_endpoint(
        sources[0].connection.name,
        {"points": _runtime_spec(sources[0]).points[:1]},
        expected_version=1,
    ).result == "SUCCESS"
    assert registry.delete_endpoint(sources[2].connection.name).result == "SUCCESS"
    return registry


def test_dynamic_runtime_state_recovery_restores_enabled_endpoints(tmp_path: Path) -> None:
    sources = tuple(_build_http_source(index, _choose_port()) for index in range(3))
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    state_dir = tmp_path / "runtime"
    registry: EndpointRuntimeRegistry | None = None
    recovered_registry: EndpointRuntimeRegistry | None = None
    try:
        fleet.start()
        registry = _prepare_registry(state_dir, sources)
        recovered_registry = _build_registry(state_dir)
        recovered = recovered_registry.recover()
        running_ids = {runtime.endpoint_id for runtime in recovered if runtime.state.value == "running"}
        assert sources[0].connection.name in running_ids
    finally:
        if registry is not None:
            _shutdown_registry(registry)
        if recovered_registry is not None:
            _shutdown_registry(recovered_registry)
        fleet.stop()


def test_dynamic_runtime_state_recovery_keeps_paused_endpoint_paused(tmp_path: Path) -> None:
    sources = tuple(_build_http_source(index, _choose_port()) for index in range(3))
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    state_dir = tmp_path / "runtime"
    registry: EndpointRuntimeRegistry | None = None
    recovered_registry: EndpointRuntimeRegistry | None = None
    try:
        fleet.start()
        registry = _prepare_registry(state_dir, sources)
        recovered_registry = _build_registry(state_dir)
        recovered = recovered_registry.recover()
        paused = {runtime.endpoint_id for runtime in recovered if runtime.state.value == "paused"}
        assert sources[1].connection.name in paused
    finally:
        if registry is not None:
            _shutdown_registry(registry)
        if recovered_registry is not None:
            _shutdown_registry(recovered_registry)
        fleet.stop()


def test_dynamic_runtime_state_recovery_does_not_restore_deleted_endpoint(tmp_path: Path) -> None:
    sources = tuple(_build_http_source(index, _choose_port()) for index in range(3))
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    state_dir = tmp_path / "runtime"
    registry: EndpointRuntimeRegistry | None = None
    recovered_registry: EndpointRuntimeRegistry | None = None
    try:
        fleet.start()
        registry = _prepare_registry(state_dir, sources)
        recovered_registry = _build_registry(state_dir)
        recovered = recovered_registry.recover()
        recovered_ids = {runtime.endpoint_id for runtime in recovered}
        assert sources[2].connection.name not in recovered_ids
    finally:
        if registry is not None:
            _shutdown_registry(registry)
        if recovered_registry is not None:
            _shutdown_registry(recovered_registry)
        fleet.stop()


def test_dynamic_runtime_state_recovery_preserves_config_version(tmp_path: Path) -> None:
    sources = tuple(_build_http_source(index, _choose_port()) for index in range(3))
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    state_dir = tmp_path / "runtime"
    registry: EndpointRuntimeRegistry | None = None
    recovered_registry: EndpointRuntimeRegistry | None = None
    try:
        fleet.start()
        registry = _prepare_registry(state_dir, sources)
        recovered_registry = _build_registry(state_dir)
        recovered = recovered_registry.recover()
        versions = {runtime.endpoint_id: runtime.config_version for runtime in recovered}
        assert versions[sources[0].connection.name] == 2
    finally:
        if registry is not None:
            _shutdown_registry(registry)
        if recovered_registry is not None:
            _shutdown_registry(recovered_registry)
        fleet.stop()


def test_dynamic_runtime_state_recovery_records_recovery_event(tmp_path: Path) -> None:
    sources = tuple(_build_http_source(index, _choose_port()) for index in range(3))
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    state_dir = tmp_path / "runtime"
    base_registry: EndpointRuntimeRegistry | None = None
    registry: EndpointRuntimeRegistry | None = None
    try:
        fleet.start()
        base_registry = _prepare_registry(state_dir, sources)
        registry = _build_registry(state_dir)
        registry.recover()
        entries = registry._state_store.load_journal_entries()
        assert any(entry["action"] == "RECOVER" and entry["result"] == "SUCCESS" for entry in entries)
    finally:
        if base_registry is not None:
            _shutdown_registry(base_registry)
        if registry is not None:
            _shutdown_registry(registry)
        fleet.stop()
