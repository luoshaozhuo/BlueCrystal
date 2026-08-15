"""IEC 104 source reader/writer facade."""
from __future__ import annotations

from collections.abc import Sequence

from pacific.whale.shared.source.iec104.backends import (
    Iec104Lib60870Backend,
    RawIec104ReadResult,
    RawWriteItemResult,
)


class Iec104SourceReader:
    """Thin facade over the IEC 104 native runner backend."""

    def __init__(self, host: str, port: int, common_addr: int = 1) -> None:
        self._host = host
        self._port = port
        self._common_addr = common_addr
        self._backend = Iec104Lib60870Backend(host, port, common_addr)

    async def __aenter__(self) -> "Iec104SourceReader":
        await self._backend.connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self._backend.disconnect()

    async def read(self, ioa_list: Sequence[int]) -> RawIec104ReadResult:
        """Execute one IEC 104 interrogation read, returning raw results.

        Args:
            ioa_list: Target information object addresses to read.

        Returns:
            Raw read result with IOA -> (type_tag, value) mapping.
        """
        return await self._backend.read(tuple(ioa_list))

    async def write(
        self,
        ioa: int,
        command_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        """Write one IEC 104 command value.

        Args:
            ioa: Target information object address.
            command_type: Command type (C_SC_NA_1, C_SE_NC_1).
            value: String-encoded value.
            request_id: Optional caller-supplied request identifier.

        Returns:
            Per-item write result.
        """
        return await self._backend.write(
            ioa=ioa,
            command_type=command_type,
            value=value,
            request_id=request_id,
        )
