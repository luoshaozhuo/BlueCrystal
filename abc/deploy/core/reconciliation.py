"""Reconciliation Control 的后台等待与停止骨架。

控制器周期读取权威事实并调用纯 Reconciler。第一阶段 Reconciler 返回空计划，因此该模块
不执行 Ownership 或 Activation 动作；单轮计算错误被记录并在下一周期重试，不升级为
ClusterRuntime 的致命生命周期错误。
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


class ReconciliationControl:
    """管理可触发、可等待且可取消的 Reconciliation 后台循环。"""

    def __init__(
        self,
        reconcile_once: Callable[[], Awaitable[None]],
        interval_seconds: float = 1.0,
    ) -> None:
        """创建控制器但不创建后台任务。

        Args:
            reconcile_once: 每轮读取事实、计算并执行计划的异步回调。
            interval_seconds: 无外部触发时的最长等待时间，必须为正数。
        """
        if interval_seconds <= 0:
            raise ValueError("interval_seconds 必须大于零")
        self._reconcile_once = reconcile_once
        self._interval_seconds = interval_seconds
        self._wake_up = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._last_error: Exception | None = None

    @property
    def is_running(self) -> bool:
        """返回后台循环是否仍由未完成任务承载。"""
        return self._task is not None and not self._task.done()

    @property
    def last_error(self) -> Exception | None:
        """返回最近一次非致命收敛错误，不把它伪装为 Runtime 级失败。"""
        return self._last_error

    async def start(self) -> None:
        """启动后台循环；重复调用不会创建第二个并发控制器。"""
        if self.is_running:
            return
        self._last_error = None
        self._wake_up.set()
        self._task = asyncio.create_task(self._run(), name="deploy-reconciliation")

    def trigger(self) -> None:
        """请求尽快开始下一轮计算；多个触发会合并为一次唤醒。"""
        self._wake_up.set()

    async def stop(self) -> None:
        """取消并等待循环退出，确保 Runtime 关闭后不再产生控制要求。"""
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
        """串行执行收敛回调，并将单轮异常保留为可观察事实后继续等待。"""
        while True:
            try:
                await asyncio.wait_for(self._wake_up.wait(), timeout=self._interval_seconds)
            except TimeoutError:
                pass
            self._wake_up.clear()
            try:
                await self._reconcile_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                # 单轮计划错误不能让 Runtime 生命周期误判为不可清理；保留原异常供宿主观察。
                self._last_error = exc
