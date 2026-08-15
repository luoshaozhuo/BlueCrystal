"""
优化后的 ports.py
=================

定义 source 层协议端口接口。
包括可读取、可订阅、可浏览、统一 reader 端口。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Protocol, Self

from pacific.whale.shared.source.models import (
    SourceNodeInfo,
    Batch,
    SubscriptionCallback,
)


class SourceSubscriptionHandlePort(Protocol):
    """协议层订阅句柄端口。"""

    async def close(self) -> None:
        """停止订阅并释放底层资源。"""


class ReadableSourcePort(Protocol):
    """可读取 source 端口。"""

    async def read(
        self,
        addresses: Sequence[str],
        *,
        mode: Literal["full", "value_only"] = "full",
    ) -> Batch:
        """按协议层地址读取一批节点，返回统一 Batch 对象。"""


class SubscribableSourcePort(Protocol):
    """可订阅 source 端口。"""

    async def start_subscription(
        self,
        addresses: Sequence[str],
        *,
        interval_ms: int,
        on_data_change: SubscriptionCallback,
    ) -> SourceSubscriptionHandlePort:
        """按协议层地址启动订阅，回调统一 batch 对象。"""


class BrowsableSourcePort(Protocol):
    """可浏览 source 端口。"""

    async def list_nodes(self) -> tuple[SourceNodeInfo, ...]:
        """列出全部可读变量节点及其元信息。"""

    async def list_readable_variable_nodes(self) -> tuple[tuple[str, str], ...]:
        """列出全部可读变量节点路径及规范化数据类型。"""


class SourceReaderPort(
    ReadableSourcePort,
    SubscribableSourcePort,
    BrowsableSourcePort,
    Protocol,
):
    """通用 source reader 端口。"""

    @property
    def endpoint(self) -> str:
        """返回底层 endpoint。"""

    async def __aenter__(self) -> Self:
        """进入连接态 source session。"""

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        """退出连接态 source session。"""
