"""IEC 61850 MMS backend base types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class RawMmsReadResult:
    """Raw IEC 61850 MMS read result.

    One MMS read yields the value of one object reference.
    """

    ok: bool
    obj_ref: str
    value_type: str | None
    value: str | None
    error_reason: str | None = None
    exception: str | None = None


@dataclass(frozen=True, slots=True)
class RawWriteItemResult:
    """Result of writing one MMS variable."""

    obj_ref: str
    ok: bool
    status_code: str | None
    error_message: str | None
    value_type: str | None = None


@runtime_checkable
class Iec61850MmsClientBackend(Protocol):
    """Protocol for IEC 61850 MMS client backend."""

    async def connect(self) -> None:
        """Open backend connection."""

    async def disconnect(self) -> None:
        """Close backend connection."""

    async def read(
        self,
        obj_ref: str,
        fc: str,
        *,
        request_id: str = "",
    ) -> RawMmsReadResult:
        """Read one MMS variable.

        Args:
            obj_ref: MMS object reference (e.g. "Simulator/GGIO1.SPCtrl1.setVal").
            fc: Functional constraint (e.g. "ST", "MX", "SP", "NONE").
            request_id: Optional caller-supplied request identifier.
        """

    async def write(
        self,
        obj_ref: str,
        fc: str,
        value_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        """Write one MMS variable.

        Args:
            obj_ref: MMS object reference.
            fc: Functional constraint.
            value_type: Type hint (BOOLEAN, INT32, UINT32, FLOAT32, FLOAT64, VISIBLE_STRING).
            value: String-encoded value.
            request_id: Optional caller-supplied identifier.
        """
