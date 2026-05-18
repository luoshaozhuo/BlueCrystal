# mypy: disable-error-code=import-untyped
"""Reusable OPC UA source access adapter."""

from __future__ import annotations

import time
from datetime import datetime

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec, TickResult
from whale.shared.source.models import SourceConnectionProfile
from whale.shared.source.opcua.reader import OpcUaSourceReader


def normalize_opcua_node_id(address: str) -> str:
    """Normalize one point address into OPC UA string NodeId form.

    Args:
        address: Raw point address.

    Returns:
        Address with the ``s=`` prefix required by the adapter.
    """

    stripped = address.strip()
    if stripped.startswith("s="):
        return stripped
    return f"s={stripped}"


def build_opcua_endpoint_url(endpoint: SourceEndpointSpec) -> str:
    """Build an OPC UA endpoint URL from one endpoint spec.

    Args:
        endpoint: Reusable source endpoint specification.

    Returns:
        Protocol endpoint URL for ``OpcUaSourceReader``.
    """

    transport = endpoint.transport.strip().lower() if endpoint.transport else "tcp"
    scheme = "opc.tcp" if transport == "tcp" else f"opc.{transport}"
    return f"{scheme}://{endpoint.host}:{endpoint.port}"


def _raw_value_count(data_values: tuple[object, ...] | list[object]) -> int:
    count = 0
    for item in data_values:
        if hasattr(item, "Value"):
            count += 1
        elif getattr(item, "value", None) is not None:
            count += 1
        elif item is not None:
            count += 1
    return count


class OpcUaSourceAccessAdapter:
    """Read repeatedly from an OPC UA source via prepared raw reads."""

    def __init__(
        self,
        endpoint: SourceEndpointSpec,
        points: tuple[SourcePointSpec, ...],
        *,
        read_timeout_s: float,
    ) -> None:
        """Initialize the reusable OPC UA access adapter.

        Args:
            endpoint: Endpoint definition for the reader connection.
            points: Point definitions to normalize into prepared reads.
            read_timeout_s: Reader timeout in seconds.
        """

        self._endpoint = endpoint
        self._points = points
        self._read_timeout_s = read_timeout_s
        self._reader: OpcUaSourceReader | None = None
        self._plan: object | None = None
        self._addresses = tuple(normalize_opcua_node_id(point.address) for point in points)

    async def connect(self) -> None:
        """Connect the underlying ``OpcUaSourceReader``."""

        self._reader = OpcUaSourceReader(
            SourceConnectionProfile(
                endpoint=build_opcua_endpoint_url(self._endpoint),
                namespace_uri=self._endpoint.namespace_uri,
                timeout_seconds=self._read_timeout_s,
                params=dict(self._endpoint.params),
            )
        )
        await self._reader.__aenter__()

    async def prepare_read(self) -> None:
        """Prepare the reusable raw-read plan used by ``read_tick``."""

        if self._reader is None:
            raise RuntimeError("reader_not_connected")
        self._plan = self._reader.prepare_read(self._addresses)

    async def close(self) -> None:
        """Close the underlying reader and clear prepared state."""

        if self._reader is None:
            return
        try:
            await self._reader.__aexit__(None, None, None)
        finally:
            self._reader = None
            self._plan = None

    async def read_tick(self, *, expected_value_count: int) -> TickResult:
        """Execute one prepared raw read and normalize the result.

        Args:
            expected_value_count: Expected number of values for batch-size validation.

        Returns:
            Normalized read tick result.
        """

        if self._reader is None or self._plan is None:
            return TickResult(False, 0, 0.0, None, "reader_not_ready")

        started_at = time.perf_counter()
        try:
            raw = await self._reader.read_prepared_raw(self._plan)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000.0
            return TickResult(False, 0, elapsed_ms, None, type(exc).__name__)

        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        value_count = _raw_value_count(tuple(raw.data_values))
        response_timestamp_s = (
            raw.response_timestamp.timestamp() if isinstance(raw.response_timestamp, datetime) else None
        )

        if not raw.ok:
            return TickResult(False, value_count, elapsed_ms, response_timestamp_s, raw.error_reason)
        if value_count != expected_value_count:
            return TickResult(False, value_count, elapsed_ms, response_timestamp_s, "batch_mismatch")
        if response_timestamp_s is None:
            return TickResult(False, value_count, elapsed_ms, None, "missing_response_timestamp")

        return TickResult(True, value_count, elapsed_ms, response_timestamp_s)
