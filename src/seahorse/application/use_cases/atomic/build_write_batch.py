"""从 WritePlan 与数据源端口构建 WriteBatch。

本用例是 Seahorse DataSource runtime 的最小应用层编排：它只基于纯
WritePlan/DataSourceSpec 契约批量取值并组装 WriteBatch，不调用 Starfish
writer，不运行 scheduler executor，也不查询 Whale DB。
"""

from __future__ import annotations

from dataclasses import dataclass

from seahorse.application.exceptions import DataSourceRuntimeError
from seahorse.application.ports.data_source_port import DataSourcePort
from seahorse.domain.runtime_contract import WriteBatch, WriteItem, WritePlan


@dataclass(slots=True)
class BuildWriteBatchUseCase:
    """按 WritePlan 生成单个 tick 的 WriteBatch。

    Attributes:
        data_source_port: 数据源批量取值端口；由 container 注入具体实现。
    """

    data_source_port: DataSourcePort

    def execute(
        self,
        *,
        write_plan: WritePlan,
        timestamp_ns: int,
        tick_index: int,
        batch_id: str | None = None,
    ) -> WriteBatch:
        """为一个逻辑 tick 生成 WriteBatch。

        Args:
            write_plan: 已构建并校验过的内存运行计划。
            timestamp_ns: 本次 batch 的时间戳，单位纳秒。
            tick_index: 本次 batch 的逻辑 tick 序号。
            batch_id: 可选 batch 标识；未传入时用 plan/tick 派生稳定标识。

        Returns:
            按 WritePlan 字段顺序生成的 WriteBatch。

        Raises:
            DataSourceRuntimeError: 数据源未返回字段需要的 source_id。
        """
        values = self.data_source_port.resolve_batch(
            write_plan.data_sources,
            timestamp_ns=timestamp_ns,
            tick_index=tick_index,
        )
        items: list[WriteItem] = []
        for field_binding in write_plan.field_bindings():
            if field_binding.source_id not in values:
                raise DataSourceRuntimeError(
                    f"字段 {field_binding.field_id} 缺少 source_id 值: {field_binding.source_id}"
                )
            items.append(
                WriteItem(
                    target=field_binding.target,
                    value=values[field_binding.source_id],
                    source_id=field_binding.source_id,
                    timestamp_ns=timestamp_ns,
                )
            )
        return WriteBatch(
            plan_id=write_plan.plan_id,
            batch_id=batch_id or f"{write_plan.plan_id.value}:tick:{tick_index}",
            items=tuple(items),
        )


__all__ = ["BuildWriteBatchUseCase"]
