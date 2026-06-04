"""文件接入仓储层。

提供故障事件元数据的持久化和查询能力。
当前仅实现内存路径，供开发期和模块集成期验证使用。

本文件包含：
- FaultEventRepositoryPort: 故障事件仓储端口。
- InMemoryFaultEventRepository: 测试用内存实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from whale.ingest.file_ingest.models import FaultEventMetadata


class FaultEventRepositoryPort(ABC):
    """故障事件仓储端口。

    管理故障事件元数据的持久化和查询。

    实现方责任：
    - 保存故障事件元数据。
    - 支持按 event_id、source_id、时间范围查询。

    不负责：
    - 波形数据本身的存储（由 StandardizedWaveformSinkPort 负责）。
    - 故障事件的实时告警分发。
    """

    @abstractmethod
    async def save(self, event: FaultEventMetadata) -> None:
        """保存一条故障事件元数据。

        Args:
            event: 故障事件元数据。

        Raises:
            RuntimeError: 持久化失败。
        """
        ...

    @abstractmethod
    async def find_by_event_id(self, event_id: str) -> FaultEventMetadata | None:
        """按 event_id 查询故障事件。

        Args:
            event_id: 故障事件唯一标识。

        Returns:
            FaultEventMetadata 实例，不存在时返回 None。
        """
        ...

    @abstractmethod
    async def find_by_source_id(self, source_id: str) -> list[FaultEventMetadata]:
        """按 source_id 查询故障事件列表。

        Args:
            source_id: 数据源标识。

        Returns:
            符合条件的故障事件列表。
        """
        ...


class InMemoryFaultEventRepository(FaultEventRepositoryPort):
    """测试用内存故障事件仓储。

    将所有故障事件元数据保存在内存字典中，支持按 event_id 和
    source_id 查询。

    Attributes:
        _events: event_id 到 FaultEventMetadata 的映射字典。
    """

    def __init__(self) -> None:
        """初始化空的内存故障事件仓储。"""
        self._events: dict[str, FaultEventMetadata] = {}

    async def save(self, event: FaultEventMetadata) -> None:
        """将故障事件元数据保存到内存。

        Args:
            event: 故障事件元数据。
        """
        self._events[event.event_id] = event

    async def find_by_event_id(self, event_id: str) -> FaultEventMetadata | None:
        """按 event_id 查询故障事件。

        Args:
            event_id: 故障事件唯一标识。

        Returns:
            FaultEventMetadata 实例，不存在时返回 None。
        """
        return self._events.get(event_id)

    async def find_by_source_id(self, source_id: str) -> list[FaultEventMetadata]:
        """按 source_id 查询故障事件列表。

        Args:
            source_id: 数据源标识。

        Returns:
            符合条件的故障事件列表，按存入顺序排列。
        """
        return [e for e in self._events.values() if e.source_id == source_id]
