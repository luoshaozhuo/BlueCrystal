"""Logs 输出端口."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import LogEvent


@runtime_checkable
class LogSink(Protocol):
    """结构化日志输出端口.

    Sink 只负责把已经形成的 LogEvent 输出到某个介质；日志语义、上下文补全、
    脱敏等规则不属于 Sink。
    """

    def write(self, event: LogEvent) -> None:
        """输出一条日志事件."""

    def flush(self) -> None:
        """刷新尚未落地的数据."""

    def close(self) -> None:
        """释放 Sink 资源."""
