"""Metrics 应用服务."""

from __future__ import annotations

from collections.abc import Mapping

from .models import MetricRegistrySnapshot
from .ports import MetricRegistry


class MetricService:
    """提供稳定的 Metrics 写入与查询入口."""

    def __init__(self, registry: MetricRegistry) -> None:
        self._registry = registry

    def increment(
        self,
        name: str,
        amount: float = 1.0,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        self._registry.increment_counter(name, amount, labels=labels)

    def set_gauge(
        self,
        name: str,
        value: float,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        self._registry.set_gauge(name, value, labels=labels)

    def add_gauge(
        self,
        name: str,
        delta: float,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        self._registry.add_gauge(name, delta, labels=labels)

    def observe(
        self,
        name: str,
        value: float,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        self._registry.observe_histogram(name, value, labels=labels)

    def snapshot(self) -> MetricRegistrySnapshot:
        return self._registry.snapshot()

    def clear(self) -> None:
        self._registry.clear()
