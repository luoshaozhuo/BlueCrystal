"""进程内 Metrics Registry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from threading import RLock

from ..models import (
    CounterMetricSnapshot,
    GaugeMetricSnapshot,
    HistogramMetricSnapshot,
    MetricLabelSet,
    MetricRegistrySnapshot,
)

MetricKey = tuple[str, MetricLabelSet]


@dataclass(slots=True)
class _HistogramState:
    count: int = 0
    sum: float = 0.0
    min: float | None = None
    max: float | None = None

    def observe(self, value: float) -> None:
        self.count += 1
        self.sum += value
        self.min = value if self.min is None else min(self.min, value)
        self.max = value if self.max is None else max(self.max, value)


class InMemoryMetricRegistry:
    """线程安全的 P0 进程内 Metrics Registry."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._counters: dict[MetricKey, float] = {}
        self._gauges: dict[MetricKey, float] = {}
        self._histograms: dict[MetricKey, _HistogramState] = {}

    def increment_counter(
        self,
        name: str,
        amount: float = 1.0,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        _validate_metric_name(name)
        _validate_number(amount)
        if amount < 0:
            raise ValueError("counter amount must be greater than or equal to 0")

        key = _metric_key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + amount

    def set_gauge(
        self,
        name: str,
        value: float,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        _validate_metric_name(name)
        _validate_number(value)
        key = _metric_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def add_gauge(
        self,
        name: str,
        delta: float,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        _validate_metric_name(name)
        _validate_number(delta)
        key = _metric_key(name, labels)
        with self._lock:
            self._gauges[key] = self._gauges.get(key, 0.0) + delta

    def observe_histogram(
        self,
        name: str,
        value: float,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        _validate_metric_name(name)
        _validate_number(value)
        key = _metric_key(name, labels)
        with self._lock:
            state = self._histograms.setdefault(key, _HistogramState())
            state.observe(value)

    def snapshot(self) -> MetricRegistrySnapshot:
        with self._lock:
            counters = tuple(
                CounterMetricSnapshot(name=name, labels=labels, value=value)
                for (name, labels), value in sorted(self._counters.items())
            )
            gauges = tuple(
                GaugeMetricSnapshot(name=name, labels=labels, value=value)
                for (name, labels), value in sorted(self._gauges.items())
            )
            histograms = tuple(
                HistogramMetricSnapshot(
                    name=name,
                    labels=labels,
                    count=state.count,
                    sum=state.sum,
                    min=state.min,
                    max=state.max,
                )
                for (name, labels), state in sorted(self._histograms.items())
            )

        return MetricRegistrySnapshot(
            collected_at=datetime.now(timezone.utc),
            counters=counters,
            gauges=gauges,
            histograms=histograms,
        )

    def clear(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


def _metric_key(
    name: str,
    labels: Mapping[str, str] | None,
) -> MetricKey:
    normalized: list[tuple[str, str]] = []
    for raw_key, raw_value in (labels or {}).items():
        key = str(raw_key).strip()
        if not key:
            raise ValueError("metric label name must not be empty")
        normalized.append((key, str(raw_value)))
    return name, tuple(sorted(normalized))


def _validate_metric_name(name: str) -> None:
    if not name or not name.strip():
        raise ValueError("metric name must not be empty")


def _validate_number(value: float) -> None:
    if not isfinite(float(value)):
        raise ValueError("metric value must be finite")
