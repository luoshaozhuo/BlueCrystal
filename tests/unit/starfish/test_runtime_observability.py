"""Runtime observability v1 单元测试。

本文件使用 fake driver/factory 验证 RuntimeEvent、RuntimeState、
RuntimeSnapshot 与非侵入式事件 hook，不启动真实 socket、native runner 或
外部观测系统。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from starfish.api.server_manager_api import StarfishServerManager
from starfish.application import StarfishRuntimeContext
from starfish.application.runtime import RuntimeEvent, RuntimeEventBus, RuntimeSnapshot
from starfish.application.runtime import create_server_registry
from starfish.domain import (
    DriverEntry,
    StarfishEndpointConfig,
    StarfishServerConfig,
    StarfishServerMemberConfig,
    ValidationResult,
)


class FakeDriver:
    """记录调用并返回固定值的 driver 测试替身。"""

    def __init__(self) -> None:
        self.started = 0
        self.stopped = 0
        self.writes: list[tuple[str, Any]] = []

    def start(self) -> None:
        """记录 start 调用。"""
        self.started += 1

    def stop(self) -> None:
        """记录 stop 调用。"""
        self.stopped += 1

    def read(self, point_id: str | list[str] | None = None) -> dict[str, Any]:
        """返回可断言的读取值。"""
        return {"point_id": point_id, "value": 42}

    def write(self, point_id: str, value: Any) -> None:
        """记录写入参数。"""
        self.writes.append((point_id, value))

    def health(self) -> dict[str, Any]:
        """返回固定健康状态。"""
        return {"status": "ok"}


class FailingReadDriver(FakeDriver):
    """read 固定失败的 driver 测试替身。"""

    def read(self, point_id: str | list[str] | None = None) -> dict[str, Any]:
        """抛出稳定错误，验证 ERROR hook。"""
        raise RuntimeError("read boom")


class FakeFactory:
    """为单 endpoint 创建 fake driver entry 的 factory。"""

    def __init__(self, driver: FakeDriver | None = None) -> None:
        self.driver = driver or FakeDriver()

    def create_driver_for_endpoint(
        self,
        server: StarfishServerMemberConfig,
        endpoint: StarfishEndpointConfig,
    ) -> DriverEntry:
        """返回可用 fake DriverEntry。"""
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=self.driver,
            available=True,
            reason="fake",
            mode="fake",
        )


class FailingEventBus:
    """emit/tail 都失败的事件总线替身。"""

    def emit(self, event: RuntimeEvent) -> None:
        """模拟 event storage 异常。"""
        raise RuntimeError("event bus down")

    def tail(self, n: int = 100) -> list[RuntimeEvent]:
        """模拟 snapshot 查询异常。"""
        raise RuntimeError("event bus down")


def _config() -> StarfishServerConfig:
    """构造单 endpoint runtime 配置。"""
    return StarfishServerConfig(
        scenario_id="obs-scenario",
        config_name="obs",
        servers=[
            StarfishServerMemberConfig(
                server_id="node-a",
                server_name="Node A",
                endpoints=[
                    StarfishEndpointConfig(
                        endpoint_id="ep-a",
                        protocol="HTTP_REST",
                        host="127.0.0.1",
                        port=18080,
                    )
                ],
            )
        ],
    )


def _manager(driver: FakeDriver | None = None) -> StarfishServerManager:
    """创建绑定 fake registry 的 StarfishServerManager。"""
    config = _config()
    registry = create_server_registry(config, FakeFactory(driver))
    return StarfishServerManager(
        Path("obs_server_plan.json"),
        context=StarfishRuntimeContext(
            config=config,
            validation=ValidationResult(),
            registry=registry,
        ),
    )


def test_event_bus_tail_returns_recent_events() -> None:
    """RuntimeEventBus 应返回最近 n 条事件。"""
    bus = RuntimeEventBus()
    bus.emit(RuntimeEvent(1.0, "START", "node", "i1", "fake", {}))
    bus.emit(RuntimeEvent(2.0, "STOP", "node", "i1", "fake", {}))

    assert [event.type for event in bus.tail(1)] == ["STOP"]


def test_manager_emits_start_read_write_stop_events_and_snapshot() -> None:
    """API 调用点应发出 START/READ/WRITE/STOP 并能生成 snapshot。"""
    driver = FakeDriver()
    manager = _manager(driver)

    manager.start()
    assert manager.read(endpoint_id="ep-a") == {
        "point_id": None,
        "value": 42,
    }
    manager.write("p1", 7, endpoint_id="ep-a")
    manager.stop()

    event_types = [event.type for event in manager.registry.event_bus.tail()]
    assert event_types == ["START", "READ", "WRITE", "STOP"]
    assert driver.started == 1
    assert driver.stopped == 1
    assert driver.writes == [("p1", 7)]

    snapshot = manager.registry.runtime_graph.snapshot()
    assert isinstance(snapshot, RuntimeSnapshot)
    assert snapshot.graph is manager.registry.runtime_graph
    assert [state.status for state in snapshot.states] == ["STOPPED"]
    assert [event.type for event in snapshot.events_tail] == event_types
    assert manager.registry.runtime_graph.health_summary() == {
        "node_count": 1,
        "running_instances": 0,
        "degraded_instances": 0,
    }


def test_read_error_records_error_event_without_swallowing_exception() -> None:
    """driver 失败时记录 ERROR，原异常仍按原行为抛出。"""
    manager = _manager(FailingReadDriver())

    try:
        manager.read(endpoint_id="ep-a")
    except RuntimeError as exc:
        assert str(exc) == "read boom"
    else:
        raise AssertionError("read should raise")

    snapshot = manager.registry.runtime_graph.snapshot()
    assert [event.type for event in snapshot.events_tail] == ["ERROR"]
    assert snapshot.states[0].last_error == "read boom"
    assert snapshot.states[0].health_score == 0.0


def test_event_emit_failure_is_non_intrusive() -> None:
    """event bus 失败不得影响 DriverInstance 主状态路径。"""
    registry = create_server_registry(_config(), FakeFactory())
    instance = registry.runtime_graph.find_binding("node-a:ep-a").driver_instance
    instance.event_bus = FailingEventBus()
    registry.runtime_graph.event_bus = FailingEventBus()

    instance.emit_runtime_event("START", node_id="node-a")
    snapshot = registry.runtime_graph.snapshot()

    assert snapshot.events_tail == []
