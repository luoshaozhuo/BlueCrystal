"""Seahorse DataSource runtime 最小实现单元测试。

验证对象：内存 DataSourcePort adapter 与 BuildWriteBatchUseCase。
测试阶段：P1/P2。本文件只验证基于 WritePlan/DataSourceSpec 的内存取值和
WriteBatch 组装，不连接 Starfish、不启动 scheduler、不查询 Whale DB，也
不证明真实 50Hz runtime 或真实 replay 文件 streaming 可用。
"""

from __future__ import annotations

import pytest

from seahorse.application.exceptions import DataSourceRuntimeError
from seahorse.application.ports.data_source_port import DataSourcePort
from seahorse.application.use_cases.atomic import BuildWriteBatchUseCase
from seahorse.container import build_data_source_runtime, build_write_batch_use_case
from seahorse.domain.runtime_contract import (
    DataSourceKind,
    DataSourceSpec,
    DataSourceValueKind,
    EndpointBinding,
    FieldBinding,
    PeriodicScheduleSpec,
    ScheduleSpec,
    ServerBinding,
    WritePlan,
    WritePlanId,
    WriteTarget,
)
from seahorse.infrastructure.data_sources import InMemoryDataSourceRuntime


def _plan_with_sources(data_sources: tuple[DataSourceSpec, ...]) -> WritePlan:
    """构造按 source 顺序绑定字段的 WritePlan。"""
    fields = tuple(
        FieldBinding(
            field_id=f"field-{index}",
            target=WriteTarget(
                server_id="srv-1",
                endpoint_id="ep-1",
                point_id=f"point-{index}",
            ),
            source_id=source.source_id,
        )
        for index, source in enumerate(data_sources, start=1)
    )
    return WritePlan(
        plan_id=WritePlanId("plan-datasource"),
        servers=(
            ServerBinding(
                server_id="srv-1",
                endpoints=(
                    EndpointBinding(
                        endpoint_id="ep-1",
                        protocol="OPC_UA",
                        fields=fields,
                    ),
                ),
            ),
        ),
        data_sources=data_sources,
        schedule=ScheduleSpec.periodic(PeriodicScheduleSpec.from_period_ms(1000)),
    )


def test_random_datasource_generates_stable_values_for_supported_value_types() -> None:
    """random 数据源按 value_type 生成稳定 numeric/bool/string/nominal 值。"""
    runtime = InMemoryDataSourceRuntime()
    specs = (
        DataSourceSpec("random-num", DataSourceKind.RANDOM, seed=1),
        DataSourceSpec("random-bool", DataSourceKind.RANDOM, seed=1, value_type=DataSourceValueKind.BOOL),
        DataSourceSpec(
            "random-string",
            DataSourceKind.RANDOM,
            seed=1,
            value_type=DataSourceValueKind.STRING,
        ),
        DataSourceSpec(
            "random-nominal",
            DataSourceKind.RANDOM,
            reference="nominal:OPEN,CLOSED",
            seed=1,
            value_type=DataSourceValueKind.NOMINAL,
        ),
    )

    first = runtime.resolve_batch(specs, timestamp_ns=1_000, tick_index=3)
    second = runtime.resolve_batch(specs, timestamp_ns=1_000, tick_index=3)

    assert first == second
    assert isinstance(first["random-num"], float)
    assert isinstance(first["random-bool"], bool)
    assert isinstance(first["random-string"], str)
    assert first["random-nominal"] in {"OPEN", "CLOSED"}


def test_sample_function_and_replay_datasources_resolve_from_memory() -> None:
    """sample/function/replay 均只使用内存配置取值。"""
    runtime = InMemoryDataSourceRuntime(
        samples={"sample-ref": 12.5},
        replay_rows={"replay-ref": (100, 101, 102)},
    )
    specs = (
        DataSourceSpec("sample-src", DataSourceKind.SAMPLE, reference="sample-ref"),
        DataSourceSpec("function-src", DataSourceKind.FUNCTION, reference="linear:2:10"),
        DataSourceSpec("replay-src", DataSourceKind.REPLAY, reference="replay-ref"),
    )

    values = runtime.resolve_batch(specs, timestamp_ns=5_000_000_000, tick_index=2)

    assert values == {
        "sample-src": 12.5,
        "function-src": 14.0,
        "replay-src": 102,
    }


def test_function_datasource_supports_time_and_constant_references() -> None:
    """function 数据源支持最小时间函数和常量函数。"""
    runtime = InMemoryDataSourceRuntime()

    assert (
        runtime.resolve_value(
            DataSourceSpec("time-src", DataSourceKind.FUNCTION, reference="time_seconds"),
            timestamp_ns=2_500_000_000,
            tick_index=9,
        )
        == 2.5
    )
    assert (
        runtime.resolve_value(
            DataSourceSpec("constant-src", DataSourceKind.FUNCTION, reference="constant:42"),
            timestamp_ns=0,
            tick_index=0,
        )
        == 42
    )


def test_datasource_runtime_rejects_missing_in_memory_config() -> None:
    """sample/replay 缺少内存数据时显式失败。"""
    runtime = InMemoryDataSourceRuntime()

    with pytest.raises(DataSourceRuntimeError, match="sample 数据源未加载"):
        runtime.resolve_value(
            DataSourceSpec("missing-sample", DataSourceKind.SAMPLE),
            timestamp_ns=0,
        )

    with pytest.raises(DataSourceRuntimeError, match="replay 数据源未加载"):
        runtime.resolve_value(
            DataSourceSpec("missing-replay", DataSourceKind.REPLAY),
            timestamp_ns=0,
        )


def test_build_write_batch_use_case_generates_batch_in_write_plan_order() -> None:
    """BuildWriteBatchUseCase 按 WritePlan 字段顺序生成 WriteBatch。"""
    data_sources = (
        DataSourceSpec("sample-src", DataSourceKind.SAMPLE, reference="sample-ref"),
        DataSourceSpec("function-src", DataSourceKind.FUNCTION, reference="tick"),
    )
    plan = _plan_with_sources(data_sources)
    use_case = BuildWriteBatchUseCase(
        data_source_port=InMemoryDataSourceRuntime(samples={"sample-ref": "ready"})
    )

    batch = use_case.execute(write_plan=plan, timestamp_ns=123_000, tick_index=7)

    assert batch.plan_id == plan.plan_id
    assert batch.batch_id == "plan-datasource:tick:7"
    assert [item.target.point_id for item in batch.items] == ["point-1", "point-2"]
    assert [item.value for item in batch.items] == ["ready", 7]
    assert all(item.timestamp_ns == 123_000 for item in batch.items)


def test_build_write_batch_use_case_rejects_missing_source_value() -> None:
    """数据源端口未返回字段引用的 source_id 时，不生成不完整 batch。"""
    class _EmptyDataSourcePort:
        """返回空映射的数据源端口测试替身。"""

        def resolve_value(
            self,
            spec: DataSourceSpec,
            *,
            timestamp_ns: int,
            tick_index: int = 0,
        ) -> None:
            """本测试不使用单值取值。"""
            _ = (spec, timestamp_ns, tick_index)
            return None

        def resolve_batch(
            self,
            specs: tuple[DataSourceSpec, ...],
            *,
            timestamp_ns: int,
            tick_index: int = 0,
        ) -> dict[str, None]:
            """返回空 batch 以模拟端口缺失值。"""
            _ = (specs, timestamp_ns, tick_index)
            return {}

    plan = _plan_with_sources((DataSourceSpec("src-1", DataSourceKind.SAMPLE),))
    use_case = BuildWriteBatchUseCase(data_source_port=_EmptyDataSourcePort())

    with pytest.raises(DataSourceRuntimeError, match="缺少 source_id 值"):
        use_case.execute(write_plan=plan, timestamp_ns=0, tick_index=0)


def test_container_builds_default_datasource_runtime_and_batch_use_case() -> None:
    """container 默认装配内存 data source runtime 和 batch 用例。"""
    port = build_data_source_runtime(samples={"src": True})
    use_case = build_write_batch_use_case(port)

    assert isinstance(port, DataSourcePort)
    assert isinstance(use_case, BuildWriteBatchUseCase)
