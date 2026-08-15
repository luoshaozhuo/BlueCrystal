"""Seahorse 时钟端口。"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class ClockPort(Protocol):
    """提供当前时间的应用端口。"""

    def monotonic_ns(self) -> int:
        """返回单调时钟纳秒值。"""
        ...

    def now(self) -> datetime:
        """返回墙上时钟时间。"""
        ...
