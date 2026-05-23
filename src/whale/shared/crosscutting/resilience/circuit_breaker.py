"""Minimal circuit-breaker model primitives."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CircuitBreaker:
    """Tiny circuit-breaker state holder for future wrapper use."""

    failure_threshold: int = 5
    failure_count: int = 0
    open_state: bool = False

