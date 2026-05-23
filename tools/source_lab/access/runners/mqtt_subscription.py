"""MQTT topic subscribe runner（原生 socket 协议握手）。"""

from __future__ import annotations

import socket

from tools.source_lab.access.runners.generic_streaming import GenericStreamingSubscriptionRunner, StreamingSample
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.subscribe.model import SubscribeScanConfig


def _encode_remaining_length(value: int) -> bytes:
    chunks: list[int] = []
    remaining = value
    while True:
        byte = remaining % 128
        remaining //= 128
        if remaining > 0:
            byte |= 0x80
        chunks.append(byte)
        if remaining == 0:
            break
    return bytes(chunks)


def _mqtt_connect_packet(client_id: str) -> bytes:
    payload = len(client_id).to_bytes(2, "big") + client_id.encode("utf-8")
    vh = b"\x00\x04MQTT\x04\x02\x00\x3c"
    return b"\x10" + _encode_remaining_length(len(vh) + len(payload)) + vh + payload


def _mqtt_subscribe_packet(packet_id: int, topic: str) -> bytes:
    topic_bytes = topic.encode("utf-8")
    payload = len(topic_bytes).to_bytes(2, "big") + topic_bytes + b"\x00"
    vh = packet_id.to_bytes(2, "big")
    return b"\x82" + _encode_remaining_length(len(vh) + len(payload)) + vh + payload


class MqttSubscriptionRunner(GenericStreamingSubscriptionRunner):
    """MQTT subscribe runner。"""

    name = "mqtt_subscription_runner"

    def read_stream_sample(self, spec: RunnerEndpointPlan, *, config: SubscribeScanConfig) -> StreamingSample:
        topic = str(spec.source.endpoint.params.get("mqtt_topic", "source_lab/points"))
        client_id = str(spec.source.endpoint.params.get("mqtt_client_id", "source-lab-runner"))
        try:
            with socket.create_connection((spec.source.endpoint.host, spec.source.endpoint.port), timeout=config.read_timeout_s) as client:
                client.sendall(_mqtt_connect_packet(client_id))
                connack = client.recv(4)
                if len(connack) < 4 or connack[0] != 0x20 or connack[3] != 0x00:
                    return StreamingSample(value_count=0, bad_count=1)
                client.sendall(_mqtt_subscribe_packet(1, topic))
                suback = client.recv(8)
                if not suback or suback[0] != 0x90:
                    return StreamingSample(value_count=0, bad_count=1)
                # 读取一帧发布消息（如果 broker 立即推送）。
                _ = client.recv(1024)
                return StreamingSample(value_count=len(spec.source.points), data_age_ms=0.0)
        except OSError:
            return StreamingSample(value_count=0, bad_count=1)
