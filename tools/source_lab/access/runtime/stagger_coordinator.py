"""Endpoint stagger offset coordinator."""

from __future__ import annotations

import threading

from tools.source_lab.access.runtime.endpoint_runtime import EndpointRuntimeConfig


class StaggerCoordinator:
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

