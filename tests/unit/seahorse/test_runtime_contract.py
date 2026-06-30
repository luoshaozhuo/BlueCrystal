"""Seahorse runtime contract 单元测试。

验证对象：Round 2 新增的纯领域模型、runtime skeleton、application ports
与 atomic use cases。
测试阶段：P1/P2，本文件只验证内存契约和静态接口形状。
不能证明：真实 50Hz 调度性能、真实 Starfish writer、真实 Whale DB 查询、
真实 replay 文件读取或事件/手动触发执行器可用。
"""

from __future__ import annotations

import pytest

from seahorse.application.ports.scheduler_port import SchedulerPort
from seahorse.application.ports.starfish_writer_port import StarfishWriterPort
from seahorse.application.runtime import (
    RuntimeContext,
    RuntimeGraph,
    RuntimeNodeKind,
    RuntimePhase,
    RuntimeSnapshot,
    RuntimeState,
)
from seahorse.application.use_cases.atomic import (
    BuildWritePlanUseCase,
    ValidateWritePlanUseCase,
    update_runtime_period,
)
from seahorse.domain.runtime_contract import (
    DataSourceKind,
    DataSourceSpec,
    DataSourceValueKind,
    EndpointBinding,
    EventTriggerSpec,
    FieldBinding,
    ManualTriggerSpec,
    PeriodicScheduleSpec,
    RandomTimeScheduleSpec,
    ScheduleKind,
    ScheduleSpec,
    ServerBinding,
    WriteBatch,
    WriteBatchResult,
    WriteFailure,
    WriteItem,
    WritePlan,
    WritePlanId,
    WriteTarget,
    validate_write_plan,
)


def _sample_plan() -> WritePlan:
    """构造一个最小有效 WritePlan。"""
    target = WriteTarget(
        server_id="srv-1",
        endpoint_id="ep-1",
        point_id="pt-1",
        field_name="value",
    )
    field = FieldBinding(field_id="field-1", target=target, source_id="src-random")
    endpoint = EndpointBinding(endpoint_id="ep-1", protocol="OPC_UA", fields=(field,))
    server = ServerBinding(server_id="srv-1", endpoints=(endpoint,))
    return WritePlan(
        plan_id=WritePlanId("plan-1"),
        servers=(server,),
        data_sources=(
            DataSourceSpec(
                source_id="src-random",
                kind=DataSourceKind.RANDOM,
                seed=42,
            ),
        ),
        schedule=ScheduleSpec.periodic(PeriodicScheduleSpec.from_period_ms(20)),
    )


def test_schedule_spec_supports_required_trigger_kinds() -> None:
    """ScheduleSpec 能表达周期、随机时刻、手动触发和事件触发。"""
    periodic = ScheduleSpec.periodic(PeriodicScheduleSpec.from_period_ms(20))
    random_time = ScheduleSpec.random_time(
        RandomTimeScheduleSpec(window_start_ns=100, window_end_ns=200, seed=1)
    )
    manual = ScheduleSpec.manual(ManualTriggerSpec(trigger_name="operator"))
    event = ScheduleSpec.event(EventTriggerSpec(event_type="alarm"))

    assert periodic.kind is ScheduleKind.PERIODIC
    assert random_time.kind is ScheduleKind.RANDOM_TIME
    assert manual.kind is ScheduleKind.MANUAL_TRIGGER
    assert event.kind is ScheduleKind.EVENT_TRIGGER


def test_periodic_schedule_expresses_50hz_config_without_runtime_claim() -> None:
    """50Hz 只作为 period<=20ms 的配置判断，不代表性能保证。"""
    exactly_50hz = PeriodicScheduleSpec.from_period_ms(20)
    slower = PeriodicScheduleSpec.from_period_ms(25)

    assert exactly_50hz.period_ns == 20_000_000
    assert exactly_50hz.supports_50hz_target()
    assert not slower.supports_50hz_target()


def test_data_source_spec_supports_four_source_kinds() -> None:
    """DataSourceSpec 能表达 random、sample、function、replay 四类来源。"""
    kinds = {
        DataSourceSpec("random-src", DataSourceKind.RANDOM).kind,
        DataSourceSpec("sample-src", DataSourceKind.SAMPLE).kind,
        DataSourceSpec("function-src", DataSourceKind.FUNCTION, reference="curve_a").kind,
        DataSourceSpec("replay-src", DataSourceKind.REPLAY, reference="logical_replay").kind,
    }

    assert kinds == {
        DataSourceKind.RANDOM,
        DataSourceKind.SAMPLE,
        DataSourceKind.FUNCTION,
        DataSourceKind.REPLAY,
    }


def test_data_source_spec_keeps_numeric_value_type_default() -> None:
    """DataSourceSpec 默认 numeric，且能显式表达 bool/string/nominal。"""
    assert DataSourceSpec("src-default", DataSourceKind.RANDOM).value_type is (
        DataSourceValueKind.NUMERIC
    )
    assert DataSourceSpec(
        "src-bool",
        DataSourceKind.RANDOM,
        value_type=DataSourceValueKind.BOOL,
    ).value_type is DataSourceValueKind.BOOL
    assert DataSourceSpec(
        "src-string",
        DataSourceKind.RANDOM,
        value_type=DataSourceValueKind.STRING,
    ).value_type is DataSourceValueKind.STRING
    assert DataSourceSpec(
        "src-nominal",
        DataSourceKind.RANDOM,
        value_type=DataSourceValueKind.NOMINAL,
    ).value_type is DataSourceValueKind.NOMINAL


def test_write_plan_validation_detects_unknown_source() -> None:
    """WritePlan 校验能发现字段引用未知数据源。"""
    plan = _sample_plan()
    bad_field = FieldBinding(
        field_id="field-bad",
        target=WriteTarget("srv-1", "ep-1", "pt-2"),
        source_id="missing",
    )
    bad_endpoint = EndpointBinding(endpoint_id="ep-1", protocol="OPC_UA", fields=(bad_field,))
    bad_plan = WritePlan(
        plan_id=plan.plan_id,
        servers=(ServerBinding(server_id="srv-1", endpoints=(bad_endpoint,)),),
        data_sources=plan.data_sources,
        schedule=plan.schedule,
    )

    errors = validate_write_plan(bad_plan)
    assert any("未知 source_id" in error for error in errors)


def test_write_batch_result_models_failures() -> None:
    """WriteBatch/WriteBatchResult 表达 batch 写入和失败明细。"""
    plan = _sample_plan()
    item = WriteItem(
        target=plan.field_bindings()[0].target,
        value=12.5,
        source_id="src-random",
        timestamp_ns=123,
    )
    batch = WriteBatch(plan_id=plan.plan_id, batch_id="batch-1", items=(item,))
    failure = WriteFailure(target=item.target, reason="writer unavailable", retryable=True)
    result = WriteBatchResult(batch_id=batch.batch_id, accepted_count=0, failures=(failure,))

    assert batch.items == (item,)
    assert not result.success
    assert result.failures[0].retryable


def test_runtime_state_transitions_are_pure_and_guarded() -> None:
    """RuntimeState 支持 CREATED/RUNNING/PAUSED/STOPPED/ERROR 的纯转移。"""
    created = RuntimeState()
    running = created.transition_to(RuntimePhase.RUNNING, reason="start")
    paused = running.transition_to(RuntimePhase.PAUSED, reason="manual pause")
    resumed = paused.transition_to(RuntimePhase.RUNNING, reason="resume")
    stopped = resumed.transition_to(RuntimePhase.STOPPED, reason="done")

    assert created.phase is RuntimePhase.CREATED
    assert stopped.phase is RuntimePhase.STOPPED
    with pytest.raises(ValueError, match="非法 runtime 状态转移"):
        stopped.transition_to(RuntimePhase.RUNNING)


def test_runtime_graph_and_snapshot_do_not_expose_infrastructure_objects() -> None:
    """RuntimeGraph/Snapshot 只输出稳定诊断数据。"""
    plan = _sample_plan()
    graph = RuntimeGraph.from_write_plan(plan)
    context = RuntimeContext.from_write_plan(runtime_id="rt-1", write_plan=plan)
    snapshot = RuntimeSnapshot(runtime_id=context.runtime_id, state=context.state, graph=graph)

    node_types = {node.node_type for node in graph.nodes}
    diagnostic = snapshot.to_diagnostic_view()

    assert RuntimeNodeKind.PLAN in node_types
    assert RuntimeNodeKind.DATA_SOURCE in node_types
    assert RuntimeNodeKind.FIELD in node_types
    assert diagnostic["runtime_id"] == "rt-1"
    assert diagnostic["node_count"] == len(graph.nodes)
    assert "node_ids" in diagnostic


class _FakeMetadataPort:
    """只返回内存 server binding 的 WhaleMetadataPort 测试替身。"""

    def __init__(self, plan: WritePlan) -> None:
        """保存测试计划。"""
        self._plan = plan

    def load_servers(self, plan_id: WritePlanId) -> tuple[ServerBinding, ...]:
        """返回计划内 server 集合。"""
        assert plan_id == self._plan.plan_id
        return self._plan.servers

    def load_endpoints(self, server_id: str) -> tuple[EndpointBinding, ...]:
        """返回指定 server 的 endpoint 集合。"""
        return self._plan.servers[0].endpoints if server_id == "srv-1" else ()

    def load_fields(self, endpoint_id: str) -> tuple[FieldBinding, ...]:
        """返回指定 endpoint 的 field 集合。"""
        return self._plan.servers[0].endpoints[0].fields if endpoint_id == "ep-1" else ()


def test_build_and_validate_write_plan_use_cases_are_port_based() -> None:
    """atomic use cases 只依赖端口和纯模型。"""
    plan = _sample_plan()
    builder = BuildWritePlanUseCase(metadata_port=_FakeMetadataPort(plan))
    built = builder.execute(
        plan_id=plan.plan_id,
        data_sources=plan.data_sources,
        schedule=plan.schedule,
    )
    result = ValidateWritePlanUseCase().execute(built)

    assert built == plan
    assert result.is_valid


class _FakeScheduler:
    """只记录 period update 的 SchedulerPort 测试替身。"""

    def __init__(self) -> None:
        """初始化记录容器。"""
        self.updated: tuple[WritePlanId, int] | None = None

    def register_schedule(self, plan_id: WritePlanId, schedule: ScheduleSpec) -> None:
        """测试不需要注册调度。"""
        if isinstance(schedule.detail, PeriodicScheduleSpec):
            self.updated = (plan_id, schedule.detail.period_ns)

    def update_period(self, plan_id: WritePlanId, period_ns: int) -> ScheduleSpec:
        """记录周期更新并返回新契约。"""
        self.updated = (plan_id, period_ns)
        return ScheduleSpec.periodic(PeriodicScheduleSpec(period_ns=period_ns))


def test_update_runtime_period_uses_contract_without_sleeping() -> None:
    """周期更新用例只返回配置契约，不执行真实调度。"""
    scheduler = _FakeScheduler()
    plan_id = WritePlanId("plan-1")

    schedule = update_runtime_period(plan_id=plan_id, period_ns=10_000_000, scheduler=scheduler)

    assert schedule.kind is ScheduleKind.PERIODIC
    assert scheduler.updated == (plan_id, 10_000_000)


def test_starfish_writer_port_exposes_batch_not_write_one() -> None:
    """StarfishWriterPort 暴露 batch 接口，不提供 write_one 热路径。"""
    assert hasattr(StarfishWriterPort, "write_batch")
    assert not hasattr(StarfishWriterPort, "write_one")
    assert hasattr(SchedulerPort, "update_period")
