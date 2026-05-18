"""Factory helpers for source_lab simulators."""

from __future__ import annotations

from tools.source_lab.opcua.open62541_source_simulator import (
    Open62541SourceSimulator,
)
from tools.source_lab.contracts import SourceSimulator
from tools.source_lab.model import SimulatedSource


def _normalize_protocol(value: str) -> str:
    """Normalize protocol labels to a stable key."""

    return value.strip().lower().replace("_", "").replace("-", "")


def build_simulator(source: SimulatedSource) -> SourceSimulator:
    """Build one simulator directly from one source definition.

    Args:
        source: Simulated source definition.

    Returns:
        Source simulator instance.

    Raises:
        ValueError: If protocol is unsupported.
    """
    protocol = _normalize_protocol(source.connection.protocol)

    if protocol == "opcua":
        return Open62541SourceSimulator(source)

    raise ValueError(f"Unsupported source simulator type: {source.connection.protocol}")
