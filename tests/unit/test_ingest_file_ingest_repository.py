"""文件接入仓储层单元测试。

验证 InMemoryFaultEventRepository 的保存、查询和端口契约。

被验证对象：
- whale.ingest.file_ingest.repository: InMemoryFaultEventRepository,
  FaultEventRepositoryPort

测试阶段：开发期验证 (unit，无外部依赖)。
不能证明：真实 DB 持久化和事务行为。
"""

from __future__ import annotations

import inspect

import pytest

from whale.ingest.file_ingest.models import FaultEventMetadata
from whale.ingest.file_ingest.repository import (
    FaultEventRepositoryPort,
    InMemoryFaultEventRepository,
)


class TestInMemoryFaultEventRepository:
    """InMemoryFaultEventRepository 单元测试。"""

    @pytest.mark.asyncio
    async def test_save_and_find_by_event_id(self) -> None:
        """验证保存后可按 event_id 查询。"""
        repo = InMemoryFaultEventRepository()
        event = FaultEventMetadata(
            event_id="flt-001",
            source_id="src-1",
            event_type="TRIP",
            severity="CRITICAL",
        )
        await repo.save(event)

        found = await repo.find_by_event_id("flt-001")
        assert found is not None
        assert found.event_id == "flt-001"
        assert found.source_id == "src-1"
        assert found.event_type == "TRIP"
        assert found.severity == "CRITICAL"

    @pytest.mark.asyncio
    async def test_find_by_event_id_not_found(self) -> None:
        """验证不存在的 event_id 返回 None。"""
        repo = InMemoryFaultEventRepository()
        found = await repo.find_by_event_id("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_find_by_source_id(self) -> None:
        """验证按 source_id 查询。"""
        repo = InMemoryFaultEventRepository()
        await repo.save(FaultEventMetadata(
            event_id="flt-a", source_id="src-1", event_type="TYPE_A",
        ))
        await repo.save(FaultEventMetadata(
            event_id="flt-b", source_id="src-1", event_type="TYPE_B",
        ))
        await repo.save(FaultEventMetadata(
            event_id="flt-c", source_id="src-2", event_type="TYPE_A",
        ))

        src1_events = await repo.find_by_source_id("src-1")
        assert len(src1_events) == 2
        event_ids = {e.event_id for e in src1_events}
        assert event_ids == {"flt-a", "flt-b"}

        src2_events = await repo.find_by_source_id("src-2")
        assert len(src2_events) == 1
        assert src2_events[0].event_id == "flt-c"

    @pytest.mark.asyncio
    async def test_find_by_source_id_empty(self) -> None:
        """验证不存在的 source_id 返回空列表。"""
        repo = InMemoryFaultEventRepository()
        events = await repo.find_by_source_id("nonexistent")
        assert events == []

    @pytest.mark.asyncio
    async def test_save_overwrites_same_event_id(self) -> None:
        """验证相同 event_id 再次保存会覆盖。"""
        repo = InMemoryFaultEventRepository()
        event1 = FaultEventMetadata(
            event_id="flt-001", source_id="src-1", event_type="OLD_TYPE",
        )
        await repo.save(event1)

        event2 = FaultEventMetadata(
            event_id="flt-001", source_id="src-2", event_type="NEW_TYPE",
        )
        await repo.save(event2)

        found = await repo.find_by_event_id("flt-001")
        assert found is not None
        assert found.source_id == "src-2"
        assert found.event_type == "NEW_TYPE"


class TestFaultEventRepositoryPort:
    """FaultEventRepositoryPort 端口契约测试。"""

    def test_port_is_abstract(self) -> None:
        """验证端口是抽象基类。"""
        assert inspect.isabstract(FaultEventRepositoryPort)

    def test_port_has_required_methods(self) -> None:
        """验证端口定义了必要的抽象方法。"""
        assert hasattr(FaultEventRepositoryPort, "save")
        assert getattr(FaultEventRepositoryPort.save, "__isabstractmethod__", False)
        assert hasattr(FaultEventRepositoryPort, "find_by_event_id")
        assert getattr(FaultEventRepositoryPort.find_by_event_id, "__isabstractmethod__", False)
        assert hasattr(FaultEventRepositoryPort, "find_by_source_id")
        assert getattr(FaultEventRepositoryPort.find_by_source_id, "__isabstractmethod__", False)
