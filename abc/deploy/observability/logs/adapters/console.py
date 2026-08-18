"""Console LogSink 实现."""

from __future__ import annotations

import sys
from threading import Lock
from typing import TextIO

from ..models import LogEvent


class ConsoleLogSink:
    """将结构化日志以紧凑可读文本写到控制台."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stdout
        self._lock = Lock()
        self._closed = False

    def write(self, event: LogEvent) -> None:
        if self._closed:
            raise RuntimeError("ConsoleLogSink is closed")

        line = _format_console_line(event)
        with self._lock:
            self._stream.write(line + "\n")
            self._stream.flush()

    def flush(self) -> None:
        if self._closed:
            return
        with self._lock:
            self._stream.flush()

    def close(self) -> None:
        """不关闭 stdout/stderr，只标记该 Sink 不再接受写入."""
        if self._closed:
            return
        self.flush()
        self._closed = True


def _format_console_line(event: LogEvent) -> str:
    parts = [
        event.timestamp.isoformat().replace("+00:00", "Z"),
        event.level.value,
        f"[{event.component}]",
        event.event,
    ]

    if event.message:
        parts.append(event.message)

    correlation = _correlation_fields(event)
    if correlation:
        parts.append(correlation)

    if event.fields:
        details = " ".join(
            f"{key}={value!r}" for key, value in event.fields.items()
        )
        if details:
            parts.append(details)

    if event.exception is not None:
        parts.append(
            f"exception={event.exception.type}: {event.exception.message}"
        )

    return " | ".join(parts)


def _correlation_fields(event: LogEvent) -> str:
    values: list[str] = []
    if event.runtime_id is not None:
        values.append(f"runtime_id={event.runtime_id}")
    if event.node_id is not None:
        values.append(f"node_id={event.node_id}")
    if event.request_id is not None:
        values.append(f"request_id={event.request_id}")
    if event.task_id is not None:
        values.append(f"task_id={event.task_id}")
    if event.connection_id is not None:
        values.append(f"connection_id={event.connection_id}")
    return " ".join(values)
