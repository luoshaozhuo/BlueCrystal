"""Seahorse 最小 tick 驱动 runtime executor。

本模块位于 application/runtime，只依赖纯契约、application use case 与端口。
它按 ScheduleSpec 判断单个 tick 是否 due，生成 WriteBatch 并记录到内存
诊断结构；不 sleep、不创建线程、不调用 Starfish writer、不查询 Whale DB。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from pacific.seahorse.application.exceptions import SchedulerRuntimeError, SeahorseApplicationError
from pacific.seahorse.application.runtime.context import RuntimeContext
from pacific.seahorse.application.runtime.event_bus import RuntimeEvent, RuntimeEventBus
from pacific.seahorse.application.runtime.state import RuntimePhase
from pacific.seahorse.application.use_cases.atomic import BuildWriteBatchUseCase, DispatchWriteBatchUseCase
from pacific.seahorse.domain.runtime_contract import (
    EventTriggerSpec,
    ManualTriggerSpec,
    PeriodicScheduleSpec,
    RandomTimeScheduleSpec,
    ScheduleKind,
    ScheduleSpec,
    WriteBatch,
    WriteBatchResult,
)


@dataclass(slots=True)
class RuntimeExecutorDiagnostics:
    """tick executor 的纯内存诊断数据。

    Attributes:
        tick_index: 已成功生成 batch 的逻辑 tick 序号。
        last_tick_at: 最近一次生成 batch 的单调时间戳。
        last_batch_size: 最近一次 batch item 数量。
        generated_batch_count: 累计生成 batch 数量。
        missed_tick_count: 周期调度下估算错过的 tick 数量。
        last_error: 最近一次稳定错误摘要。
        last_dispatch_status: 最近一次 dispatch 状态。
        last_write_success_count: 最近一次 dispatch 成功写入 item 数。
        last_write_failure_count: 最近一次 dispatch 失败 item 数。
        last_writer_error: 最近一次 writer 失败摘要。
    """

    tick_index: int = 0
    last_tick_at: int | None = None
    last_batch_size: int = 0
    generated_batch_count: int = 0
    missed_tick_count: int = 0
    last_error: str = ""
    last_dispatch_status: str = ""
    last_write_success_count: int = 0
    last_write_failure_count: int = 0
    last_writer_error: str = ""

    def to_diagnostic_view(self) -> dict[str, str | int | None]:
        """输出快照可消费的稳定诊断字段。"""
        return {
            "tick_index": self.tick_index,
            "last_tick_at": self.last_tick_at,
            "last_batch_size": self.last_batch_size,
            "generated_batch_count": self.generated_batch_count,
            "missed_tick_count": self.missed_tick_count,
            "last_error": self.last_error,
            "last_dispatch_status": self.last_dispatch_status,
            "last_write_success_count": self.last_write_success_count,
            "last_write_failure_count": self.last_write_failure_count,
            "last_writer_error": self.last_writer_error,
        }


@dataclass(slots=True)
class RuntimeExecutor:
    """内存 tick executor。

    executor 只驱动 `BuildWriteBatchUseCase` 生成 batch 并保存在内存列表。
    它的 lifecycle 是可测试的同步方法，不表达真实 scheduler executor 性能。

    Attributes:
        context: 运行上下文，必须携带 WritePlan。
        batch_builder: WriteBatch 生成用例。
        dispatch_use_case: 可选 WriteBatch 分发用例；未配置时 tick 不写入。
        event_bus: 内存事件记录器，用于 event schedule 和诊断事件。
    """

    context: RuntimeContext
    batch_builder: BuildWriteBatchUseCase
    dispatch_use_case: DispatchWriteBatchUseCase | None = None
    event_bus: RuntimeEventBus = field(default_factory=RuntimeEventBus)
    diagnostics: RuntimeExecutorDiagnostics = field(default_factory=RuntimeExecutorDiagnostics)
    generated_batches: list[WriteBatch] = field(default_factory=list)
    current_schedule: ScheduleSpec | None = None
    _next_random_due_at: int | None = None
    _manual_triggers: list[str] = field(default_factory=list)
    _event_cursor: int = 0

    def start(self, *, now_ns: int) -> None:
        """启动内存 executor。

        Args:
            now_ns: 启动时的单调时钟纳秒值；仅用于初始化随机时刻调度。

        Raises:
            SchedulerRuntimeError: RuntimeContext 未携带 WritePlan。
        """
        if self.context.write_plan is None:
            raise SchedulerRuntimeError("RuntimeContext.write_plan 不能为空")
        self.current_schedule = self.context.write_plan.schedule
        self.context.state = self.context.state.transition_to(
            RuntimePhase.RUNNING,
            reason="scheduler start",
        )
        if self.current_schedule.kind is ScheduleKind.RANDOM_TIME:
            self._next_random_due_at = now_ns + self._next_random_delay()
        self.event_bus.publish(RuntimeEvent(event_type="scheduler.started"))

    def pause(self, *, reason: str = "scheduler pause") -> None:
        """暂停 executor；暂停期间 tick 不生成 batch。"""
        self.context.state = self.context.state.transition_to(RuntimePhase.PAUSED, reason=reason)

    def resume(self, *, reason: str = "scheduler resume") -> None:
        """从暂停恢复到 RUNNING。"""
        self.context.state = self.context.state.transition_to(RuntimePhase.RUNNING, reason=reason)

    def stop(self, *, reason: str = "scheduler stop") -> None:
        """停止 executor；停止后不可再次运行。"""
        self.context.state = self.context.state.transition_to(RuntimePhase.STOPPED, reason=reason)

    def trigger_manual(self, trigger_name: str) -> None:
        """登记一次手动触发。

        Args:
            trigger_name: 触发名，必须匹配 ManualTriggerSpec.trigger_name 才会 due。
        """
        self._manual_triggers.append(trigger_name)

    def publish_event(self, event: RuntimeEvent) -> None:
        """向内存事件总线发布事件，供 event schedule 消费。"""
        self.event_bus.publish(event)

    def update_period(self, *, period_ns: int) -> ScheduleSpec:
        """动态更新内存周期配置。

        Args:
            period_ns: 新周期纳秒值，必须大于 0。

        Returns:
            更新后的 ScheduleSpec。
        """
        self.current_schedule = ScheduleSpec.periodic(PeriodicScheduleSpec(period_ns=period_ns))
        if self.context.write_plan is not None:
            self.event_bus.publish(
                RuntimeEvent(
                    event_type="scheduler.period_updated",
                    payload={"period_ns": period_ns},
                )
            )
        return self.current_schedule

    def tick(self, *, now_ns: int) -> WriteBatch | None:
        """执行一次同步 tick 判断。

        Args:
            now_ns: 当前单调时钟纳秒值。

        Returns:
            due 时返回生成的 WriteBatch；未 due 或非 RUNNING 状态返回 None。

        Raises:
            SchedulerRuntimeError: batch 生成失败或上下文无 WritePlan。
        """
        if self.context.state.phase is not RuntimePhase.RUNNING:
            return None
        if self.context.write_plan is None:
            raise SchedulerRuntimeError("RuntimeContext.write_plan 不能为空")
        if self.current_schedule is None:
            self.current_schedule = self.context.write_plan.schedule
        if not self._is_due(now_ns=now_ns):
            return None
        next_tick_index = self.diagnostics.tick_index + 1
        try:
            batch = self.batch_builder.execute(
                write_plan=self.context.write_plan,
                timestamp_ns=now_ns,
                tick_index=next_tick_index,
            )
        except SeahorseApplicationError as exc:
            self.diagnostics.last_error = str(exc)
            self.context.state = self.context.state.transition_to(
                RuntimePhase.ERROR,
                reason=str(exc),
            )
            raise SchedulerRuntimeError(str(exc)) from exc

        self._record_generated_batch(batch=batch, now_ns=now_ns)
        self.event_bus.publish(
            RuntimeEvent(
                event_type="scheduler.batch_generated",
                payload={
                    "tick_index": self.diagnostics.tick_index,
                    "batch_size": self.diagnostics.last_batch_size,
                },
            )
        )
        return batch

    def tick_and_dispatch(self, *, now_ns: int) -> WriteBatchResult | None:
        """执行一次 tick，并在生成 batch 后调用 writer dispatch。

        Args:
            now_ns: 当前单调时钟纳秒值。

        Returns:
            未 due 或非 RUNNING 状态返回 None；已配置 dispatch_use_case 且
            due 时返回 WriteBatchResult。

        Raises:
            SchedulerRuntimeError: 未配置 dispatch_use_case，或 batch 生成失败。
        """
        batch = self.tick(now_ns=now_ns)
        if batch is None:
            return None
        if self.dispatch_use_case is None:
            self.diagnostics.last_dispatch_status = "not_configured"
            raise SchedulerRuntimeError("RuntimeExecutor.dispatch_use_case 不能为空")

        result = self.dispatch_use_case.execute(batch)
        self._record_dispatch_result(result)
        self.event_bus.publish(
            RuntimeEvent(
                event_type="scheduler.batch_dispatched",
                payload={
                    "batch_id": result.batch_id,
                    "accepted_count": result.accepted_count,
                    "failure_count": len(result.failures),
                },
            )
        )
        return result

    def snapshot_diagnostics(self) -> dict[str, str | int | None]:
        """返回 RuntimeSnapshot 可嵌入的 executor 诊断字段。"""
        return self.diagnostics.to_diagnostic_view()

    def _is_due(self, *, now_ns: int) -> bool:
        """判断当前 schedule 是否 due。"""
        schedule = self.current_schedule
        if schedule is None:
            return False
        if schedule.kind is ScheduleKind.PERIODIC:
            return self._is_periodic_due(schedule.detail, now_ns=now_ns)
        if schedule.kind is ScheduleKind.RANDOM_TIME:
            return self._is_random_time_due(now_ns=now_ns)
        if schedule.kind is ScheduleKind.MANUAL_TRIGGER:
            return self._consume_manual_trigger(schedule.detail)
        if schedule.kind is ScheduleKind.EVENT_TRIGGER:
            return self._consume_matching_event(schedule.detail)
        return False

    def _is_periodic_due(self, detail: object, *, now_ns: int) -> bool:
        """判断 periodic schedule 是否 due，并累计 missed tick。"""
        if not isinstance(detail, PeriodicScheduleSpec):
            return False
        if self.diagnostics.last_tick_at is None:
            return True
        elapsed = now_ns - self.diagnostics.last_tick_at
        if elapsed < detail.period_ns:
            return False
        due_intervals = elapsed // detail.period_ns
        if due_intervals > 1:
            self.diagnostics.missed_tick_count += due_intervals - 1
        return True

    def _is_random_time_due(self, *, now_ns: int) -> bool:
        """判断 deterministic random-time schedule 是否 due。"""
        if self._next_random_due_at is None:
            self._next_random_due_at = now_ns + self._next_random_delay()
        if now_ns < self._next_random_due_at:
            return False
        self._next_random_due_at = now_ns + self._next_random_delay()
        return True

    def _consume_manual_trigger(self, detail: object) -> bool:
        """消费一次匹配的 manual trigger。"""
        if not isinstance(detail, ManualTriggerSpec):
            return False
        for index, trigger_name in enumerate(self._manual_triggers):
            if trigger_name == detail.trigger_name:
                del self._manual_triggers[index]
                return True
        return False

    def _consume_matching_event(self, detail: object) -> bool:
        """消费 event bus 中尚未处理的匹配事件。"""
        if not isinstance(detail, EventTriggerSpec):
            return False
        while self._event_cursor < len(self.event_bus.events):
            event = self.event_bus.events[self._event_cursor]
            self._event_cursor += 1
            if event.event_type == detail.event_type:
                return True
        return False

    def _next_random_delay(self) -> int:
        """生成下一次 random-time due 延迟。"""
        schedule = self.current_schedule
        if schedule is None or not isinstance(schedule.detail, RandomTimeScheduleSpec):
            return 0
        detail = schedule.detail
        seed = (detail.seed or 0) + self.diagnostics.generated_batch_count
        generator = random.Random(seed)
        return generator.randint(detail.window_start_ns, detail.window_end_ns)

    def _record_generated_batch(self, *, batch: WriteBatch, now_ns: int) -> None:
        """记录 batch 和诊断字段。"""
        self.generated_batches.append(batch)
        self.diagnostics.tick_index += 1
        self.diagnostics.last_tick_at = now_ns
        self.diagnostics.last_batch_size = len(batch.items)
        self.diagnostics.generated_batch_count += 1
        self.diagnostics.last_error = ""

    def _record_dispatch_result(self, result: WriteBatchResult) -> None:
        """记录 writer dispatch 诊断字段。"""
        self.diagnostics.last_dispatch_status = "success" if result.success else "partial_failure"
        self.diagnostics.last_write_success_count = result.accepted_count
        self.diagnostics.last_write_failure_count = len(result.failures)
        self.diagnostics.last_writer_error = "; ".join(
            failure.reason for failure in result.failures
        )


__all__ = ["RuntimeExecutor", "RuntimeExecutorDiagnostics"]
