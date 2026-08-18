"""Metrics 输出端口."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from .models import MetricRegistrySnapshot


@runtime_checkable
class MetricRegistry(Protocol):
    """Metrics Registry 抽象."""

    def increment_counter(
        self,
        name: str,
        amount: float = 1.0,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None: ...

    def set_gauge(
        self,
        name: str,
        value: float,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None: ...

    def add_gauge(
        self,
        name: str,
        delta: float,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None: ...

    def observe_histogram(
        self,
        name: str,
        value: float,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None: ...

    def snapshot(self) -> MetricRegistrySnapshot: ...

    def clear(self) -> None: ...
