"""Seahorse 内存 runtime smoke workflow 单元测试。

验证对象：
- :class:`seahorse.application.use_cases.atomic.RuntimeSmokeWorkflow`
- :class:`seahorse.application.use_cases.atomic.RuntimeSmokeReport`
- :func:`seahorse.container.build_runtime_smoke_workflow`
- :meth:`seahorse.api.seahorse_facade.SeahorseFacade.run_runtime_smoke`

测试阶段：P1/P2。本文件只验证 WritePlan -> BuildWriteBatchUseCase ->
RuntimeExecutor.tick_and_dispatch -> DispatchWriteBatchUseCase ->
InMemoryStarfishWriterBackend 的最小可用链路，不接真实 Starfish、
不调用 socket、subprocess、native runner 或 ServerSimulatorFacade，
也不启动真实 scheduler。
"""

from __future__ import annotations

from seahorse.adapters.gateways import StarfishWriterGateway
from seahorse.api.seahorse_facade import SeahorseFacade
from seahorse.application.runtime import RuntimeContext, RuntimeExecutor
from seahorse.application.use_cases.atomic import (
    BuildWriteBatchUseCase,
    DispatchWriteBatchUseCase,
    RuntimeSmokeReport,
    RuntimeSmokeWorkflow,
)
from seahorse.application.use_cases.atomic.runtime_smoke_workflow import (
    RuntimeSmokeWorkflow as _WorkflowDirect,
)
from seahorse.container import (
    build_dispatch_write_batch_use_case,
    build_runtime_executor,
    build_runtime_smoke_workflow,
    build_starfish_writer_backend,
    build_starfish_writer_gateway,
    build_write_batch_use_case,
)
from seahorse.domain.runtime_contract import (
    DataSourceKind,
    DataSourceSpec,
    EndpointBinding,
    FieldBinding,
    ManualTriggerSpec,
    PeriodicScheduleSpec,
    ScheduleSpec,
    ServerBinding,
    WritePlan,
    WritePlanId,
    WriteTarget,
)
from seahorse.infrastructure.data_sources import InMemoryDataSourceRuntime
from seahorse.infrastructure.drivers import InMemoryStarfishWriterBackend


def _write_plan() -> WritePlan:
    """构造 dispatch 测试用 WritePlan。"""
    source = DataSourceSpec("src-1", DataSourceKind.SAMPLE, reference="sample-1")
    field = FieldBinding(
        field_id="field-1",
        target=WriteTarget("srv-1", "ep-1", "point-1", "value"),
        source_id=source.source_id,
    )
    return WritePlan(
        plan_id=WritePlanId("plan-smoke"),
        servers=(
            ServerBinding(
                server_id="srv-1",
                endpoints=(
                    EndpointBinding(endpoint_id="ep-1", protocol="OPC_UA", fields=(field,)),
                ),
            ),
        ),
        data_sources=(source,),
        schedule=ScheduleSpec.periodic(PeriodicScheduleSpec(period_ns=1)),
    )


def test_container_builds_runtime_smoke_workflow_with_full_chain() -> None:
    """container 默认装配的 workflow 串联 build/tick/dispatch 全链路。"""
    plan = _write_plan()
    workflow = build_runtime_smoke_workflow(
        runtime_id="rt-container-smoke",
        write_plan=plan,
        batch_builder=BuildWriteBatchUseCase(
            data_source_port=InMemoryDataSourceRuntime(samples={"sample-1": 5})
        ),
    )

    report = workflow.run(now_ns=0, ticks=1)

    assert isinstance(report, RuntimeSmokeReport)
    assert report.plan_id == plan.plan_id
    assert report.runtime_id == "rt-container-smoke"
    assert report.tick_count == 1
    assert report.generated_batch_count == 1
    assert report.dispatch_count == 1
    assert report.writer_history_count == 1


def test_runtime_smoke_workflow_records_writer_failures_and_history() -> None:
    """workflow 配置化失败会写入 failure_count 与 writer history。"""
    backend = InMemoryStarfishWriterBackend(
        fail_server_ids=frozenset({"srv-1"}),
    )
    writer = StarfishWriterGateway(backend=backend)
    dispatch = DispatchWriteBatchUseCase(writer=writer)
    builder = BuildWriteBatchUseCase(
        data_source_port=InMemoryDataSourceRuntime(samples={"sample-1": 9})
    )
    executor = RuntimeExecutor(
        context=RuntimeContext.from_write_plan(
            runtime_id="rt-smoke-fail", write_plan=_write_plan()
        ),
        batch_builder=builder,
        dispatch_use_case=dispatch,
    )
    workflow = RuntimeSmokeWorkflow(
        runtime_id="rt-smoke-fail",
        executor=executor,
        batch_builder=builder,
        dispatch_use_case=dispatch,
        writer=writer,
        write_plan=_write_plan(),
    )

    report = workflow.run(now_ns=0, ticks=1)

    assert report.success_count == 0
    assert report.failure_count == 1
    assert report.dispatch_status == "partial_failure"
    assert report.writer_history_count == 1
    assert "configured writer failure" in report.last_error


def test_runtime_smoke_workflow_handles_zero_due_ticks() -> None:
    """未触发 manual schedule 时 executor 不生成 batch，report 全为 0。"""
    plan = WritePlan(
        plan_id=WritePlanId("plan-zero-tick"),
        servers=(
            ServerBinding(
                server_id="srv-1",
                endpoints=(
                    EndpointBinding(
                        endpoint_id="ep-1",
                        protocol="OPC_UA",
                        fields=(
                            FieldBinding(
                                field_id="field-1",
                                target=WriteTarget("srv-1", "ep-1", "point-1"),
                                source_id="src-1",
                            ),
                        ),
                    ),
                ),
            ),
        ),
        data_sources=(DataSourceSpec("src-1", DataSourceKind.SAMPLE, reference="sample-1"),),
        schedule=ScheduleSpec.manual(ManualTriggerSpec(trigger_name="never")),
    )
    workflow = build_runtime_smoke_workflow(
        runtime_id="rt-zero-tick",
        write_plan=plan,
        batch_builder=BuildWriteBatchUseCase(
            data_source_port=InMemoryDataSourceRuntime(samples={"sample-1": 1})
        ),
    )

    report = workflow.run(now_ns=0, ticks=3)

    assert report.tick_count == 0
    assert report.generated_batch_count == 0
    assert report.dispatch_count == 0
    assert report.writer_history_count == 0
    assert report.last_error == ""


def test_runtime_smoke_workflow_returns_diagnostic_view_with_required_fields() -> None:
    """RuntimeSmokeReport.to_diagnostic_view 暴露全部稳定字段。"""
    workflow = build_runtime_smoke_workflow(
        runtime_id="rt-view",
        write_plan=_write_plan(),
        batch_builder=BuildWriteBatchUseCase(
            data_source_port=InMemoryDataSourceRuntime(samples={"sample-1": 2})
        ),
    )

    view = workflow.run(now_ns=0, ticks=1).to_diagnostic_view()

    expected_keys = {
        "plan_id",
        "runtime_id",
        "tick_count",
        "generated_batch_count",
        "dispatch_count",
        "success_count",
        "failure_count",
        "last_error",
        "writer_history_count",
        "dispatch_status",
    }
    assert expected_keys.issubset(view.keys())


def test_facade_run_runtime_smoke_uses_container_default_assembly() -> None:
    """facade 在未传入 workflow 时由 container 装配并返回稳定 report。"""
    facade = SeahorseFacade()
    plan = _write_plan()
    workflow = build_runtime_smoke_workflow(
        runtime_id="facade-smoke",
        write_plan=plan,
        batch_builder=BuildWriteBatchUseCase(
            data_source_port=InMemoryDataSourceRuntime(samples={"sample-1": 7})
        ),
    )

    report = facade.run_runtime_smoke(plan, ticks=1, workflow=workflow)

    assert report.plan_id == plan.plan_id
    assert report.runtime_id == "facade-smoke"
    assert report.tick_count == 1
    assert report.writer_history_count == 1
    assert isinstance(report, RuntimeSmokeReport)


def test_facade_run_runtime_smoke_accepts_injected_workflow() -> None:
    """facade 在传入 workflow 时直接复用，不重新装配。"""
    facade = SeahorseFacade()
    plan = _write_plan()
    workflow = build_runtime_smoke_workflow(
        runtime_id="facade-injected",
        write_plan=plan,
        batch_builder=BuildWriteBatchUseCase(
            data_source_port=InMemoryDataSourceRuntime(samples={"sample-1": 4})
        ),
    )

    report = facade.run_runtime_smoke(plan, ticks=2, workflow=workflow)

    assert report.runtime_id == "facade-injected"
    assert report.tick_count == 2
    assert report.generated_batch_count == 2


def test_runtime_executor_tick_still_only_generates_when_dispatch_missing() -> None:
    """默认 ``tick()`` 在未配置 dispatch 时只生成 batch，行为不变。"""
    backend = InMemoryStarfishWriterBackend()
    builder = BuildWriteBatchUseCase(
        data_source_port=InMemoryDataSourceRuntime(samples={"sample-1": 1})
    )
    executor = build_runtime_executor(
        runtime_id="rt-tick-only",
        write_plan=_write_plan(),
        batch_builder=builder,
    )
    executor.start(now_ns=0)

    batch = executor.tick(now_ns=0)
    _ = backend  # 避免 backend 局部未使用提示；backend 仅用于校验 history 隔离

    assert batch is not None
    assert backend.history == []
    assert executor.diagnostics.generated_batch_count == 1
    assert executor.diagnostics.last_dispatch_status == ""


def test_container_helpers_share_default_backend_via_writer_gateway() -> None:
    """container 暴露的 writer gateway 与 backend 共享同一 history。"""
    backend = build_starfish_writer_backend(fail_field_ids=frozenset({"quality"}))
    writer = build_starfish_writer_gateway(backend)
    use_case = build_dispatch_write_batch_use_case(writer)
    builder = build_write_batch_use_case(
        InMemoryDataSourceRuntime(samples={"sample-1": 1})
    )
    executor = build_runtime_executor(
        runtime_id="rt-share-history",
        write_plan=_write_plan(),
        batch_builder=builder,
        dispatch_use_case=use_case,
    )
    executor.start(now_ns=0)
    executor.tick_and_dispatch(now_ns=0)

    assert len(backend.history) == 1
    assert len(writer.history) == 1
    assert writer.history[0].batch_id == backend.history[0].batch_id


def test_runtime_smoke_workflow_alias_is_canonical_class() -> None:
    """``RuntimeSmokeWorkflow`` 同时通过 atomic.__init__ 与子模块暴露同一类。"""
    from seahorse.application.use_cases.atomic import RuntimeSmokeWorkflow as _FromInit

    assert _FromInit is RuntimeSmokeWorkflow
    assert _FromInit is _WorkflowDirect