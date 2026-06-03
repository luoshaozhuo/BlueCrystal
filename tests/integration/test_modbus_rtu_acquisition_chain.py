"""Modbus RTU 全链路采集集成测试。

被验证对象：Modbus RTU shared_source backend + ingest adapter 全链路。
证据等级：L3 simulator — 使用 mock ModbusRtuSerialBackend 模拟串口响应。
不能证明：真实 RS-485 串口设备通信、电气特性、线路噪声、时序约束。

Mock 策略：
- 通过 mock 注入 backend，替代真实串口操作；
- 模拟正常 FC03 读取响应和异常响应；
- adapter -> reader -> backend 的三层调用链完整；
- E2E 边界：mock serial backend -> reader -> ingest adapter -> AcquiredNodeStateBatch。

环境说明：无真实串口设备时，本测试提供 L3 simulator 级别覆盖。
L4 integration（真实串口）标记为 environment-pending。
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from whale.ingest.adapters.source.modbus_rtu_source_acquisition_adapter import (
    ModbusRtuSourceAcquisitionAdapter,
)
from whale.ingest.ports.source.source_acquisition_port import SourceReadError
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.modbus_rtu.backends.base import (
    ModbusRtuPreparedReadPlan,
    RawModbusRtuReadResult,
)


def _make_connection(serial_port: str = "/dev/ttyUSB0") -> SourceConnectionData:
    return SourceConnectionData(
        host=serial_port,
        port=0,
        ied_name="rtu-ied",
        ld_name="rtu-ld",
        namespace_uri="modbus_rtu://",
        params={
            "baudrate": 9600,
            "parity": "N",
            "stop_bits": 1,
            "data_bits": 8,
            "modbus_unit_id": 1,
        },
    )


def _make_execution() -> AcquisitionExecutionOptions:
    return AcquisitionExecutionOptions(
        protocol="modbus_rtu",
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


@pytest.mark.asyncio
async def test_modbus_rtu_full_chain_single_register() -> None:
    """全链路：mock serial backend -> reader -> adapter -> batch（单寄存器）。

    验证读取单个 holding register 的完整数据流：
    1. Adapter 解析 relative_path 为寄存器地址
    2. Reader prepare_read + read_prepared 正确调用
    3. 原始结果转换为 AcquiredNodeStateBatch
    4. 值和时间戳正确传递
    """
    raw = RawModbusRtuReadResult(
        ok=True,
        values=(48879,),  # 0xBEEF
        response_timestamp=datetime(2026, 6, 2, 12, 0, 0, tzinfo=UTC),
    )

    mock_reader = MagicMock()
    mock_reader.prepare_read = MagicMock(return_value=ModbusRtuPreparedReadPlan(
        reg_addrs=(100,), unit_id=1,
    ))
    mock_reader.read_prepared = AsyncMock(return_value=raw)
    mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
    mock_reader.__aexit__ = AsyncMock(return_value=None)

    adapter = ModbusRtuSourceAcquisitionAdapter()

    with patch(
        "whale.ingest.adapters.source.modbus_rtu_source_acquisition_adapter.ModbusRtuSourceReader",
        return_value=mock_reader,
    ):
        batch = await adapter.read(
            _make_execution(),
            _make_connection(),
            [AcquisitionItemData(key="reg100", relative_path="100", profile_item_id=1)],
        )

    assert isinstance(batch, AcquiredNodeStateBatch)
    assert len(batch.values) == 1
    assert batch.values[0].value == "48879"
    assert batch.values[0].quality == "GOOD"
    assert batch.availability_status == "VALID"
    assert batch.attributes["acquisition_kind"] == "read"
    assert batch.client_received_at is not None
    assert batch.client_processed_at is not None


@pytest.mark.asyncio
async def test_modbus_rtu_full_chain_multi_register() -> None:
    """全链路：多寄存器批量读取。

    验证读取多个寄存器时值的顺序和数量正确。
    """
    raw = RawModbusRtuReadResult(
        ok=True,
        values=(100, 200, 300),
        response_timestamp=datetime(2026, 6, 2, 12, 0, 0, tzinfo=UTC),
    )

    mock_reader = MagicMock()
    mock_reader.prepare_read = MagicMock(return_value=ModbusRtuPreparedReadPlan(
        reg_addrs=(100, 101, 102), unit_id=1,
    ))
    mock_reader.read_prepared = AsyncMock(return_value=raw)
    mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
    mock_reader.__aexit__ = AsyncMock(return_value=None)

    adapter = ModbusRtuSourceAcquisitionAdapter()

    items = [
        AcquisitionItemData(key="r0", relative_path="100", profile_item_id=1),
        AcquisitionItemData(key="r1", relative_path="101", profile_item_id=2),
        AcquisitionItemData(key="r2", relative_path="102", profile_item_id=3),
    ]

    with patch(
        "whale.ingest.adapters.source.modbus_rtu_source_acquisition_adapter.ModbusRtuSourceReader",
        return_value=mock_reader,
    ):
        batch = await adapter.read(
            _make_execution(), _make_connection(), items,
        )

    assert len(batch.values) == 3
    assert batch.values[0].value == "100"
    assert batch.values[1].value == "200"
    assert batch.values[2].value == "300"


@pytest.mark.asyncio
async def test_modbus_rtu_full_chain_oserror_mapping() -> None:
    """全链路：OSError 应映射为 SourceReadError（serial_port_error）。

    验证串口通信异常被正确转换为 ingest 错误体系。
    """
    mock_reader = MagicMock()
    mock_reader.prepare_read = MagicMock(side_effect=OSError("No such device"))
    mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
    mock_reader.__aexit__ = AsyncMock(return_value=None)

    adapter = ModbusRtuSourceAcquisitionAdapter()

    with patch(
        "whale.ingest.adapters.source.modbus_rtu_source_acquisition_adapter.ModbusRtuSourceReader",
        return_value=mock_reader,
    ):
        with pytest.raises(SourceReadError, match="serial_port_error"):
            await adapter.read(
                _make_execution(),
                _make_connection(),
                [AcquisitionItemData(key="r0", relative_path="100", profile_item_id=1)],
            )


@pytest.mark.asyncio
async def test_modbus_rtu_full_chain_crc_error_from_backend() -> None:
    """全链路：CRC 错误从 backend 传播到 adapter。

    验证协议层错误（CRC 校验失败）的正确错误传播路径。
    """
    raw = RawModbusRtuReadResult(
        ok=False,
        values=(),
        error_reason="crc_error",
        exception="CRC 校验失败: 收到 0x1234，期望 0x5678",
    )

    mock_reader = MagicMock()
    mock_reader.prepare_read = MagicMock(return_value=MagicMock())
    mock_reader.read_prepared = AsyncMock(return_value=raw)
    mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
    mock_reader.__aexit__ = AsyncMock(return_value=None)

    adapter = ModbusRtuSourceAcquisitionAdapter()

    with patch(
        "whale.ingest.adapters.source.modbus_rtu_source_acquisition_adapter.ModbusRtuSourceReader",
        return_value=mock_reader,
    ):
        with pytest.raises(SourceReadError, match="crc_error"):
            await adapter.read(
                _make_execution(),
                _make_connection(),
                [AcquisitionItemData(key="r0", relative_path="100", profile_item_id=1)],
            )
