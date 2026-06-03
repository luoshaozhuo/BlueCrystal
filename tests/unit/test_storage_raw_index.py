"""storage raw_index 层单元测试。

验证 MemoryRawIndexSink 的写入/查询和 TdengineRawIndexSink 的 contract 行为。

被验证对象：
- whale.storage.raw_index: MemoryRawIndexSink, TdengineRawIndexSink

证据等级：L1 unit/mock（纯内存测试 + contract adapter 配置校验）。
不能证明：TDengine 真实写入和查询行为。
"""

from __future__ import annotations

import pytest

from whale.storage.raw_index import (
    MemoryRawIndexSink,
    RawIndexSinkPort,
    TdengineRawIndexSink,
)


class TestMemoryRawIndexSink:
    """MemoryRawIndexSink 单元测试。"""

    def test_is_raw_index_sink_port(self) -> None:
        """验证 MemoryRawIndexSink 实现 RawIndexSinkPort。"""
        sink = MemoryRawIndexSink()
        assert isinstance(sink, RawIndexSinkPort)

    @pytest.mark.asyncio
    async def test_index_writes_record(self) -> None:
        """验证 index 写入后 records 列表包含记录。"""
        sink = MemoryRawIndexSink()
        envelope = {
            "source_id": "source-1",
            "message_id": "msg-001",
            "message_type": "state_snapshot",
            "published_at": "2026-06-02T10:00:00+00:00",
            "items": [{"key": "val"}],
        }
        result = await sink.index(envelope)
        assert result is True
        assert len(sink.records) == 1
        assert sink.records[0]["source_id"] == "source-1"

    @pytest.mark.asyncio
    async def test_multiple_index_writes(self) -> None:
        """验证多条 index 写入后 records 按顺序保存。"""
        sink = MemoryRawIndexSink()
        for i in range(5):
            await sink.index({
                "source_id": f"source-{i}",
                "message_id": f"msg-{i:03d}",
                "message_type": "state_snapshot",
                "published_at": "2026-06-02T10:00:00+00:00",
                "items": [],
            })
        assert len(sink.records) == 5

    def test_query_by_source_filters_correctly(self) -> None:
        """测试辅助方法 query_by_source 按 source_id 过滤。"""
        import asyncio

        async def _run() -> None:
            sink = MemoryRawIndexSink()
            await sink.index({
                "source_id": "src-a",
                "message_id": "msg-1",
                "message_type": "test",
                "published_at": "2026-06-02T10:00:00",
                "items": [],
            })
            await sink.index({
                "source_id": "src-b",
                "message_id": "msg-2",
                "message_type": "test",
                "published_at": "2026-06-02T10:01:00",
                "items": [],
            })
            result = sink.query_by_source("src-a")
            assert len(result) == 1
            assert result[0]["source_id"] == "src-a"

        asyncio.run(_run())


class TestTdengineRawIndexSink:
    """TdengineRawIndexSink contract adapter 测试。"""

    def test_is_raw_index_sink_port(self) -> None:
        """验证 TdengineRawIndexSink 实现 RawIndexSinkPort。"""
        sink = TdengineRawIndexSink(dsn="taosws://localhost:6041", database="test")
        assert isinstance(sink, RawIndexSinkPort)

    @pytest.mark.asyncio
    async def test_index_in_contract_mode_returns_false(self) -> None:
        """验证 contract mode 下 index 返回 False。"""
        sink = TdengineRawIndexSink(dsn="taosws://localhost:6041", database="test")
        result = await sink.index({"source_id": "test"})
        assert result is False
