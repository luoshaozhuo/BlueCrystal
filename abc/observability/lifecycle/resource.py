"""Lifecycle resource protocol."""

from __future__ import annotations

from typing import Protocol


class LifecycleResource(Protocol):
    """Managed lifecycle resource."""

    async def start(self) -> None:
        """Initialize resource."""
        ...

    async def shutdown(self) -> None:
        """Release resource."""
        ...
