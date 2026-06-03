"""HTTP REST 全链路采集集成测试。

验证完整三层采集链路：
1. shared/source/http_rest client backend（HttpRestClientBackend）
2. ingest adapter（HttpRestSourceAcquisitionAdapter）
3. batch 转换

证据等级：L3 simulator — 使用 mock HttpRestClientBackend 模拟 HTTP 服务器响应。
不能证明：真实 HTTP 服务器连接行为和 TLS 握手。
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from whale.ingest.adapters.source.http_rest_source_acquisition_adapter import (
    HttpRestSourceAcquisitionAdapter,
)
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.http_rest.client import HttpResponseData


def _make_execution() -> AcquisitionExecutionOptions:
    return AcquisitionExecutionOptions(
        protocol="http_rest",
        transport="HTTP",
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
        host="localhost",
        port=8080,
        ied_name="http-server",
        ld_name="http-ld",
        namespace_uri="http://",
        params={"base_url": "http://localhost:8080"},
    )


def _make_item(
    key: str = "temp1", relative_path: str = "/api/temperature"
) -> AcquisitionItemData:
    return AcquisitionItemData(
        key=key,
        relative_path=relative_path,
        profile_item_id=1,
    )


def _make_http_response(
    status_code: int = 200,
    body: str | None = None,
    json_body: dict | None = None,
    ok: bool = True,
    error_reason: str | None = None,
) -> HttpResponseData:
    if body is None and json_body is not None:
        body = json.dumps(json_body)
    elif body is None:
        body = "{}"
    return HttpResponseData(
        ok=ok,
        status_code=status_code,
        body=body,
        json_body=json_body,
        error_reason=error_reason,
    )


@pytest.mark.asyncio
async def test_http_rest_full_chain_read_with_mock_backend() -> None:
    """全链路：mock backend -> HTTP REST adapter -> batch。

    使用 mock HttpRestClientBackend 模拟 HTTP 200 响应，
    验证 adapter 正确转换响应为 AcquiredNodeStateBatch。
    """
    mock_response = _make_http_response(
        status_code=200,
        body=json.dumps({"temperature": 22.3}),
        json_body={"temperature": 22.3},
    )
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch(
        "whale.ingest.adapters.source.http_rest_source_acquisition_adapter.HttpRestClientBackend",
        return_value=mock_client,
    ):
        adapter = HttpRestSourceAcquisitionAdapter()
        batch = await adapter.read(
            _make_execution(),
            _make_connection(),
            [_make_item()],
        )

        assert isinstance(batch, AcquiredNodeStateBatch)
        assert batch.availability_status == "VALID"
        assert len(batch.values) == 1
        val = batch.values[0]
        assert val.node_key == "temp1"
        assert val.quality == "GOOD"
        assert "http_status" in val.attributes
        assert val.attributes["http_status"] == "200"


@pytest.mark.asyncio
async def test_http_rest_full_chain_error_response() -> None:
    """HTTP 500 错误时，节点应标记为 BAD quality。"""
    mock_response = _make_http_response(
        status_code=500,
        ok=False,
        error_reason="HTTP 500",
    )
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch(
        "whale.ingest.adapters.source.http_rest_source_acquisition_adapter.HttpRestClientBackend",
        return_value=mock_client,
    ):
        adapter = HttpRestSourceAcquisitionAdapter()
        batch = await adapter.read(
            _make_execution(),
            _make_connection(),
            [_make_item()],
        )

        assert batch.values[0].quality == "BAD"


@pytest.mark.asyncio
async def test_http_rest_full_chain_json_path_extraction() -> None:
    """JSON Path 提取应正确从嵌套 JSON 中取值。"""
    body = json.dumps({"data": {"value": 42}})
    mock_response = _make_http_response(
        status_code=200,
        body=body,
        json_body={"data": {"value": 42}},
    )
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch(
        "whale.ingest.adapters.source.http_rest_source_acquisition_adapter.HttpRestClientBackend",
        return_value=mock_client,
    ):
        adapter = HttpRestSourceAcquisitionAdapter()
        item = _make_item("val", "/api/data#$.data.value")
        batch = await adapter.read(
            _make_execution(),
            _make_connection(),
            [item],
        )

        assert batch.values[0].quality == "GOOD"
        # JSON path 提取应返回 "42"
        assert batch.values[0].value == "42"


@pytest.mark.asyncio
async def test_http_rest_full_chain_multiple_items() -> None:
    """多 item 采集应分别发送请求并返回对应值。"""
    mock_resp1 = _make_http_response(
        status_code=200,
        body="temp_value",
    )
    mock_resp2 = _make_http_response(
        status_code=200,
        body="humid_value",
    )
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=[mock_resp1, mock_resp2])

    with patch(
        "whale.ingest.adapters.source.http_rest_source_acquisition_adapter.HttpRestClientBackend",
        return_value=mock_client,
    ):
        adapter = HttpRestSourceAcquisitionAdapter()
        items = [
            _make_item("t", "/api/temp"),
            _make_item("h", "/api/humid"),
        ]
        batch = await adapter.read(_make_execution(), _make_connection(), items)

        assert len(batch.values) == 2
        assert batch.values[0].quality == "GOOD"
        assert batch.values[1].quality == "GOOD"
