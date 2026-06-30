"""Seahorse scheduler executor 最小实现单元测试。

验证对象：application runtime executor、infrastructure fake clock/step helper、
container 装配。
测试阶段：P1/P2。本文件只验证同步内存 tick 语义，不启动真实 scheduler、
不 sleep、不调用 Starfish writer、不证明真实 50Hz 性能。
"""

from __future__ import annotations

import pytest

from seahorse.application.exceptions import SchedulerRuntimeError
from seahorse.application.runtime import RuntimeContext, RuntimeEvent, RuntimeExecutor, RuntimePhase
from seahorse.application.runtime.snapshot import RuntimeSnapshot
from seahorse.application.use_cases.atomic import BuildWriteBatchUseCase
from seahorse.container import build_deterministic_scheduler, build_runtime_executor
from seahorse.domain.runtime_contract import (
    DataSourceKind,
    DataSourceSpec,
    EndpointBinding,
    EventTriggerSpec,
    FieldBinding,
    ManualTriggerSpec,
    PeriodicScheduleSpec,
    RandomTimeScheduleSpec,
    ScheduleSpec,
    ServerBinding,
    WritePlan,
    WritePlanId,
    WriteTarget,
)
from seahorse.infrastructure.data_sources import InMemoryDataSourceRuntime
from seahorse.infrastructure.schedulers import FakeClock


def _write_plan(schedule: ScheduleSpec) -> WritePlan:
    """构造一个单字段 WritePlan。"""
    source = DataSourceSpec("sample-src", DataSourceKind.SAMPLE, reference="sample-ref")
    field = FieldBinding(
        field_id="field-1",
        target=WriteTarget("srv-1", "ep-1", "point-1"),
        source_id=source.source_id,
    )
    return WritePlan(
        plan_id=WritePlanId("plan-scheduler"),
        servers=(
            ServerBinding(
                server_id="srv-1",
                endpoints=(
                    EndpointBinding(endpoint_id="ep-1", protocol="OPC_UA", fields=(field,)),
                ),
            ),
        ),
        data_sources=(source,),
        schedule=schedule,
    )


def _executor(schedule: ScheduleSpec) -> RuntimeExecutor:
    """构造使用内存 sample 数据源的 RuntimeExecutor。"""
    return RuntimeExecutor(
        context=RuntimeContext.from_write_plan(
            runtime_id="rt-1",
            write_plan=_write_plan(schedule),
        ),
        batch_builder=BuildWriteBatchUseCase(
            data_source_port=InMemoryDataSourceRuntime(samples={"sample-ref": 7})
        ),
    )


def test_periodic_executor_generates_batches_and_counts_missed_ticks() -> None:
    """periodic schedule 按 period due，并记录 missed_tick_count。"""
    executor = _executor(ScheduleSpec.periodic(PeriodicScheduleSpec(period_ns=10)))
    executor.start(now_ns=0)

    first = executor.tick(now_ns=0)
    early = executor.tick(now_ns=5)
    second = executor.tick(now_ns=35)

    assert first is not None
    assert early is None
    assert second is not None
    assert executor.diagnostics.tick_index == 2
    assert executor.diagnostics.generated_batch_count == 2
    assert executor.diagnostics.last_batch_size == 1
    assert executor.diagnostics.last_tick_at == 35
    assert executor.diagnostics.missed_tick_count == 2
    assert [batch.items[0].value for batch in executor.generated_batches] == [7, 7]


def test_random_time_executor_uses_deterministic_due_window() -> None:
    """random_time schedule 使用确定性窗口，不依赖真实随机执行器。"""
    executor = _executor(
        ScheduleSpec.random_time(
            RandomTimeScheduleSpec(window_start_ns=100, window_end_ns=101, seed=3)
        )
    )
    executor.start(now_ns=0)

    assert executor.tick(now_ns=99) is None
    batch = executor.tick(now_ns=200)

    assert batch is not None
    assert executor.diagnostics.generated_batch_count == 1


def test_manual_executor_requires_explicit_trigger() -> None:
    """manual schedule 只有收到匹配 trigger 才 due。"""
    executor = _executor(ScheduleSpec.manual(ManualTriggerSpec(trigger_name="operator")))
    executor.start(now_ns=0)

    assert executor.tick(now_ns=0) is None
    executor.trigger_manual("ignored")
    assert executor.tick(now_ns=1) is None
    executor.trigger_manual("operator")
    batch = executor.tick(now_ns=2)

    assert batch is not None
    assert executor.diagnostics.tick_index == 1


def test_event_executor_requires_matching_runtime_event() -> None:
    """event schedule 只有 event_bus 中出现匹配事件才 due。"""
    executor = _executor(ScheduleSpec.event(EventTriggerSpec(event_type="alarm")))
    executor.start(now_ns=0)

    executor.publish_event(RuntimeEvent(event_type="other"))
    assert executor.tick(now_ns=1) is None
    executor.publish_event(RuntimeEvent(event_type="alarm"))
    batch = executor.tick(now_ns=2)

    assert batch is not None
    assert executor.diagnostics.generated_batch_count == 1


def test_executor_lifecycle_pause_resume_stop() -> None:
    """executor 支持 CREATED/RUNNING/PAUSED/STOPPED 生命周期。"""
    executor = _executor(ScheduleSpec.periodic(PeriodicScheduleSpec(period_ns=10)))
    executor.start(now_ns=0)
    executor.pause(reason="test pause")

    assert executor.context.state.phase is RuntimePhase.PAUSED
    assert executor.tick(now_ns=0) is None

    executor.resume(reason="test resume")
    assert executor.context.state.phase is RuntimePhase.RUNNING
    assert executor.tick(now_ns=0) is not None

    executor.stop(reason="test stop")
    assert executor.context.state.phase is RuntimePhase.STOPPED
    assert executor.tick(now_ns=10) is None


def test_executor_records_error_state_when_batch_generation_fails() -> None:
    """batch 生成失败时进入 ERROR 并记录 last_error。"""
    executor = RuntimeExecutor(
        context=RuntimeContext.from_write_plan(
            runtime_id="rt-error",
            write_plan=_write_plan(ScheduleSpec.periodic(PeriodicScheduleSpec(period_ns=10))),
        ),
        batch_builder=BuildWriteBatchUseCase(data_source_port=InMemoryDataSourceRuntime()),
    )
    executor.start(now_ns=0)

    with pytest.raises(SchedulerRuntimeError, match="sample 数据源未加载"):
        executor.tick(now_ns=0)

    assert executor.context.state.phase is RuntimePhase.ERROR
    assert "sample 数据源未加载" in executor.diagnostics.last_error


def test_executor_updates_period_in_memory_only() -> None:
    """动态更新周期只修改 executor 内存 schedule，不宣称真实性能。"""
    executor = _executor(ScheduleSpec.periodic(PeriodicScheduleSpec(period_ns=20)))
    executor.start(now_ns=0)
    updated = executor.update_period(period_ns=5)

    assert updated.detail.period_ns == 5
    assert executor.current_schedule == updated
    assert executor.tick(now_ns=0) is not None
    assert executor.tick(now_ns=4) is None
    assert executor.tick(now_ns=5) is not None


def test_runtime_snapshot_includes_executor_diagnostics() -> None:
    """RuntimeSnapshot 可包含 tick/batch/error/missed tick 诊断字段。"""
    executor = _executor(ScheduleSpec.periodic(PeriodicScheduleSpec(period_ns=10)))
    executor.start(now_ns=0)
    executor.tick(now_ns=0)
    snapshot = RuntimeSnapshot(
        runtime_id=executor.context.runtime_id,
        state=executor.context.state,
        graph=executor.context.graph,
        diagnostics=executor.snapshot_diagnostics(),
    )

    view = snapshot.to_diagnostic_view()

    assert view["diagnostics"]["tick_index"] == 1
    assert view["diagnostics"]["generated_batch_count"] == 1
    assert view["diagnostics"]["last_batch_size"] == 1
    assert view["diagnostics"]["missed_tick_count"] == 0
    assert view["diagnostics"]["last_error"] == ""


def test_fake_clock_and_deterministic_scheduler_step_executor() -> None:
    """infrastructure scheduler helper 用 fake clock 同步驱动 executor。"""
    clock = FakeClock()
    scheduler = build_deterministic_scheduler(clock)
    executor = build_runtime_executor(
        runtime_id="rt-container",
        write_plan=_write_plan(ScheduleSpec.periodic(PeriodicScheduleSpec(period_ns=10))),
        batch_builder=BuildWriteBatchUseCase(
            data_source_port=InMemoryDataSourceRuntime(samples={"sample-ref": 7})
        ),
    )
    executor.start(now_ns=clock.monotonic_ns())

    first = scheduler.step(executor)
    clock.advance_ns(10)
    second = scheduler.step(executor)

    assert first is not None
    assert second is not None
    assert executor.diagnostics.generated_batch_count == 2
