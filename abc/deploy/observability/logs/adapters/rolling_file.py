"""Rolling File LogSink 实现."""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock

from ..models import LogEvent, LogLevel


_LOGGING_LEVELS = {
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.INFO: logging.INFO,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.ERROR: logging.ERROR,
    LogLevel.CRITICAL: logging.CRITICAL,
}


class RollingFileLogSink:
    """将每条 LogEvent 作为一行 JSON 写入滚动日志文件.

    P0 面向单进程 Standalone Runtime。标准库 RotatingFileHandler 可处理同一进程
    多线程写入，但不提供多进程文件轮转协调；未来多进程部署应改为每进程独立文件
    或集中式日志后端。
    """

    def __init__(
        self,
        path: str | Path,
        *,
        max_bytes: int = 50 * 1024 * 1024,
        backup_count: int = 10,
        encoding: str = "utf-8",
    ) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be greater than 0")
        if backup_count < 0:
            raise ValueError("backup_count must be greater than or equal to 0")

        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._handler = RotatingFileHandler(
            filename=self._path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
            delay=True,
        )
        self._handler.setFormatter(logging.Formatter("%(message)s"))
        self._lock = Lock()
        self._closed = False

    @property
    def path(self) -> Path:
        return self._path

    def write(self, event: LogEvent) -> None:
        if self._closed:
            raise RuntimeError("RollingFileLogSink is closed")

        message = _serialize_json_line(event)
        record = logging.LogRecord(
            name="bluecrystal.observability",
            level=_LOGGING_LEVELS[event.level],
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None,
        )

        # Handler 自己也有 lock；此锁额外保护 close/write 的本地生命周期竞争。
        with self._lock:
            self._handler.handle(record)

    def flush(self) -> None:
        if self._closed:
            return
        with self._lock:
            self._handler.flush()

    def close(self) -> None:
        if self._closed:
            return
        with self._lock:
            self._handler.flush()
            self._handler.close()
            self._closed = True


def _serialize_json_line(event: LogEvent) -> str:
    payload: dict[str, object] = {
        "timestamp": event.timestamp.isoformat().replace("+00:00", "Z"),
        "level": event.level.value,
        "component": event.component,
        "event": event.event,
        "message": event.message,
    }

    if event.runtime_id is not None:
        payload["runtime_id"] = event.runtime_id
    if event.node_id is not None:
        payload["node_id"] = event.node_id
    if event.request_id is not None:
        payload["request_id"] = event.request_id
    if event.task_id is not None:
        payload["task_id"] = event.task_id
    if event.connection_id is not None:
        payload["connection_id"] = event.connection_id
    if event.fields:
        payload["fields"] = dict(event.fields)
    if event.exception is not None:
        payload["exception"] = {
            "type": event.exception.type,
            "message": event.exception.message,
            "traceback": event.exception.traceback,
        }

    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        default=repr,
    )
