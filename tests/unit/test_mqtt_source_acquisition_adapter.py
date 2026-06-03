"""MQTT 采集适配器单元测试。

被验证对象：``whale.ingest.adapters.source.mqtt_source_acquisition_adapter.MqttSourceAcquisitionAdapter``。
测试阶段：开发期验证 (unit/mock) — 使用 mock MqttClientBackend 模拟 MQTT broker。
不能证明：真实 broker 连接、网络故障恢复。

依赖：
- mock whale.shared.source.mqtt.client.MqttClientBackend；
- 不依赖外部 MQTT broker。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from whale.ingest.adapters.source.mqtt_source_acquisition_adapter import (
    MqttSourceAcquisitionAdapter,
)
from whale.ingest.ports.source.source_acquisition_port import SourceReadError
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.mqtt.client import MqttMessage, MqttSubscribeResult


def _make_execution(protocol: str = "mqtt") -> AcquisitionExecutionOptions:
    return AcquisitionExecutionOptions(
        protocol=protocol,
        transport="MQTT",
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


def _make_connection(host: str = "localhost", port: int = 1883) -> SourceConnectionData:
    return SourceConnectionData(
        host=host,
        port=port,
        ied_name="mqtt-ied",
        ld_name="mqtt-ld",
        namespace_uri="mqtt://",
        params={},
    )


def _make_item(key: str = "temp1", relative_path: str = "sensor/temperature") -> AcquisitionItemData:
    return AcquisitionItemData(
        key=key,
        relative_path=relative_path,
        profile_item_id=1,
    )


def _make_message(topic: str = "sensor/temperature", payload: str = "25.5") -> MqttMessage:
    return MqttMessage(topic=topic, payload=payload)


@pytest.mark.asyncio
async def test_mqtt_adapter_read_returns_batch() -> None:
    """MQTT 适配器 read 应在收到消息后返回 AcquiredNodeStateBatch。"""
    msg = _make_message()
    mock_result = MqttSubscribeResult(
        ok=True,
        messages=(msg,),
        topic_filter="sensor/temperature",
    )

    mock_client = MagicMock()
    mock_client.connect = AsyncMock()
    mock_client.subscribe_and_receive = AsyncMock(return_value=mock_result)
    mock_client.disconnect = AsyncMock()

    with patch(
        "whale.ingest.adapters.source.mqtt_source_acquisition_adapter.MqttClientBackend",
        return_value=mock_client,
    ):
        adapter = MqttSourceAcquisitionAdapter()
        execution = _make_execution()
        connection = _make_connection()
        items = [_make_item()]

        batch = await adapter.read(execution, connection, items)

        assert isinstance(batch, AcquiredNodeStateBatch)
        assert batch.availability_status == "VALID"
        assert len(batch.values) == 1
        assert batch.values[0].value == "25.5"
        assert batch.values[0].quality == "GOOD"
        assert batch.values[0].node_key == "temp1"


@pytest.mark.asyncio
async def test_mqtt_adapter_supports_subscription_is_false() -> None:
    """MQTT 适配器 supports_subscription 应返回 False。"""
    adapter = MqttSourceAcquisitionAdapter()
    result = adapter.supports_subscription(_make_execution(), _make_connection())
    assert result is False


@pytest.mark.asyncio
async def test_mqtt_adapter_read_raises_on_connection_failure() -> None:
    """MQTT 适配器在连接失败时应抛出 SourceReadError。"""
    mock_client = MagicMock()
    mock_client.connect = AsyncMock(side_effect=ConnectionError("simulated failure"))

    with patch(
        "whale.ingest.adapters.source.mqtt_source_acquisition_adapter.MqttClientBackend",
        return_value=mock_client,
    ):
        adapter = MqttSourceAcquisitionAdapter()
        with pytest.raises(SourceReadError, match="MQTT connection failed"):
            await adapter.read(
                _make_execution(),
                _make_connection(),
                [_make_item()],
            )


@pytest.mark.asyncio
async def test_mqtt_adapter_read_raises_on_subscribe_failure() -> None:
    """MQTT 适配器在订阅失败时应抛出 SourceReadError。"""
    mock_result = MqttSubscribeResult(
        ok=False,
        messages=(),
        error_reason="no_messages_received",
    )
    mock_client = MagicMock()
    mock_client.connect = AsyncMock()
    mock_client.subscribe_and_receive = AsyncMock(return_value=mock_result)
    mock_client.disconnect = AsyncMock()

    with patch(
        "whale.ingest.adapters.source.mqtt_source_acquisition_adapter.MqttClientBackend",
        return_value=mock_client,
    ):
        adapter = MqttSourceAcquisitionAdapter()
        with pytest.raises(SourceReadError, match="subscribe failed"):
            await adapter.read(
                _make_execution(),
                _make_connection(),
                [_make_item()],
            )


@pytest.mark.asyncio
async def test_mqtt_adapter_handles_multiple_items() -> None:
    """MQTT 适配器应正确处理多 item 场景（消息数少于 item 数时填充 UNKNOWN）。"""
    msgs = (
        _make_message("sensor/t1", "10.0"),
        _make_message("sensor/t2", "20.0"),
    )
    mock_result = MqttSubscribeResult(ok=True, messages=msgs)

    mock_client = MagicMock()
    mock_client.connect = AsyncMock()
    mock_client.subscribe_and_receive = AsyncMock(return_value=mock_result)
    mock_client.disconnect = AsyncMock()

    with patch(
        "whale.ingest.adapters.source.mqtt_source_acquisition_adapter.MqttClientBackend",
        return_value=mock_client,
    ):
        adapter = MqttSourceAcquisitionAdapter()
        items = [
            _make_item("t1", "sensor/t1"),
            _make_item("t2", "sensor/t2"),
            _make_item("t3", "sensor/t3"),
        ]
        batch = await adapter.read(_make_execution(), _make_connection(), items)

        assert len(batch.values) == 3
        assert batch.values[0].quality == "GOOD"
        assert batch.values[1].quality == "GOOD"
        assert batch.values[2].quality == "UNKNOWN"

    mock_client.disconnect.assert_called()
