"""Modbus RTU backend 基础类型定义。

定义 Protocol 接口和数据载体，供 serial backend 和可能的 native C backend 实现。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RawModbusRtuReadResult:
    """Modbus RTU 原始读取结果（FC03）。

    Attributes:
        ok: 读取是否成功。
        values: 各寄存器的整数值元组，按请求地址顺序排列。
        response_timestamp: 响应时间戳（UTC）。
        error_reason: 失败原因分类（如 timeout、crc_error、protocol_error）。
        exception: 原始异常信息。
    """

    ok: bool
    values: tuple[int, ...]
    response_timestamp: datetime | None = None
    error_reason: str | None = None
    exception: str | None = None


@dataclass(frozen=True, slots=True)
class ModbusRtuPreparedReadPlan:
    """Modbus RTU 预准备读取计划。

    包含寄存器地址列表和 unit_id，
    供 backend.read_prepared 使用。
    """

    reg_addrs: tuple[int, ...]
    unit_id: int = 1


class ModbusRtuClientBackend(Protocol):
    """Modbus RTU 客户端 backend Protocol。

    实现方必须提供异步的串行连接管理、
    prepare_read / read_prepared 读取流程和资源清理。
    """

    async def connect(self) -> None:
        """打开串口连接并配置参数。

        在首次读取或写入前调用。
        实现方必须处理串口打开、参数配置（波特率、
        校验位、停止位、数据位）和连接状态管理。
        """
        ...

    async def disconnect(self) -> None:
        """关闭串口连接并释放资源。

        必须在不再需要连接时调用以释放文件描述符。
        实现方必须处理正常关闭和异常关闭路径。
        """
        ...

    def prepare_read(self, reg_addrs: tuple[int, ...]) -> ModbusRtuPreparedReadPlan:
        """为给定寄存器地址列表准备可复用的读取计划。

        Args:
            reg_addrs: 目标 holding register 地址元组。

        Returns:
            预准备读取计划对象。
        """
        ...

    async def read_prepared(self, plan: ModbusRtuPreparedReadPlan) -> RawModbusRtuReadResult:
        """按预准备计划执行一次 Modbus RTU 读取（FC03）。

        Args:
            plan: 由 prepare_read 创建的读取计划。

        Returns:
            原始读取结果，包含寄存器值或错误信息。
        """
        ...
