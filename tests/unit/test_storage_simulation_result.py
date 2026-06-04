"""storage simulation_result 单元测试。

验证 SimulationResultTimeSeriesSinkPort、InMemorySimulationResultTimeSeriesSink
和 TdengineSimulationResultTimeSeriesSink contract adapter 的端口契约和内存实现行为。

被验证对象：
- whale.storage.simulation_result: InMemorySimulationResultTimeSeriesSink,
  TdengineSimulationResultTimeSeriesSink, SimulationResultTimeSeriesSinkPort

测试阶段：开发期验证 (unit，无外部依赖)。
不能证明：TDengine 真实存储的写入和查询行为。
"""

from __future__ import annotations

import inspect

import pytest

from whale.storage.simulation_result import (
    InMemorySimulationResultTimeSeriesSink,
    SimulationResultTimeSeriesSinkPort,
    TdengineSimulationResultTimeSeriesSink,
)


class TestInMemorySimulationResultTimeSeriesSink:
    """InMemorySimulationResultTimeSeriesSink 单元测试。"""

    @pytest.mark.asyncio
    async def test_write_single_channel(self) -> None:
        """验证写入单通道时序数据。"""
        sink = InMemorySimulationResultTimeSeriesSink()
        ok = await sink.write_result_series(
            result_code="RES_001",
            channel_name="gen_speed_rpm",
            timestamps=["2025-01-01T00:00:00Z", "2025-01-01T00:00:01Z"],
            values=[12.5, 13.0],
            unit="rpm",
            value_type="FLOAT64",
        )
        assert ok is True
        data = await sink.read_result_series("RES_001", "gen_speed_rpm")
        assert len(data) == 2
        assert data[0]["result_code"] == "RES_001"
        assert data[0]["channel_name"] == "gen_speed_rpm"
        assert data[0]["value"] == 12.5

    @pytest.mark.asyncio
    async def test_write_and_read_multiple_channels(self) -> None:
        """验证写入多个通道的数据并分别查询。"""
        sink = InMemorySimulationResultTimeSeriesSink()
        await sink.write_result_series(
            result_code="RES_001",
            channel_name="gen_speed",
            timestamps=["2025-01-01T00:00:00Z"],
            values=[12.0],
        )
        await sink.write_result_series(
            result_code="RES_001",
            channel_name="wind_speed",
            timestamps=["2025-01-01T00:00:00Z"],
            values=[8.5],
        )
        await sink.write_result_series(
            result_code="RES_002",
            channel_name="gen_speed",
            timestamps=["2025-01-01T00:00:00Z"],
            values=[15.0],
        )

        ch1 = await sink.read_result_series("RES_001", "gen_speed")
        assert len(ch1) == 1
        assert ch1[0]["value"] == 12.0

        ch2 = await sink.read_result_series("RES_001", "wind_speed")
        assert len(ch2) == 1
        assert ch2[0]["value"] == 8.5

        ch3 = await sink.read_result_series("RES_002", "gen_speed")
        assert len(ch3) == 1
        assert ch3[0]["value"] == 15.0

    @pytest.mark.asyncio
    async def test_read_nonexistent_result(self) -> None:
        """验证读取不存在的结果返回空列表。"""
        sink = InMemorySimulationResultTimeSeriesSink()
        data = await sink.read_result_series("NONEXISTENT", "ch1")
        assert data == []

    @pytest.mark.asyncio
    async def test_time_range_filter(self) -> None:
        """验证时间范围过滤。"""
        sink = InMemorySimulationResultTimeSeriesSink()
        await sink.write_result_series(
            result_code="RES_T",
            channel_name="ch",
            timestamps=[
                "2025-01-01T00:00:00Z",
                "2025-01-01T00:00:05Z",
                "2025-01-01T00:00:10Z",
            ],
            values=[1.0, 2.0, 3.0],
        )
        # 查询中间段
        data = await sink.read_result_series(
            "RES_T", "ch",
            start_time="2025-01-01T00:00:02Z",
            end_time="2025-01-01T00:00:08Z",
        )
        assert len(data) == 1
        assert data[0]["value"] == 2.0

    @pytest.mark.asyncio
    async def test_read_with_start_time_only(self) -> None:
        """验证仅指定起始时间查询。"""
        sink = InMemorySimulationResultTimeSeriesSink()
        ts = [
            "2025-01-01T00:00:00Z",
            "2025-01-01T00:00:05Z",
            "2025-01-01T00:00:10Z",
        ]
        await sink.write_result_series(
            result_code="R", channel_name="c", timestamps=ts, values=[1, 2, 3],
        )
        data = await sink.read_result_series(
            "R", "c", start_time="2025-01-01T00:00:05Z",
        )
        assert len(data) == 2
        assert data[0]["value"] == 2

    @pytest.mark.asyncio
    async def test_read_with_end_time_only(self) -> None:
        """验证仅指定结束时间查询。"""
        sink = InMemorySimulationResultTimeSeriesSink()
        ts = [
            "2025-01-01T00:00:00Z",
            "2025-01-01T00:00:05Z",
            "2025-01-01T00:00:10Z",
        ]
        await sink.write_result_series(
            result_code="R", channel_name="c", timestamps=ts, values=[1, 2, 3],
        )
        data = await sink.read_result_series(
            "R", "c", end_time="2025-01-01T00:00:05Z",
        )
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_write_with_metadata(self) -> None:
        """验证写入携带扩展元数据。"""
        sink = InMemorySimulationResultTimeSeriesSink()
        await sink.write_result_series(
            result_code="RES_M",
            channel_name="ch",
            timestamps=["2025-01-01T00:00:00Z"],
            values=[1.0],
            metadata={"simulator": "OpenFAST", "version": "3.5"},
        )
        data = await sink.read_result_series("RES_M", "ch")
        assert data[0]["metadata"]["simulator"] == "OpenFAST"
        assert data[0]["metadata"]["version"] == "3.5"

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        """验证清空所有记录。"""
        sink = InMemorySimulationResultTimeSeriesSink()
        await sink.write_result_series(
            result_code="R1", channel_name="c1",
            timestamps=["2025-01-01T00:00:00Z"], values=[1.0],
        )
        assert len(await sink.read_result_series("R1", "c1")) == 1
        sink.clear()
        assert len(await sink.read_result_series("R1", "c1")) == 0

    @pytest.mark.asyncio
    async def test_result_sorted_by_timestamp(self) -> None:
        """验证查询结果按时间戳排序。"""
        sink = InMemorySimulationResultTimeSeriesSink()
        await sink.write_result_series(
            result_code="R",
            channel_name="c",
            timestamps=[
                "2025-01-01T00:00:10Z",
                "2025-01-01T00:00:00Z",
                "2025-01-01T00:00:05Z",
            ],
            values=[3.0, 1.0, 2.0],
        )
        data = await sink.read_result_series("R", "c")
        timestamps = [d["timestamp"] for d in data]
        assert timestamps == sorted(timestamps)

    @pytest.mark.asyncio
    async def test_empty_write(self) -> None:
        """验证空时间戳和值列表的写入。"""
        sink = InMemorySimulationResultTimeSeriesSink()
        ok = await sink.write_result_series(
            result_code="R", channel_name="c", timestamps=[], values=[],
        )
        assert ok is True
        data = await sink.read_result_series("R", "c")
        assert data == []


class TestSimulationResultTimeSeriesSinkPort:
    """端口契约测试。"""

    def test_port_is_abstract(self) -> None:
        """验证端口是抽象基类。"""
        assert inspect.isabstract(SimulationResultTimeSeriesSinkPort)

    def test_port_has_write_method(self) -> None:
        """验证端口定义了 write_result_series 抽象方法。"""
        assert hasattr(SimulationResultTimeSeriesSinkPort, "write_result_series")
        method = getattr(SimulationResultTimeSeriesSinkPort, "write_result_series")
        assert getattr(method, "__isabstractmethod__", False)

    def test_port_has_read_method(self) -> None:
        """验证端口定义了 read_result_series 抽象方法。"""
        assert hasattr(SimulationResultTimeSeriesSinkPort, "read_result_series")
        method = getattr(SimulationResultTimeSeriesSinkPort, "read_result_series")
        assert getattr(method, "__isabstractmethod__", False)


class TestTdengineSimulationResultTimeSeriesSink:
    """TDengine contract adapter 测试。"""

    @pytest.mark.asyncio
    async def test_write_returns_false_in_contract_mode(self) -> None:
        """验证 contract-only 模式下 write 返回 False。"""
        sink = TdengineSimulationResultTimeSeriesSink(dsn="localhost:6041")
        ok = await sink.write_result_series(
            result_code="R", channel_name="c",
            timestamps=["2025-01-01T00:00:00Z"], values=[1.0],
        )
        assert ok is False

    @pytest.mark.asyncio
    async def test_read_returns_empty_in_contract_mode(self) -> None:
        """验证 contract-only 模式下 read 返回空列表。"""
        sink = TdengineSimulationResultTimeSeriesSink(dsn="localhost:6041")
        data = await sink.read_result_series("R", "c")
        assert data == []

    def test_invalid_dsn_sets_config_invalid(self) -> None:
        """验证无效 DSN 时 config_valid 为 False。"""
        sink = TdengineSimulationResultTimeSeriesSink(dsn="")
        assert sink._config_valid is False

    @pytest.mark.asyncio
    async def test_write_with_invalid_dsn_still_returns_false(self) -> None:
        """验证无效 DSN 时仍然安全返回 False，不抛异常。"""
        sink = TdengineSimulationResultTimeSeriesSink(dsn="")
        ok = await sink.write_result_series(
            result_code="R", channel_name="c",
            timestamps=["2025-01-01T00:00:00Z"], values=[1.0],
        )
        assert ok is False
        data = await sink.read_result_series("R", "c")
        assert data == []

    def test_valid_dsn_sets_config_valid(self) -> None:
        """验证有效 DSN 时 config_valid 为 True。"""
        sink = TdengineSimulationResultTimeSeriesSink(dsn="td01:6041")
        assert sink._config_valid is True

    @pytest.mark.asyncio
    async def test_read_with_invalid_dsn_returns_empty(self) -> None:
        """验证无效 DSN 时读取安全返回空列表。"""
        sink = TdengineSimulationResultTimeSeriesSink(dsn="")
        data = await sink.read_result_series("R", "c")
        assert data == []
