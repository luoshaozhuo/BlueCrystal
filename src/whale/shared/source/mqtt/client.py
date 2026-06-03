"""MQTT 生产级 shared source backend。

提供基于 asyncio stream 的轻量级 MQTT 客户端实现，
支持 MQTT v3.1.1 CONNECT / SUBSCRIBE / 消息接收 / DISCONNECT。

职责边界：
- 实现 MQTT 客户端连接、订阅和消息接收；
- 不负责业务数据映射或采集策略编排——这些由 ingest adapter 处理；
- 不负责持久化或缓存——由上层 state cache 处理；
- 当前为 python_lightweight_runner 级别，
  不依赖外部 MQTT 库（如 paho-mqtt），仅使用 Python 标准库 asyncio。

资源生命周期：
- connect() / disconnect() 显式管理 TCP 连接；
- 使用 asyncio stream（asyncio.StreamReader / asyncio.StreamWriter）；
- 超时通过 asyncio.wait_for 保证。

Write 状态：
- MQTT PUBLISH（写入）当前为 NOT_IMPLEMENTED；
- 仅支持 SUBSCRIBE 消息接收。
"""
from __future__ import annotations

import asyncio
import logging
import struct
from dataclasses import dataclass, field
from datetime import datetime, timezone

LOGGER = logging.getLogger(__name__)

# MQTT v3.1.1 固定头标志
_MQTT_CONNECT = 0x10
_MQTT_CONNACK = 0x20
_MQTT_PUBLISH = 0x30
_MQTT_SUBACK = 0x90
_MQTT_UNSUBACK = 0xB0
_MQTT_DISCONNECT = 0xE0


@dataclass(frozen=True, slots=True)
class MqttMessage:
    """从 MQTT broker 接收的单条消息。

    Attributes:
        topic: 消息所属 topic。
        payload: 消息负载（解码后的字符串）。
        qos: 消息 QoS 级别。
        received_at: 消息接收时间戳（UTC）。
    """

    topic: str
    payload: str
    qos: int = 0
    received_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass(frozen=True, slots=True)
class MqttSubscribeResult:
    """MQTT 订阅结果。

    Attributes:
        ok: 订阅是否成功。
        messages: 接收到的消息列表。
        error_reason: 失败原因（仅 ok=False 时有效）。
        topic_filter: 订阅的 topic filter。
    """

    ok: bool
    messages: tuple[MqttMessage, ...] = ()
    error_reason: str | None = None
    topic_filter: str = "#"
    connection_details: dict[str, object] = field(default_factory=dict)


class MqttClientBackend:
    """基于 asyncio 的轻量级 MQTT v3.1.1 客户端。

    支持 CONNECT、SUBSCRIBE、消息接收和 DISCONNECT。
    当前为 python_lightweight_runner 级别实现。

    Args:
        host: MQTT broker 主机地址。
        port: MQTT broker TCP 端口。
        client_id: MQTT 客户端标识符。
        keepalive_seconds: MQTT keep-alive 间隔（秒），默认 30。
    """

    def __init__(
        self,
        host: str,
        port: int = 1883,
        *,
        client_id: str = "whale-mqtt-client",
        keepalive_seconds: int = 30,
    ) -> None:
        self._host = host
        self._port = port
        self._client_id = client_id
        self._keepalive_seconds = keepalive_seconds
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False

    async def connect(self, timeout_seconds: float = 10.0) -> None:
        """建立 TCP 连接并发送 MQTT CONNECT 报文。

        Args:
            timeout_seconds: 连接超时（秒）。

        Raises:
            ConnectionError: TCP 连接或 MQTT 握手失败。
            asyncio.TimeoutError: 连接超时。
        """
        if self._connected:
            return

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=timeout_seconds,
            )
        except Exception as exc:
            raise ConnectionError(
                f"MQTT TCP connect failed to {self._host}:{self._port}: {exc}"
            ) from exc

        try:
            assert self._writer is not None and self._reader is not None
            connect_packet = self._build_connect_packet()
            self._writer.write(connect_packet)
            await self._writer.drain()

            ack = await asyncio.wait_for(self._reader.readexactly(4), timeout=5.0)
            if not (ack[0] == _MQTT_CONNACK and ack[1] == 2 and ack[3] == 0):
                raise ConnectionError(
                    f"MQTT CONNACK rejected: {ack.hex()}"
                )
            self._connected = True
        except Exception:
            await self.disconnect()
            raise

    async def disconnect(self) -> None:
        """发送 MQTT DISCONNECT 报文并关闭 TCP 连接。

        幂等：多次调用安全。
        """
        writer = self._writer
        self._writer = None
        self._reader = None
        self._connected = False

        if writer is not None:
            try:
                writer.write(bytes([_MQTT_DISCONNECT, 0]))
                await writer.drain()
            except Exception:
                pass
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def subscribe_and_receive(
        self,
        topic_filter: str,
        *,
        qos: int = 0,
        max_messages: int = 1,
        timeout_seconds: float = 30.0,
    ) -> MqttSubscribeResult:
        """订阅 topic 并接收指定数量的消息。

        发送 SUBSCRIBE 报文后阻塞等待消息到达，收到足够消息或超时后返回。

        Args:
            topic_filter: MQTT topic filter（支持通配符 # 和 +）。
            qos: 订阅的 QoS 级别（0、1 或 2）。
            max_messages: 期望接收的最大消息数。
            timeout_seconds: 等待消息的超时时间（秒）。

        Returns:
            MqttSubscribeResult 包含接收到的消息列表。

        Raises:
            ConnectionError: 连接未建立或订阅失败。
        """
        if not self._connected or self._writer is None or self._reader is None:
            raise ConnectionError("MQTT client not connected. Call connect() first.")

        # Send SUBSCRIBE
        packet_id = 1  # simplified single-subscription
        subscribe_packet = self._build_subscribe_packet(packet_id, topic_filter, qos)
        self._writer.write(subscribe_packet)
        await self._writer.drain()

        # Read SUBACK
        try:
            suback = await asyncio.wait_for(self._reader.readexactly(5), timeout=5.0)
            if suback[0] != _MQTT_SUBACK or suback[1] != 3:
                raise ConnectionError(
                    f"MQTT SUBACK invalid: {suback.hex()}"
                )
        except asyncio.TimeoutError:
            raise ConnectionError("MQTT SUBSCRIBE timeout waiting for SUBACK")

        # Receive messages
        messages: list[MqttMessage] = []
        try:
            while len(messages) < max_messages:
                msg = await asyncio.wait_for(
                    self._read_one_publish(), timeout=timeout_seconds
                )
                messages.append(msg)
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, ConnectionError):
            pass

        return MqttSubscribeResult(
            ok=len(messages) > 0,
            messages=tuple(messages),
            error_reason="no_messages_received" if not messages else None,
            topic_filter=topic_filter,
        )

    async def _read_one_publish(self) -> MqttMessage:
        """读取一条 PUBLISH 报文。

        Returns:
            解析后的 MqttMessage。

        Raises:
            ConnectionError: 连接异常时。
        """
        assert self._reader is not None

        # Read fixed header byte 0
        first_byte = await self._reader.readexactly(1)
        if first_byte[0] & 0xF0 != _MQTT_PUBLISH:
            raise ConnectionError(
                f"Expected PUBLISH packet, got byte={first_byte.hex()}"
            )

        # Read remaining length (variable-length encoding)
        remaining_length = 0
        multiplier = 1
        for _ in range(4):
            byte = await self._reader.readexactly(1)
            encoded = byte[0]
            remaining_length += (encoded & 0x7F) * multiplier
            multiplier *= 128
            if (encoded & 0x80) == 0:
                break

        # Read remaining bytes
        raw = await self._reader.readexactly(remaining_length)

        # Parse topic length
        topic_len = struct.unpack("!H", raw[0:2])[0]
        topic = raw[2:2 + topic_len].decode("utf-8", errors="replace")

        # Payload starts after topic
        payload_start = 2 + topic_len
        payload = raw[payload_start:].decode("utf-8", errors="replace").strip()

        return MqttMessage(
            topic=topic,
            payload=payload,
            qos=0,
            received_at=datetime.now(tz=timezone.utc),
        )

    def _build_connect_packet(self) -> bytes:
        """构建 MQTT CONNECT 报文（v3.1.1）。

        Returns:
            CONNECT 报文字节。
        """
        protocol_name = b"MQTT"
        protocol_level = 4  # v3.1.1
        flags = 2  # clean session
        keepalive = self._keepalive_seconds

        client_id_bytes = self._client_id.encode("utf-8")

        variable_header = struct.pack(
            "!HBBH",
            len(protocol_name),
            protocol_level,
            flags,
            keepalive,
        ) + protocol_name

        payload = (
            struct.pack("!H", len(client_id_bytes)) + client_id_bytes
        )

        remaining_length = len(variable_header) + len(payload)
        remaining_bytes = self._encode_remaining_length(remaining_length)

        return bytes([_MQTT_CONNECT]) + remaining_bytes + variable_header + payload

    def _build_subscribe_packet(
        self, packet_id: int, topic_filter: str, qos: int
    ) -> bytes:
        """构建 MQTT SUBSCRIBE 报文。

        Args:
            packet_id: 报文标识符。
            topic_filter: 订阅 topic filter。
            qos: QoS 级别。

        Returns:
            SUBSCRIBE 报文字节。
        """
        topic_bytes = topic_filter.encode("utf-8")
        variable_header = struct.pack("!H", packet_id)
        payload = (
            struct.pack("!H", len(topic_bytes)) + topic_bytes + bytes([qos & 0x03])
        )
        remaining_length = len(variable_header) + len(payload)
        remaining_bytes = self._encode_remaining_length(remaining_length)
        return bytes([_MQTT_SUBACK | 2]) + remaining_bytes + variable_header + payload

    @staticmethod
    def _encode_remaining_length(value: int) -> bytes:
        """编码 MQTT 剩余长度字段（可变长度编码）。

        Args:
            value: 剩余长度值（0-268435455）。

        Returns:
            编码后的字节序列。
        """
        result = bytearray()
        while True:
            byte = value % 128
            value //= 128
            if value > 0:
                byte |= 0x80
            result.append(byte)
            if value == 0:
                break
        return bytes(result)

    async def __aenter__(self) -> MqttClientBackend:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.disconnect()
