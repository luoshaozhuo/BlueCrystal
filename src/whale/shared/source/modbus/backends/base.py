"""Modbus TCP backend base types."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RawModbusReadResult:
    """Raw Modbus TCP read result (FC03)."""

    ok: bool
    values: tuple[int, ...]
    response_timestamp: datetime | None = None
    error_reason: str | None = None
    exception: str | None = None


@dataclass(frozen=True, slots=True)
class RawWriteItemResult:
    """Result of writing one Modbus register value."""

    reg_addr: int
    ok: bool
    status_code: str | None
    error_message: str | None


@dataclass(frozen=True, slots=True)
class ModbusPreparedReadPlan:
    """Modbus-specific prepared read plan."""

    reg_addrs: tuple[int, ...]
    unit_id: int = 1


class ModbusClientBackend(Protocol):
    """Protocol for Modbus TCP client backend."""

    async def connect(self) -> None:
        """Open backend connection."""

    async def disconnect(self) -> None:
        """Close backend connection."""

    def prepare_read(self, reg_addrs: tuple[int, ...]) -> ModbusPreparedReadPlan:
        """Prepare a reusable read plan for register addresses."""

    async def read_prepared(self, plan: ModbusPreparedReadPlan) -> RawModbusReadResult:
        """Read holding registers according to the prepared plan."""

    async def write(
        self,
        reg_addr: int,
        value_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        """Write one holding register value.

        Args:
            reg_addr: Target holding register address (0-based).
            value_type: Type hint (uint16, int16, bool).
            value: String-encoded value.
            request_id: Optional caller-supplied identifier.
        """
