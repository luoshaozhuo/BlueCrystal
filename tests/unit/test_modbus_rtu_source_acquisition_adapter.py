"""Modbus RTU source 采集适配器单元测试。

被验证对象：``whale.ingest.adapters.source.modbus_rtu_source_acquisition_adapter.ModbusRtuSourceAcquisitionAdapter``。
测试阶段：开发期验证 (unit/mock) — 使用 mock ModbusRtuSourceReader 模拟串口读取。
不能证明：真实串口设备通信、Modbus RTU 时序约束。

Mock 策略：
- mock whale.shared.source.modbus_rtu.reader.ModbusRtuSourceReader；
- mock __aenter__/__aexit__ 和 read_prepared 方法；
- 不依赖真实 /dev/tty* 设备。
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from whale.ingest.adapters.source.modbus_rtu_source_acquisition_adapter import (
    ModbusRtuSourceAcquisitionAdapter,
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
from whale.shared.source.modbus_rtu.backends.base import (
    RawModbusRtuReadResult,
)


def _make_execution(protocol: str = "modbus_rtu") -> AcquisitionExecutionOptions:
    """构造测试用采集执行选项。"""
    return AcquisitionExecutionOptions(
        protocol=protocol,
        transport="SERIAL",
        acquisition_mode="READ",
        interval_ms=1000,
        request_timeout_ms=5000,
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
    """构造测试用 Modbus RTU 串口连接。"""
    base_params: dict[str, object] = {
        "baudrate": 9600,
        "parity": "N",
        "stop_bits": 1,
        "data_bits": 8,
        "modbus_unit_id": 1,
    }
    if params:
        base_params.update(params)
    return SourceConnectionData(
        host=serial_port,
        port=0,  # RTU 不使用 TCP 端口
        ied_name="rtu-ied",
        ld_name="rtu-ld",
        namespace_uri="modbus_rtu://",
        params=base_params,
    )


def _make_item(key: str = "reg1", relative_path: str = "100") -> AcquisitionItemData:
    """构造测试用采集点位。"""
    return AcquisitionItemData(
        key=key,
        relative_path=relative_path,
        profile_item_id=1,
    )


def _make_raw_result(
    ok: bool = True,
    values: tuple[int, ...] = (4660,),
) -> RawModbusRtuReadResult:
    """构造测试用原始读取结果。"""
    return RawModbusRtuReadResult(
        ok=ok,
        values=values,
        response_timestamp=datetime(2026, 6, 2, 12, 0, 0, tzinfo=UTC),
    )


class TestModbusRtuAdapterRead:
    """Modbus RTU adapter read 方法测试。"""

    @pytest.mark.asyncio
    async def test_read_returns_batch(self) -> None:
        """正常读取应返回 AcquiredNodeStateBatch。"""
        adapter = ModbusRtuSourceAcquisitionAdapter()
        raw = _make_raw_result(ok=True, values=(4660,))

        mock_reader = MagicMock()
        mock_reader.prepare_read = MagicMock(return_value=MagicMock())
        mock_reader.read_prepared = AsyncMock(return_value=raw)
        mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
        mock_reader.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "whale.ingest.adapters.source.modbus_rtu_source_acquisition_adapter.ModbusRtuSourceReader",
            return_value=mock_reader,
        ):
            batch = await adapter.read(
                _make_execution(),
                _make_connection(),
                [_make_item("reg1", "100")],
            )

        assert isinstance(batch, AcquiredNodeStateBatch)
        assert len(batch.values) == 1
        assert batch.values[0].value == "4660"
        assert batch.values[0].quality == "GOOD"
        assert batch.availability_status == "VALID"

    @pytest.mark.asyncio
    async def test_read_raw_failure_raises(self) -> None:
        """原始读取失败应抛出 SourceReadError。"""
        adapter = ModbusRtuSourceAcquisitionAdapter()
        raw = _make_raw_result(ok=False, values=(), )
        raw = RawModbusRtuReadResult(
            ok=False, values=(),
            error_reason="crc_error", exception="CRC 校验失败",
        )

        mock_reader = MagicMock()
        mock_reader.prepare_read = MagicMock(return_value=MagicMock())
        mock_reader.read_prepared = AsyncMock(return_value=raw)
        mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
        mock_reader.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "whale.ingest.adapters.source.modbus_rtu_source_acquisition_adapter.ModbusRtuSourceReader",
            return_value=mock_reader,
        ):
            with pytest.raises(SourceReadError, match="raw read failed"):
                await adapter.read(
                    _make_execution(),
                    _make_connection(),
                    [_make_item("reg1", "100")],
                )

    @pytest.mark.asyncio
    async def test_read_value_mismatch_raises(self) -> None:
        """返回值数量不匹配应抛出 SourceReadError。"""
        adapter = ModbusRtuSourceAcquisitionAdapter()
        raw = _make_raw_result(ok=True, values=(4660, 1234))  # 2 values, 1 item

        mock_reader = MagicMock()
        mock_reader.prepare_read = MagicMock(return_value=MagicMock())
        mock_reader.read_prepared = AsyncMock(return_value=raw)
        mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
        mock_reader.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "whale.ingest.adapters.source.modbus_rtu_source_acquisition_adapter.ModbusRtuSourceReader",
            return_value=mock_reader,
        ):
            with pytest.raises(SourceReadError, match="does not match"):
                await adapter.read(
                    _make_execution(),
                    _make_connection(),
                    [_make_item("reg1", "100")],
                )


class TestModbusRtuAdapterAddressResolution:
    """地址解析测试。"""

    def test_resolve_hex_address(self) -> None:
        """十六进制地址应正确解析。"""
        adapter = ModbusRtuSourceAcquisitionAdapter()
        item = _make_item("reg1", "0x0064")
        addrs = adapter._resolve_reg_addrs(
            _make_connection(), [item]
        )
        assert addrs == [100]

    def test_resolve_decimal_address(self) -> None:
        """十进制地址应正确解析。"""
        adapter = ModbusRtuSourceAcquisitionAdapter()
        item = _make_item("reg1", "40001")
        addrs = adapter._resolve_reg_addrs(
            _make_connection(), [item]
        )
        assert addrs == [40001]

    def test_resolve_invalid_address_raises(self) -> None:
        """无效地址应抛出 ValueError。"""
        adapter = ModbusRtuSourceAcquisitionAdapter()
        item = _make_item("reg1", "not_a_number")
        with pytest.raises(ValueError, match="Cannot resolve"):
            adapter._resolve_reg_addrs(
                _make_connection(), [item]
            )


class TestModbusRtuAdapterConnectionParams:
    """连接参数提取测试。"""

    def test_build_reader_from_connection_host(self) -> None:
        """应从 connection.host 提取串口路径。"""
        reader = ModbusRtuSourceAcquisitionAdapter._build_reader(
            _make_execution(),
            _make_connection("/dev/ttyUSB0"),
        )
        assert reader._serial_port == "/dev/ttyUSB0"
        assert reader._baudrate == 9600

    def test_missing_serial_port_raises(self) -> None:
        """缺少串口路径时应抛出 ValueError。"""
        conn = SourceConnectionData(
            host="", port=0, ied_name="rtu", ld_name="rtu",
            namespace_uri="", params={},
        )
        with pytest.raises(ValueError, match="serial_port"):
            ModbusRtuSourceAcquisitionAdapter._build_reader(
                _make_execution(), conn
            )


class TestModbusRtuAdapterSubscription:
    """订阅模式不支持测试。"""

    @pytest.mark.asyncio
    async def test_start_subscription_raises(self) -> None:
        """Modbus RTU 不支持订阅，应抛出错误。"""
        adapter = ModbusRtuSourceAcquisitionAdapter()
        with pytest.raises(SourceSubscriptionUnsupportedError):
            await adapter.start_subscription(
                _make_execution(),
                _make_connection(),
                [_make_item()],
                state_received=AsyncMock(),
            )
