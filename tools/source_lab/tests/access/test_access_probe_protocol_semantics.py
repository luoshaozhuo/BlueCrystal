"""Protocol semantic probe tests for MQTT and IEC61850 report."""

from __future__ import annotations

import socket
from typing import cast

import pytest

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec  # type: ignore[import-untyped]

from tools.source_lab.access.common.io import FieldEndpointMetadata
from tools.source_lab.access.polling.model import CapacityStatus, ProbeConfig
from tools.source_lab.access.probe import _probe_iec61850_report, _probe_mqtt_streaming
from tools.source_lab.access.providers.base import SourceRuntimeSpec


def _config() -> ProbeConfig:
    return ProbeConfig(protocol="mqtt", timeout_s=1.0, samples=1, concurrency=1, tcp_timeout_s=1.0)


def _source(protocol: str) -> SourceRuntimeSpec:
    return SourceRuntimeSpec(
        endpoint=SourceEndpointSpec(
            name="source-1",
            host="127.0.0.1",
            port=1883,
            protocol=protocol,
            params={"mqtt_topic": "source_lab/points"},
        ),
        points=(SourcePointSpec(address="IED.LD.LN.DO"),),
        runtime_handle=FieldEndpointMetadata(endpoint_id="ep-1", profile_id="pf-1", protocol=protocol),
    )


class _FakeSocket:
    def __init__(self, recv_chunks: list[bytes]) -> None:
        self._recv_chunks = recv_chunks
        self.sent: list[bytes] = []

    def __enter__(self) -> "_FakeSocket":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        del exc_type, exc, tb

    def settimeout(self, timeout: float) -> None:
        del timeout

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def recv(self, _size: int) -> bytes:
        if not self._recv_chunks:
            return b""
        return self._recv_chunks.pop(0)


def _mqtt_publish(topic: str, payload: str) -> bytes:
    topic_bytes = topic.encode("utf-8")
    payload_bytes = payload.encode("utf-8")
    body = len(topic_bytes).to_bytes(2, "big") + topic_bytes + payload_bytes
    return bytes([0x30, len(body)]) + body


def test_mqtt_probe_passes_with_publish_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source("mqtt")
    fake_socket = _FakeSocket(
        [
            b"\x20\x02\x00\x00",  # CONNACK
            b"\x90\x03\x00\x01\x00",  # SUBACK
            _mqtt_publish("source_lab/points", "1"),
        ]
    )

    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *args, **kwargs: cast(object, fake_socket),
    )

    row = _probe_mqtt_streaming(source, config=_config())

    assert row.status == CapacityStatus.PASS
    assert row.reason == ""


def test_mqtt_probe_fails_when_publish_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source("mqtt")
    fake_socket = _FakeSocket(
        [
            b"\x20\x02\x00\x00",  # CONNACK
            b"\x90\x03\x00\x01\x00",  # SUBACK
            b"\x30\x02\x00\x00",  # malformed publish
        ]
    )

    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *args, **kwargs: cast(object, fake_socket),
    )

    row = _probe_mqtt_streaming(source, config=_config())

    assert row.status == CapacityStatus.FAIL
    assert row.reason == "mqtt_publish_invalid"


def test_iec61850_report_probe_requires_mms_like_response(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source("iec61850_report")
    fake_socket = _FakeSocket([b"\x30\x03\xa0\x01\x00"])

    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *args, **kwargs: cast(object, fake_socket),
    )

    row = _probe_iec61850_report(source, config=_config())

    assert row.status == CapacityStatus.PASS


def test_iec61850_report_probe_fails_on_invalid_response(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source("iec61850_report")
    fake_socket = _FakeSocket([b"\x00\x00"])

    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *args, **kwargs: cast(object, fake_socket),
    )

    row = _probe_iec61850_report(source, config=_config())

    assert row.status == CapacityStatus.FAIL
    assert row.reason == "iec61850_report_invalid_response"
