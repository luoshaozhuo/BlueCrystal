"""Metrics registry lifecycle."""

from __future__ import annotations

from prometheus_client import CollectorRegistry


class MetricsRegistry:
    """Own Prometheus collector registry."""

    def __init__(
        self,
        registry: CollectorRegistry | None = None,
    ) -> None:
        self.registry = registry or CollectorRegistry()
        self._started = False

    async def start(self) -> None:
        """Initialize metrics resources."""
        self._started = True

    async def shutdown(self) -> None:
        """Release metrics resources."""
        self._started = False
