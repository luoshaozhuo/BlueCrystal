"""Seahorse scheduler 基础设施时钟。

本模块提供 `ClockPort` 的最小实现和测试友好的 fake clock。它不创建线程、
不执行 sleep loop，也不声明真实 50Hz 调度能力。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

from pacific.seahorse.application.ports.clock_port import ClockPort
from pacific.seahorse.application.runtime.executor import RuntimeExecutor
from pacific.seahorse.domain.runtime_contract import WriteBatch


@dataclass(slots=True)
class MonotonicClock(ClockPort):
    """基于标准库 time 的 ClockPort 实现。"""

    def monotonic_ns(self) -> int:
        """返回当前单调时钟纳秒值。"""
        return time.monotonic_ns()

    def now(self) -> datetime:
        """返回 UTC 墙上时钟时间。"""
        return datetime.now(timezone.utc)


@dataclass(slots=True)
class FakeClock(ClockPort):
    """测试用可推进时钟。

    Attributes:
        current_ns: 当前单调时钟纳秒值。
    """

    current_ns: int = 0

    def monotonic_ns(self) -> int:
        """返回当前 fake 单调时钟纳秒值。"""
        return self.current_ns

    def now(self) -> datetime:
        """按 current_ns 派生 UTC 墙上时钟时间。"""
        return datetime.fromtimestamp(self.current_ns / 1_000_000_000, tz=timezone.utc)

    def advance_ns(self, delta_ns: int) -> int:
        """推进 fake 时钟。

        Args:
            delta_ns: 推进纳秒数，必须非负。

        Returns:
            推进后的 current_ns。

        Raises:
            ValueError: delta_ns 小于 0。
        """
        if delta_ns < 0:
            raise ValueError("delta_ns 不能为负")
        self.current_ns += delta_ns
        return self.current_ns


@dataclass(slots=True)
class DeterministicScheduler:
    """同步 step helper。

    该 helper 用注入的 ClockPort 调用 RuntimeExecutor.tick，不 sleep、不循环，
    便于单元测试和 container 默认装配。
    """

    clock: ClockPort

    def step(self, executor: RuntimeExecutor) -> WriteBatch | None:
        """使用当前 clock 时间驱动 executor 一次 tick。"""
        return executor.tick(now_ns=self.clock.monotonic_ns())


__all__ = ["DeterministicScheduler", "FakeClock", "MonotonicClock"]
