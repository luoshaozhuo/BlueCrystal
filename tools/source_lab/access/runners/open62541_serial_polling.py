# mypy: disable-error-code=import-untyped
"""OPC UA open62541 serial polling runner adapter for capacity scans and short probes."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
from threading import Thread

from whale.shared.source.access.opcua import build_opcua_endpoint_url  # type: ignore[import-untyped]

from tools.source_lab.access.polling.metrics import (
    ReaderStats,
    RunnerSummary,
    RunnerTrace,
    WorkerRawStats,
    record_tick,
)
from tools.source_lab.access.polling.model import CapacityScanConfig, TickResult
from tools.source_lab.access.runners.base import CapacityRunner
from tools.source_lab.access.runners.protocol import (
    ProtocolDiagnostics,
    read_protocol_line,
    start_stderr_drain_thread,
)
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan

_READY_PREFIX = "READY"
_RESULT_PREFIX = "RESULT"
_POLL_DONE_PREFIX = "POLL_DONE"
_RUNNER_SUMMARY_PREFIX = "RUNNER_SUMMARY"
_ERROR_PREFIX = "ERROR"
_RESULT_FIELD_COUNT = 13
_SUMMARY_FIELD_COUNT = 15


@dataclass(frozen=True, slots=True)
class ParsedRunnerResult:
    """Parsed ``RESULT`` row emitted by the native open62541 runner."""

    worker_index: int
    local_index: int
    global_index: int
    tick_index: int
    scheduled_ns: int
    started_ns: int
    finished_ns: int
    error_code: str | None
    lag_ms: float
    read_ms: float
    value_count: int
    response_timestamp_s: float | None


@dataclass(frozen=True, slots=True)
class _RunnerSessionResult:
    """One in-memory native runner session capture."""

    results: tuple[ParsedRunnerResult, ...]
    summary: RunnerSummary | None
    summary_line: str | None
    runner_protocol_noise_count: int
    runner_protocol_noise_samples: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OpcUaOpen62541CapacityRunner:
    """Picklable capacity runner that delegates to the native open62541 client."""

    name: str = "opcua_open62541_serial_runner"

    def run_worker(
        self,
        worker_index: int,
        specs: tuple[RunnerEndpointPlan, ...],
        target_hz: float,
        config: CapacityScanConfig,
    ) -> WorkerRawStats:
        """Run one worker partition through the open62541 serial runner.

        Args:
            worker_index: Zero-based worker slot.
            specs: Endpoint plans assigned to this worker.
            target_hz: Requested per-endpoint polling rate.
            config: Capacity scan configuration.

        Returns:
            Worker metrics produced by the native runner.
        """

        return run_serial_polling_worker(worker_index, specs, target_hz, config)


def _resolve_runner_path() -> Path:
    """Resolve the native open62541 runner executable path."""

    env_path = os.environ.get("WHALE_OPEN62541_CLIENT_RUNNER_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    suffix = ".exe" if os.name == "nt" else ""
    return (
        Path(__file__).resolve().parents[2] / "native" / "build" / f"open62541_client_runner{suffix}"
    )


def _write_endpoint_file(temp_dir: str, spec: SourceRuntimeSpec, index: int) -> Path:
    """Write one temporary node list file for the native runner."""

    path = Path(temp_dir) / f"endpoint_{index}.nodes"
    path.write_text(
        "\n".join(
            point.address[2:] if point.address.startswith("s=") else point.address
            for point in spec.points
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def parse_result_line(line: str) -> ParsedRunnerResult:
    """Parse one ``RESULT`` protocol line from the open62541 runner.

    Args:
        line: Raw tab-separated protocol line.

    Returns:
        Parsed result object.

    Raises:
        RuntimeError: If the line shape or values are invalid.
    """

    fields = line.split("\t")
    if len(fields) != _RESULT_FIELD_COUNT or fields[0] != _RESULT_PREFIX:
        raise RuntimeError(
            "Malformed open62541 runner RESULT line: "
            f"expected {_RESULT_FIELD_COUNT} tab fields, got {len(fields)}: {line!r}"
        )

    try:
        response_timestamp_raw = float(fields[12])
        return ParsedRunnerResult(
            worker_index=int(fields[1]),
            local_index=int(fields[2]),
            global_index=int(fields[3]),
            tick_index=int(fields[4]),
            scheduled_ns=int(fields[5]),
            started_ns=int(fields[6]),
            finished_ns=int(fields[7]),
            error_code=None if fields[8] == "OK" else fields[8],
            lag_ms=float(fields[9]),
            read_ms=float(fields[10]),
            value_count=int(fields[11]),
            response_timestamp_s=response_timestamp_raw if response_timestamp_raw > 0 else None,
        )
    except ValueError as exc:
        raise RuntimeError(f"Malformed open62541 runner RESULT line: {line!r}") from exc


def parse_summary_line(line: str) -> RunnerSummary:
    """Parse one ``RUNNER_SUMMARY`` protocol line from the open62541 runner.

    Args:
        line: Raw tab-separated protocol line.

    Returns:
        Parsed runner summary.

    Raises:
        RuntimeError: If the line shape or values are invalid.
    """

    fields = line.split("\t")
    if len(fields) != _SUMMARY_FIELD_COUNT or fields[0] != _RUNNER_SUMMARY_PREFIX:
        raise RuntimeError(
            "Malformed open62541 runner RUNNER_SUMMARY line: "
            f"expected {_SUMMARY_FIELD_COUNT} tab fields, got {len(fields)}: {line!r}"
        )

    try:
        return RunnerSummary(
            worker_index=int(fields[1]),
            endpoint_count=int(fields[2]),
            total_reads=int(fields[3]),
            ok_reads=int(fields[4]),
            bad_reads=int(fields[5]),
            read_errors=int(fields[6]),
            missing_response_timestamps=int(fields[7]),
            missed_ticks=int(fields[8]),
            max_lag_ms=float(fields[9]),
            max_read_ms=float(fields[10]),
            warmup_reads=int(fields[11]),
            warmup_errors=int(fields[12]),
            warmup_max_lag_ms=float(fields[13]),
            warmup_max_read_ms=float(fields[14]),
        )
    except ValueError as exc:
        raise RuntimeError(f"Malformed open62541 runner RUNNER_SUMMARY line: {line!r}") from exc


def _tick_result_from_parsed(result: ParsedRunnerResult) -> TickResult:
    """Map one parsed native runner result into the shared probe/metric shape."""

    error_code = result.error_code
    return TickResult(
        ok=error_code is None,
        value_count=result.value_count,
        elapsed_ms=result.read_ms,
        response_timestamp_s=result.response_timestamp_s,
        error=(
            "batch_mismatch"
            if error_code == "batch_mismatch"
            else "missing_response_timestamp"
            if error_code == "missing_response_timestamp"
            else error_code
        ),
    )


def _stop_process(process: subprocess.Popen[str]) -> None:
    """Stop the native runner process with graceful then forced shutdown."""

    if process.stdin is not None:
        try:
            process.stdin.write("STOP_POLL\nQUIT\n")
            process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            pass
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass

    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2.0)


def _run_serial_polling_session(
    worker_index: int,
    specs: tuple[RunnerEndpointPlan, ...],
    *,
    target_hz: float,
    warmup_s: float,
    duration_s: float,
    read_timeout_s: float,
) -> _RunnerSessionResult:
    """Run one native serial polling session and capture protocol rows."""

    if not specs:
        raise ValueError("serial polling session requires at least one endpoint plan")

    runner_path = _resolve_runner_path()
    if not runner_path.exists():
        raise RuntimeError(f"open62541 client runner executable does not exist: {runner_path}")

    period_ns = max(1, round(1_000_000_000 / target_hz))

    with tempfile.TemporaryDirectory(prefix="source_lab_access_runner_") as temp_dir:
        endpoint_files = [_write_endpoint_file(temp_dir, spec.source, spec.global_index) for spec in specs]
        diagnostics = ProtocolDiagnostics()
        process = subprocess.Popen(
            [str(runner_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        stderr_thread: Thread = start_stderr_drain_thread(getattr(process, "stderr", None), diagnostics)
        protocol_error: RuntimeError | None = None
        try:
            assert process.stdin is not None
            assert process.stdout is not None
            try:
                ready_line = read_protocol_line(
                    process.stdout,
                    allowed_prefixes=(_READY_PREFIX,),
                    error_prefix=_ERROR_PREFIX,
                    diagnostics=diagnostics,
                    label="open62541 runner",
                )
                if ready_line != _READY_PREFIX:
                    raise RuntimeError(
                        f"unexpected runner ready response: {ready_line!r}{diagnostics.render_context()}"
                    )

                process.stdin.write(
                    "START_SERIAL_POLL\t"
                    f"{worker_index}\t{target_hz:.9f}\t{period_ns}\t{warmup_s:.9f}\t"
                    f"{duration_s:.9f}\t{read_timeout_s:.9f}\t{len(specs)}\n"
                )
                for spec, node_file in zip(specs, endpoint_files):
                    source = spec.source
                    process.stdin.write(
                        "ENDPOINT\t"
                        f"{spec.global_index}\t{build_opcua_endpoint_url(source.endpoint)}\t"
                        f"{source.endpoint.namespace_uri or '-'}\t{source.endpoint.ied_name or '-'}\t"
                        f"{source.endpoint.ld_name or '-'}\t{node_file}\t{spec.offset_ns}\n"
                    )
                process.stdin.write("END_SERIAL_POLL\n")
                process.stdin.flush()

                results: list[ParsedRunnerResult] = []
                summary_line: str | None = None
                summary: RunnerSummary | None = None
                while True:
                    line = read_protocol_line(
                        process.stdout,
                        allowed_prefixes=(
                            _RESULT_PREFIX,
                            _POLL_DONE_PREFIX,
                            _RUNNER_SUMMARY_PREFIX,
                        ),
                        error_prefix=_ERROR_PREFIX,
                        diagnostics=diagnostics,
                        label="open62541 runner",
                    )
                    if line.startswith(_RESULT_PREFIX):
                        results.append(parse_result_line(line))
                        continue
                    if line.startswith(_RUNNER_SUMMARY_PREFIX):
                        summary_line = line
                        summary = parse_summary_line(line)
                        continue
                    if line.startswith(_POLL_DONE_PREFIX):
                        break
            except RuntimeError as exc:
                protocol_error = exc
                results = []
                summary_line = None
                summary = None
        finally:
            _stop_process(process)
            stderr_thread.join(timeout=1.0)

        if protocol_error is not None:
            message = str(protocol_error)
            context = diagnostics.render_context()
            if context and context not in message:
                message = f"{message}{context}"
            raise RuntimeError(message) from protocol_error
        if process.returncode not in {0, None}:
            raise RuntimeError(
                "open62541 runner exited with non-zero status "
                f"{process.returncode} for worker {worker_index}{diagnostics.render_context()}"
            )

    return _RunnerSessionResult(
        results=tuple(results),
        summary=summary,
        summary_line=summary_line,
        runner_protocol_noise_count=diagnostics.stdout_noise_count,
        runner_protocol_noise_samples=tuple(diagnostics.stdout_noise_samples),
    )


def _empty_worker_stats(worker_index: int) -> WorkerRawStats:
    """Build an empty worker stats row for buckets without endpoints."""

    return WorkerRawStats(
        worker_index=worker_index,
        reader_count=0,
        batch_mismatches=0,
        read_errors=0,
        missing_response_timestamps=0,
        response_timestamps_by_reader=(),
        max_observed_concurrent_reads=0,
        total_reads=0,
        ok_reads=0,
        value_count=0,
        runner_protocol_noise_count=0,
        runner_protocol_noise_samples=(),
    )


def run_serial_polling_probe(
    source: SourceRuntimeSpec,
    *,
    config: CapacityScanConfig,
    samples: int = 1,
) -> tuple[TickResult, ...]:
    """Run one or more short OPC UA polls for a single endpoint.

    Args:
        source: Field source to probe.
        config: Shared access config providing timeout settings.
        samples: Number of probe samples to collect.

    Returns:
        Normalized probe tick results in runner order.
    """

    session = _run_serial_polling_session(
        0,
        (RunnerEndpointPlan(global_index=0, source=source, offset_ns=0),),
        target_hz=1.0,
        warmup_s=0.0,
        duration_s=max(1.0, float(samples)),
        read_timeout_s=config.read_timeout_s,
    )
    return tuple(_tick_result_from_parsed(item) for item in session.results[:samples])


def run_serial_polling_worker(
    worker_index: int,
    specs: tuple[RunnerEndpointPlan, ...],
    target_hz: float,
    config: CapacityScanConfig,
) -> WorkerRawStats:
    """Run one worker partition using the native open62541 serial poll protocol.

    Args:
        worker_index: Zero-based worker slot.
        specs: Endpoint plans assigned to this worker.
        target_hz: Requested per-endpoint polling rate.
        config: Capacity scan configuration.

    Returns:
        Raw worker metrics aggregated from native runner rows.
    """

    if not specs:
        return _empty_worker_stats(worker_index)

    session = _run_serial_polling_session(
        worker_index,
        specs,
        target_hz=target_hz,
        warmup_s=config.warmup_s,
        duration_s=config.level_duration_s,
        read_timeout_s=config.read_timeout_s,
    )

    stats_by_reader = [ReaderStats() for _ in specs]
    top_lag_traces: list[RunnerTrace] = []
    top_read_traces: list[RunnerTrace] = []
    for result in session.results:
        local_index = result.local_index
        if local_index < 0 or local_index >= len(stats_by_reader):
            raise RuntimeError(
                f"open62541 runner returned invalid local_index {local_index} for worker {worker_index}"
            )
        record_tick(stats_by_reader[local_index], _tick_result_from_parsed(result))

        if config.runner_trace_enabled:
            trace = RunnerTrace(
                worker_index=result.worker_index,
                local_index=result.local_index,
                global_index=result.global_index,
                tick_index=result.tick_index,
                lag_ms=result.lag_ms,
                read_ms=result.read_ms,
            )
            top_lag_traces.append(trace)
            top_read_traces.append(trace)

    if config.runner_trace_enabled:
        top_lag_traces = sorted(top_lag_traces, key=lambda item: item.lag_ms, reverse=True)[
            : config.runner_trace_top_n
        ]
        top_read_traces = sorted(top_read_traces, key=lambda item: item.read_ms, reverse=True)[
            : config.runner_trace_top_n
        ]
    else:
        top_lag_traces = []
        top_read_traces = []

    return WorkerRawStats(
        worker_index=worker_index,
        reader_count=len(stats_by_reader),
        batch_mismatches=sum(item.batch_mismatches for item in stats_by_reader),
        read_errors=sum(item.read_errors for item in stats_by_reader),
        missing_response_timestamps=sum(item.missing_response_timestamps for item in stats_by_reader),
        response_timestamps_by_reader=tuple(tuple(item.response_timestamps) for item in stats_by_reader),
        max_observed_concurrent_reads=1 if stats_by_reader else 0,
        total_reads=sum(item.total_reads for item in stats_by_reader),
        ok_reads=sum(item.ok_reads for item in stats_by_reader),
        value_count=sum(item.value_count for item in stats_by_reader),
        runner_summary=session.summary,
        top_lag_traces=tuple(top_lag_traces),
        top_read_traces=tuple(top_read_traces),
        runner_protocol_noise_count=getattr(session, "runner_protocol_noise_count", 0),
        runner_protocol_noise_samples=getattr(session, "runner_protocol_noise_samples", ()),
    )
