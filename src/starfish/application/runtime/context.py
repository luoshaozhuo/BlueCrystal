"""Starfish application runtime kernel root。

本模块是 `application.runtime` 的唯一入口对象所在地：`StarfishRuntimeContext`
持有已校验配置、校验结果与运行时 registry 视图。RuntimeRegistry 与
ServerRegistry 只构建和保存 RuntimeGraph 状态，不启动 driver、不解析文件、
不选择具体协议实现。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from starfish.application.ports.driver_factory import DriverFactoryPort
from starfish.application.runtime.event_bus import RuntimeEventBus
from starfish.application.runtime.graph import (
    DriverCapability,
    DriverInstance,
    DriverRuntimeHandle,
    DriverState,
    RuntimeBinding,
    RuntimeGraph,
    RuntimeNode,
    RuntimeSignal,
)
from starfish.domain import (
    DriverEntry,
    StarfishEndpointConfig,
    StarfishServerConfig,
    StarfishServerMemberConfig,
    ValidationResult,
)


def _runtime_binding_id(
    server: StarfishServerMemberConfig,
    endpoint: StarfishEndpointConfig,
    index: int,
) -> str:
    """生成稳定 binding id，避免 endpoint_id 缺失时运行图不可定位。"""
    server_id = server.server_id or server.server_name or "server"
    endpoint_id = endpoint.endpoint_id or endpoint.endpoint_name or f"endpoint_{index}"
    return f"{server_id}:{endpoint_id}"


def _driver_instance_from_entry(
    entry: DriverEntry,
    *,
    binding_id: str,
    version: str,
    event_bus: RuntimeEventBus | None = None,
) -> DriverInstance:
    """将 adapter factory 输出转换为 Runtime v2 DriverInstance。

    Args:
        entry: 由 application port 返回的 driver entry。
        binding_id: RuntimeGraph binding 标识。
        version: 实例版本，用于 hot swap 区分新旧实例。
        event_bus: 可选的 runtime 内部事件总线。

    Returns:
        已初始化到 INITIALIZED 状态的 DriverInstance。
    """
    instance = DriverInstance(
        id=f"{binding_id}:{version}",
        version=version,
        protocol=entry.endpoint.protocol,
        state=DriverState.CREATED,
        driver=entry.driver,
        runtime=DriverRuntimeHandle(
            mode=entry.mode,
            available=entry.available,
            reason=entry.reason,
        ),
        config={
            "server_id": entry.server.server_id,
            "server_name": entry.server.server_name,
            "endpoint": asdict(entry.endpoint),
        },
        capability=DriverCapability(names=list(entry.server.capabilities)),
        event_bus=event_bus,
    )
    instance.initialize()
    return instance


def _driver_entry_from_binding(
    server: StarfishServerMemberConfig,
    binding: RuntimeBinding,
) -> DriverEntry:
    """从 RuntimeGraph binding 生成旧 entries 兼容视图。"""
    instance = binding.driver_instance
    return DriverEntry(
        server=server,
        endpoint=binding.endpoint,
        driver=instance.driver,
        available=instance.runtime.available,
        reason=instance.runtime.reason,
        mode=instance.runtime.mode,
    )


class RuntimeRegistry:
    """RuntimeGraph 构建器。

    只通过 DriverFactoryPort 请求 driver entry，并将结果装入
    nodes[] -> bindings[] -> driver_instance 结构。
    """

    def __init__(
        self,
        driver_factory: DriverFactoryPort,
        *,
        event_bus: RuntimeEventBus | None = None,
    ) -> None:
        """初始化 registry 所需 port。

        Args:
            driver_factory: 由 adapter 实现的 driver factory port。
            event_bus: 可选 runtime event bus；未传入时创建进程内默认实例。
        """
        self._driver_factory = driver_factory
        self._event_bus = event_bus or RuntimeEventBus()

    def build_runtime_graph(self, config: StarfishServerConfig) -> RuntimeGraph:
        """根据已校验配置构建 RuntimeGraph。

        Args:
            config: 已通过加载与校验的 Starfish server 配置。

        Returns:
            nodes[] -> bindings[] -> driver_instance 结构的运行图。
        """
        graph = RuntimeGraph(
            scenario_id=config.scenario_id,
            config_name=config.config_name,
            event_bus=self._event_bus,
        )
        for server in config.servers:
            node_id = server.server_id or server.server_name or f"node_{len(graph.nodes)}"
            node = RuntimeNode(node_id=node_id, server=server)
            for index, endpoint in enumerate(server.endpoints):
                binding_id = _runtime_binding_id(server, endpoint, index)
                entry = self._driver_factory.create_driver_for_endpoint(server, endpoint)
                node.bindings.append(
                    RuntimeBinding(
                        binding_id=binding_id,
                        endpoint=endpoint,
                        driver_instance=_driver_instance_from_entry(
                            entry,
                            binding_id=binding_id,
                            version="v2",
                            event_bus=self._event_bus,
                        ),
                        signals=[
                            RuntimeSignal(
                                signal_id=point.point_id or point.point_name,
                                point=point,
                            )
                            for point in server.points
                        ],
                    )
                )
            graph.nodes.append(node)
        return graph


@dataclass
class ServerRegistry:
    """一份 server 配置对应的 RuntimeGraph 注册表视图。

    本类只保存已构建的 RuntimeGraph、提供 endpoint/entry 到
    node/binding/instance 的解析，以及刷新旧 entries 兼容视图。启动、停止、
    健康检查、读写和 hot swap 旧实例停机均由 application use case 执行。
    """

    config: StarfishServerConfig
    runtime_graph: RuntimeGraph
    event_bus: RuntimeEventBus = field(default_factory=RuntimeEventBus)
    entries: list[DriverEntry] = field(default_factory=list)

    def refresh_entries(self) -> None:
        """从 RuntimeGraph 生成 entries 兼容视图。"""
        self.entries = [
            _driver_entry_from_binding(node.server, binding)
            for node in self.runtime_graph.nodes
            for binding in node.bindings
        ]

    def available_entries(self) -> list[DriverEntry]:
        """返回当前可执行的 DriverEntry 兼容视图。"""
        return [
            entry for entry in self.entries
            if entry.available and entry.driver is not None
        ]

    def resolve_entry(self, endpoint_id: str | None) -> DriverEntry:
        """按 endpoint_id 解析可用 entry。

        Args:
            endpoint_id: endpoint 标识；为 None 时要求当前只有一个可用 endpoint。

        Returns:
            匹配的 DriverEntry。

        Raises:
            ValueError: endpoint 不存在，或未指定 endpoint_id 时存在多个可用 endpoint。
        """
        available_entries = self.available_entries()
        if endpoint_id is None:
            if len(available_entries) != 1:
                raise ValueError("存在多个可用 endpoint，请显式传入 endpoint_id。")
            return available_entries[0]

        for entry in available_entries:
            if entry.endpoint.endpoint_id == endpoint_id:
                return entry
        raise ValueError(f"未找到可用 endpoint: {endpoint_id}")

    def resolve_instance_for_entry(self, entry: DriverEntry) -> DriverInstance:
        """查找 entry 对应的当前 DriverInstance。"""
        return self.resolve_node_binding_for_entry(entry)[1].driver_instance

    def create_driver_instance(
        self,
        entry: DriverEntry,
        *,
        binding_id: str,
        version: str = "v2",
    ) -> DriverInstance:
        """根据 DriverEntry 构建新的 DriverInstance。

        该方法只做结构转换和状态初始化，不启动、停止或调用 driver。
        """
        return _driver_instance_from_entry(
            entry,
            binding_id=binding_id,
            version=version,
            event_bus=self.event_bus,
        )

    def resolve_node_binding_for_entry(
        self,
        entry: DriverEntry,
    ) -> tuple[RuntimeNode, RuntimeBinding]:
        """查找 entry 对应的 node 与 binding。"""
        for node in self.runtime_graph.nodes:
            for binding in node.bindings:
                if binding.endpoint is entry.endpoint:
                    return node, binding
                if (
                    binding.endpoint.endpoint_id
                    and binding.endpoint.endpoint_id == entry.endpoint.endpoint_id
                ):
                    return node, binding
        raise KeyError(f"未找到 endpoint 对应 DriverInstance: {entry.endpoint.endpoint_id}")


def create_server_registry(
    config: StarfishServerConfig,
    driver_factory: DriverFactoryPort,
) -> ServerRegistry:
    """根据配置和 driver factory 创建 Runtime v2 注册表。

    Args:
        config: 已通过校验的 server 配置。
        driver_factory: application port，由 adapter 提供协议选择和 driver 创建。

    Returns:
        已装配所有 endpoint entry 的 ServerRegistry。
    """
    event_bus = RuntimeEventBus()
    runtime_graph = RuntimeRegistry(driver_factory, event_bus=event_bus).build_runtime_graph(config)
    registry = ServerRegistry(
        config=config,
        runtime_graph=runtime_graph,
        event_bus=event_bus,
    )
    registry.refresh_entries()
    return registry


@dataclass(frozen=True)
class StarfishRuntimeContext:
    """runtime 唯一状态容器。

    context 是 API/Façade 与 use case 之间传递 runtime kernel 的唯一对象；
    它不作为外部 DTO 或网络契约暴露，也不携带 driver I/O 实现细节。
    """

    config: StarfishServerConfig
    validation: ValidationResult
    registry: ServerRegistry


__all__ = [
    "RuntimeRegistry",
    "ServerRegistry",
    "StarfishRuntimeContext",
    "create_server_registry",
]
