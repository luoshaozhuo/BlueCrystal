"""Internal typing contracts for source_lab.

This module is a lightweight tool-side typing helper. It is not a
production ports/adapters architecture boundary.
"""

from __future__ import annotations

from typing import Protocol


class SourceSimulator(Protocol):
    """Lifecycle contract for one running simulated server."""

    @property
    def endpoint(self) -> str: ...

    @property
    def name(self) -> str: ...

    def start(self) -> "SourceSimulator": ...

    def stop(self) -> None: ...

    def __enter__(self) -> "SourceSimulator": ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: ...

    def writes(self, values_by_key: dict[str, str | int | float | bool]) -> None: ...
