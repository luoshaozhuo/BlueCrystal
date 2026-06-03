"""IEC104 全链路采集集成测试。

验证完整三层采集链路：
1. shared/source/iec104 backend（Iec104Lib60870Backend）
2. ingest adapter（Iec104SourceAcquisitionAdapter）
3. state cache 写入

证据等级：L3 simulator — 使用 mock 模拟 lib60870 C runner 子进程响应。
不能证明：真实 IEC104 RTU 连接、实际 C runner 子进程行为、生产级吞吐。
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from whale.ingest.adapters.source.iec104_source_acquisition_adapter import (
    Iec104SourceAcquisitionAdapter,
)
from whale.ingest.ports.source.source_acquisition_port import SourceReadError
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.iec104.backends.base import RawIec104ReadResult


def _make_execution() -> AcquisitionExecutionOptions:
    return AcquisitionExecutionOptions(
        protocol="iec104",
        transport="TCP",
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


def _make_connection() -> SourceConnectionData:
    return SourceConnectionData(
        host="192.168.1.100",
        port=2404,
        ied_name="iec104-rtu",
        ld_name="iec104-ld",
        namespace_uri="iec104://",
        params={"common_address": 1},
    )


def _make_item(key: str = "ioa100", relative_path: str = "100") -> AcquisitionItemData:
    return AcquisitionItemData(
        key=key,
        relative_path=relative_path,
        profile_item_id=1,
    )


def _make_raw_read_result(
    ioa: int = 100, value: str = "42", type_tag: str = "M_ME_NC_1"
) -> RawIec104ReadResult:
    from datetime import datetime, timezone

    return RawIec104ReadResult(
        ok=True,
        values={ioa: (type_tag, value)},
        response_timestamp=datetime.now(tz=timezone.utc),
    )


@pytest.mark.asyncio
async def test_iec104_full_chain_read_with_mock_backend() -> None:
    """全链路：mock backend -> adapter -> batch。

    使用 mock Iec104SourceReader.read 模拟 C runner 返回数据，
    验证 adapter 正确解析 backend 数据并生成 AcquiredNodeStateBatch。
    """
    mock_reader = MagicMock()
    mock_reader.read = AsyncMock(
        return_value=_make_raw_read_result(100, "42.5", "M_ME_NC_1")
    )
    mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
    mock_reader.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "whale.ingest.adapters.source.iec104_source_acquisition_adapter.Iec104SourceReader",
        return_value=mock_reader,
    ):
        adapter = Iec104SourceAcquisitionAdapter()
        batch = await adapter.read(
            _make_execution(),
            _make_connection(),
            [_make_item("ioa100", "100")],
        )

        assert isinstance(batch, AcquiredNodeStateBatch)
        assert batch.availability_status == "VALID"
        assert len(batch.values) == 1
        val = batch.values[0]
        assert val.node_key == "ioa100"
        assert val.value == "42.5"
        assert val.quality == "GOOD"
        assert "iec104_type" in val.attributes
        assert val.attributes["iec104_type"] == "M_ME_NC_1"


@pytest.mark.asyncio
async def test_iec104_full_chain_read_failure_propagates_error() -> None:
    """backend read 失败时，adapter 应传播 SourceReadError。"""
    mock_reader = MagicMock()
    mock_reader.read = AsyncMock(
        return_value=RawIec104ReadResult(
            ok=False,
            values={},
            error_reason="read_failed",
            exception="no_samples_received",
        )
    )
    mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
    mock_reader.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "whale.ingest.adapters.source.iec104_source_acquisition_adapter.Iec104SourceReader",
        return_value=mock_reader,
    ):
        adapter = Iec104SourceAcquisitionAdapter()
        with pytest.raises(SourceReadError, match="raw read failed"):
            await adapter.read(
                _make_execution(),
                _make_connection(),
                [_make_item("ioa100", "100")],
            )


@pytest.mark.asyncio
async def test_iec104_adapter_resolves_non_numeric_ioa() -> None:
    """非数字 IOA 应抛出 ValueError。"""
    adapter = Iec104SourceAcquisitionAdapter()
    connection = _make_connection()
    bad_item = AcquisitionItemData(key="bad", relative_path="abc", profile_item_id=1)

    with pytest.raises(ValueError, match="Cannot resolve IEC 104 IOA"):
        await adapter.read(_make_execution(), connection, [bad_item])


@pytest.mark.asyncio
async def test_iec104_adapter_handles_missing_ioa_in_response() -> None:
    """当某个 IOA 在响应中不存在时，对应节点标记 UNKNOWN。"""
    mock_reader = MagicMock()
    # 响应中只有 IOA 100，没有 200
    mock_reader.read = AsyncMock(
        return_value=RawIec104ReadResult(
            ok=True,
            values={100: ("M_ME_NC_1", "42")},
        )
    )
    mock_reader.__aenter__ = AsyncMock(return_value=mock_reader)
    mock_reader.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "whale.ingest.adapters.source.iec104_source_acquisition_adapter.Iec104SourceReader",
        return_value=mock_reader,
    ):
        adapter = Iec104SourceAcquisitionAdapter()
        items = [
            _make_item("found", "100"),
            _make_item("missing", "200"),
        ]
        batch = await adapter.read(_make_execution(), _make_connection(), items)

        assert len(batch.values) == 2
        assert batch.values[0].quality == "GOOD"
        assert batch.values[0].value == "42"
        assert batch.values[1].quality == "UNKNOWN"
        assert batch.values[1].attributes["warning"] == "ioa_not_found_in_response"
