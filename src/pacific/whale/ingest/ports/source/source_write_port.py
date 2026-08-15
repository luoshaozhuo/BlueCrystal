"""Source write/control port for ingest.

定义 ingest 对 source 写入 / 控制能力的抽象需求。
独立于 SourceAcquisitionPort，不混入采集读路径。
"""

from __future__ import annotations

from typing import Protocol

from pacific.whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from pacific.whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
)
from pacific.whale.ingest.usecases.dtos.source_write_result import SourceWriteResult


class SourceWritePort(Protocol):
    """生产设备写入 / 控制命令的抽象端口。

    职责：
    - 接收写入请求（执行选项 + 连接 + 点位列表）。
    - 通过具体协议 adapter 执行写入。
    - 返回每个点位的结构化结果。
    - 不依赖 source_lab。
    - 不依赖 cache 或 Kafka。
    """

    async def write(
        self,
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
    ) -> SourceWriteResult:
        """对指定 connection 执行一次设备写入。

        Args:
            execution: 写入执行选项，含 dry_run、超时等。
            connection: 目标 source 连接。
            items: 待写入点位列表。

        Returns:
            结构化写入结果，含 per-item 状态。
        """
