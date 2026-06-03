"""多协议采集端口调度适配器。

根据 ``execution.protocol`` 从 ``SourceAcquisitionPortRegistry`` 解析对应的采集适配器，
将 read/start_subscription/supports_subscription 调用委托给正确的协议适配器。

本适配器是 composition root 中多协议采集链的关键组件，
使得 build_source_acquisition_composition 不再硬编码单一 OPC UA adapter，
而是在运行时根据请求协议动态选择 IEC104/OPC UA/Modbus/IEC61850/MQTT/HTTP REST 等适配器。

职责边界：
- 只负责协议解析和适配器委托，不负责采集逻辑本身；
- 不负责缓存、重试、授权、审计、日志——这些由上层 decorator 链处理；
- 不负责 protocol key 标准化细节，委托给 registry。

资源生命周期：无状态，不持有连接或子进程。
"""

from __future__ import annotations

from whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionPort,
    SubscriptionStateHandler,
    SourceSubscriptionHandle,
)
from whale.ingest.ports.source.source_acquisition_port_registry import (
    SourceAcquisitionPortRegistry,
)
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData


class DispatchSourceAcquisitionAdapter(SourceAcquisitionPort):
    """根据请求协议动态分发到对应采集适配器。

    持有 SourceAcquisitionPortRegistry，每次 read/start_subscription 调用时
    根据 execution.protocol 查找对应的协议适配器并委托。

    Args:
        registry: 按协议注册的采集端口注册表。

    Raises:
        ValueError: 当 protocol 未在 registry 中注册时。
    """

    def __init__(self, registry: SourceAcquisitionPortRegistry) -> None:
        self._registry = registry

    def _resolve_adapter(self, protocol: str) -> SourceAcquisitionPort:
        """根据协议名解析对应的采集端口适配器。

        Args:
            protocol: 采集请求中的协议名。

        Returns:
            注册的 SourceAcquisitionPort 实现。

        Raises:
            ValueError: 当 protocol 未注册时。
        """
        return self._registry.get(protocol)

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """查询目标协议适配器是否支持订阅模式。

        将调用委托给 protocol 对应的适配器。
        """
        adapter = self._resolve_adapter(execution.protocol)
        return adapter.supports_subscription(execution, connection)

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """执行一次协议特定的批量读取。

        根据 execution.protocol 解析对应的协议适配器并委托 read 调用。
        """
        adapter = self._resolve_adapter(execution.protocol)
        return await adapter.read(execution, connection, items)

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        """启动协议特定的订阅采集。

        根据 execution.protocol 解析对应的协议适配器并委托 start_subscription 调用。
        """
        adapter = self._resolve_adapter(execution.protocol)
        return await adapter.start_subscription(
            execution, connection, items, state_received=state_received,
        )
