"""Protocol-specific probe handshake dispatch tests."""

from __future__ import annotations

import pytest

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec  # type: ignore[import-untyped]

from tools.source_lab.access.common.io import FieldEndpointMetadata
from tools.source_lab.access.polling.model import CapacityStatus, ProbeConfig, ServerProbeResult
from tools.source_lab.access.probe import _polling_tcp_probe, _streaming_probe_success
from tools.source_lab.access.providers.base import SourceRuntimeSpec


def _config() -> ProbeConfig:
    return ProbeConfig(protocol="opcua", timeout_s=5.0, samples=2, concurrency=2, tcp_timeout_s=1.0)


def _source(protocol: str) -> SourceRuntimeSpec:
    return SourceRuntimeSpec(
        endpoint=SourceEndpointSpec(
            name="source-1",
            host="127.0.0.1",
            port=48001,
            protocol=protocol,
        ),
        points=(SourcePointSpec(address="IED.LD.LN.DO"),),
        runtime_handle=FieldEndpointMetadata(endpoint_id="ep-1", profile_id="pf-1", protocol=protocol),
    )


def _pass_row(source: SourceRuntimeSpec, protocol: str) -> ServerProbeResult:
    return ServerProbeResult(
        endpoint_id="ep-1",
        profile_id="pf-1",
        protocol=protocol,
        host=source.endpoint.host,
        port=source.endpoint.port,
        point_count=1,
        tcp_status="PASS",
        protocol_status="PASS",
        readable_count=1,
        expected_count=1,
        latency=None,
        missing_ts=False,
        status=CapacityStatus.PASS,
        reason="",
    )


def test_polling_probe_dispatches_modbus_tcp(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source("modbus_tcp")
    called = {"modbus": False}

    def _fake(source_arg: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
        del config
        called["modbus"] = True
        return _pass_row(source_arg, "modbus_tcp")

    monkeypatch.setattr("tools.source_lab.access.probe._probe_modbus_tcp", _fake)

    result = _polling_tcp_probe(source, config=_config())

    assert called["modbus"] is True
    assert result.protocol == "modbus_tcp"


def test_polling_probe_dispatches_iec104(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source("iec104")
    called = {"iec104": False}

    def _fake(source_arg: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
        del config
        called["iec104"] = True
        return _pass_row(source_arg, "iec104")

    monkeypatch.setattr("tools.source_lab.access.probe._probe_iec104", _fake)

    result = _polling_tcp_probe(source, config=_config())

    assert called["iec104"] is True
    assert result.protocol == "iec104"


def test_streaming_probe_dispatches_mqtt(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source("mqtt")
    called = {"mqtt": False}

    def _fake(source_arg: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
        del config
        called["mqtt"] = True
        return _pass_row(source_arg, "mqtt")

    monkeypatch.setattr("tools.source_lab.access.probe._probe_mqtt_streaming", _fake)

    result = _streaming_probe_success(source, config=_config())

    assert called["mqtt"] is True
    assert result.protocol == "mqtt"


def test_streaming_probe_dispatches_iec61850_report(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source("iec61850_report")
    called = {"report": False}

    def _fake(source_arg: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
        del config
        called["report"] = True
        return _pass_row(source_arg, "iec61850_report")

    monkeypatch.setattr("tools.source_lab.access.probe._probe_iec61850_report", _fake)

    result = _streaming_probe_success(source, config=_config())

    assert called["report"] is True
    assert result.protocol == "iec61850_report"
