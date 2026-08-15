"""Modbus TCP source reader/writer facade."""
from __future__ import annotations

from collections.abc import Sequence

from pacific.whale.shared.source.modbus.backends import (
    ModbusPreparedReadPlan,
    ModbusTcpClientBackend,
    RawModbusReadResult,
    RawWriteItemResult,
)


class ModbusSourceReader:
    """Thin facade over the modbus TCP native backend."""

    def __init__(self, host: str, port: int, unit_id: int = 1) -> None:
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._backend = ModbusTcpClientBackend(host, port, unit_id)

    async def __aenter__(self) -> "ModbusSourceReader":
        await self._backend.connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self._backend.disconnect()

    def prepare_read(self, reg_addrs: Sequence[int]) -> ModbusPreparedReadPlan:
        """Prepare a reusable read plan for register addresses."""
        return self._backend.prepare_read(tuple(reg_addrs))

    async def read_prepared(self, plan: ModbusPreparedReadPlan) -> RawModbusReadResult:
        """Execute one prepared raw read (FC03)."""
        return await self._backend.read_prepared(plan)

    async def read(self, reg_addrs: Sequence[int]) -> RawModbusReadResult:
        """Convenience: prepare + read in one call."""
        plan = self.prepare_read(reg_addrs)
        return await self.read_prepared(plan)

    async def write(
        self,
        reg_addr: int,
        value_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        """Write one holding register value (FC06).

        Args:
            reg_addr: Target holding register address.
            value_type: Type hint (uint16, int16, bool).
            value: String-encoded value.
            request_id: Optional caller-supplied request identifier.
        """
        return await self._backend.write(
            reg_addr=reg_addr,
            value_type=value_type,
            value=value,
            request_id=request_id,
        )
