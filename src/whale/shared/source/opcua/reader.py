"""Open62541-backed OPC UA raw polling facade."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from whale.shared.source.models import Batch, SourceConnectionProfile
from whale.shared.source.opcua.backends import (
    PreparedReadPlan,
    RawOpcUaReadResult,
    build_client_backend,
)


@dataclass(slots=True)
class OpcUaSubscriptionHandle:
    """Unsupported subscription placeholder kept for import compatibility."""

    async def close(self) -> None:
        raise NotImplementedError("OPC UA subscription is not supported in open62541-only mode")


class OpcUaSourceReader:
    """Thin facade over the open62541 raw polling backend."""

    def __init__(self, connection: SourceConnectionProfile) -> None:
        self._connection = connection
        self._backend = build_client_backend(connection)

    @property
    def endpoint(self) -> str:
        return self._connection.endpoint

    async def __aenter__(self) -> "OpcUaSourceReader":
        await self._backend.connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self._backend.disconnect()

    def prepare_read(self, addresses: Sequence[str]) -> PreparedReadPlan:
        """Prepare a reusable raw-read plan."""

        return self._backend.prepare_read(addresses)

    async def read_prepared_raw(self, plan: PreparedReadPlan) -> RawOpcUaReadResult:
        """Execute one prepared raw read."""

        return await self._backend.read_prepared_raw(plan)

    async def read(
        self,
        addresses: Sequence[str],
        *,
        mode: str = "value_only",
    ) -> Batch:
        """Reject full Batch APIs that are outside the open62541-only scope."""

        raise NotImplementedError(
            "open62541-only source_lab path does not provide Batch conversion; "
            "use prepare_read/read_prepared_raw instead"
        )

    async def start_subscription(self, *args: object, **kwargs: object) -> None:
        """Reject subscription APIs removed from the source_lab access path."""

        raise NotImplementedError("OPC UA subscription is not supported in open62541-only mode")

    async def list_nodes(self) -> tuple[object, ...]:
        """Reject browse APIs removed from the source_lab access path."""

        raise NotImplementedError("OPC UA browse is not supported in open62541-only mode")

    async def list_readable_variable_nodes(self) -> tuple[tuple[str, str], ...]:
        """Reject browse APIs removed from the source_lab access path."""

        raise NotImplementedError("OPC UA browse is not supported in open62541-only mode")
