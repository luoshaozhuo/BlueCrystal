"""MQTT-like DriverPort adapter。

adapter 层不直接创建 socket 或线程 server；轻量 TCP JSON 行协议由
infrastructure backend 实现，本类仅作为应用端口适配器暴露。
"""

from __future__ import annotations

import queue
from typing import Any

from starfish.adapters.drivers.backend_ports import DelegatingDriverAdapter, DriverBackend


class SubscriptionQueue:
    """MQTT 订阅队列句柄。

    可独立作为内存队列使用，也可包装 infrastructure backend 返回的队列对象。
    """

    def __init__(self, delegate: Any | None = None) -> None:
        self._delegate = delegate
        self._q: queue.Queue[tuple[str, Any]] = queue.Queue()

    def get(self, timeout: float | None = None) -> tuple[str, Any]:
        """获取下一个变更通知。"""
        if self._delegate is not None:
            return self._delegate.get(timeout=timeout)
        return self._q.get(timeout=timeout)

    def get_nowait(self) -> tuple[str, Any] | None:
        """非阻塞获取下一个变更通知。"""
        if self._delegate is not None:
            return self._delegate.get_nowait()
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None

    def _put(self, point_id: str, value: Any) -> None:
        """向队列推入一个变更通知。"""
        if self._delegate is not None and hasattr(self._delegate, "_put"):
            self._delegate._put(point_id, value)
            return
        self._q.put((point_id, value))


class MqttDriverAdapter(DelegatingDriverAdapter):
    """MQTT-like driver adapter，委托 infrastructure backend 执行物理 I/O。"""

    def __init__(self, backend: DriverBackend) -> None:
        """接收已创建的 MQTT-like backend。"""
        super().__init__(backend)

    def subscribe(self, point_ids: list[str]) -> SubscriptionQueue:
        """订阅点位并返回 adapter 层队列句柄。"""
        return SubscriptionQueue(self.backend.subscribe(point_ids))


__all__ = ["MqttDriverAdapter", "SubscriptionQueue"]
