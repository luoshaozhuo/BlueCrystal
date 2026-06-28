"""IEC 61850 Report native DriverPort adapter。"""

from __future__ import annotations

import queue
from typing import Any

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class ReportQueue:
    """IEC61850 Report 事件队列句柄。

    可独立作为内存事件队列使用，也可包装 backend 返回的队列对象。
    """

    def __init__(self, delegate: Any | None = None) -> None:
        self._delegate = delegate
        self._queue: queue.Queue[dict[str, Any]] = queue.Queue()

    def put(self, event: dict[str, Any]) -> None:
        """向队列尾部插入一个 report 事件。"""
        if self._delegate is not None and hasattr(self._delegate, "put"):
            self._delegate.put(event)
            return
        self._queue.put(event)

    def get(self, timeout: float | None = None) -> dict[str, Any]:
        """获取下一个 report。"""
        if self._delegate is not None:
            return self._delegate.get(timeout=timeout)
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_nowait(self) -> dict[str, Any] | None:
        """非阻塞获取 report。"""
        if self._delegate is not None:
            return self._delegate.get_nowait()
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def drain(self) -> list[dict[str, Any]]:
        """排空队列中所有事件。"""
        if self._delegate is not None and hasattr(self._delegate, "drain"):
            return self._delegate.drain()
        events: list[dict[str, Any]] = []
        while True:
            try:
                events.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return events

    def qsize(self) -> int:
        """返回队列当前大小。"""
        if self._delegate is not None and hasattr(self._delegate, "qsize"):
            return self._delegate.qsize()
        return self._queue.qsize()


class Iec61850ReportDriverAdapter(DelegatingDriverAdapter):
    """IEC 61850 Report adapter，native runner 子进程由 infrastructure backend 管理。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 IEC61850 Report backend。"""
        super().__init__(backend)


__all__ = ["Iec61850ReportDriverAdapter", "ReportQueue"]
