"""Reusable runtime models for source access adapters."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SourceEndpointSpec:
    """Describe one source endpoint independent of adapter implementation.

    Args:
        name: Stable endpoint name used by callers for reporting.
        host: Endpoint host or IP.
        port: Endpoint port.
        protocol: Protocol label such as ``opcua``.
        transport: Transport label, defaulting to TCP semantics.
        namespace_uri: Optional namespace URI used by protocol readers.
        ied_name: Optional IED name kept for callers that model IEC-style sources.
        ld_name: Optional logical-device name kept for callers that model IEC-style sources.
        params: Protocol-specific connection parameters.
    """

    name: str
    host: str
    port: int
    protocol: str
    transport: str = "tcp"
    namespace_uri: str | None = None
    ied_name: str = ""
    ld_name: str = ""
    params: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SourcePointSpec:
    """Describe one source point independent of adapter implementation.

    Args:
        address: Protocol-layer point address.
        name: Optional stable point name.
        data_type: Optional data type label.
        ln_name: Optional logical-node name.
        do_name: Optional data-object name.
        unit: Optional engineering unit.
    """

    address: str
    name: str | None = None
    data_type: str | None = None
    ln_name: str | None = None
    do_name: str | None = None
    unit: str | None = None


@dataclass(frozen=True, slots=True)
class TickResult:
    """Normalize one adapter read tick into tool-independent metrics.

    Args:
        ok: Whether the read tick satisfied the adapter's success criteria.
        value_count: Number of values observed in the response.
        elapsed_ms: End-to-end elapsed time for the tick.
        response_timestamp_s: Normalized response timestamp in seconds, when available.
        error: Stable error label when the tick failed.
    """

    ok: bool
    value_count: int
    elapsed_ms: float
    response_timestamp_s: float | None
    error: str | None = None
