"""speed layer index 和 standardized 管道集成测试。

验证 message → raw_index 和 message → standardized 的完整闭环。
测试 ServingCacheUpdater 集成：消息 → serving cache 更新。

被验证对象：
- whale.speed_layer.writers: RawIndexWriter, StandardizedWriter, ServingCacheUpdater
- whale.storage.raw_index: MemoryRawIndexSink
- whale.storage.standardized: MemoryStandardizedSink
- whale.storage.serving_cache: InMemoryServingCache

证据等级：L3 simulator（全内存闭环，完整链路覆盖）。
不能证明：TDengine 真实时序写入、Redis serving cache 真实读写。
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from whale.message_pipeline.adapters.in_memory import (
    InMemoryDeadLetterSink,
    InMemoryMessageBus,
)
from whale.message_pipeline.model import Envelope
from whale.speed_layer.writers import (
    RawIndexWriter,
    ServingCacheUpdater,
    StandardizedWriter,
)
from whale.storage.raw_index import MemoryRawIndexSink
from whale.storage.serving_cache import InMemoryServingCache
from whale.storage.standardized import MemoryStandardizedSink


def _make_envelope(
    message_id: str = "msg-001",
    source_id: str = "source-1",
    device_id: str = "dev-1",
    variable_key: str = "temp",
    value: str = "25.5",
) -> Envelope:
    """构造测试用 Envelope（含 device 和 variable 信息）。"""
    return Envelope(
        schema_version="1.0",
        message_id=message_id,
        message_type="state_snapshot",
        trace_id=f"trace-{message_id}",
        source_id=source_id,
        published_at=datetime.now(tz=timezone.utc),
        items=[
            {
                "variable_key": variable_key,
                "value": value,
                "device_id": device_id,
                "quality_code": "0",
            }
        ],
    )


class TestRawIndexPipeline:
    """raw_index pipeline 集成测试。"""

    @pytest.mark.asyncio
    async def test_message_to_raw_index_flow(self) -> None:
        """验证消息发布 → raw_index 写入的闭环。"""
        bus = InMemoryMessageBus()
        index = MemoryRawIndexSink()
        dlq = InMemoryDeadLetterSink()

        for i in range(5):
            await bus.publish(
                _make_envelope(
                    message_id=f"msg-{i:03d}",
                    source_id=f"source-{i % 2}",
                )
            )

        writer = RawIndexWriter(source=bus, index=index, dlq=dlq)
        count = await writer.run("whale.state_snapshot", "group-index")
        assert count == 5
        assert len(index.records) == 5

    @pytest.mark.asyncio
    async def test_source_id_grouping(self) -> None:
        """验证按 source_id 过滤查询正确。"""
        bus = InMemoryMessageBus()
        index = MemoryRawIndexSink()
        dlq = InMemoryDeadLetterSink()

        await bus.publish(_make_envelope(source_id="src-a", message_id="a-1"))
        await bus.publish(_make_envelope(source_id="src-a", message_id="a-2"))
        await bus.publish(_make_envelope(source_id="src-b", message_id="b-1"))

        writer = RawIndexWriter(source=bus, index=index, dlq=dlq)
        await writer.run("whale.state_snapshot", "group-index")

        src_a = index.query_by_source("src-a")
        assert len(src_a) == 2
        src_b = index.query_by_source("src-b")
        assert len(src_b) == 1


class TestStandardizedPipeline:
    """standardized pipeline 集成测试。"""

    @pytest.mark.asyncio
    async def test_message_to_standardized_flow(self) -> None:
        """验证消息发布 → standardized 写入的闭环。"""
        bus = InMemoryMessageBus()
        sink = MemoryStandardizedSink()
        dlq = InMemoryDeadLetterSink()

        for i in range(3):
            await bus.publish(
                _make_envelope(
                    message_id=f"msg-{i:03d}",
                    device_id=f"dev-{i}",
                    variable_key="temp",
                    value=str(25 + i),
                )
            )

        writer = StandardizedWriter(source=bus, sink=sink, dlq=dlq)
        count = await writer.run("whale.state_snapshot", "group-std")
        assert count == 3
        assert len(sink.states) == 3

        # 验证 node state 转换正确
        assert sink.states[0]["node_key"] == "dev-0"
        assert sink.states[0]["variable_key"] == "temp"
        assert sink.states[2]["value"] == "27"


class TestServingCachePipeline:
    """serving cache pipeline 集成测试。"""

    @pytest.mark.asyncio
    async def test_message_to_serving_cache_flow(self) -> None:
        """验证消息发布 → serving cache 更新的闭环。"""
        bus = InMemoryMessageBus()
        cache = InMemoryServingCache(default_ttl_seconds=60)
        dlq = InMemoryDeadLetterSink()

        await bus.publish(
            _make_envelope(
                source_id="src-1",
                device_id="dev-1",
                variable_key="temp",
                value="25.5",
            )
        )

        updater = ServingCacheUpdater(source=bus, cache=cache, dlq=dlq)
        count = await updater.run("whale.state_snapshot", "group-cache")
        assert count == 1

        # 验证缓存可查询
        cached = await cache.get("src-1:dev-1:temp")
        assert cached is not None
        assert cached["value"] == "25.5"
        assert cached["source_id"] == "src-1"

    @pytest.mark.asyncio
    async def test_serving_cache_size(self) -> None:
        """验证缓存写入后 size 正确。"""
        bus = InMemoryMessageBus()
        cache = InMemoryServingCache(default_ttl_seconds=60)
        dlq = InMemoryDeadLetterSink()

        for i in range(3):
            await bus.publish(
                _make_envelope(
                    device_id=f"dev-{i}",
                    variable_key="temp",
                    value=str(20 + i),
                )
            )

        updater = ServingCacheUpdater(source=bus, cache=cache, dlq=dlq)
        await updater.run("whale.state_snapshot", "group-cache")
        assert cache.size() == 3
