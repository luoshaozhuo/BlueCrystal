"""Source write port registry for ingest."""

from __future__ import annotations

from typing import Protocol

from whale.ingest.ports.source.source_write_port import SourceWritePort


class SourceWritePortRegistry(Protocol):
    """Resolve one write port implementation for a protocol."""

    def get(self, protocol: str) -> SourceWritePort:
        """Return the write port registered for the given protocol."""
