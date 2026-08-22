"""Instrumentation registry lifecycle."""

from __future__ import annotations

from collections.abc import Iterable

from .base import Instrumentation


class InstrumentationRegistry:
    """Install and uninstall instrumentation adapters."""

    def __init__(
        self,
        instrumentations: Iterable[Instrumentation] = (),
    ) -> None:
        self._items = list(instrumentations)

    def register(self, instrumentation: Instrumentation) -> None:
        """Register adapter."""
        self._items.append(instrumentation)

    async def start(self) -> None:
        """Install all instrumentation."""
        for item in self._items:
            result = item.install()
            if hasattr(result, "__await__"):
                await result

    async def shutdown(self) -> None:
        """Uninstall all instrumentation."""
        for item in reversed(self._items):
            result = item.uninstall()
            if hasattr(result, "__await__"):
                await result

    def get_instrumentations(self):
        """Return registered adapters."""
        return tuple(self._items)
