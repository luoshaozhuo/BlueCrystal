"""Seahorse StarfishWriter batch dispatch 最小实现测试。

本文件只验证应用端口、gateway、内存 backend 与 RuntimeExecutor 的同步
内存分发语义，不连接真实 writer，也不证明高频运行性能。
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from seahorse.adapters.gateways import StarfishWriterGateway
from seahorse.application.exceptions import SchedulerRuntimeError
from seahorse.application.ports.starfish_writer_port import StarfishWriterPort
from seahorse.application.runtime import RuntimeContext, RuntimeExecutor
from seahorse.application.use_cases.atomic import BuildWriteBatchUseCase, DispatchWriteBatchUseCase
from seahorse.container import (
    build_dispatch_write_batch_use_case,
    build_runtime_executor,
    build_starfish_writer_backend,
    build_starfish_writer_gateway,
)
from seahorse.domain.runtime_contract import (
    DataSourceKind,
    DataSourceSpec,
    EndpointBinding,
    FieldBinding,
    PeriodicScheduleSpec,
    ScheduleSpec,
    ServerBinding,
    WriteBatch,
    WriteBatchResult,
    WriteItem,
    WritePlan,
    WritePlanId,
    WriteTarget,
)
from seahorse.infrastructure.data_sources import InMemoryDataSourceRuntime
from seahorse.infrastructure.drivers import InMemoryStarfishWriterBackend


def _batch(batch_id: str = "batch-1") -> WriteBatch:
    """构造两个 item 的 WriteBatch。"""
    return WriteBatch(
        plan_id=WritePlanId("plan-writer"),
        batch_id=batch_id,
        items=(
            WriteItem(
                target=WriteTarget("srv-1", "ep-1", "point-1", "value"),
                value=1,
                source_id="src-1",
                timestamp_ns=100,
            ),
            WriteItem(
                target=WriteTarget("srv-2", "ep-2", "point-2", "quality"),
                value=True,
                source_id="src-2",
                timestamp_ns=100,
            ),
        ),
    )


def _write_plan() -> WritePlan:
    """构造 RuntimeExecutor dispatch 测试用 WritePlan。"""
    source = DataSourceSpec("src-1", DataSourceKind.SAMPLE, reference="sample-1")
    field = FieldBinding(
        field_id="field-1",
        target=WriteTarget("srv-1", "ep-1", "point-1", "value"),
        source_id=source.source_id,
    )
    return WritePlan(
        plan_id=WritePlanId("plan-runtime-writer"),
        servers=(
            ServerBinding(
                server_id="srv-1",
                endpoints=(
                    EndpointBinding(endpoint_id="ep-1", protocol="OPC_UA", fields=(field,)),
                ),
            ),
        ),
        data_sources=(source,),
        schedule=ScheduleSpec.periodic(PeriodicScheduleSpec(period_ns=10)),
    )


def test_dispatch_write_batch_success_records_backend_history() -> None:
    """dispatch use case 经 gateway 调用内存 backend，并记录 batch history。"""
    backend = InMemoryStarfishWriterBackend()
    use_case = DispatchWriteBatchUseCase(writer=StarfishWriterGateway(backend=backend))
    batch = _batch()

    result = use_case.execute(batch)

    assert result == WriteBatchResult(batch_id="batch-1", accepted_count=2)
    assert backend.history == [batch]


def test_dispatch_write_batch_returns_partial_failures() -> None:
    """backend 可按 endpoint_id 和 point_id 配置部分失败。"""
    backend = InMemoryStarfishWriterBackend(
        fail_endpoint_ids=frozenset({"ep-1"}),
        fail_point_ids=frozenset({"point-2"}),
    )
    use_case = DispatchWriteBatchUseCase(writer=StarfishWriterGateway(backend=backend))

    result = use_case.execute(_batch())

    assert result.success is False
    assert result.accepted_count == 0
    assert [failure.target.endpoint_id for failure in result.failures] == ["ep-1", "ep-2"]
    assert all(failure.retryable for failure in result.failures)


def test_dispatch_write_batch_converges_writer_exception_to_failure_result() -> None:
    """writer 异常被应用用例收敛为 retryable failure result。"""
    backend = InMemoryStarfishWriterBackend(exception_batch_ids=frozenset({"boom"}))
    use_case = DispatchWriteBatchUseCase(writer=StarfishWriterGateway(backend=backend))

    result = use_case.execute(_batch("boom"))

    assert result.batch_id == "boom"
    assert result.accepted_count == 0
    assert len(result.failures) == 2
    assert all("writer dispatch failed" in failure.reason for failure in result.failures)
    assert all(failure.retryable for failure in result.failures)
    assert backend.history == []


@dataclass(slots=True)
class _InjectedBackend:
    """gateway 注入测试用 backend。"""

    result: WriteBatchResult
    seen_batches: list[WriteBatch]

    def dispatch_batch(self, batch: WriteBatch) -> WriteBatchResult:
        """记录被 gateway 委托的 batch。"""
        self.seen_batches.append(batch)
        return self.result


def test_starfish_writer_gateway_uses_injected_backend() -> None:
    """gateway 不创建 backend，只委托给构造时注入的对象。"""
    batch = _batch()
    backend = _InjectedBackend(
        result=WriteBatchResult(batch_id=batch.batch_id, accepted_count=2),
        seen_batches=[],
    )
    gateway = StarfishWriterGateway(backend=backend)

    result = gateway.write_batch(batch)

    assert result.accepted_count == 2
    assert backend.seen_batches == [batch]


def test_runtime_executor_tick_and_dispatch_updates_diagnostics() -> None:
    """RuntimeExecutor 可选 dispatch 路径记录 writer 诊断字段。"""
    backend = InMemoryStarfishWriterBackend(fail_server_ids=frozenset({"srv-1"}))
    executor = RuntimeExecutor(
        context=RuntimeContext.from_write_plan(runtime_id="rt-writer", write_plan=_write_plan()),
        batch_builder=BuildWriteBatchUseCase(
            data_source_port=InMemoryDataSourceRuntime(samples={"sample-1": 42})
        ),
        dispatch_use_case=DispatchWriteBatchUseCase(
            writer=StarfishWriterGateway(backend=backend)
        ),
    )
    executor.start(now_ns=0)

    result = executor.tick_and_dispatch(now_ns=0)

    assert result is not None
    assert result.success is False
    assert executor.diagnostics.last_dispatch_status == "partial_failure"
    assert executor.diagnostics.last_write_success_count == 0
    assert executor.diagnostics.last_write_failure_count == 1
    assert "configured writer failure" in executor.diagnostics.last_writer_error
    assert len(backend.history) == 1


def test_runtime_executor_requires_dispatch_use_case_for_dispatch_path() -> None:
    """tick_and_dispatch 未配置 dispatch_use_case 时给出稳定错误。"""
    executor = RuntimeExecutor(
        context=RuntimeContext.from_write_plan(runtime_id="rt-no-writer", write_plan=_write_plan()),
        batch_builder=BuildWriteBatchUseCase(
            data_source_port=InMemoryDataSourceRuntime(samples={"sample-1": 42})
        ),
    )
    executor.start(now_ns=0)

    with pytest.raises(SchedulerRuntimeError, match="dispatch_use_case"):
        executor.tick_and_dispatch(now_ns=0)

    assert executor.diagnostics.last_dispatch_status == "not_configured"


def test_container_wires_default_writer_dispatch_components() -> None:
    """container 默认装配内存 backend、gateway、dispatch use case 和 executor。"""
    backend = build_starfish_writer_backend(fail_field_ids=frozenset({"value"}))
    writer = build_starfish_writer_gateway(backend)
    use_case = build_dispatch_write_batch_use_case(writer)
    executor = build_runtime_executor(
        runtime_id="rt-container-writer",
        write_plan=_write_plan(),
        batch_builder=BuildWriteBatchUseCase(
            data_source_port=InMemoryDataSourceRuntime(samples={"sample-1": 42})
        ),
        dispatch_use_case=use_case,
    )
    executor.start(now_ns=0)

    result = executor.tick_and_dispatch(now_ns=0)

    assert isinstance(backend, InMemoryStarfishWriterBackend)
    assert result is not None
    assert result.success is False
    assert backend.history


def test_starfish_writer_port_has_no_write_one_hot_path() -> None:
    """StarfishWriterPort 不暴露逐点写入接口。"""
    assert not hasattr(StarfishWriterPort, "write_one")
