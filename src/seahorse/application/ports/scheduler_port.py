"""Seahorse scheduler 端口。

本端口仅声明调度生命周期能力，不实现 50Hz runtime 或后台任务。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from seahorse.domain.runtime_contract import ScheduleSpec, WritePlanId


@runtime_checkable
class SchedulerPort(Protocol):
    """调度器抽象端口。

    端口只声明调度配置和周期更新，不 sleep、不创建线程、不创建 asyncio task。
    """

    def register_schedule(self, plan_id: WritePlanId, schedule: ScheduleSpec) -> None:
        """登记运行计划调度契约。"""
        ...

    def update_period(self, plan_id: WritePlanId, period_ns: int) -> ScheduleSpec:
        """更新周期配置并返回新的调度契约。"""
        ...
