"""Modbus RTU source reader facade。

薄封装层，将 backend 的 Protocol 接口暴露为
同步构造 + 异步上下文管理器，供 ingest adapter 使用。
"""
from __future__ import annotations

from collections.abc import Sequence

from pacific.whale.shared.source.modbus_rtu.backends import (
    ModbusRtuPreparedReadPlan,
    ModbusRtuSerialBackend,
    RawModbusRtuReadResult,
)


class ModbusRtuSourceReader:
    """Modbus RTU 串行读取器的薄封装 facade。

    封装 ModbusRtuSerialBackend 的构造、连接管理和读取操作，
    提供统一的 async context manager 接口。

    Args:
        serial_port: 串口设备路径。
        baudrate: 波特率（默认 9600）。
        parity: 校验位 ('N'/'E'/'O'，默认 'N')。
        stop_bits: 停止位（1 或 2，默认 1）。
        data_bits: 数据位（7 或 8，默认 8）。
        unit_id: Modbus 从站地址（默认 1）。
        timeout: 读取超时秒数（默认 5.0）。
    """

    def __init__(
        self,
        serial_port: str,
        baudrate: int = 9600,
        parity: str = "N",
        stop_bits: int = 1,
        data_bits: int = 8,
        unit_id: int = 1,
        timeout: float = 5.0,
    ) -> None:
        self._serial_port = serial_port
        self._baudrate = baudrate
        self._parity = parity
        self._stop_bits = stop_bits
        self._data_bits = data_bits
        self._unit_id = unit_id
        self._timeout = timeout
        self._backend = ModbusRtuSerialBackend(
            serial_port=serial_port,
            baudrate=baudrate,
            parity=parity,
            stop_bits=stop_bits,
            data_bits=data_bits,
            unit_id=unit_id,
            timeout=timeout,
        )

    async def __aenter__(self) -> "ModbusRtuSourceReader":
        await self._backend.connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self._backend.disconnect()

    def prepare_read(self, reg_addrs: Sequence[int]) -> ModbusRtuPreparedReadPlan:
        """为给定寄存器地址列表准备读取计划。

        Args:
            reg_addrs: 寄存器地址序列。

        Returns:
            预准备读取计划。
        """
        return self._backend.prepare_read(tuple(reg_addrs))

    async def read_prepared(
        self, plan: ModbusRtuPreparedReadPlan
    ) -> RawModbusRtuReadResult:
        """按预准备计划执行一次 FC03 读取。

        Args:
            plan: 由 prepare_read 创建的读取计划。

        Returns:
            原始读取结果。
        """
        return await self._backend.read_prepared(plan)

    async def read(self, reg_addrs: Sequence[int]) -> RawModbusRtuReadResult:
        """便捷方法：prepare + read 一步完成。

        Args:
            reg_addrs: 寄存器地址序列。

        Returns:
            原始读取结果。
        """
        plan = self.prepare_read(reg_addrs)
        return await self.read_prepared(plan)
