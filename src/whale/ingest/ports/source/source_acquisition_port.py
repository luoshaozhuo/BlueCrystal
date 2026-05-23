"""source 采集端口定义。

本模块定义 usecase / role 依赖的数据源采集能力接口。

设计约定：
- SourceAcquisitionPort 只表达 source 采集能力，不关心缓存、不关心调度；
- read() 表示对一个 connection 执行一次完整读取，返回一个 batch；
- start_subscription() 表示启动订阅，后续通过 batch callback 返回变化批次；
- batch 是同一个 source/LD 的状态更新单元；
- 订阅模式下的 initial read baseline 由 SubscriptionAcquisitionRole 编排，不放在 port 内。
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData


SubscriptionStateHandler = Callable[[AcquiredNodeStateBatch], Awaitable[None]]


class SourceAcquisitionError(RuntimeError):
    """source 采集错误基类。"""


class SourceReadError(SourceAcquisitionError):
    """一次 source read 失败。"""


class SourceReadTimeoutError(SourceReadError):
    """一次 source read 因超时失败。"""


class SourceBatchMismatchError(SourceReadError):
    """一次 source read 返回值数量与请求点位数量不匹配。"""


class SourceReadOnceFailedError(SourceReadError):
    """read-once 模式下全部连接读取失败。"""


class SourceSubscriptionUnsupportedError(SourceAcquisitionError):
    """当前 source reader 不支持订阅采集。"""


class SourceSubscriptionHandle(Protocol):
    """协议层订阅句柄。"""

    async def close(self) -> None:
        """停止订阅并释放底层资源。"""


class SourceAcquisitionPort(Protocol):
    """source 状态采集端口。"""

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """返回当前 connection 是否支持订阅采集。"""

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """对一个 connection 执行一次完整读取。

        返回值是一个 batch，表示同一个 source/LD 在本次读取中的完整状态样本。
        """

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        """启动订阅并立即返回订阅句柄。

        订阅产生的数据变化以 AcquiredNodeStateBatch 形式回调给 state_received。
        """
