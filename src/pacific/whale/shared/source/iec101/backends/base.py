"""IEC 101 backend 基础类型定义。

定义 Protocol 接口和数据载体，供 serial backend 和可能的
native C backend 实现。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RawIec101ReadResult:
    """IEC 101 原始 interrogation（总召唤）读取结果。

    Attributes:
        ok: 读取是否成功。
        values: IOA -> (type_tag, value_str) 映射。
            type_tag 为 IEC 101 类型标识（如 M_ME_NC_1）。
        response_timestamp: 响应时间戳（UTC）。
        error_reason: 失败原因分类（如 timeout、protocol_error）。
        exception: 原始异常信息。
    """

    ok: bool
    values: dict[int, tuple[str, str]]
    """IOA -> (type_tag, value_str) 映射。"""
    response_timestamp: datetime | None = None
    error_reason: str | None = None
    exception: str | None = None


@dataclass(frozen=True, slots=True)
class Iec101PreparedReadPlan:
    """IEC 101 预准备读取计划。

    包含 IOA 列表、link_address 和 common_address。
    """

    ioa_list: tuple[int, ...]
    link_address: int = 1
    common_address: int = 1


class Iec101ClientBackend(Protocol):
    """IEC 101 客户端 backend Protocol。

    实现方必须提供异步的串行连接管理、
    interrogation 读取流程和资源清理。

    IEC 101 通过串行链路进行通信，
    支持 interrogation（C_IC_NA_1 总召唤）和
    spontaneous 数据上报。
    """

    async def connect(self) -> None:
        """打开串口连接并配置参数。

        在首次读取前调用。
        实现方必须处理串口打开、参数配置和连接状态管理。
        """
        ...

    async def disconnect(self) -> None:
        """关闭串口连接并释放资源。

        必须在不再需要连接时调用以释放文件描述符。
        """
        ...

    async def read(self, ioa_list: tuple[int, ...]) -> RawIec101ReadResult:
        """执行一次 IEC 101 interrogation（总召唤）读取。

        发送 C_IC_NA_1 激活命令，
        收集返回的 ASDU 数据，
        发送 C_IC_NA_1 停止命令。

        Args:
            ioa_list: 目标信息对象地址列表。

        Returns:
            原始读取结果，包含 IOA -> (type_tag, value) 映射。
        """
        ...
