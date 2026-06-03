"""数据集市层（mart）——面向业务服务的预聚合数据。

mart 层从 warehouse 层消费数据，按业务服务需要预聚合和物化，
支撑低延迟查询和 API 响应。

本文件包含：
- MartSinkPort: 数据集市写入端口。
- InMemoryMartSink: 测试用内存实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any


class MartSinkPort(ABC):
    """数据集市写入端口。

    将预聚合数据写入数据集市。典型场景包括：场站日发电量汇总、设备可用率、
    告警统计等面向特定业务服务的物化视图。

    实现方责任：
    - 维护聚合维度和度量定义。
    - 支持定期刷新和增量更新。
    - 提供低延迟查询接口。

    不负责：
    - 聚合计算逻辑本身（由 processing/aggregation 层负责）。
    """

    @abstractmethod
    async def upsert_view(
        self,
        view_name: str,
        key: str,
        data: dict[str, Any],
    ) -> bool:
        """写入或更新一个物化视图条目。

        Args:
            view_name: 视图名称。
            key: 视图条目主键。
            data: 视图条目数据。

        Returns:
            True 表示写入成功。

        Raises:
            RuntimeError: 写入失败。
        """
        ...

    @abstractmethod
    async def get_view(self, view_name: str, key: str) -> dict[str, Any] | None:
        """按视图和主键查询。

        Args:
            view_name: 视图名称。
            key: 视图条目主键。

        Returns:
            视图条目数据，不存在时返回 None。
        """
        ...


class InMemoryMartSink(MartSinkPort):
    """测试用内存 mart 实现。

    所有物化视图保存在内存中，按视图名和主键两层索引。

    Attributes:
        views: 视图名 -> 主键 -> 数据 的两层映射。
    """

    def __init__(self) -> None:
        """初始化空的内存 mart。"""
        self.views: dict[str, dict[str, dict[str, Any]]] = {}

    async def upsert_view(
        self,
        view_name: str,
        key: str,
        data: dict[str, Any],
    ) -> bool:
        """向内存视图写入或更新条目。

        Args:
            view_name: 视图名称。
            key: 视图条目主键。
            data: 视图条目数据。

        Returns:
            始终返回 True。
        """
        if view_name not in self.views:
            self.views[view_name] = {}
        record = dict(data)
        record["_updated_at"] = datetime.now(tz=timezone.utc).isoformat()
        self.views[view_name][key] = record
        return True

    async def get_view(
        self, view_name: str, key: str
    ) -> dict[str, Any] | None:
        """从内存视图查询条目。

        Args:
            view_name: 视图名称。
            key: 视图条目主键。

        Returns:
            视图条目数据，不存在时返回 None。
        """
        view = self.views.get(view_name, {})
        return view.get(key)
