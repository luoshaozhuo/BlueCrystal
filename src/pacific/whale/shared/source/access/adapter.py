"""Reusable source access adapter interfaces."""

from __future__ import annotations

from typing import Protocol

from pacific.whale.shared.source.access.model import TickResult


class SourceAccessAdapter(Protocol):
    """Protocol-agnostic adapter contract for repeated source reads."""

    async def connect(self) -> None:
        """Open the protocol connection required for reading."""

    async def prepare_read(self) -> None:
        """Prepare any reusable state required before repeated read ticks."""

    async def read_tick(self, *, expected_value_count: int) -> TickResult:
        """Execute one normalized read tick."""

    async def close(self) -> None:
        """Release adapter resources and close the connection."""
