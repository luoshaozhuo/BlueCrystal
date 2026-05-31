"""Tests for the OPC UA open62541 subscription runner adapter."""

from __future__ import annotations

import io
from pathlib import Path
import subprocess

import pytest

from tools.source_lab.access.polling.model import CapacityMode
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.open62541_subscription import (
    OpcUaOpen62541SubscribeRunner,
    _stop_process,
    parse_endpoint_diag_line,
    parse_notify_line,
    parse_summary_line,
    run_open62541_subscribe_worker,
)
from tools.source_lab.access.runners.protocol import RUNNER_PROTOCOL_NOISE_LIMIT
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.subscribe.model import SubscribeScanConfig
from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec


def _config(*, runner_trace_enabled: bool = False, runner_trace_top_n: int = 2) -> SubscribeScanConfig:
    return SubscribeScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        process_count=1,
        publishing_interval_ms=100.0,
        sampling_interval_ms=100.0,
        queue_size=1,
        duration_s=5.0,
        runner_trace_enabled=runner_trace_enabled,
        runner_trace_top_n=runner_trace_top_n,
        source_update_enabled=True,
    )


def _plan() -> RunnerEndpointPlan:
    return RunnerEndpointPlan(
        global_index=9,
        source=SourceRuntimeSpec(
            endpoint=SourceEndpointSpec(
                name="source-9",
                host="127.0.0.1",
                port=48009,
                protocol="opcua",
            ),
            points=(SourcePointSpec(address="IED.LD.LN.DO"),),
        ),
        offset_ns=0,
    )


def test_parse_notify_line() -> None:
    parsed = parse_notify_line(
        "NOTIFY\t3\t4\t17\t8\t12\t11\t1\t2\t9\t1712345678.250000\t12345.250000\t12345.251500\t1712345678.350000\t3.500"
    )

    assert parsed.worker_index == 3
    assert parsed.local_index == 4
    assert parsed.global_index == 17
    assert parsed.local_notify_seq == 9
    assert parsed.publish_ts_s == pytest.approx(1712345678.25)
    assert parsed.notify_ts_s == pytest.approx(12345.25)
    assert parsed.flush_ts_s == pytest.approx(12345.2515)
    assert parsed.recv_ts_s == pytest.approx(1712345678.35)
    assert parsed.data_age_ms == pytest.approx(3.5)


def test_parse_notify_line_pre_flush_protocol_without_flush_timestamp() -> None:
    parsed = parse_notify_line(
        "NOTIFY\t3\t4\t17\t8\t12\t11\t1\t2\t9\t1712345678.250000\t12345.250000\t1712345678.350000\t3.500"
    )

    assert parsed.publish_ts_s == pytest.approx(1712345678.25)
    assert parsed.notify_ts_s == pytest.approx(12345.25)
    assert parsed.flush_ts_s is None
    assert parsed.recv_ts_s == pytest.approx(1712345678.35)


def test_parse_notify_line_legacy_without_notify_timestamp() -> None:
    parsed = parse_notify_line("NOTIFY\t3\t4\t17\t8\t12\t11\t1\t2\t9\t1712345678.250000\t1712345678.350000\t3.500")

    assert parsed.publish_ts_s == pytest.approx(1712345678.25)
    assert parsed.notify_ts_s is None
    assert parsed.flush_ts_s is None
    assert parsed.recv_ts_s == pytest.approx(1712345678.35)


def test_parse_summary_line() -> None:
    parsed = parse_summary_line(
        "SUB_SUMMARY\t2\t4\t4\t120\t118\t2\t10\t118\t0\t0\t0\t0\t1\t2\t0\t0\t0\t0\t0\t0\t-\t7.500\t2.500\t110.000"
    )

    assert parsed.worker_index == 2
    assert parsed.endpoint_count == 4
    assert parsed.monitored_created == 118
    assert parsed.keepalive_count == 1
    assert parsed.keepalive_miss_count == 2
    assert parsed.resubscribe_count == 0
    assert parsed.unrecovered_endpoint_count == 0
    assert parsed.recovery_duration_ms == pytest.approx(7.5)
    assert parsed.max_publish_gap_ms == pytest.approx(110.0)


def test_parse_summary_line_covers_recovery_counters_and_reason() -> None:
    parsed = parse_summary_line(
        "SUB_SUMMARY\t1\t2\t2\t10\t10\t0\t40\t40\t0\t0\t0\t0\t4\t3\t5\t6\t7\t5\t2\t1\tconnect_timeout\t12.750\t6.250\t200.000"
    )

    assert parsed.keepalive_miss_count == 3
    assert parsed.publish_timeout_count == 5
    assert parsed.reconnect_count == 6
    assert parsed.resubscribe_count == 7
    assert parsed.resubscribe_success_count == 5
    assert parsed.resubscribe_failure_count == 2
    assert parsed.unrecovered_endpoint_count == 1
    assert parsed.last_reconnect_reason == "connect_timeout"
    assert parsed.recovery_duration_ms == pytest.approx(12.75)


def test_parse_endpoint_diag_line() -> None:
    parsed = parse_endpoint_diag_line("SUB_ENDPOINT_DIAG\t2\t4\t17\t99\t1001\t4.250\t0.125\t50.000\t50.000")

    assert parsed.worker_index == 2
    assert parsed.local_index == 4
    assert parsed.global_index == 17
    assert parsed.notification_count == 99
    assert parsed.run_iterate_count == 1001
    assert parsed.max_dispatch_gap_ms == pytest.approx(4.25)
    assert parsed.max_run_iterate_duration_ms == pytest.approx(0.125)
    assert parsed.revised_publishing_interval_ms == pytest.approx(50.0)
    assert parsed.revised_sampling_interval_ms == pytest.approx(50.0)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("NOTIFY\t0\t1", "Malformed open62541 subscription runner NOTIFY line"),
        ("SUB_SUMMARY\t0\t1", "Malformed open62541 subscription runner SUB_SUMMARY line"),
    ],
)
def test_parse_lines_reject_malformed(line: str, message: str) -> None:
    parser = parse_notify_line if line.startswith("NOTIFY") else parse_summary_line
    with pytest.raises(RuntimeError, match=message):
        parser(line)


def test_runner_adapter_delegates() -> None:
    runner = OpcUaOpen62541SubscribeRunner()
    assert runner.name == "opcua_open62541_subscription_runner"


def test_run_worker_trace_disabled_drops_traces(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_subscription._run_subscription_session",
        lambda *args, **kwargs: type(
            "_Session",
            (),
            {
                "notifies": (
                    parse_notify_line(
                        "NOTIFY\t0\t0\t9\t1\t1\t1\t0\t0\t1\t1712345678.250000\t12345.250000\t12345.251000\t1712345678.350000\t3.500"
                    ),
                ),
                "summary": parse_summary_line(
                    "SUB_SUMMARY\t0\t1\t1\t1\t1\t0\t1\t1\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t-\t0.000\t3.500\t0.000"
                ),
                "endpoint_diagnostics": (
                    parse_endpoint_diag_line(
                        "SUB_ENDPOINT_DIAG\t0\t0\t9\t1\t100\t4.000\t0.100\t100.000\t100.000"
                    ),
                ),
            },
        )(),
    )

    stats = run_open62541_subscribe_worker(0, (_plan(),), _config())

    assert stats.notification_count == 1
    assert stats.batches[0].notify_timestamp_ns == 12_345_250_000_000
    assert stats.batches[0].flush_timestamp_ns == 12_345_251_000_000
    assert stats.endpoint_diagnostics[0].max_dispatch_gap_ms == pytest.approx(4.0)
    assert stats.top_data_age_traces == ()


def test_run_worker_trace_enabled_keeps_top_n(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_subscription._run_subscription_session",
        lambda *args, **kwargs: type(
            "_Session",
            (),
            {
                "notifies": (
                    parse_notify_line(
                        "NOTIFY\t0\t0\t9\t1\t1\t1\t0\t0\t1\t1712345678.250000\t12345.250000\t12345.251000\t1712345678.350000\t3.500"
                    ),
                    parse_notify_line(
                        "NOTIFY\t0\t0\t9\t1\t1\t1\t0\t0\t2\t1712345678.450000\t12345.450000\t12345.451000\t1712345678.550000\t8.500"
                    ),
                ),
                "summary": parse_summary_line(
                    "SUB_SUMMARY\t0\t1\t1\t1\t1\t0\t2\t2\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t-\t0.000\t8.500\t200.000"
                ),
            },
        )(),
    )

    stats = run_open62541_subscribe_worker(0, (_plan(),), _config(runner_trace_enabled=True, runner_trace_top_n=1))

    assert len(stats.top_data_age_traces) == 1
    assert stats.top_data_age_traces[0].data_age_ms == pytest.approx(8.5)


def test_run_worker_raises_on_non_zero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    protocol = "\n".join(["READY", "SUB_DONE\t0"])

    class _FakeProcess:
        def __init__(self) -> None:
            self.stdin = io.StringIO()
            self.stdout = io.StringIO(protocol)
            self.stderr = io.StringIO("runner stderr line\n")
            self.returncode = 7

        def wait(self, timeout: float | None = None) -> int:
            return self.returncode

        def terminate(self) -> None:
            return None

        def kill(self) -> None:
            return None

    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_subscription._resolve_runner_path",
        lambda: Path("/tmp/open62541_subscription_runner"),
    )
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_subscription.subprocess.Popen",
        lambda *args, **kwargs: _FakeProcess(),
    )

    with pytest.raises(RuntimeError, match="non-zero status 7.*runner stderr line"):
        run_open62541_subscribe_worker(0, (_plan(),), _config())


def test_run_worker_raises_on_error_line(monkeypatch: pytest.MonkeyPatch) -> None:
    protocol = "\n".join(["READY", "ERROR\tinvalid_input", "SUB_DONE\t0"])

    class _FakeProcess:
        def __init__(self) -> None:
            self.stdin = io.StringIO()
            self.stdout = io.StringIO(protocol)
            self.stderr = io.StringIO()
            self.returncode = 0

        def wait(self, timeout: float | None = None) -> int:
            return self.returncode

        def terminate(self) -> None:
            return None

        def kill(self) -> None:
            return None

    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_subscription._resolve_runner_path",
        lambda: Path("/tmp/open62541_subscription_runner"),
    )
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_subscription.subprocess.Popen",
        lambda *args, **kwargs: _FakeProcess(),
    )

    with pytest.raises(RuntimeError, match="protocol error"):
        run_open62541_subscribe_worker(0, (_plan(),), _config())


def test_run_worker_records_small_protocol_noise(monkeypatch: pytest.MonkeyPatch) -> None:
    protocol = "\n".join(
        [
            "READY",
            "open62541: lifecycle log on stdout",
            "NOTIFY\t0\t0\t9\t1\t1\t1\t0\t0\t1\t1712345678.250000\t1712345678.350000\t3.500",
            "SUB_SUMMARY\t0\t1\t1\t1\t1\t0\t1\t1\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t-\t0.000\t3.500\t0.000",
            "SUB_DONE\t0",
        ]
    )

    class _FakeProcess:
        def __init__(self) -> None:
            self.stdin = io.StringIO()
            self.stdout = io.StringIO(protocol)
            self.stderr = io.StringIO()
            self.returncode = 0

        def wait(self, timeout: float | None = None) -> int:
            return self.returncode

        def terminate(self) -> None:
            return None

        def kill(self) -> None:
            return None

    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_subscription._resolve_runner_path",
        lambda: Path("/tmp/open62541_subscription_runner"),
    )
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_subscription.subprocess.Popen",
        lambda *args, **kwargs: _FakeProcess(),
    )

    stats = run_open62541_subscribe_worker(0, (_plan(),), _config())

    assert stats.runner_protocol_noise_count == 1
    assert stats.runner_protocol_noise_samples == ("open62541: lifecycle log on stdout",)


def test_run_worker_fails_when_protocol_noise_exceeds_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    noise = [f"noise-{index}" for index in range(RUNNER_PROTOCOL_NOISE_LIMIT + 1)]
    protocol = "\n".join(["READY", *noise])

    class _FakeProcess:
        def __init__(self) -> None:
            self.stdin = io.StringIO()
            self.stdout = io.StringIO(protocol)
            self.stderr = io.StringIO("stderr tail\n")
            self.returncode = 0

        def wait(self, timeout: float | None = None) -> int:
            return self.returncode

        def terminate(self) -> None:
            return None

        def kill(self) -> None:
            return None

    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_subscription._resolve_runner_path",
        lambda: Path("/tmp/open62541_subscription_runner"),
    )
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_subscription.subprocess.Popen",
        lambda *args, **kwargs: _FakeProcess(),
    )

    with pytest.raises(RuntimeError, match="non-protocol stdout noise.*stderr tail"):
        run_open62541_subscribe_worker(0, (_plan(),), _config())


def test_stop_process_terminates_then_kills_after_timeouts() -> None:
    class _FakeStdin:
        def write(self, text: str) -> int:
            return len(text)

        def flush(self) -> None:
            return None

        def close(self) -> None:
            return None

    class _FakeProcess:
        returncode: int | None

        def __init__(self) -> None:
            self.stdin = _FakeStdin()
            self.stderr = None
            self.returncode = None
            self.wait_calls = 0
            self.terminate_called = False
            self.kill_called = False

        def wait(self, timeout: float | None = None) -> int:
            self.wait_calls += 1
            if self.wait_calls <= 2:
                raise subprocess.TimeoutExpired(cmd="runner", timeout=timeout or 0.0)
            self.returncode = -9
            return -9

        def terminate(self) -> None:
            self.terminate_called = True

        def kill(self) -> None:
            self.kill_called = True

    process = _FakeProcess()
    # _FakeProcess 模拟 subprocess.Popen，但无法真正继承 Popen，
    # 仅用于验证 _stop_process 的 terminate/kill 调用顺序。
    _stop_process(process)  # type: ignore[arg-type]
    assert process.terminate_called is True
    assert process.kill_called is True
