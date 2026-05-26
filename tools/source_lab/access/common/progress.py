"""容量扫描进度渲染共享工具。

负责：在终端中渲染容量矩阵扫描的文本进度条。
不负责：指标计算、结果持久化。
"""

from __future__ import annotations

import sys


class CapacityProgressBar:
    """Render one capacity progress line on TTY stderr only."""

    _BAR_WIDTH = 16

    def __init__(self, access_mode: str, total: int) -> None:
        self._access_mode = access_mode
        self._total = max(0, total)
        self._enabled = self._total > 0 and sys.stderr.isatty()
        self._last_width = 0

    def update(
        self,
        *,
        process_count: int,
        process_max: int,
        server_count: int,
        server_max: int,
        hz: float,
        hz_max: float,
        current: int,
    ) -> None:
        """Refresh the progress bar with the latest executed combination."""

        if not self._enabled:
            return
        percent = min(100, round((current / self._total) * 100)) if self._total else 100
        filled = min(self._BAR_WIDTH, round((percent / 100) * self._BAR_WIDTH))
        bar = ("█" * filled) + ("░" * (self._BAR_WIDTH - filled))
        message = (
            f"[capacity] {self._access_mode:<9} "
            f"proc={process_count}/{process_max} "
            f"srv={server_count}/{server_max} "
            f"hz={hz:.1f}/{hz_max:.1f} "
            f"[{bar}] {percent:>3}%"
        )
        padded = message.ljust(max(len(message), self._last_width))
        sys.stderr.write("\r" + padded)
        sys.stderr.flush()
        self._last_width = len(padded)

    def close(self) -> None:
        """Clear any rendered progress line."""

        if not self._enabled or self._last_width <= 0:
            return
        sys.stderr.write("\r" + (" " * self._last_width) + "\r")
        sys.stderr.flush()
        self._last_width = 0
