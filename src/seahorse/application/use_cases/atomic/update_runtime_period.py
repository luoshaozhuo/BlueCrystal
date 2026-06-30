"""更新 runtime 周期配置的纯用例。

本用例只生成新的 ScheduleSpec，必要时通过 SchedulerPort 提交抽象配置；
它不 sleep、不启动线程、不创建 asyncio task。
"""

from __future__ import annotations

from seahorse.application.ports.scheduler_port import SchedulerPort
from seahorse.domain.runtime_contract import PeriodicScheduleSpec, ScheduleSpec, WritePlanId


def update_runtime_period(
    *,
    plan_id: WritePlanId,
    period_ns: int,
    scheduler: SchedulerPort | None = None,
) -> ScheduleSpec:
    """更新运行计划周期配置。

    Args:
        plan_id: 运行计划标识。
        period_ns: 新周期纳秒值，必须大于 0。
        scheduler: 可选 scheduler 端口；传入时只提交配置契约。

    Returns:
        新的周期调度契约。
    """
    schedule = ScheduleSpec.periodic(PeriodicScheduleSpec(period_ns=period_ns))
    if scheduler is not None:
        return scheduler.update_period(plan_id, period_ns)
    return schedule
