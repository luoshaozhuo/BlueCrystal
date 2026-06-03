"""IEC 101 全链路采集集成测试。

被验证对象：IEC 101 shared_source backend + ingest adapter 全链路。
测试阶段：模块集成期验证 (simulator) — 使用 mock Iec101SerialBackend 模拟串口响应。
不能证明：真实 RS-232 串口设备通信、IEC 101 设备互操作性、interrogation 时序。

Mock 策略：
- 通过 mock 注入 backend，替代真实串口操作；
- 模拟正常 interrogation 响应和异常响应；
- adapter -> reader -> backend 的三层调用链完整；
- E2E 边界：mock serial backend -> reader -> ingest adapter -> AcquiredNodeStateBatch。

环境说明：无真实串口设备时，本测试提供模块集成期验证 (simulator) 级别覆盖。
跨模块联调期验证（真实串口）标记为 MISSING_ENVIRONMENT。
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from whale.ingest.adapters.source.iec101_source_acquisition_adapter import (
    Iec101SourceAcquisitionAdapter,
)
from whale.ingest.ports.source.source_acquisition_port import SourceReadError
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.iec101.backends.base import RawIec101ReadResult


def _make_connection(serial_port: str = "/dev/ttyUSB0") -> SourceConnectionData:
    return SourceConnectionData(
        host=serial_port,
        port=0,
        ied_name="iec101-ied",
        ld_name="iec101-ld",
        namespace_uri="iec101://",
        params={
            "baudrate": 9600,
            "parity": "E",
            "stop_bits": 1,
            "data_bits": 8,
            "link_address": 1,
            "common_address": 1,
        },
    )


def _make_execution() -> AcquisitionExecutionOptions:
    return AcquisitionExecutionOptions(
        protocol="iec101",
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


@pytest.mark.asyncio
async def test_iec101_full_chain_single_ioa() -> None:
    """全链路：mock serial backend -> reader -> adapter -> batch（单个 IOA）。

    验证 interrogation 读取单个 IOA 的完整数据流：
    1. Adapter 解析 relative_path 为 IOA
    2. Reader read 正确调用
    3. 原始结果转换为 AcquiredNodeStateBatch
    4. IEC 101 类型标签正确传递
    """
    raw = RawIec101ReadResult(
        ok=True,
        values={100: ("M_ME_NC_1", "42.500")},
        response_timestamp=datetime(2026, 6, 2, 12, 0, 0, tzinfo=UTC),
    )

    mock_reader = MagicMock()
    mock_reader.read = AsyncMock(return_value=raw)
    mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
    mock_reader.__aexit__ = AsyncMock(return_value=None)

    adapter = Iec101SourceAcquisitionAdapter()

    with patch(
        "whale.ingest.adapters.source.iec101_source_acquisition_adapter.Iec101SourceReader",
        return_value=mock_reader,
    ):
        batch = await adapter.read(
            _make_execution(),
            _make_connection(),
            [AcquisitionItemData(
                key="temp1", relative_path="100", profile_item_id=1,
            )],
        )

    assert isinstance(batch, AcquiredNodeStateBatch)
    assert len(batch.values) == 1
    assert batch.values[0].value == "42.500"
    assert batch.values[0].quality == "GOOD"
    assert batch.values[0].attributes.get("iec101_type") == "M_ME_NC_1"
    assert batch.availability_status == "VALID"


@pytest.mark.asyncio
async def test_iec101_full_chain_multi_ioa() -> None:
    """全链路：多 IOA interrogation 读取。

    验证读取多个 IOA 时所有值正确映射。
    """
    raw = RawIec101ReadResult(
        ok=True,
        values={
            100: ("M_ME_NC_1", "42.500"),
            101: ("M_ME_NB_1", "32767"),
            102: ("M_SP_NA_1", "1"),
        },
        response_timestamp=datetime(2026, 6, 2, 12, 0, 0, tzinfo=UTC),
    )

    mock_reader = MagicMock()
    mock_reader.read = AsyncMock(return_value=raw)
    mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
    mock_reader.__aexit__ = AsyncMock(return_value=None)

    adapter = Iec101SourceAcquisitionAdapter()

    items = [
        AcquisitionItemData(key="v", relative_path="100", profile_item_id=1),
        AcquisitionItemData(key="v", relative_path="101", profile_item_id=2),
        AcquisitionItemData(key="v", relative_path="102", profile_item_id=3),
    ]

    with patch(
        "whale.ingest.adapters.source.iec101_source_acquisition_adapter.Iec101SourceReader",
        return_value=mock_reader,
    ):
        batch = await adapter.read(
            _make_execution(), _make_connection(), items,
        )

    assert len(batch.values) == 3
    assert batch.values[0].value == "42.500"
    assert batch.values[1].value == "32767"
    assert batch.values[2].value == "1"


@pytest.mark.asyncio
async def test_iec101_full_chain_oserror_mapping() -> None:
    """全链路：OSError 应映射为 SourceReadError（serial_port_error）。

    验证串口通信异常被正确转换为 ingest 错误体系。
    """
    mock_reader = MagicMock()
    mock_reader.read = AsyncMock(side_effect=OSError("No such device"))
    mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
    mock_reader.__aexit__ = AsyncMock(return_value=None)

    adapter = Iec101SourceAcquisitionAdapter()

    with patch(
        "whale.ingest.adapters.source.iec101_source_acquisition_adapter.Iec101SourceReader",
        return_value=mock_reader,
    ):
        with pytest.raises(SourceReadError, match="serial_port_error"):
            await adapter.read(
                _make_execution(),
                _make_connection(),
                [AcquisitionItemData(key="v", relative_path="100", profile_item_id=1)],
            )


@pytest.mark.asyncio
async def test_iec101_full_chain_ioa_not_found() -> None:
    """全链路：IOA 不在响应中时应标记 UNKNOWN 质量。

    验证当请求的 IOA 不在设备响应中时，适配器正确处理
    缺失值：标记 UNKNOWN 质量并附带 warning 属性。
    """
    raw = RawIec101ReadResult(
        ok=True,
        values={200: ("M_ME_NC_1", "77.0")},  # 只有 IOA 200
        response_timestamp=datetime(2026, 6, 2, 12, 0, 0, tzinfo=UTC),
    )

    mock_reader = MagicMock()
    mock_reader.read = AsyncMock(return_value=raw)
    mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
    mock_reader.__aexit__ = AsyncMock(return_value=None)

    adapter = Iec101SourceAcquisitionAdapter()

    with patch(
        "whale.ingest.adapters.source.iec101_source_acquisition_adapter.Iec101SourceReader",
        return_value=mock_reader,
    ):
        batch = await adapter.read(
            _make_execution(),
            _make_connection(),
            [AcquisitionItemData(key="v", relative_path="100", profile_item_id=1)],
        )

    assert batch.values[0].quality == "UNKNOWN"
    assert "ioa_not_found_in_response" in str(
        batch.values[0].attributes.get("warning", "")
    )
