"""subscription endpoint 动态调整测试。

验证 subscription endpoint 在 runtime 的创建、修改和移除行为。
测试阶段：开发期验证 (contract)。
"""
from __future__ import annotations

import random
import socket
import time
from pathlib import Path

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.mqtt_subscription import MqttSubscriptionRunner
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
        port = rng.randint(64501, 65480)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("no available port")


def _build_mqtt_source(index: int, port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"mqtt-dyn-{index}",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="mqtt",
            ied_name="",
            ld_name="",
            namespace_uri=None,
        ),
        points=(SimulatedPoint(ln_name="mqtt", do_name="payload", unit=None, data_type="INT32"),),
    )


def _runtime_spec(source: SimulatedSource, topic: str) -> SourceRuntimeSpec:
    return SourceRuntimeSpec(
        endpoint=SourceEndpointSpec(
            name=source.connection.name,
            host=source.connection.host,
            port=source.connection.port,
            protocol=source.connection.protocol,
            transport=source.connection.transport,
            params={"mqtt_topic": topic, "mqtt_client_id": f"client-{source.connection.name}"},
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
        subscription_runner_factory=lambda _protocol: MqttSubscriptionRunner(),
    )
    registry = EndpointRuntimeRegistry(
        session_manager=session_manager,
        continuity_monitor=monitor,
        stagger_coordinator=stagger,
        state_store=RuntimeStateStore(str(tmp_path / "runtime")),
    )
    return registry, monitor


def _subscribe_config(source: SimulatedSource, topic: str) -> EndpointRuntimeConfig:
    spec = _runtime_spec(source, topic)
    return EndpointRuntimeConfig(
        endpoint_id=spec.endpoint.name,
        protocol="mqtt",
        mode=EndpointMode.SUBSCRIBE,
        source=spec,
        publishing_interval_ms=120.0,
        read_timeout_s=1.0,
    )


def _shutdown_registry(registry: EndpointRuntimeRegistry) -> None:
    for runtime in registry.list_status():
        if runtime.state.value != "deleted":
            registry.stop_endpoint(runtime.endpoint_id)


def test_dynamic_mqtt_pause_one_topic_keeps_others_receiving(tmp_path: Path) -> None:
    sources = tuple(_build_mqtt_source(index, _choose_port()) for index in range(3))
    registry, monitor = _build_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    try:
        fleet.start()
        for index, source in enumerate(sources):
            assert registry.add_endpoint(_subscribe_config(source, f"topic/{index}")).result == "SUCCESS"
        time.sleep(0.8)
        before = monitor.snapshot()

        assert registry.pause_endpoint(sources[0].connection.name).result == "SUCCESS"
        time.sleep(0.5)
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_actual_samples > before[source.connection.name].endpoint_actual_samples
            assert after[source.connection.name].endpoint_restart_count == before[source.connection.name].endpoint_restart_count
    finally:
        _shutdown_registry(registry)
        fleet.stop()


def test_dynamic_mqtt_replace_one_topic_keeps_others_receiving(tmp_path: Path) -> None:
    sources = tuple(_build_mqtt_source(index, _choose_port()) for index in range(3))
    registry, monitor = _build_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    try:
        fleet.start()
        for index, source in enumerate(sources):
            registry.add_endpoint(_subscribe_config(source, f"topic/{index}"))
        time.sleep(0.8)
        before = monitor.snapshot()

        result = registry.update_endpoint(
            sources[0].connection.name,
            {
                "params": {
                    "mqtt_topic": "topic/replaced",
                    "mqtt_client_id": "client-replaced",
                }
            },
            expected_version=1,
        )
        assert result.result == "SUCCESS"
        time.sleep(0.5)
        after = monitor.snapshot()

        for source in sources[1:]:
            assert after[source.connection.name].endpoint_actual_samples > before[source.connection.name].endpoint_actual_samples
            assert after[source.connection.name].unaffected_endpoint_continuity_breaks == 0
    finally:
        _shutdown_registry(registry)
        fleet.stop()


class _FailingSessionManager:
    """测试用 EndpointSessionManager stub。

    start_endpoint 故意抛出异常以模拟启动失败。
    不继承 EndpointSessionManager（构造函数签名不同），
    传入 EndpointRuntimeRegistry 时需 type: ignore。
    """

    def start_endpoint(self, runtime: object, config: object) -> None:
        raise RuntimeError("intentional failure")

    def pause_endpoint(self, runtime: object) -> None:
        return None

    def resume_endpoint(self, runtime: object) -> None:
        return None

    def stop_endpoint(self, runtime: object) -> None:
        return None

    def replace_endpoint(self, runtime: object, config: object) -> None:
        raise RuntimeError("intentional failure")


def test_dynamic_subscription_journal_records_allow_deny_success_failed(tmp_path: Path) -> None:
    source = _build_mqtt_source(1, _choose_port())
    registry, _monitor = _build_registry(tmp_path)
    fleet = SourceSimulatorFleet.create((source,), update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    try:
        fleet.start()
        assert registry.add_endpoint(_subscribe_config(source, "topic/ok")).result == "SUCCESS"
        assert registry.pause_endpoint(source.connection.name).result == "SUCCESS"
        assert registry.pause_endpoint(source.connection.name).result == "DENY"

        # _FailingSessionManager 为测试 stub，仅用于模拟启动失败，
        # 不继承 EndpointSessionManager。
        failing_registry = EndpointRuntimeRegistry(
            session_manager=_FailingSessionManager(),  # type: ignore[arg-type]
            continuity_monitor=ContinuityMonitor(),
            stagger_coordinator=StaggerCoordinator(),
            state_store=RuntimeStateStore(str(tmp_path / "failed-runtime")),
        )
        failed = failing_registry.add_endpoint(_subscribe_config(source, "topic/fail"))
        assert failed.result == "FAILED"

        entries = registry._state_store.load_journal_entries() + failing_registry._state_store.load_journal_entries()
        results = {entry["result"] for entry in entries}
        assert "SUCCESS" in results
        assert "DENY" in results
        assert "FAILED" in results
    finally:
        _shutdown_registry(registry)
        fleet.stop()
