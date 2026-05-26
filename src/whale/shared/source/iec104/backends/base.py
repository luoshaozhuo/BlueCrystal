"""IEC 104 backend base types."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RawIec104ReadResult:
    """Raw IEC 104 read result from interrogation."""

    ok: bool
    values: dict[int, tuple[str, str]]
    """IOA -> (type_tag, value_str) mapping."""
    response_timestamp: datetime | None = None
    error_reason: str | None = None
    exception: str | None = None


@dataclass(frozen=True, slots=True)
class RawWriteItemResult:
    """Result of writing one IEC 104 command."""

    ioa: int
    ok: bool
    status_code: str | None
    error_message: str | None
    command_type: str | None = None


@dataclass(frozen=True, slots=True)
class Iec104PreparedReadPlan:
    """IEC 104-specific prepared read plan."""

    ioa_list: tuple[int, ...]
    common_addr: int = 1


class Iec104ClientBackend(Protocol):
    """Protocol for IEC 104 client backend."""

    async def connect(self) -> None:
        """Open backend connection."""

    async def disconnect(self) -> None:
        """Close backend connection."""

    async def read(self, ioa_list: tuple[int, ...]) -> RawIec104ReadResult:
        """Read values for given IOA list via interrogation."""

    async def write(
        self,
        ioa: int,
        command_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        """Write one command value.

        Args:
            ioa: Target information object address.
            command_type: Command type (C_SC_NA_1, C_SE_NC_1).
            value: String-encoded value.
            request_id: Optional caller-supplied identifier.
        """
