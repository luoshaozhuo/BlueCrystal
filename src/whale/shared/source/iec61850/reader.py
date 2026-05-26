"""IEC 61850 MMS source reader facade."""

from __future__ import annotations

from whale.shared.source.iec61850.backends import (
    LibIec61850MmsClientBackend,
    RawMmsReadResult,
    RawWriteItemResult,
)


class Iec61850MmsSourceReader:
    """Thin facade over the libiec61850 MMS backend."""

    def __init__(self, host: str, port: int, *, timeout_seconds: float = 5.0) -> None:
        self._host = host
        self._port = port
        self._timeout_seconds = timeout_seconds
        self._backend = LibIec61850MmsClientBackend(host, port, timeout_seconds=timeout_seconds)

    async def __aenter__(self) -> "Iec61850MmsSourceReader":
        await self._backend.connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self._backend.disconnect()

    async def read(
        self,
        obj_ref: str,
        fc: str = "NONE",
        *,
        request_id: str = "",
    ) -> RawMmsReadResult:
        """Read one MMS variable.

        Args:
            obj_ref: MMS object reference.
            fc: Functional constraint (ST, MX, SP, or NONE).
            request_id: Optional caller-supplied request identifier.

        Returns:
            Raw read result.
        """
        return await self._backend.read(
            obj_ref=obj_ref,
            fc=fc,
            request_id=request_id,
        )

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
            request_id: Optional caller-supplied request identifier.

        Returns:
            Per-item write result.
        """
        return await self._backend.write(
            obj_ref=obj_ref,
            fc=fc,
            value_type=value_type,
            value=value,
            request_id=request_id,
        )
