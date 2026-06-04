"""storage waveform 层单元测试。

验证 StandardizedWaveformSinkPort、InMemoryStandardizedWaveformSink 和
TdengineStandardizedWaveformSink contract adapter 的端口契约和内存实现行为。

被验证对象：
- whale.storage.waveform: InMemoryStandardizedWaveformSink,
  TdengineStandardizedWaveformSink, StandardizedWaveformSinkPort

测试阶段：开发期验证 (unit，无外部依赖)。
不能证明：TDengine 真实存储的写入和查询行为。
"""

from __future__ import annotations

import pytest

from whale.storage.waveform import (
    InMemoryStandardizedWaveformSink,
    StandardizedWaveformSinkPort,
    TdengineStandardizedWaveformSink,
)


class TestInMemoryStandardizedWaveformSink:
    """InMemoryStandardizedWaveformSink 单元测试。"""

    @pytest.mark.asyncio
    async def test_write_single_waveform(self) -> None:
        """验证写入单条波形记录。"""
        sink = InMemoryStandardizedWaveformSink()
        ok = await sink.write_waveform(
            event_id="evt-001",
            source_id="src-1",
            channel_key="ch_a",
            timestamps=["2025-01-01T00:00:00Z", "2025-01-01T00:00:01Z"],
            values=[1.0, 2.0],
            sample_rate_hz=1000.0,
            unit="V",
            value_type="FLOAT64",
            quality_code="0",
            channel_id="0",
        )
        assert ok is True

        records = sink.query_by_event("evt-001")
        assert len(records) == 1
        assert records[0]["event_id"] == "evt-001"
        assert records[0]["source_id"] == "src-1"
        assert records[0]["channel_key"] == "ch_a"
        assert records[0]["sample_rate_hz"] == 1000.0
        assert records[0]["unit"] == "V"

    @pytest.mark.asyncio
    async def test_query_by_event_id(self) -> None:
        """验证按 event_id 查询波形记录。"""
        sink = InMemoryStandardizedWaveformSink()
        await sink.write_waveform(
            event_id="evt-a", source_id="src-1", channel_key="ch_1",
            timestamps=["2025-01-01T00:00:00Z"], values=[1.0],
        )
        await sink.write_waveform(
            event_id="evt-b", source_id="src-2", channel_key="ch_2",
            timestamps=["2025-01-01T00:00:00Z"], values=[2.0],
        )

        a_records = sink.query_by_event("evt-a")
        assert len(a_records) == 1
        assert a_records[0]["event_id"] == "evt-a"

        b_records = sink.query_by_event("evt-b")
        assert len(b_records) == 1
        assert b_records[0]["event_id"] == "evt-b"

        empty = sink.query_by_event("evt-nonexistent")
        assert len(empty) == 0

    @pytest.mark.asyncio
    async def test_query_by_source_id(self) -> None:
        """验证按 source_id 查询波形记录。"""
        sink = InMemoryStandardizedWaveformSink()
        await sink.write_waveform(
            event_id="evt-1", source_id="src-a", channel_key="ch_1",
            timestamps=["2025-01-01T00:00:00Z"], values=[1.0],
        )
        await sink.write_waveform(
            event_id="evt-2", source_id="src-a", channel_key="ch_2",
            timestamps=["2025-01-01T00:00:00Z"], values=[2.0],
        )
        await sink.write_waveform(
            event_id="evt-3", source_id="src-b", channel_key="ch_1",
            timestamps=["2025-01-01T00:00:00Z"], values=[3.0],
        )

        a_records = sink.query_by_source("src-a")
        assert len(a_records) == 2

        b_records = sink.query_by_source("src-b")
        assert len(b_records) == 1

    @pytest.mark.asyncio
    async def test_write_with_metadata(self) -> None:
        """验证波形写入携带扩展元数据。"""
        sink = InMemoryStandardizedWaveformSink()
        await sink.write_waveform(
            event_id="evt-001",
            source_id="src-1",
            channel_key="ch_a",
            timestamps=["2025-01-01T00:00:00Z"],
            values=[1.0],
            metadata={"trigger_reason": "overcurrent", "duration_ms": 150},
        )
        records = sink.query_by_event("evt-001")
        assert records[0]["metadata"]["trigger_reason"] == "overcurrent"
        assert records[0]["metadata"]["duration_ms"] == 150

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        """验证清空所有记录。"""
        sink = InMemoryStandardizedWaveformSink()
        await sink.write_waveform(
            event_id="evt-1", source_id="src-1", channel_key="ch_1",
            timestamps=["2025-01-01T00:00:00Z"], values=[1.0],
        )
        assert len(sink.query_by_event("evt-1")) == 1
        sink.clear()
        assert len(sink.query_by_event("evt-1")) == 0

    @pytest.mark.asyncio
    async def test_timestamps_and_values_are_copied(self) -> None:
        """验证写入的 timestamps 和 values 列表是副本，修改原始列表不影响已存储记录。"""
        sink = InMemoryStandardizedWaveformSink()
        ts = ["2025-01-01T00:00:00Z"]
        vals = [1.0]
        await sink.write_waveform(
            event_id="evt-1", source_id="src-1", channel_key="ch_1",
            timestamps=ts, values=vals,
        )
        ts.append("2025-01-01T00:00:01Z")
        vals.append(2.0)
        records = sink.query_by_event("evt-1")
        assert len(records[0]["timestamps"]) == 1
        assert len(records[0]["values"]) == 1


class TestStandardizedWaveformSinkPort:
    """StandardizedWaveformSinkPort 端口契约测试。

    验证端口是 ABC 且定义了必要的抽象方法。
    """

    def test_port_is_abstract(self) -> None:
        """验证端口是抽象基类。"""
        import inspect
        assert inspect.isabstract(StandardizedWaveformSinkPort)

    def test_port_has_write_waveform_method(self) -> None:
        """验证端口定义了 write_waveform 抽象方法。"""
        assert hasattr(StandardizedWaveformSinkPort, "write_waveform")
        method = getattr(StandardizedWaveformSinkPort, "write_waveform")
        assert getattr(method, "__isabstractmethod__", False)


class TestTdengineStandardizedWaveformSink:
    """TdengineStandardizedWaveformSink contract adapter 测试。

    验证 contract adapter 在 environment-pending 模式下的行为。
    """

    @pytest.mark.asyncio
    async def test_write_returns_false_in_contract_mode(self) -> None:
        """验证 contract-only 模式下 write_waveform 返回 False。"""
        sink = TdengineStandardizedWaveformSink(dsn="localhost:6041")
        ok = await sink.write_waveform(
            event_id="evt-1", source_id="src-1", channel_key="ch_1",
            timestamps=["2025-01-01T00:00:00Z"], values=[1.0],
        )
        assert ok is False

    def test_invalid_dsn_sets_config_invalid(self) -> None:
        """验证无效 DSN 时 config_valid 为 False。"""
        sink = TdengineStandardizedWaveformSink(dsn="")
        assert sink._config_valid is False

    @pytest.mark.asyncio
    async def test_write_with_invalid_dsn_still_returns_false(self) -> None:
        """验证无效 DSN 时仍然安全返回 False，不抛异常。"""
        sink = TdengineStandardizedWaveformSink(dsn="")
        ok = await sink.write_waveform(
            event_id="evt-1", source_id="src-1", channel_key="ch_1",
            timestamps=["2025-01-01T00:00:00Z"], values=[1.0],
        )
        assert ok is False

    def test_valid_dsn_sets_config_valid(self) -> None:
        """验证有效 DSN 时 config_valid 为 True。"""
        sink = TdengineStandardizedWaveformSink(dsn="td01:6041")
        assert sink._config_valid is True
