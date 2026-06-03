"""HTTP REST 采集适配器单元测试。

被验证对象：``whale.ingest.adapters.source.http_rest_source_acquisition_adapter.HttpRestSourceAcquisitionAdapter``。
测试阶段：开发期验证 (unit/mock) — 使用 mock HttpRestClientBackend 模拟 HTTP 服务器。
不能证明：真实 HTTP 服务器连接、TLS 握手、JSON Path 复杂路径。

依赖：
- mock whale.shared.source.http_rest.client.HttpRestClientBackend；
- 不依赖外部 HTTP 服务器。
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


def _make_execution(protocol: str = "http_rest") -> AcquisitionExecutionOptions:
    return AcquisitionExecutionOptions(
        protocol=protocol,
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


def _make_connection(host: str = "localhost", port: int = 8080) -> SourceConnectionData:
    return SourceConnectionData(
        host=host,
        port=port,
        ied_name="http-ied",
        ld_name="http-ld",
        namespace_uri="http://",
        params={"base_url": "http://localhost:8080"},
    )


def _make_item(
    key: str = "temp1",
    relative_path: str = "/api/temperature",
) -> AcquisitionItemData:
    return AcquisitionItemData(
        key=key,
        relative_path=relative_path,
        profile_item_id=1,
    )


@pytest.mark.asyncio
async def test_http_adapter_read_returns_batch() -> None:
    """HTTP 适配器 read 应在 200 响应后返回 AcquiredNodeStateBatch。"""
    body = json.dumps({"temperature": 25.5})
    mock_response = HttpResponseData(
        ok=True,
        status_code=200,
        body=body,
        json_body={"temperature": 25.5},
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
        assert len(batch.values) == 1
        assert batch.values[0].quality == "GOOD"
        assert "temperature" in batch.values[0].value or "25.5" in batch.values[0].value


@pytest.mark.asyncio
async def test_http_adapter_handles_error_response() -> None:
    """HTTP 适配器在 4xx/5xx 响应时标记 BAD quality。"""
    mock_response = HttpResponseData(
        ok=False,
        status_code=500,
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
async def test_http_adapter_supports_subscription_is_false() -> None:
    """HTTP 适配器 supports_subscription 应返回 False。"""
    adapter = HttpRestSourceAcquisitionAdapter()
    result = adapter.supports_subscription(_make_execution(), _make_connection())
    assert result is False


def test_http_adapter_parse_json_path() -> None:
    """JSON Path 提取应从响应 JSON 中正确提取值。"""
    data = {"data": {"temperature": 25.5, "humidity": 60}}

    # 简单键访问
    result = HttpRestSourceAcquisitionAdapter._resolve_json_path(data, "$.data.temperature")
    assert result == 25.5

    # 第一级键
    result = HttpRestSourceAcquisitionAdapter._resolve_json_path(data, "$.data")
    assert result == {"temperature": 25.5, "humidity": 60}

    # 无效路径
    result = HttpRestSourceAcquisitionAdapter._resolve_json_path(data, "$.nonexistent")
    assert result is None


def test_http_adapter_parse_relative_path() -> None:
    """relative_path 解析应正确分离 HTTP 路径和 JSON Path。"""
    path, jp = HttpRestSourceAcquisitionAdapter._parse_relative_path("/api/data#$.value")
    assert path == "/api/data"
    assert jp == "$.value"

    path, jp = HttpRestSourceAcquisitionAdapter._parse_relative_path("/api/data")
    assert path == "/api/data"
    assert jp is None

    path, jp = HttpRestSourceAcquisitionAdapter._parse_relative_path("")
    assert path == "/"
    assert jp is None
