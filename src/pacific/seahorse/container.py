"""Seahorse composition root。

本模块只负责默认依赖装配，不包含 Whale ORM 到 WritePlan 的映射规则。
真实 repository、driver backend、scheduler 和 telemetry 必须在这里或
infrastructure factory 中创建，再注入用例。
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from pacific.seahorse.api.seahorse_facade import SeahorseFacade
from pacific.seahorse.adapters.gateways import StarfishWriterGateway
from pacific.seahorse.application.runtime import RuntimeContext, RuntimeExecutor
from pacific.seahorse.application.ports.clock_port import ClockPort
from pacific.seahorse.application.ports.data_source_port import DataSourcePort
from pacific.seahorse.application.ports.starfish_writer_port import StarfishWriterPort
from pacific.seahorse.application.use_cases.atomic import BuildWriteBatchUseCase, BuildWritePlanUseCase
from pacific.seahorse.application.use_cases.atomic import DispatchWriteBatchUseCase
from pacific.seahorse.application.use_cases.atomic import RuntimeSmokeWorkflow
from pacific.seahorse.domain.runtime_contract import PointFieldValue, WritePlan
from pacific.seahorse.infrastructure.data_sources import InMemoryDataSourceRuntime
from pacific.seahorse.infrastructure.drivers import InMemoryStarfishWriterBackend
from pacific.seahorse.infrastructure.repositories import WhaleMetadataRepository
from pacific.seahorse.infrastructure.schedulers import DeterministicScheduler, MonotonicClock

SessionScopeFactory = Callable[[], AbstractContextManager[Session]]


def build_seahorse_facade() -> SeahorseFacade:
    """构建 Seahorse facade。

    Returns:
        不含外部连接的 SeahorseFacade 实例。
    """
    return SeahorseFacade()


def build_write_plan_use_case(
    session_factory: SessionScopeFactory | None = None,
) -> BuildWritePlanUseCase:
    """构建默认 WritePlan 读取用例。

    Args:
        session_factory: 可选 Whale SQLAlchemy session scope 工厂；未传入时
            repository 使用 Whale shared persistence 的默认 `session_scope`。

    Returns:
        已注入 Whale metadata repository 的 BuildWritePlanUseCase。
    """
    return BuildWritePlanUseCase(
        metadata_port=WhaleMetadataRepository(session_factory=session_factory)
    )


def build_data_source_runtime(
    *,
    samples: dict[str, PointFieldValue] | None = None,
    replay_rows: dict[str, tuple[PointFieldValue, ...]] | None = None,
) -> DataSourcePort:
    """构建默认内存 DataSource runtime。

    Args:
        samples: 可选 sample 数据源内存映射。
        replay_rows: 可选 replay 数据源内存 rows 映射。

    Returns:
        不连接外部系统的 DataSourcePort 实例。
    """
    return InMemoryDataSourceRuntime(
        samples=samples or {},
        replay_rows=replay_rows or {},
    )


def build_write_batch_use_case(
    data_source_port: DataSourcePort | None = None,
) -> BuildWriteBatchUseCase:
    """构建默认 WriteBatch 生成用例。

    Args:
        data_source_port: 可选数据源端口；未传入时使用内存 runtime adapter。

    Returns:
        已注入 DataSourcePort 的 BuildWriteBatchUseCase。
    """
    return BuildWriteBatchUseCase(
        data_source_port=data_source_port or build_data_source_runtime()
    )


def build_starfish_writer_backend(
    *,
    fail_server_ids: frozenset[str] = frozenset(),
    fail_endpoint_ids: frozenset[str] = frozenset(),
    fail_field_ids: frozenset[str] = frozenset(),
    fail_point_ids: frozenset[str] = frozenset(),
    exception_batch_ids: frozenset[str] = frozenset(),
) -> InMemoryStarfishWriterBackend:
    """构建默认内存 Starfish writer backend。

    Args:
        fail_server_ids: 需要配置为失败的 server_id 集合。
        fail_endpoint_ids: 需要配置为失败的 endpoint_id 集合。
        fail_field_ids: 需要配置为失败的 field 名或 stable target key 集合。
        fail_point_ids: 需要配置为失败的 point_id 集合。
        exception_batch_ids: 需要模拟 backend 异常的 batch_id 集合。

    Returns:
        只记录内存历史的 writer backend。
    """
    return InMemoryStarfishWriterBackend(
        fail_server_ids=fail_server_ids,
        fail_endpoint_ids=fail_endpoint_ids,
        fail_field_ids=fail_field_ids,
        fail_point_ids=fail_point_ids,
        exception_batch_ids=exception_batch_ids,
    )


def build_starfish_writer_gateway(
    backend: InMemoryStarfishWriterBackend | None = None,
) -> StarfishWriterPort:
    """构建默认 StarfishWriterPort gateway。

    Args:
        backend: 可选内存 backend；未传入时创建新的内存 backend。

    Returns:
        已注入 backend 的 StarfishWriterPort。
    """
    return StarfishWriterGateway(backend=backend or build_starfish_writer_backend())


def build_dispatch_write_batch_use_case(
    writer: StarfishWriterPort | None = None,
) -> DispatchWriteBatchUseCase:
    """构建默认 WriteBatch dispatch 用例。

    Args:
        writer: 可选 writer 端口；未传入时使用内存 gateway。

    Returns:
        已注入 writer 的 DispatchWriteBatchUseCase。
    """
    return DispatchWriteBatchUseCase(writer=writer or build_starfish_writer_gateway())


def build_runtime_executor(
    *,
    runtime_id: str,
    write_plan: WritePlan,
    batch_builder: BuildWriteBatchUseCase | None = None,
    dispatch_use_case: DispatchWriteBatchUseCase | None = None,
) -> RuntimeExecutor:
    """构建默认内存 RuntimeExecutor。

    Args:
        runtime_id: 运行实例标识。
        write_plan: 已构建的内存 WritePlan。
        batch_builder: 可选 WriteBatch 生成用例；未传入时使用默认内存 data source。
        dispatch_use_case: 可选 WriteBatch 分发用例；未传入时 executor 只生成 batch，
            仍可通过 ``tick_and_dispatch`` 显式驱动 dispatch；不传则只生成 batch。

    Returns:
        默认装配的 RuntimeExecutor，包含 batch_builder 和可空 dispatch_use_case。
    """
    return RuntimeExecutor(
        context=RuntimeContext.from_write_plan(runtime_id=runtime_id, write_plan=write_plan),
        batch_builder=batch_builder or build_write_batch_use_case(),
        dispatch_use_case=dispatch_use_case,
    )


def build_runtime_smoke_workflow(
    *,
    runtime_id: str,
    write_plan: WritePlan,
    batch_builder: BuildWriteBatchUseCase | None = None,
    dispatch_use_case: DispatchWriteBatchUseCase | None = None,
    writer: StarfishWriterPort | None = None,
) -> RuntimeSmokeWorkflow:
    """构建默认内存 RuntimeSmokeWorkflow。

    该 workflow 不接真实 Starfish runtime，也不启动 scheduler；它通过
    container 默认装配串联 build batch / tick / dispatch 全链路，供
    facade、CLI 或脚本验证最小可用性。

    Args:
        runtime_id: smoke 运行实例标识。
        write_plan: 已构建的内存 WritePlan。
        batch_builder: 可选 WriteBatch 生成用例。
        dispatch_use_case: 可选 WriteBatch 分发用例。
        writer: 可选 StarfishWriterPort 实现；未传入时使用内存 gateway。

    Returns:
        已注入 executor、batch_builder、dispatch_use_case 与 writer 的
        :class:`RuntimeSmokeWorkflow`。
    """
    resolved_writer = writer or build_starfish_writer_gateway()
    resolved_dispatch = dispatch_use_case or DispatchWriteBatchUseCase(writer=resolved_writer)
    resolved_builder = batch_builder or build_write_batch_use_case()
    executor = RuntimeExecutor(
        context=RuntimeContext.from_write_plan(runtime_id=runtime_id, write_plan=write_plan),
        batch_builder=resolved_builder,
        dispatch_use_case=resolved_dispatch,
    )
    return RuntimeSmokeWorkflow(
        runtime_id=runtime_id,
        executor=executor,
        batch_builder=resolved_builder,
        dispatch_use_case=resolved_dispatch,
        writer=resolved_writer,
        write_plan=write_plan,
    )


def build_deterministic_scheduler(
    clock: ClockPort | None = None,
) -> DeterministicScheduler:
    """构建同步 step scheduler helper。

    Args:
        clock: 可选 ClockPort 实现；默认使用 MonotonicClock。

    Returns:
        不 sleep、不启动线程的 DeterministicScheduler。
    """
    return DeterministicScheduler(clock=clock or MonotonicClock())
