"""storage standardized 层单元测试。

验证 MemoryStandardizedSink 的写入/查询和 TdengineStandardizedSink 的 contract 行为。

被验证对象：
- whale.storage.standardized: MemoryStandardizedSink, TdengineStandardizedSink

测试阶段：开发期验证 (unit/mock)（纯内存测试 + contract adapter 配置校验）。
不能证明：TDengine 真实写入和查询行为。
"""

from __future__ import annotations

import pytest

from whale.storage.standardized import (
    MemoryStandardizedSink,
    StandardizedTimeSeriesSinkPort,
    TdengineStandardizedSink,
)


class TestMemoryStandardizedSink:
    """MemoryStandardizedSink 单元测试。"""

    def test_is_standardized_sink_port(self) -> None:
        """验证 MemoryStandardizedSink 实现 StandardizedTimeSeriesSinkPort。"""
        sink = MemoryStandardizedSink()
        assert isinstance(sink, StandardizedTimeSeriesSinkPort)

    @pytest.mark.asyncio
    async def test_write_batch(self) -> None:
        """验证批量写入 node states 并正确记录。"""
        sink = MemoryStandardizedSink()
        node_states = [
            {
                "node_key": "dev-1",
                "variable_key": "temp",
                "value": "25.5",
                "quality_code": "0",
                "schema_version": "1.0",
                "observed_at": "2026-06-02T10:00:00Z",
                "received_at": "2026-06-02T10:00:01Z",
            },
            {
                "node_key": "dev-2",
                "variable_key": "humidity",
                "value": "60",
                "quality_code": "0",
                "schema_version": "1.0",
                "observed_at": "2026-06-02T10:00:00Z",
                "received_at": "2026-06-02T10:00:01Z",
            },
        ]
        written = await sink.write(node_states)
        assert written == 2
        assert len(sink.states) == 2

    @pytest.mark.asyncio
    async def test_query_by_node(self) -> None:
        """验证 query_by_node 按 node_key 过滤正确。"""
        sink = MemoryStandardizedSink()
        await sink.write([
            {"node_key": "dev-1", "variable_key": "temp", "value": "25"},
            {"node_key": "dev-1", "variable_key": "press", "value": "101"},
            {"node_key": "dev-2", "variable_key": "temp", "value": "30"},
        ])

        dev1 = sink.query_by_node("dev-1")
        assert len(dev1) == 2

        dev1_temp = sink.query_by_node("dev-1", variable_key="temp")
        assert len(dev1_temp) == 1
        assert dev1_temp[0]["value"] == "25"

    @pytest.mark.asyncio
    async def test_write_empty_batch(self) -> None:
        """验证写入空列表返回 0。"""
        sink = MemoryStandardizedSink()
        written = await sink.write([])
        assert written == 0


class TestTdengineStandardizedSink:
    """TdengineStandardizedSink contract adapter 测试。"""

    def test_is_standardized_sink_port(self) -> None:
        """验证 TdengineStandardizedSink 实现 StandardizedTimeSeriesSinkPort。"""
        sink = TdengineStandardizedSink(dsn="taosws://localhost:6041", database="test")
        assert isinstance(sink, StandardizedTimeSeriesSinkPort)

    @pytest.mark.asyncio
    async def test_write_contract_mode_returns_zero(self) -> None:
        """验证 contract mode 下 write 返回 0。"""
        sink = TdengineStandardizedSink(dsn="taosws://localhost:6041", database="test")
        result = await sink.write([{"node_key": "test", "value": "1"}])
        assert result == 0
