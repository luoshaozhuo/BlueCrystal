"""Logs 应用服务."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from types import MappingProxyType

from deploy.observability.shared import get_observation_context

from .models import ExceptionInfo, LogEvent, LogLevel
from .ports import LogSink


_REDACTED = "***REDACTED***"
_MAX_VALUE_LENGTH = 4096
_MAX_NESTING_DEPTH = 6
_SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "private_key",
        "database_password",
        "db_password",
    }
)


class LogService:
    """创建结构化 LogEvent 并输出到一个或多个 LogSink."""

    def __init__(self, sinks: Sequence[LogSink]) -> None:
        """初始化.

        Args:
            sinks: 日志输出端。允许为空；此时 emit 为 no-op。
        """
        self._sinks = tuple(sinks)

    def debug(
        self,
        *,
        component: str,
        event: str,
        message: str,
        fields: Mapping[str, object] | None = None,
    ) -> None:
        """记录 DEBUG 日志."""
        self.emit(
            level=LogLevel.DEBUG,
            component=component,
            event=event,
            message=message,
            fields=fields,
        )

    def info(
        self,
        *,
        component: str,
        event: str,
        message: str,
        fields: Mapping[str, object] | None = None,
    ) -> None:
        """记录 INFO 日志."""
        self.emit(
            level=LogLevel.INFO,
            component=component,
            event=event,
            message=message,
            fields=fields,
        )

    def warning(
        self,
        *,
        component: str,
        event: str,
        message: str,
        fields: Mapping[str, object] | None = None,
        exception: BaseException | None = None,
    ) -> None:
        """记录 WARNING 日志."""
        self.emit(
            level=LogLevel.WARNING,
            component=component,
            event=event,
            message=message,
            fields=fields,
            exception=exception,
        )

    def error(
        self,
        *,
        component: str,
        event: str,
        message: str,
        fields: Mapping[str, object] | None = None,
        exception: BaseException | None = None,
    ) -> None:
        """记录 ERROR 日志."""
        self.emit(
            level=LogLevel.ERROR,
            component=component,
            event=event,
            message=message,
            fields=fields,
            exception=exception,
        )

    def critical(
        self,
        *,
        component: str,
        event: str,
        message: str,
        fields: Mapping[str, object] | None = None,
        exception: BaseException | None = None,
    ) -> None:
        """记录 CRITICAL 日志."""
        self.emit(
            level=LogLevel.CRITICAL,
            component=component,
            event=event,
            message=message,
            fields=fields,
            exception=exception,
        )

    def emit(
        self,
        *,
        level: LogLevel,
        component: str,
        event: str,
        message: str,
        fields: Mapping[str, object] | None = None,
        exception: BaseException | None = None,
    ) -> LogEvent:
        """创建并输出一条日志事件.

        Observability 输出失败不能覆盖业务行为，因此某个 Sink 写入失败时继续尝试
        其余 Sink，并仅向 stderr 做最小 fallback 报告。
        """
        context = get_observation_context()
        log_event = LogEvent(
            timestamp=datetime.now(timezone.utc),
            level=level,
            component=component,
            event=event,
            message=_bounded_text(message),
            runtime_id=context.runtime_id,
            request_id=context.request_id,
            task_id=context.task_id,
            connection_id=context.connection_id,
            node_id=context.node_id,
            fields=MappingProxyType(_sanitize_mapping(fields or {})),
            exception=(
                ExceptionInfo.from_exception(exception)
                if exception is not None
                else None
            ),
        )

        for sink in self._sinks:
            try:
                sink.write(log_event)
            except Exception as exc:
                _fallback_sink_error(sink, exc)

        return log_event

    def flush(self) -> None:
        """刷新全部 Sink；单个 Sink 失败不阻断其余 Sink."""
        for sink in self._sinks:
            try:
                sink.flush()
            except Exception as exc:
                _fallback_sink_error(sink, exc)

    def close(self) -> None:
        """关闭全部 Sink；单个 Sink 失败不阻断其余 Sink."""
        for sink in reversed(self._sinks):
            try:
                sink.close()
            except Exception as exc:
                _fallback_sink_error(sink, exc)


def _sanitize_mapping(value: Mapping[str, object], *, depth: int = 0) -> dict[str, object]:
    """递归清理日志扩展字段并脱敏敏感键."""
    if depth >= _MAX_NESTING_DEPTH:
        return {"value": "<max-depth>"}

    result: dict[str, object] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key)
        if _is_sensitive_key(key):
            result[key] = _REDACTED
            continue
        result[key] = _sanitize_value(raw_value, depth=depth + 1)
    return result


def _sanitize_value(value: object, *, depth: int) -> object:
    """把扩展字段转换为适合日志序列化的有限结构."""
    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return _bounded_text(value)

    if isinstance(value, Mapping):
        return _sanitize_mapping(value, depth=depth)

    if isinstance(value, (list, tuple, set, frozenset)):
        if depth >= _MAX_NESTING_DEPTH:
            return ["<max-depth>"]
        return [_sanitize_value(item, depth=depth + 1) for item in value]

    return _bounded_text(repr(value))


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return normalized in _SENSITIVE_KEYS


def _bounded_text(value: str) -> str:
    if len(value) <= _MAX_VALUE_LENGTH:
        return value
    return value[:_MAX_VALUE_LENGTH] + "…<truncated>"


def _fallback_sink_error(sink: object, exception: BaseException) -> None:
    """避免使用 Logs 自身报告 Logs 故障，防止递归."""
    try:
        sys.stderr.write(
            "BlueCrystal observability log sink failure: "
            f"sink={type(sink).__name__} error={type(exception).__name__}: {exception}\n"
        )
        sys.stderr.flush()
    except Exception:
        pass
