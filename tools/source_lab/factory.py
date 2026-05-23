"""Factory helpers for source_lab simulators."""

from __future__ import annotations

from tools.source_lab.contracts import SourceSimulator
from tools.source_lab.model import SimulatedSource
from tools.source_lab.protocols.registry import get_simulator_factory


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
    try:
        factory = get_simulator_factory(protocol)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported source simulator type: {source.connection.protocol}"
        ) from exc
    return factory(source)
