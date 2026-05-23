"""Tests for the OPC UA open62541 runner adapter and protocol parsing."""

from __future__ import annotations

import io
from pathlib import Path
import subprocess

import pytest

from tools.source_lab.access.polling.metrics import RunnerSummary
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.open62541_serial_polling import (
    OpcUaOpen62541CapacityRunner,
    _stop_process,
    parse_result_line,
    parse_summary_line,
    run_serial_polling_probe,
    run_serial_polling_worker,
)
from tools.source_lab.access.runners.protocol import RUNNER_PROTOCOL_NOISE_LIMIT
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec


def _config() -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        hz_start=10.0,
        hz_step=10.0,
        hz_max=10.0,
        process_count=1,
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


def test_parse_result_line_parses_local_and_global_index() -> None:
    parsed = parse_result_line(
        "RESULT\t3\t4\t17\t9\t100\t101\t102\tOK\t1.25\t2.50\t8\t1712345678.250000"
    )

    assert parsed.worker_index == 3
    assert parsed.local_index == 4
    assert parsed.global_index == 17
    assert parsed.tick_index == 9
    assert parsed.response_timestamp_s == pytest.approx(1712345678.25)


@pytest.mark.parametrize(
    ("error_code", "expected"),
    [
        ("OK", (0, 0, 0)),
        ("batch_mismatch", (1, 0, 0)),
        ("missing_response_timestamp", (0, 1, 0)),
        ("transport_error", (0, 0, 1)),
    ],
)
def test_parse_result_line_maps_error_semantics(
    monkeypatch: pytest.MonkeyPatch,
    error_code: str,
    expected: tuple[int, int, int],
) -> None:
    protocol = "\n".join(
        [
            "READY",
            (
                "RESULT\t0\t0\t9\t0\t100\t101\t102\t"
                f"{error_code}\t1.25\t2.50\t1\t1712345678.250000"
            ),
            "RUNNER_SUMMARY\t0\t1\t1\t0\t0\t0\t0\t0\t1.250\t2.500\t0\t0\t0.000\t0.000",
            "POLL_DONE\t0",
        ]
    )

    class _FakeProcess:
        def __init__(self) -> None:
            self.stdin = io.StringIO()
            self.stdout = io.StringIO(protocol)
            self.returncode = 0
            self.wait_calls = 0
            self.terminate_called = False
            self.kill_called = False

        def wait(self, timeout: float | None = None) -> int:
            self.wait_calls += 1
            return 0

        def terminate(self) -> None:
            self.terminate_called = True

        def kill(self) -> None:
            self.kill_called = True

    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling._resolve_runner_path",
        lambda: Path("/tmp/open62541_client_runner"),
    )
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling.subprocess.Popen",
        lambda *args, **kwargs: _FakeProcess(),
    )

    stats = run_serial_polling_worker(0, (_plan(),), 10.0, _config())

    assert (stats.batch_mismatches, stats.missing_response_timestamps, stats.read_errors) == expected


def test_run_serial_polling_worker_ignores_value_lines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol = "\n".join(
        [
            "READY",
            "RESULT\t0\t0\t9\t0\t100\t101\t102\tOK\t1.25\t2.50\t1\t1712345678.250000",
            "VALUE\t0\t0\t9\t0\tGOOD\t123.4\t1712345678.000000\t1712345678.250000",
            "RUNNER_SUMMARY\t0\t1\t1\t1\t0\t0\t0\t0\t1.250\t2.500\t0\t0\t0.000\t0.000",
            "POLL_DONE\t0",
        ]
    )

    class _FakeProcess:
        def __init__(self) -> None:
            self.stdin = io.StringIO()
            self.stdout = io.StringIO(protocol)
            self.returncode = 0
            self.wait_calls = 0
            self.terminate_called = False
            self.kill_called = False

        def wait(self, timeout: float | None = None) -> int:
            self.wait_calls += 1
            return 0

        def terminate(self) -> None:
            self.terminate_called = True

        def kill(self) -> None:
            self.kill_called = True

    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling._resolve_runner_path",
        lambda: Path("/tmp/open62541_client_runner"),
    )
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling.subprocess.Popen",
        lambda *args, **kwargs: _FakeProcess(),
    )

    stats = run_serial_polling_worker(0, (_plan(),), 10.0, _config())

    assert stats.ok_reads == 1


def test_parse_result_line_rejects_malformed_line() -> None:
    with pytest.raises(RuntimeError, match="Malformed open62541 runner RESULT line"):
        parse_result_line("RESULT\t0\t1")


def test_parse_summary_line_parses_measurement_and_warmup_fields() -> None:
    parsed = parse_summary_line(
        "RUNNER_SUMMARY\t2\t4\t8\t7\t1\t0\t1\t3\t1.250\t2.500\t2\t1\t0.750\t1.500"
    )

    assert isinstance(parsed, RunnerSummary)
    assert parsed.worker_index == 2
    assert parsed.endpoint_count == 4
    assert parsed.total_reads == 8
    assert parsed.missing_response_timestamps == 1
    assert parsed.missed_ticks == 3
    assert parsed.max_lag_ms == pytest.approx(1.25)
    assert parsed.warmup_reads == 2
    assert parsed.warmup_max_read_ms == pytest.approx(1.5)


def test_parse_summary_line_rejects_malformed_line() -> None:
    with pytest.raises(RuntimeError, match="Malformed open62541 runner RUNNER_SUMMARY line"):
        parse_summary_line("RUNNER_SUMMARY\t0\t1")


def test_stop_process_terminates_then_kills_after_timeouts() -> None:
    class _FakeStdin:
        def write(self, text: str) -> int:
            return len(text)

        def flush(self) -> None:
            return None

        def close(self) -> None:
            return None

    class _FakeProcess:
        def __init__(self) -> None:
            self.stdin = _FakeStdin()
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

    _stop_process(process)

    assert process.terminate_called is True
    assert process.kill_called is True


def test_run_serial_polling_worker_raises_on_non_zero_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol = "\n".join(["READY", "POLL_DONE\t0"])

    class _FakeProcess:
        def __init__(self) -> None:
            self.stdin = io.StringIO()
            self.stdout = io.StringIO(protocol)
            self.returncode = 7

        def wait(self, timeout: float | None = None) -> int:
            return self.returncode

        def terminate(self) -> None:
            return None

        def kill(self) -> None:
            return None

    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling._resolve_runner_path",
        lambda: Path("/tmp/open62541_client_runner"),
    )
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling.subprocess.Popen",
        lambda *args, **kwargs: _FakeProcess(),
    )

    with pytest.raises(RuntimeError, match="non-zero status 7"):
        run_serial_polling_worker(0, (_plan(),), 10.0, _config())


def test_run_serial_polling_worker_raises_on_error_line(monkeypatch: pytest.MonkeyPatch) -> None:
    protocol = "\n".join(["READY", "ERROR\tserial\tbad_input", "POLL_DONE\t0"])

    class _FakeProcess:
        def __init__(self) -> None:
            self.stdin = io.StringIO()
            self.stdout = io.StringIO(protocol)
            self.stderr = io.StringIO("stderr line\n")
            self.returncode = 0

        def wait(self, timeout: float | None = None) -> int:
            return self.returncode

        def terminate(self) -> None:
            return None

        def kill(self) -> None:
            return None

    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling._resolve_runner_path",
        lambda: Path("/tmp/open62541_client_runner"),
    )
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling.subprocess.Popen",
        lambda *args, **kwargs: _FakeProcess(),
    )

    with pytest.raises(RuntimeError, match="protocol error.*stderr_tail"):
        run_serial_polling_worker(0, (_plan(),), 10.0, _config())


def test_run_serial_polling_worker_records_small_protocol_noise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    protocol = "\n".join(
        [
            "READY",
            "open62541: stdout noise",
            "RESULT\t0\t0\t9\t0\t100\t101\t102\tOK\t1.25\t2.50\t1\t1712345678.250000",
            "RUNNER_SUMMARY\t0\t1\t1\t1\t0\t0\t0\t0\t1.250\t2.500\t0\t0\t0.000\t0.000",
            "POLL_DONE\t0",
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
        "tools.source_lab.access.runners.open62541_serial_polling._resolve_runner_path",
        lambda: Path("/tmp/open62541_client_runner"),
    )
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling.subprocess.Popen",
        lambda *args, **kwargs: _FakeProcess(),
    )

    stats = run_serial_polling_worker(0, (_plan(),), 10.0, _config())

    assert stats.runner_protocol_noise_count == 1
    assert stats.runner_protocol_noise_samples == ("open62541: stdout noise",)


def test_run_serial_polling_worker_fails_on_protocol_noise_overflow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        "tools.source_lab.access.runners.open62541_serial_polling._resolve_runner_path",
        lambda: Path("/tmp/open62541_client_runner"),
    )
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling.subprocess.Popen",
        lambda *args, **kwargs: _FakeProcess(),
    )

    with pytest.raises(RuntimeError, match="non-protocol stdout noise.*stderr tail"):
        run_serial_polling_worker(0, (_plan(),), 10.0, _config())


def test_run_serial_polling_worker_returns_summary_and_top_traces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling._run_serial_polling_session",
        lambda *args, **kwargs: type(
            "_Session",
            (),
            {
                "results": (
                    parse_result_line(
                        "RESULT\t0\t0\t9\t0\t100\t101\t102\tOK\t3.50\t1.50\t1\t1712345678.250000"
                    ),
                    parse_result_line(
                        "RESULT\t0\t0\t9\t1\t200\t201\t202\tOK\t1.25\t4.50\t1\t1712345678.350000"
                    ),
                ),
                "summary": parse_summary_line(
                    "RUNNER_SUMMARY\t0\t1\t2\t2\t0\t0\t0\t4\t3.500\t4.500\t0\t0\t0.000\t0.000"
                ),
                "summary_line": "",
            },
        )(),
    )
    config = CapacityScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        hz_start=10.0,
        hz_step=10.0,
        hz_max=10.0,
        process_count=1,
        runner_trace_enabled=True,
        runner_trace_top_n=1,
    )

    stats = run_serial_polling_worker(0, (_plan(),), 10.0, config)

    assert stats.runner_summary is not None
    assert stats.runner_summary.missed_ticks == 4
    assert len(stats.top_lag_traces) == 1
    assert len(stats.top_read_traces) == 1
    assert stats.top_lag_traces[0].lag_ms == pytest.approx(3.5)
    assert stats.top_read_traces[0].read_ms == pytest.approx(4.5)


def test_run_serial_polling_probe_returns_tick_results(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling._run_serial_polling_session",
        lambda *args, **kwargs: type(
            "_Session",
            (),
            {
                "results": (
                    parse_result_line(
                        "RESULT\t0\t0\t0\t0\t100\t101\t102\tOK\t1.25\t2.50\t1\t1712345678.250000"
                    ),
                    parse_result_line(
                        "RESULT\t0\t0\t0\t1\t200\t201\t202\tOK\t1.50\t2.75\t1\t1712345679.250000"
                    ),
                ),
                "summary": None,
                "summary_line": None,
            },
        )(),
    )

    ticks = run_serial_polling_probe(_plan().source, config=_config(), samples=2)

    assert len(ticks) == 2
    assert ticks[0].ok is True
    assert ticks[0].value_count == 1


def test_run_serial_polling_probe_returns_empty_when_session_has_no_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling._run_serial_polling_session",
        lambda *args, **kwargs: type("_Session", (), {"results": (), "summary": None, "summary_line": None})(),
    )

    assert run_serial_polling_probe(_plan().source, config=_config(), samples=1) == ()


def test_adapter_class_delegates_to_worker_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = run_serial_polling_worker
    observed: list[tuple[int, int, float]] = []

    def _fake_runner(worker_index, specs, target_hz, config):
        observed.append((worker_index, len(specs), target_hz))
        return expected(worker_index, (), target_hz, config)

    monkeypatch.setattr(
        "tools.source_lab.access.runners.open62541_serial_polling.run_serial_polling_worker",
        _fake_runner,
    )

    runner = OpcUaOpen62541CapacityRunner()
    stats = runner.run_worker(0, (_plan(),), 10.0, _config())

    assert runner.name == "opcua_open62541_serial_runner"
    assert observed == [(0, 1, 10.0)]
    assert stats.reader_count == 0
