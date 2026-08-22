"""Core observability manager."""

from __future__ import annotations

from ..config import ObservabilityConfig
from .lifecycle.resource import LifecycleResource


class ObservabilityManager:
    """Coordinate observability capabilities."""

    def __init__(
        self,
        config: ObservabilityConfig,
    ) -> None:
        self.config = config
        self.resources: list[LifecycleResource] = []

    def register_resource(
        self,
        resource: LifecycleResource,
    ) -> None:
        """Register lifecycle resource."""
        self.resources.append(resource)

    async def start(self) -> None:
        """Start registered resources."""
        for resource in self.resources:
            await resource.start()

    async def shutdown(self) -> None:
        """Shutdown resources in reverse order."""
        for resource in reversed(self.resources):
            await resource.shutdown()
