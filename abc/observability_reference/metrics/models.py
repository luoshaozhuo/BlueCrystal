"""Metrics 只读快照模型."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

MetricLabelSet = tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class CounterMetricSnapshot:
    """Counter 当前值."""

    name: str
    labels: MetricLabelSet
    value: float


@dataclass(frozen=True, slots=True)
class GaugeMetricSnapshot:
    """Gauge 当前值."""

    name: str
    labels: MetricLabelSet
    value: float


@dataclass(frozen=True, slots=True)
class HistogramMetricSnapshot:
    """Histogram 的 P0 聚合快照."""

    name: str
    labels: MetricLabelSet
    count: int
    sum: float
    min: float | None
    max: float | None


@dataclass(frozen=True, slots=True)
class MetricRegistrySnapshot:
    """某一时刻的完整 Metrics Registry 快照."""

    collected_at: datetime
    counters: tuple[CounterMetricSnapshot, ...]
    gauges: tuple[GaugeMetricSnapshot, ...]
    histograms: tuple[HistogramMetricSnapshot, ...]
