"""MQTT 全链路采集集成测试。

验证完整三层采集链路：
1. shared/source/mqtt client backend（MqttClientBackend）
2. ingest adapter（MqttSourceAcquisitionAdapter）
3. batch 转换

测试阶段：模块集成期验证 (simulator) — 使用 mock MqttClientBackend 模拟 MQTT broker 响应。
不能证明：真实 MQTT broker 连接行为和网络故障恢复。
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


def _make_execution() -> AcquisitionExecutionOptions:
    return AcquisitionExecutionOptions(
        protocol="mqtt",
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


def _make_connection() -> SourceConnectionData:
    return SourceConnectionData(
        host="localhost",
        port=1883,
        ied_name="mqtt-broker",
        ld_name="mqtt-ld",
        namespace_uri="mqtt://",
        params={},
    )


def _make_item(key: str = "t1", relative_path: str = "sensor/temp") -> AcquisitionItemData:
    return AcquisitionItemData(
        key=key,
        relative_path=relative_path,
        profile_item_id=1,
    )


@pytest.mark.asyncio
async def test_mqtt_full_chain_read_with_mock_backend() -> None:
    """全链路：mock backend -> MQTT adapter -> batch。

    使用 mock MqttClientBackend 模拟 broker subscribe 返回消息，
    验证 adapter 正确转换消息为 AcquiredNodeStateBatch。
    """
    msg = MqttMessage(topic="sensor/temperature", payload="25.5")
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
        batch = await adapter.read(
            _make_execution(),
            _make_connection(),
            [_make_item("t1", "sensor/temperature")],
        )

        assert isinstance(batch, AcquiredNodeStateBatch)
        assert batch.availability_status == "VALID"
        assert len(batch.values) == 1
        val = batch.values[0]
        assert val.node_key == "t1"
        assert val.value == "25.5"
        assert val.quality == "GOOD"
        assert "mqtt_topic" in val.attributes
        assert val.attributes["mqtt_topic"] == "sensor/temperature"

    mock_client.connect.assert_called()
    mock_client.disconnect.assert_called()


@pytest.mark.asyncio
async def test_mqtt_full_chain_empty_messages_raises_error() -> None:
    """MQTT 全链路：无消息订阅应抛出 SourceReadError。"""
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
async def test_mqtt_full_chain_connect_failure() -> None:
    """MQTT 全链路：连接失败时适配器应抛出 SourceReadError。"""
    mock_client = MagicMock()
    mock_client.connect = AsyncMock(
        side_effect=ConnectionError("Connection refused")
    )

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
