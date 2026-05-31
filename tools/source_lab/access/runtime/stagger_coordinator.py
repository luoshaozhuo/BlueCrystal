"""Endpoint stagger offset coordinator."""

from __future__ import annotations

import threading

from tools.source_lab.access.runtime.endpoint_runtime import EndpointRuntimeConfig


class StaggerCoordinator:
    """Endpoint 启动错峰协调器，分配 stagger offset 避免并发冲击。

    根据当前已注册 endpoint 数量和预期周期计算每个新 endpoint 的纳秒级偏移量，
    确保多个 endpoint 不会在同一时刻同时发起外部连接。
    支持 offset 的持久化快照和恢复。

    不负责：offset 的实时调整、endpoint 生命周期管理。
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._offsets: dict[str, int] = {}

    def assign_offset(self, config: EndpointRuntimeConfig) -> tuple[int, bool]:
        with self._lock:
            if config.endpoint_id in self._offsets:
                return self._offsets[config.endpoint_id], False

            period_ns = max(1, round(config.expected_period_ms() * 1_000_000))
            slot = len(self._offsets)
            step = max(1, period_ns // 1024)
            offset = min(period_ns - 1, slot * step)
            self._offsets[config.endpoint_id] = offset
            return offset, False

    def preserve_offset(self, endpoint_id: str) -> int:
        with self._lock:
            return self._offsets.get(endpoint_id, 0)

    def delete_offset(self, endpoint_id: str) -> None:
        with self._lock:
            self._offsets.pop(endpoint_id, None)

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._offsets)

    def load_snapshot(self, offsets: dict[str, int]) -> None:
        with self._lock:
            self._offsets = dict(offsets)

