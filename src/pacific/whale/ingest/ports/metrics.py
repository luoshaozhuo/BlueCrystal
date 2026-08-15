"""Ingest 指标 port 接口。声明计数器、直方图等指标契约，由具体 sink 实现。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class IngestMetricEvent:
    """IngestMetricEvent 方法。"""
    operation: str
    source_id: str | None
    protocol: str | None
    duration_ms: float
    status: str
    error_code: str | None
    timestamp: datetime


class IngestMetricsPort(Protocol):
    """IngestMetricsPort 方法。"""
    def emit(self, event: IngestMetricEvent) -> None:
        """发送一条指标事件到配置的 sink。"""
