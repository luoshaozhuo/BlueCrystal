from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


class PreparedReadPlan(Protocol):
    """Marker protocol for backend-specific prepared read plans.

    The current polling backends expose different prepared-read internals.
    Readers and tests can rely on the normalized logical node paths through
    this shared protocol, while each backend keeps its own low-level payload.
    """

    @property
    def node_paths(self) -> tuple[str, ...]:
        """Return normalized logical node paths included in this plan."""


@dataclass(frozen=True, slots=True)
class Open62541PreparedReadPlan:
    """open62541-specific prepared read plan for raw polling."""

    node_paths: tuple[str, ...]
    node_ids: tuple[str, ...]
    namespace_uri: str | None
    namespace_index: int | None = None


@dataclass(frozen=True, slots=True)
class RawDataValue:
    """Backend-neutral raw data value used by raw-polling backends.

    The current open62541 raw polling backend returns one decoded VALUE record
    per node through the native runner protocol, including ``value``,
    ``status_code`` and source/server timestamps when available.
    """

    value: object
    source_timestamp: datetime | None = None
    server_timestamp: datetime | None = None
    status_code: str | None = None


@dataclass(frozen=True, slots=True)
class RawOpcUaReadResult:
    """Raw OPC UA read result before Batch/NodeValueChange conversion.

    This is the backend raw-polling boundary. Converting raw values into
    ``Batch`` and ``NodeValueChange`` objects remains the responsibility of the
    ``OpcUaSourceReader`` facade layer.
    """

    ok: bool
    data_values: Sequence[object]
    response_timestamp: datetime | None
    error_reason: str | None = None
    exception: str | None = None
    retry_count: int = 0


@runtime_checkable
class OpcUaClientBackend(Protocol):
    """Protocol for OPC UA client backend used by raw polling."""

    async def connect(self) -> None:
        """Open backend connection."""

    async def disconnect(self) -> None:
        """Close backend connection."""

    @property
    def namespace_index(self) -> int | None:
        """Resolved namespace index, if configured."""

    def prepare_read(self, addresses: Sequence[str]) -> PreparedReadPlan:
        """Prepare a reusable read plan for stable node paths."""

    async def read_prepared_raw(
        self,
        plan: PreparedReadPlan,
    ) -> RawOpcUaReadResult:
        """Read prepared DataValues without constructing Batch."""
