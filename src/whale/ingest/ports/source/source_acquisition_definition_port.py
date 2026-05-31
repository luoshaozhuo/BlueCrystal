"""端口接口定义。

定义调用方契约和实现方责任，相关功能。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from whale.ingest.ports.runtime.source_runtime_config_port import (
    SourceRuntimeConfigData,
)
from whale.ingest.usecases.dtos.source_acquisition_request import AcquisitionItemData
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData


@dataclass(slots=True)
class SourceAcquisitionDefinition:
    """描述一个 source 采集定义。"""

    ld_id: str
    connection: SourceConnectionData
    items: list[AcquisitionItemData]

    request_timeout_ms: int
    poll_interval_ms: int

    polling_max_concurrent_connections: int = 4
    polling_connection_start_interval_ms: int = 0

    subscription_start_interval_ms: int = 0
    subscription_notification_queue_size: int = 1000
    subscription_notification_max_lag_ms: int = 5000


class SourceAcquisitionDefinitionPort(Protocol):
    """从运行时配置加载源采集定义。"""

    def get_config(
        self,
        runtime_config: SourceRuntimeConfigData,
    ) -> SourceAcquisitionDefinition:
        """返回源采集定义。"""
