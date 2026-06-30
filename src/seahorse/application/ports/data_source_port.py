"""Seahorse 数据源端口。

端口只描述应用层可消费的数据源取值能力，不绑定 Whale ORM、真实文件
streaming 或协议 driver。调用方应在 runtime tick 内一次性批量取值，再
组装 WriteBatch；端口本身不写 Starfish、不调度线程。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from seahorse.domain.runtime_contract import DataSourceSpec, PointFieldValue


@runtime_checkable
class DataSourcePort(Protocol):
    """数据源取值端口。

    实现方可来自 random、sample、function 或 replay 契约。`tick_index`
    是调用方传入的逻辑 tick 序号，用于 replay 内存行选择和函数数据源；
    本端口不承诺真实 scheduler executor 已存在。
    """

    def resolve_value(
        self,
        spec: DataSourceSpec,
        *,
        timestamp_ns: int,
        tick_index: int = 0,
    ) -> PointFieldValue:
        """按数据源契约解析单个 tick 的值。

        Args:
            spec: 数据源契约。
            timestamp_ns: 本次取值的时间戳，单位纳秒。
            tick_index: 本次取值的逻辑 tick 序号。

        Returns:
            可写入 batch 的字段值；None 表示该数据源明确不携带值。
        """
        ...

    def resolve_batch(
        self,
        specs: tuple[DataSourceSpec, ...],
        *,
        timestamp_ns: int,
        tick_index: int = 0,
    ) -> dict[str, PointFieldValue]:
        """按多个数据源契约解析同一 tick 的 source_id 到值映射。

        Args:
            specs: 数据源契约集合。
            timestamp_ns: 本次取值的时间戳，单位纳秒。
            tick_index: 本次取值的逻辑 tick 序号。

        Returns:
            以 ``DataSourceSpec.source_id`` 为 key 的值映射。
        """
        ...
