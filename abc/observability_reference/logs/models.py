"""Logs 领域模型."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from traceback import format_exception
from types import MappingProxyType
from typing import Mapping


class LogLevel(StrEnum):
    """BlueCrystal 统一日志级别."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class ExceptionInfo:
    """可序列化的异常快照.

    不在 LogEvent 中长期持有原始 Exception 对象，避免后续 Adapter 需要理解
    Python 异常对象，也避免无意保留异常关联对象。
    """

    type: str
    message: str
    traceback: str

    @classmethod
    def from_exception(cls, exception: BaseException) -> "ExceptionInfo":
        """从 Python 异常创建日志异常快照."""
        return cls(
            type=type(exception).__name__,
            message=str(exception),
            traceback="".join(
                format_exception(
                    type(exception),
                    exception,
                    exception.__traceback__,
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class LogEvent:
    """一条结构化日志事件."""

    timestamp: datetime
    level: LogLevel
    component: str
    event: str
    message: str

    runtime_id: str | None = None
    request_id: str | None = None
    task_id: int | None = None
    connection_id: str | None = None
    node_id: str | None = None

    fields: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    exception: ExceptionInfo | None = None
