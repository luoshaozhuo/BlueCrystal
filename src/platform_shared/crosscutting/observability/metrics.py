"""Metrics sink protocol shared by adapters and wrappers."""

from __future__ import annotations

from typing import Protocol


class MetricsSinkPort(Protocol):
    """Record counters and timing without coupling to one metrics backend."""

    def increment(self, metric_name: str, value: int = 1, **labels: str) -> None:
        """Increment one named counter."""

    def observe_duration(
        self,
        metric_name: str,
        duration_seconds: float,
        **labels: str,
    ) -> None:
        """Record one duration measurement."""
