"""Runtime v2.2 运行图与实例化契约测试。

本文件验证 application registry 与 domain RuntimeGraph 的本地契约：
使用 fake driver/factory，不启动真实 socket、native runner 或 subprocess，
因此不能证明真实协议 I/O 可用。
"""

from __future__ import annotations

from typing import Any

import pytest

from starfish.application.ports import DriverPort, RegistryPort
from starfish.application.orchestration.registry import RuntimeRegistry, create_server_registry
from starfish.application.use_cases import (
    HotSwapDriverInstanceUseCase,
    StartSystemUseCase,
    StopSystemUseCase,
)
from starfish.application.runtime import DriverState
from starfish.domain import (
    DriverEntry,
    StarfishEndpointConfig,
    StarfishPointConfig,
    StarfishServerConfig,
    StarfishServerMemberConfig,
)


class FakeDriver:
    """记录 start/stop 调用的 DriverPort 测试替身。"""

    def __init__(self) -> None:
        self.started = 0
        self.stopped = 0

    def start(self) -> None:
        """记录启动调用。"""
        self.started += 1

    def stop(self) -> None:
        """记录停止调用。"""
        self.stopped += 1

    def read(self, point_id: str | list[str] | None = None) -> dict[str, Any]:
        """返回调用参数，便于验证旧 list 调用仍兼容。"""
        return {"point_id": point_id}

    def write(self, point_id: str, value: Any) -> None:
        """fake driver 不持久化写入值。"""

    def health(self) -> dict[str, Any]:
        """返回固定健康状态。"""
        return {"status": "ok"}


class FakeFactory:
    """为每个 endpoint 创建独立 fake driver 的 factory port 替身。"""

    def __init__(self) -> None:
        self.created: list[DriverEntry] = []

    def create_driver_for_endpoint(
        self,
        server: StarfishServerMemberConfig,
        endpoint: StarfishEndpointConfig,
    ) -> DriverEntry:
        """返回可用 fake DriverEntry。"""
        entry = DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=FakeDriver(),
            available=True,
            reason=f"protocol={endpoint.protocol} -> fake",
            mode="fake",
        )
        self.created.append(entry)
        return entry


def _config() -> StarfishServerConfig:
    """构造含两个 endpoint 的最小运行配置。"""
    return StarfishServerConfig(
        scenario_id="scenario-runtime-v2",
        config_name="runtime-v2",
        servers=[
            StarfishServerMemberConfig(
                server_id="server-a",
                server_name="Server A",
                endpoints=[
                    StarfishEndpointConfig(
                        endpoint_id="http",
                        protocol="HTTP_REST",
                        host="127.0.0.1",
                        port=18080,
                    ),
                    StarfishEndpointConfig(
                        endpoint_id="mqtt",
                        protocol="MQTT",
                        host="127.0.0.1",
                        port=1883,
                    ),
                ],
                points=[
                    StarfishPointConfig(point_id="temperature", point_name="Temperature")
                ],
                capabilities=["read", "write"],
            )
        ],
    )


def test_registry_builder_builds_runtime_graph_with_driver_instances() -> None:
    """RuntimeRegistry 应构建 nodes[] -> bindings[] -> driver_instance。"""
    registry: RegistryPort = RuntimeRegistry(FakeFactory())

    graph = registry.build_runtime_graph(_config())

    assert graph.scenario_id == "scenario-runtime-v2"
    assert len(graph.nodes) == 1
    assert graph.nodes[0].node_id == "server-a"
    assert [binding.binding_id for binding in graph.nodes[0].bindings] == [
        "server-a:http",
        "server-a:mqtt",
    ]
    instances = [binding.driver_instance for binding in graph.nodes[0].bindings]
    assert [instance.protocol for instance in instances] == ["HTTP_REST", "MQTT"]
    assert {instance.state for instance in instances} == {DriverState.INITIALIZED}
    assert [instance.runtime.mode for instance in instances] == ["fake", "fake"]
    assert instances[0].capability.names == ["read", "write"]
    assert graph.nodes[0].bindings[0].signals[0].signal_id == "temperature"


def test_usecases_keep_entries_compatible_and_track_lifecycle() -> None:
    """启动/停止 usecase 保持旧 entries 兼容视图并同步实例生命周期。"""
    registry = create_server_registry(_config(), FakeFactory())
    entry = registry.entries[0]
    instance = registry.runtime_graph.find_binding("server-a:http").driver_instance

    started_entries = StartSystemUseCase().execute(registry)

    assert started_entries == registry.entries
    assert entry.driver.started == 1
    assert instance.state == DriverState.RUNNING

    StopSystemUseCase().execute(registry, started_entries)

    assert entry.driver.stopped == 1
    assert instance.state == DriverState.STOPPED


def test_hot_swap_rebinds_instance_stops_old_and_marks_retired() -> None:
    """hot swap 只替换 binding 的 DriverInstance，不 reload 代码。"""
    registry = create_server_registry(_config(), FakeFactory())
    StartSystemUseCase().execute(registry)
    old_instance = registry.runtime_graph.find_binding("server-a:http").driver_instance
    new_entry = DriverEntry(
        server=registry.config.servers[0],
        endpoint=registry.config.servers[0].endpoints[0],
        driver=FakeDriver(),
        available=True,
        reason="protocol=HTTP_REST -> fake v3",
        mode="fake-v3",
    )

    new_instance = HotSwapDriverInstanceUseCase().execute(
        registry,
        "server-a:http",
        new_entry,
        version="v3",
    )

    rebound = registry.runtime_graph.find_binding("server-a:http").driver_instance
    assert rebound is new_instance
    assert new_instance.version == "v3"
    assert new_instance.state == DriverState.INITIALIZED
    assert old_instance.state == DriverState.RETIRED
    assert old_instance.driver.stopped == 1
    assert registry.entries[0].driver is new_entry.driver
    assert registry.entries[0].mode == "fake-v3"


def test_driver_port_surface_is_runtime_v2_only() -> None:
    """DriverPort 只暴露 Runtime v2 五个统一操作。"""
    expected = {"start", "stop", "read", "write", "health"}
    actual = {
        name
        for name, value in DriverPort.__dict__.items()
        if callable(value) and not name.startswith("_")
    }

    assert actual == expected
    assert isinstance(FakeDriver(), DriverPort)


def test_driver_instance_rejects_invalid_state_transition() -> None:
    """DriverInstance 状态机拒绝未声明的跳转。"""
    graph = RuntimeRegistry(FakeFactory()).build_runtime_graph(_config())
    instance = graph.find_binding("server-a:http").driver_instance

    with pytest.raises(ValueError, match="非法 DriverInstance 状态迁移"):
        instance.mark_retired()
