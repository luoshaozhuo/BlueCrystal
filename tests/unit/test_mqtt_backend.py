"""MQTT client backend 单元测试。

被验证对象：``whale.shared.source.mqtt.client.MqttClientBackend``。
测试阶段：开发期验证 (unit/mock) — 使用 asyncio mock stream 模拟 MQTT broker 通信。
不能证明：真实 broker 连接行为、网络故障恢复、大规模消息吞吐。
"""
from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from whale.shared.source.mqtt.client import MqttClientBackend, MqttMessage, MqttSubscribeResult


def _build_connack_bytes() -> bytes:
    return bytes([0x20, 0x02, 0x00, 0x00])


def _build_suback_bytes() -> bytes:
    return bytes([0x90, 0x03, 0x00, 0x01, 0x00])


def _build_publish_bytes(topic: str, payload: str) -> bytes:
    topic_bytes = topic.encode("utf-8")
    payload_bytes = payload.encode("utf-8")
    remaining = len(topic_bytes) + 2 + len(payload_bytes)
    result = bytearray([0x30])
    value = remaining
    while True:
        byte = value % 128
        value //= 128
        if value > 0:
            byte |= 0x80
        result.append(byte)
        if value == 0:
            break
    result.extend([len(topic_bytes) >> 8, len(topic_bytes) & 0xFF])
    result.extend(topic_bytes)
    result.extend(payload_bytes)
    return bytes(result)


class _ByteBufferReader:
    """模拟 asyncio.StreamReader，从字节缓冲区按需读取。"""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._offset = 0

    async def readexactly(self, n: int) -> bytes:
        remaining = len(self._data) - self._offset
        if remaining < n:
            raise asyncio.IncompleteReadError(
                partial=self._data[self._offset:], expected=n
            )
        chunk = self._data[self._offset:self._offset + n]
        self._offset += n
        return chunk

    async def readline(self) -> bytes:
        return b""


class _FakeStreamWriter:
    """模拟 asyncio.StreamWriter。"""

    def __init__(self) -> None:
        self.written: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.written.append(data)

    async def drain(self) -> None:
        pass

    def close(self) -> None:
        pass

    async def wait_closed(self) -> None:
        pass


def _fake_open_connection_factory(reader_data: bytes):  # type: ignore[no-untyped-def]
    """返回一个可 mock 为 asyncio.open_connection 的 async 工厂。"""
    async def _factory(host, port):
        reader = _ByteBufferReader(reader_data)
        writer = _FakeStreamWriter()
        return reader, writer
    return _factory


@pytest.mark.asyncio
async def test_mqtt_connect_sends_connect_and_handles_connack() -> None:
    """MQTT connect 发送 CONNECT 报文并处理 CONNACK 响应。"""
    connack = _build_connack_bytes()
    fake_open = _fake_open_connection_factory(connack)

    with patch("asyncio.open_connection", fake_open):
        backend = MqttClientBackend(host="localhost", port=1883)
        await backend.connect(timeout_seconds=5.0)

        writer = backend._writer  # type: ignore[union-attr]
        assert writer is not None
        assert len(writer.written) >= 1  # type: ignore[attr-defined]
        connect_bytes = writer.written[0]  # type: ignore[attr-defined,index]
        assert connect_bytes[0] == 0x10

        await backend.disconnect()


@pytest.mark.asyncio
async def test_mqtt_connect_fails_on_rejected_connack() -> None:
    """MQTT connect 在收到拒绝 CONNACK 时应抛出 ConnectionError。"""
    rejected = bytes([0x20, 0x02, 0x00, 0x05])
    fake_open = _fake_open_connection_factory(rejected)

    with patch("asyncio.open_connection", fake_open):
        backend = MqttClientBackend(host="localhost", port=1883)
        with pytest.raises(ConnectionError, match="CONNACK rejected"):
            await backend.connect(timeout_seconds=5.0)


@pytest.mark.asyncio
async def test_mqtt_subscribe_and_receive_returns_messages() -> None:
    """subscribe_and_receive 应收到 PUBLISH 消息并正确返回。"""
    connack = _build_connack_bytes()
    suback = _build_suback_bytes()
    publish = _build_publish_bytes("sensor/temperature", "25.5")
    data = connack + suback + publish
    fake_open = _fake_open_connection_factory(data)

    with patch("asyncio.open_connection", fake_open):
        backend = MqttClientBackend(host="localhost", port=1883)
        await backend.connect()
        result = await backend.subscribe_and_receive(
            topic_filter="sensor/#", max_messages=1, timeout_seconds=5.0,
        )
        assert result.ok
        assert len(result.messages) == 1
        msg = result.messages[0]
        assert msg.topic == "sensor/temperature"
        assert msg.payload == "25.5"
        await backend.disconnect()


@pytest.mark.asyncio
async def test_mqtt_subscribe_timeout_returns_empty() -> None:
    """subscribe_and_receive 超时后应返回空消息列表。"""
    connack = _build_connack_bytes()
    suback = _build_suback_bytes()
    # 不发 PUBLISH — 后续 readexactly 会超时
    data = connack + suback
    fake_open = _fake_open_connection_factory(data)

    with patch("asyncio.open_connection", fake_open):
        backend = MqttClientBackend(host="localhost", port=1883)
        await backend.connect()
        result = await backend.subscribe_and_receive(
            topic_filter="#", max_messages=1, timeout_seconds=0.1,
        )
        assert not result.ok
        assert len(result.messages) == 0
        assert result.error_reason == "no_messages_received"
        await backend.disconnect()


@pytest.mark.asyncio
async def test_mqtt_disconnect_idempotent() -> None:
    """多次调用 disconnect 不应抛出异常。"""
    connack = _build_connack_bytes()
    fake_open = _fake_open_connection_factory(connack)

    with patch("asyncio.open_connection", fake_open):
        backend = MqttClientBackend(host="localhost", port=1883)
        await backend.connect()
        await backend.disconnect()
        await backend.disconnect()


def test_mqtt_message_dataclass() -> None:
    """MqttMessage 字段应正确设置。"""
    msg = MqttMessage(topic="test/topic", payload="hello", qos=0)
    assert msg.topic == "test/topic"
    assert msg.payload == "hello"
    assert msg.qos == 0
    assert msg.received_at is not None


def test_mqtt_subscribe_result_dataclass() -> None:
    """MqttSubscribeResult 字段应正确设置。"""
    msg = MqttMessage(topic="t", payload="v")
    result = MqttSubscribeResult(ok=True, messages=(msg,), topic_filter="#")
    assert result.ok
    assert len(result.messages) == 1
    assert result.messages[0].topic == "t"


@pytest.mark.asyncio
async def test_mqtt_connect_without_connection_raises() -> None:
    """未连接时调用 subscribe_and_receive 应抛出 ConnectionError。"""
    backend = MqttClientBackend(host="localhost", port=1883)
    with pytest.raises(ConnectionError, match="not connected"):
        await backend.subscribe_and_receive(topic_filter="#")
