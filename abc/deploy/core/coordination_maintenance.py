"""Coordination Maintenance 的后台生命周期骨架。

本模块承载成员心跳、Ownership 续租与协调后端健康维护未来所需的长期 asyncio Task。
第一阶段只调度宿主提供的单轮维护回调，不实现 Lease、Fail-Closed、心跳或后端健康算法；
普通单轮错误作为可观察事实保留，并不修改 ClusterRuntime 的生命周期。
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


class CoordinationMaintenance:
    """管理可触发、可等待且可取消的 Coordination Maintenance 后台循环。"""

    def __init__(
        self,
        maintain_once: Callable[[], Awaitable[None]],
        interval_seconds: float = 1.0,
    ) -> None:
        """创建维护控制器但不创建后台任务。

        Args:
            maintain_once: 每轮维护协调事实的异步回调；第一阶段不得产生 Lease 或激活副作用。
            interval_seconds: 无外部触发时的最长等待时间，必须为正数。
        """
        if interval_seconds <= 0:
            raise ValueError("interval_seconds 必须大于零")
        self._maintain_once = maintain_once
        self._interval_seconds = interval_seconds
        self._wake_up = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._last_error: Exception | None = None

    @property
    def is_running(self) -> bool:
        """返回后台维护循环是否仍由未完成任务承载。"""
        return self._task is not None and not self._task.done()

    @property
    def last_error(self) -> Exception | None:
        """返回最近一次非致命维护错误，不将其升级为 Runtime 级失败。"""
        return self._last_error

    async def start(self) -> None:
        """启动维护循环；重复调用不会创建第二个并发任务。"""
        if self.is_running:
            return
        self._last_error = None
        self._wake_up.set()
        self._task = asyncio.create_task(self._run(), name="deploy-coordination-maintenance")

    def trigger(self) -> None:
        """请求尽快执行下一轮维护；多个触发会合并为一次唤醒。"""
        self._wake_up.set()

    async def stop(self) -> None:
        """取消并等待维护循环退出，确保关闭后不再访问协调事实。"""
        task = self._task
        if task is None:
            return
        self._task = None
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _run(self) -> None:
        """串行执行维护回调，并记录单轮异常后继续下一周期。"""
        while True:
            try:
                await asyncio.wait_for(self._wake_up.wait(), timeout=self._interval_seconds)
            except TimeoutError:
                pass
            self._wake_up.clear()
            try:
                await self._maintain_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                # 单轮维护问题暂不具备 Fail-Closed 语义，仅保留给宿主观察。
                self._last_error = exc
