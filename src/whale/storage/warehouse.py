"""数据仓库层（warehouse）——面向主题分析的数据存储。

warehouse 层从 standardized 层消费数据，按业务主题组织为多维模型，
支撑报表、分析和数据服务。此为端口定义和测试实现，详细实现由后续阶段完成。

本文件包含：
- WarehouseSinkPort: 数据仓库写入端口。
- InMemoryWarehouseSink: 测试用内存实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class WarehouseSinkPort(ABC):
    """数据仓库写入端口。

    将标准化后按主题组织的数据写入数据仓库。面向分析人员和服务端查询，
    支持按时间范围和业务维度聚合。

    实现方责任：
    - 维护主题维度和度量定义。
    - 支持增量写入和全量刷新。
    - 提供查询接口供 mart/serving 层使用。

    不负责：
    - 原始时序数据存储（由 raw_index/standardized 负责）。
    - 聚合计算逻辑（由 processing 层负责）。
    """

    @abstractmethod
    async def write_fact(
        self,
        fact_table: str,
        rows: list[dict[str, Any]],
    ) -> int:
        """写入事实表数据。

        Args:
            fact_table: 事实表名称。
            rows: 待写入的行数据列表。

        Returns:
            写入的行数。

        Raises:
            RuntimeError: 写入失败。
        """
        ...

    @abstractmethod
    async def query(
        self,
        fact_table: str,
        dimensions: dict[str, str],
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """按维度和时间范围查询事实数据。

        Args:
            fact_table: 事实表名称。
            dimensions: 维度过滤条件（key=value）。
            start_time: 时间范围起点。
            end_time: 时间范围终点。

        Returns:
            符合条件的记录列表。
        """
        ...


class InMemoryWarehouseSink(WarehouseSinkPort):
    """测试用内存 warehouse 实现。

    将所有事实表数据保存在内存中，按表名分组的列表。

    Attributes:
        facts: 表名到行数据列表的映射。
    """

    def __init__(self) -> None:
        """初始化空的内存 warehouse。"""
        self.facts: dict[str, list[dict[str, Any]]] = {}

    async def write_fact(
        self,
        fact_table: str,
        rows: list[dict[str, Any]],
    ) -> int:
        """将事实行写入内存表。

        Args:
            fact_table: 事实表名称。
            rows: 待写入的行数据列表。

        Returns:
            写入的行数。
        """
        if fact_table not in self.facts:
            self.facts[fact_table] = []
        self.facts[fact_table].extend(rows)
        return len(rows)

    async def query(
        self,
        fact_table: str,
        dimensions: dict[str, str],
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """按维度和时间范围查询内存中的事实数据。

        Args:
            fact_table: 事实表名称。
            dimensions: 维度过滤条件。
            start_time: 时间范围起点。
            end_time: 时间范围终点。

        Returns:
            符合条件的记录列表。
        """
        rows = self.facts.get(fact_table, [])
        result = []
        for row in rows:
            # 维度匹配
            if not all(
                str(row.get(k)) == v for k, v in dimensions.items()
            ):
                continue
            # 时间范围匹配
            ts_str = row.get("timestamp", "")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(str(ts_str))
                    if ts < start_time or ts > end_time:
                        continue
                except (ValueError, TypeError):
                    pass
            result.append(row)
        return result
