"""IEC61850 轻量语义探测测试。

本测试只验证 source_lab 的轻量 IEC61850 runner 语义探测边界；
不验证完整 IEC61850 ASN.1/MMS/Report 标准栈。
Runner 使用最小 MMS-like 帧探测，不等价于完整工业协议栈实现。
"""

from __future__ import annotations

from dataclasses import dataclass
import socket

import pytest

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec  # type: ignore[import-untyped]

from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.iec61850_mms_polling import Iec61850MmsPollingRunner
from tools.source_lab.access.runners.iec61850_report import Iec61850ReportRunner
from tools.source_lab.access.subscribe.model import SubscribeScanConfig


@dataclass(slots=True)
class _FakeSocket:
    """Minimal socket fake for runner semantic tests."""

    recv_chunks: list[bytes]
    sent: list[bytes]

    def __enter__(self) -> "_FakeSocket":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        del exc_type, exc, tb

    def settimeout(self, timeout: float) -> None:
        del timeout

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def recv(self, _size: int) -> bytes:
        if not self.recv_chunks:
            return b""
        return self.recv_chunks.pop(0)


def _spec() -> RunnerEndpointPlan:
    return RunnerEndpointPlan(
        global_index=0,
        source=SourceRuntimeSpec(
            endpoint=SourceEndpointSpec(
                name="source-1",
                host="127.0.0.1",
                port=102,
                protocol="iec61850_mms",
            ),
            points=(SourcePointSpec(address="IED.LD0.LN.DO"),),
        ),
        offset_ns=0,
    )


def _polling_config() -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.FIELD,
        protocol="iec61850_mms",
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        hz_start=1.0,
        hz_step=1.0,
        hz_max=1.0,
        process_count=1,
        level_duration_s=1.0,
        warmup_s=0.0,
        read_timeout_s=1.0,
    )


def _subscribe_config() -> SubscribeScanConfig:
    return SubscribeScanConfig(
        mode=CapacityMode.FIELD,
        protocol="iec61850_report",
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        process_count=1,
        publishing_interval_ms=100.0,
        sampling_interval_ms=100.0,
        nominal_sample_hz=10.0,
        queue_size=1,
        duration_s=1.0,
        read_timeout_s=1.0,
        source_update_enabled=True,
        source_update_hz=10.0,
    )


def test_iec61850_mms_polling_runner_validates_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeSocket(recv_chunks=[b"\x30\x03\xa0\x01\x00"], sent=[])
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: fake)

    sample = Iec61850MmsPollingRunner().read_once(_spec(), target_hz=1.0, config=_polling_config())

    assert sample.ok is True
    assert sample.value_count == 1


def test_iec61850_mms_polling_runner_rejects_invalid_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeSocket(recv_chunks=[b"\x00\x00"], sent=[])
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: fake)

    sample = Iec61850MmsPollingRunner().read_once(_spec(), target_hz=1.0, config=_polling_config())

    assert sample.ok is False
    assert sample.error_code == "protocol_error"


def test_iec61850_report_runner_validates_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeSocket(recv_chunks=[b"\x30\x03\xa0\x01\x00"], sent=[])
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: fake)

    sample = Iec61850ReportRunner().read_stream_sample(_spec(), config=_subscribe_config())

    assert sample.value_count == 1
    assert sample.bad_count == 0


def test_iec61850_report_runner_rejects_invalid_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeSocket(recv_chunks=[b"\x00\x00"], sent=[])
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: fake)

    sample = Iec61850ReportRunner().read_stream_sample(_spec(), config=_subscribe_config())

    assert sample.value_count == 0
    assert sample.bad_count == 1
