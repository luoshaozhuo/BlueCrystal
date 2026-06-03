"""IEC 101 source 采集适配器单元测试。

被验证对象：``whale.ingest.adapters.source.iec101_source_acquisition_adapter.Iec101SourceAcquisitionAdapter``。
测试阶段：开发期验证 (unit/mock) — 使用 mock Iec101SourceReader 模拟串口读取。
不能证明：真实串口设备通信、IEC 101 interrogation 时序。

Mock 策略：
- mock whale.shared.source.iec101.reader.Iec101SourceReader；
- mock __aenter__/__aexit__ 和 read 方法；
- 不依赖真实 /dev/tty* 设备。
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from whale.ingest.adapters.source.iec101_source_acquisition_adapter import (
    Iec101SourceAcquisitionAdapter,
)
from whale.ingest.ports.source.source_acquisition_port import (
    SourceReadError,
    SourceSubscriptionUnsupportedError,
)
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.iec101.backends.base import (
    RawIec101ReadResult,
)


def _make_execution(protocol: str = "iec101") -> AcquisitionExecutionOptions:
    """构造测试用采集执行选项。"""
    return AcquisitionExecutionOptions(
        protocol=protocol,
        transport="SERIAL",
        acquisition_mode="READ",
        interval_ms=1000,
        request_timeout_ms=10000,
        freshness_timeout_ms=30000,
        alive_timeout_ms=60000,
        max_iteration=1,
        polling_max_concurrent_connections=1,
        polling_connection_start_interval_ms=0,
        subscription_start_interval_ms=0,
        subscription_notification_queue_size=100,
        subscription_notification_max_lag_ms=5000,
    )


def _make_connection(
    serial_port: str = "/dev/ttyUSB0",
    params: dict[str, object] | None = None,
) -> SourceConnectionData:
    """构造测试用 IEC 101 串口连接。"""
    base_params: dict[str, object] = {
        "baudrate": 9600,
        "parity": "E",
        "stop_bits": 1,
        "data_bits": 8,
        "link_address": 1,
        "common_address": 1,
    }
    if params:
        base_params.update(params)
    return SourceConnectionData(
        host=serial_port,
        port=0,
        ied_name="iec101-ied",
        ld_name="iec101-ld",
        namespace_uri="iec101://",
        params=base_params,
    )


def _make_item(key: str = "ioa100", relative_path: str = "100") -> AcquisitionItemData:
    """构造测试用采集点位。"""
    return AcquisitionItemData(
        key=key,
        relative_path=relative_path,
        profile_item_id=1,
    )


def _make_raw_result(
    ok: bool = True,
    values: dict[int, tuple[str, str]] | None = None,
) -> RawIec101ReadResult:
    """构造测试用原始读取结果。"""
    if values is None:
        values = {100: ("M_ME_NC_1", "42.500")}
    return RawIec101ReadResult(
        ok=ok,
        values=values,
        response_timestamp=datetime(2026, 6, 2, 12, 0, 0, tzinfo=UTC),
    )


class TestIec101AdapterRead:
    """IEC 101 adapter read 方法测试。"""

    @pytest.mark.asyncio
    async def test_read_returns_batch(self) -> None:
        """正常 interrogation 应返回 AcquiredNodeStateBatch。"""
        adapter = Iec101SourceAcquisitionAdapter()
        raw = _make_raw_result(ok=True, values={100: ("M_ME_NC_1", "42.500")})

        mock_reader = MagicMock()
        mock_reader.read = AsyncMock(return_value=raw)
        mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
        mock_reader.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "whale.ingest.adapters.source.iec101_source_acquisition_adapter.Iec101SourceReader",
            return_value=mock_reader,
        ):
            batch = await adapter.read(
                _make_execution(),
                _make_connection(),
                [_make_item("ioa100", "100")],
            )

        assert isinstance(batch, AcquiredNodeStateBatch)
        assert len(batch.values) == 1
        assert batch.values[0].value == "42.500"
        assert batch.values[0].quality == "GOOD"
        assert batch.values[0].attributes.get("iec101_type") == "M_ME_NC_1"
        assert batch.availability_status == "VALID"

    @pytest.mark.asyncio
    async def test_read_raw_failure_raises(self) -> None:
        """原始读取失败应抛出 SourceReadError。"""
        adapter = Iec101SourceAcquisitionAdapter()
        raw = RawIec101ReadResult(
            ok=False, values={},
            error_reason="read_failed",
        )

        mock_reader = MagicMock()
        mock_reader.read = AsyncMock(return_value=raw)
        mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
        mock_reader.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "whale.ingest.adapters.source.iec101_source_acquisition_adapter.Iec101SourceReader",
            return_value=mock_reader,
        ):
            with pytest.raises(SourceReadError, match="raw read failed"):
                await adapter.read(
                    _make_execution(),
                    _make_connection(),
                    [_make_item("ioa100", "100")],
                )

    @pytest.mark.asyncio
    async def test_read_ioa_not_found(self) -> None:
        """IOA 未找到时应标记 UNKNOWN。"""
        adapter = Iec101SourceAcquisitionAdapter()
        raw = _make_raw_result(
            ok=True, values={200: ("M_ME_NC_1", "77.0")}
        )  # IOA 200，但请求 IOA 100

        mock_reader = MagicMock()
        mock_reader.read = AsyncMock(return_value=raw)
        mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
        mock_reader.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "whale.ingest.adapters.source.iec101_source_acquisition_adapter.Iec101SourceReader",
            return_value=mock_reader,
        ):
            batch = await adapter.read(
                _make_execution(),
                _make_connection(),
                [_make_item("ioa100", "100")],
            )

        assert batch.values[0].quality == "UNKNOWN"
        assert "ioa_not_found_in_response" in str(
            batch.values[0].attributes.get("warning", "")
        )


class TestIec101AdapterAddressResolution:
    """IOA 解析测试。"""

    def test_resolve_valid_ioa(self) -> None:
        """有效 IOA 应正确解析。"""
        adapter = Iec101SourceAcquisitionAdapter()
        item = _make_item("ioa100", "100")
        ioa_list = adapter._resolve_ioa_list(
            _make_connection(), [item]
        )
        assert ioa_list == [100]

    def test_resolve_invalid_ioa_raises(self) -> None:
        """无法解析的 IOA 应抛出 ValueError。"""
        adapter = Iec101SourceAcquisitionAdapter()
        item = _make_item("ioa_bad", "not_a_number")
        with pytest.raises(ValueError, match="Cannot resolve"):
            adapter._resolve_ioa_list(
                _make_connection(), [item]
            )

    def test_resolve_hex_ioa(self) -> None:
        """十六进制 IOA 应被拒绝（不支持）。"""
        adapter = Iec101SourceAcquisitionAdapter()
        item = _make_item("ioa_hex", "0x64")
        with pytest.raises(ValueError, match="Cannot resolve"):
            adapter._resolve_ioa_list(
                _make_connection(), [item]
            )


class TestIec101AdapterConnectionParams:
    """连接参数提取测试。"""

    def test_build_reader_default_params(self) -> None:
        """默认参数应正确传递到 reader。"""
        reader = Iec101SourceAcquisitionAdapter._build_reader(
            _make_execution(),
            _make_connection("/dev/ttyUSB0"),
        )
        assert reader._serial_port == "/dev/ttyUSB0"
        assert reader._baudrate == 9600
        assert reader._parity == "E"
        assert reader._link_address == 1

    def test_missing_serial_port_raises(self) -> None:
        """缺少串口路径时应抛出 ValueError。"""
        conn = SourceConnectionData(
            host="", port=0, ied_name="iec101", ld_name="iec101",
            namespace_uri="", params={},
        )
        with pytest.raises(ValueError, match="serial_port"):
            Iec101SourceAcquisitionAdapter._build_reader(
                _make_execution(), conn
            )


class TestIec101AdapterSubscription:
    """订阅模式不支持测试。"""

    @pytest.mark.asyncio
    async def test_start_subscription_raises(self) -> None:
        """IEC 101 不支持 subscription，应抛出错误。"""
        adapter = Iec101SourceAcquisitionAdapter()
        with pytest.raises(SourceSubscriptionUnsupportedError):
            await adapter.start_subscription(
                _make_execution(),
                _make_connection(),
                [_make_item()],
                state_received=AsyncMock(),
            )
