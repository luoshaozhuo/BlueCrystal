"""Instrumentation interfaces."""

from __future__ import annotations

from typing import Protocol


class Instrumentation(Protocol):
    """Third-party instrumentation adapter."""

    async def install(self) -> None:
        """Install instrumentation."""
        ...

    async def uninstall(self) -> None:
        """Uninstall instrumentation."""
        ...
