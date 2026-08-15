"""IEC 101 source reader facade。

薄封装层，将 backend 的 Protocol 接口暴露为
同步构造 + 异步上下文管理器，供 ingest adapter 使用。
"""
from __future__ import annotations

from collections.abc import Sequence

from pacific.whale.shared.source.iec101.backends import (
    Iec101SerialBackend,
    RawIec101ReadResult,
)


class Iec101SourceReader:
    """IEC 101 串行读取器的薄封装 facade。

    封装 Iec101SerialBackend 的构造、连接管理和 interrogation 读取操作，
    提供统一的 async context manager 接口。

    Args:
        serial_port: 串口设备路径。
        baudrate: 波特率（默认 9600）。
        parity: 校验位（'E' 为 IEC101 标准，默认 'E'）。
        stop_bits: 停止位（默认 1）。
        data_bits: 数据位（默认 8）。
        link_address: 链路地址（默认 1）。
        common_address: ASDU 公共地址（默认 1）。
        timeout: 读取超时秒数（默认 10.0）。
    """

    def __init__(
        self,
        serial_port: str,
        baudrate: int = 9600,
        parity: str = "E",
        stop_bits: int = 1,
        data_bits: int = 8,
        link_address: int = 1,
        common_address: int = 1,
        timeout: float = 10.0,
    ) -> None:
        self._serial_port = serial_port
        self._baudrate = baudrate
        self._parity = parity
        self._stop_bits = stop_bits
        self._data_bits = data_bits
        self._link_address = link_address
        self._common_address = common_address
        self._timeout = timeout
        self._backend = Iec101SerialBackend(
            serial_port=serial_port,
            baudrate=baudrate,
            parity=parity,
            stop_bits=stop_bits,
            data_bits=data_bits,
            link_address=link_address,
            common_address=common_address,
            timeout=timeout,
        )

    async def __aenter__(self) -> "Iec101SourceReader":
        await self._backend.connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self._backend.disconnect()

    async def read(self, ioa_list: Sequence[int]) -> RawIec101ReadResult:
        """执行一次 IEC 101 interrogation（总召唤）读取。

        Args:
            ioa_list: 目标 IOA 列表。

        Returns:
            原始读取结果，包含 IOA -> (type_tag, value_str) 映射。
        """
        return await self._backend.read(tuple(ioa_list))
