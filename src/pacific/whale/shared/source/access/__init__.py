"""Reusable source access models and adapters."""

from __future__ import annotations

from pacific.whale.shared.source.access.adapter import SourceAccessAdapter
from pacific.whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec, TickResult
from pacific.whale.shared.source.access.opcua import (
    OpcUaSourceAccessAdapter,
    build_opcua_endpoint_url,
    normalize_opcua_node_id,
)


def build_source_access_adapter(
    protocol: str,
    endpoint: SourceEndpointSpec,
    points: tuple[SourcePointSpec, ...],
    *,
    read_timeout_s: float,
) -> SourceAccessAdapter:
    """Build the reusable adapter for the requested protocol.

    Args:
        protocol: Protocol label for adapter selection.
        endpoint: Endpoint definition.
        points: Point definitions to be read by the adapter.
        read_timeout_s: Read timeout in seconds.
    Returns:
        One reusable source access adapter.

    Raises:
        ValueError: If the protocol is unsupported.
    """

    normalized = protocol.strip().lower().replace("_", "").replace("-", "")
    if normalized == "opcua":
        return OpcUaSourceAccessAdapter(
            endpoint,
            points,
            read_timeout_s=read_timeout_s,
        )
    raise ValueError(f"Unsupported protocol adapter: {protocol}")


__all__ = [
    "OpcUaSourceAccessAdapter",
    "SourceAccessAdapter",
    "SourceEndpointSpec",
    "SourcePointSpec",
    "TickResult",
    "build_opcua_endpoint_url",
    "build_source_access_adapter",
    "normalize_opcua_node_id",
]
