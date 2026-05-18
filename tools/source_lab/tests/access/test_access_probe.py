"""Tests for standalone field probe behavior."""

from __future__ import annotations

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec

from tools.source_lab.access.io import FieldEndpointMetadata
from tools.source_lab.access.model import CapacityStatus, ProbeConfig, TickResult
from tools.source_lab.access.probe import run_probe
from tools.source_lab.access.providers.base import SourceRuntimeSpec


def _config(protocol: str = "opcua") -> ProbeConfig:
    """Build probe config for tests.

    Args:
        protocol: Requested probe protocol.

    Returns:
        Probe configuration used by tests.
    """

    return ProbeConfig(protocol=protocol, timeout_s=5.0, samples=3, concurrency=2, tcp_timeout_s=1.0)


def _source(protocol: str = "opcua") -> SourceRuntimeSpec:
    """Build one runtime source for probe tests.

    Args:
        protocol: Endpoint protocol label.

    Returns:
        Runtime source with field metadata attached.
    """

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


def test_probe_fails_when_tcp_is_unreachable(monkeypatch) -> None:
    monkeypatch.setattr("tools.source_lab.access.probe._tcp_reachable", lambda *args, **kwargs: False)

    result = run_probe(_config(), (_source(),))

    row = result.rows[0]
    assert row.status == CapacityStatus.FAIL
    assert row.reason == "tcp_unreachable"


def test_probe_marks_non_target_protocol_as_filtered() -> None:
    result = run_probe(_config("opcua"), (_source(protocol="modbus-tcp"),))

    row = result.rows[0]
    assert row.status == CapacityStatus.SKIP
    assert row.reason == "protocol_filtered"


def test_probe_marks_requested_non_opcua_protocol_as_unsupported() -> None:
    result = run_probe(_config("modbus-tcp"), (_source(protocol="modbus-tcp"),))

    row = result.rows[0]
    assert row.status == CapacityStatus.SKIP
    assert row.reason == "unsupported_protocol"


def test_probe_reports_runner_exception(monkeypatch) -> None:
    monkeypatch.setattr("tools.source_lab.access.probe._tcp_reachable", lambda *args, **kwargs: True)

    def _raise(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("tools.source_lab.access.probe.run_serial_polling_probe", _raise)

    result = run_probe(_config(), (_source(),))

    assert result.rows[0].reason == "runner_exception:RuntimeError"


def test_probe_short_read_ok(monkeypatch) -> None:
    monkeypatch.setattr("tools.source_lab.access.probe._tcp_reachable", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        "tools.source_lab.access.probe.run_serial_polling_probe",
        lambda *args, **kwargs: (
            TickResult(ok=True, value_count=1, elapsed_ms=2.0, response_timestamp_s=1.0),
            TickResult(ok=True, value_count=1, elapsed_ms=3.0, response_timestamp_s=2.0),
            TickResult(ok=True, value_count=1, elapsed_ms=4.0, response_timestamp_s=3.0),
        ),
    )

    result = run_probe(_config(), (_source(),))

    row = result.rows[0]
    assert row.status == CapacityStatus.PASS
    assert row.readable_count == 1
    assert row.latency is not None
    assert row.latency.mean_ms == 3.0


def test_probe_detects_value_count_mismatch(monkeypatch) -> None:
    monkeypatch.setattr("tools.source_lab.access.probe._tcp_reachable", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        "tools.source_lab.access.probe.run_serial_polling_probe",
        lambda *args, **kwargs: (TickResult(ok=True, value_count=0, elapsed_ms=2.0, response_timestamp_s=1.0),),
    )

    result = run_probe(_config(), (_source(),))

    assert result.rows[0].reason == "value_count_mismatch"


def test_probe_detects_missing_timestamp(monkeypatch) -> None:
    monkeypatch.setattr("tools.source_lab.access.probe._tcp_reachable", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        "tools.source_lab.access.probe.run_serial_polling_probe",
        lambda *args, **kwargs: (
            TickResult(ok=True, value_count=1, elapsed_ms=2.0, response_timestamp_s=None),
        ),
    )

    result = run_probe(_config(), (_source(),))

    assert result.rows[0].reason == "missing_response_timestamp"
    assert result.rows[0].missing_ts is True


def test_probe_latency_samples_include_percentiles(monkeypatch) -> None:
    monkeypatch.setattr("tools.source_lab.access.probe._tcp_reachable", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        "tools.source_lab.access.probe.run_serial_polling_probe",
        lambda *args, **kwargs: tuple(
            TickResult(ok=True, value_count=1, elapsed_ms=value, response_timestamp_s=float(index))
            for index, value in enumerate((1.0, 2.0, 3.0, 4.0, 5.0), start=1)
        ),
    )

    result = run_probe(_config(), (_source(),))

    latency = result.rows[0].latency
    assert latency is not None
    assert latency.min_ms == 1.0
    assert latency.mean_ms == 3.0
    assert latency.p95_ms >= 4.0
    assert latency.p99_ms >= latency.p95_ms
