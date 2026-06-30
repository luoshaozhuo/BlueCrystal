"""Seahorse telemetry 端口。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TelemetryPort(Protocol):
    """应用层轻量指标与诊断端口。"""

    def increment(self, name: str, value: int = 1) -> None:
        """递增计数指标。"""
        ...

    def observe(self, name: str, value: float) -> None:
        """记录一个数值观测。"""
        ...

    def diagnostic(self, name: str, message: str) -> None:
        """记录轻量诊断消息，不绑定具体 logger backend。"""
        ...
