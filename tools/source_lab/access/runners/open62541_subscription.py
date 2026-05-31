# mypy: disable-error-code=import-untyped
"""OPC UA open62541 subscription runner adapter for subscription scans."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile

from whale.shared.source.access.opcua import build_opcua_endpoint_url  # type: ignore[import-untyped]

from tools.source_lab.access.common.access_model import AccessBatch, AccessMode, AccessRunSummary
from tools.source_lab.access.common.io import FieldEndpointMetadata
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.subscribe.model import (
    SubscribeEndpointDispatchTrace,
    SubscribeRunnerTrace,
    SubscribeScanConfig,
    SubscribeWorkerRawStats,
)
from tools.source_lab.access.common.utils import normalize_protocol
from tools.source_lab.access.runners.protocol import (
    ProtocolDiagnostics,
    read_protocol_line,
    start_stderr_drain_thread,
)

_READY_PREFIX = "READY"
_NOTIFY_PREFIX = "NOTIFY"
_SUMMARY_PREFIX = "SUB_SUMMARY"
_ENDPOINT_DIAG_PREFIX = "SUB_ENDPOINT_DIAG"
_DONE_PREFIX = "SUB_DONE"
_ERROR_PREFIX = "ERROR"
_NOTIFY_FIELD_COUNT = 15
_PRE_FLUSH_NOTIFY_FIELD_COUNT = 14
_LEGACY_NOTIFY_FIELD_COUNT = 13
_SUMMARY_FIELD_COUNT = 25
_LEGACY_SUMMARY_FIELD_COUNT = 24
_ENDPOINT_DIAG_FIELD_COUNT = 10


@dataclass(frozen=True, slots=True)
class ParsedSubscribeNotify:
    """Parsed ``NOTIFY`` row emitted by the native open62541 runner."""

    worker_index: int
    local_index: int
    global_index: int
    subscription_id: int
    monitored_count: int
    value_count: int
    bad_count: int
    missing_ts_count: int
    local_notify_seq: int
    publish_ts_s: float | None
    notify_ts_s: float | None
    # Monotonic flush timestamp emitted by the native runner. This shares the
    # same clock basis as notify_ts_s and is the only safe source for
    # callback-to-flush lag.
    flush_ts_s: float | None
    # Legacy receive/emit timestamp retained for compatibility. This may use a
    # different clock basis than notify_ts_s and must not be mixed into
    # callback-to-flush lag.
    recv_ts_s: float
    data_age_ms: float | None


@dataclass(frozen=True, slots=True)
class ParsedSubscribeSummary:
    """Parsed ``SUB_SUMMARY`` row emitted by the native open62541 runner."""

    worker_index: int
    endpoint_count: int
    subscription_count: int
    monitored_expected: int
    monitored_created: int
    monitored_failed: int
    notification_count: int
    value_count: int
    bad_count: int
    missing_ts_count: int
    reserved_sequence_gap_count: int
    reserved_queue_overflow_count: int
    keepalive_count: int
    keepalive_miss_count: int
    publish_timeout_count: int
    reconnect_count: int
    resubscribe_count: int
    resubscribe_success_count: int
    resubscribe_failure_count: int
    unrecovered_endpoint_count: int
    last_reconnect_reason: str
    recovery_duration_ms: float
    max_data_age_ms: float
    max_publish_gap_ms: float


@dataclass(frozen=True, slots=True)
class ParsedSubscribeEndpointDiag:
    """Parsed ``SUB_ENDPOINT_DIAG`` row emitted by the native runner."""

    worker_index: int
    local_index: int
    global_index: int
    notification_count: int
    run_iterate_count: int
    max_dispatch_gap_ms: float
    max_run_iterate_duration_ms: float
    revised_publishing_interval_ms: float
    revised_sampling_interval_ms: float


@dataclass(frozen=True, slots=True)
class _RunnerSessionResult:
    """One in-memory native subscription runner session capture."""

    notifies: tuple[ParsedSubscribeNotify, ...]
    summary: ParsedSubscribeSummary | None
    endpoint_diagnostics: tuple[ParsedSubscribeEndpointDiag, ...]
    runner_protocol_noise_count: int
    runner_protocol_noise_samples: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OpcUaOpen62541SubscribeRunner:
    """Picklable subscription runner that delegates to the native open62541 client."""

    name: str = "opcua_open62541_subscription_runner"

    def run_worker(
        self,
        worker_index: int,
        specs: tuple[RunnerEndpointPlan, ...],
        config: SubscribeScanConfig,
    ) -> SubscribeWorkerRawStats:
        """Run one worker partition through the open62541 subscription runner."""

        return run_open62541_subscribe_worker(worker_index, specs, config)


def _resolve_runner_path() -> Path:
    """Resolve the native open62541 subscription runner executable path."""

    env_path = os.environ.get("WHALE_OPEN62541_SUBSCRIPTION_RUNNER_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    suffix = ".exe" if os.name == "nt" else ""
    return (
        Path(__file__).resolve().parents[2] / "native" / "build" / f"open62541_subscription_runner{suffix}"
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


def parse_notify_line(line: str) -> ParsedSubscribeNotify:
    """Parse one ``NOTIFY`` protocol line from the open62541 runner."""

    fields = line.split("\t")
    if len(fields) not in {_NOTIFY_FIELD_COUNT, _PRE_FLUSH_NOTIFY_FIELD_COUNT, _LEGACY_NOTIFY_FIELD_COUNT} or fields[0] != _NOTIFY_PREFIX:
        raise RuntimeError(
            "Malformed open62541 subscription runner NOTIFY line: "
            f"expected {_LEGACY_NOTIFY_FIELD_COUNT}, {_PRE_FLUSH_NOTIFY_FIELD_COUNT}, or {_NOTIFY_FIELD_COUNT} tab fields, "
            f"got {len(fields)}: {line!r}"
        )
    try:
        publish_ts_raw = float(fields[10])
        if len(fields) == _NOTIFY_FIELD_COUNT:
            notify_ts_raw = float(fields[11])
            flush_ts_raw = float(fields[12])
            recv_ts_raw = float(fields[13])
            data_age_raw = float(fields[14])
        elif len(fields) == _PRE_FLUSH_NOTIFY_FIELD_COUNT:
            notify_ts_raw = float(fields[11])
            flush_ts_raw = 0.0
            recv_ts_raw = float(fields[12])
            data_age_raw = float(fields[13])
        else:
            notify_ts_raw = 0.0
            flush_ts_raw = 0.0
            recv_ts_raw = float(fields[11])
            data_age_raw = float(fields[12])
        return ParsedSubscribeNotify(
            worker_index=int(fields[1]),
            local_index=int(fields[2]),
            global_index=int(fields[3]),
            subscription_id=int(fields[4]),
            monitored_count=int(fields[5]),
            value_count=int(fields[6]),
            bad_count=int(fields[7]),
            missing_ts_count=int(fields[8]),
            local_notify_seq=int(fields[9]),
            publish_ts_s=publish_ts_raw if publish_ts_raw > 0 else None,
            notify_ts_s=notify_ts_raw if notify_ts_raw > 0 else None,
            flush_ts_s=flush_ts_raw if flush_ts_raw > 0 else None,
            recv_ts_s=recv_ts_raw,
            data_age_ms=data_age_raw if data_age_raw >= 0 else None,
        )
    except ValueError as exc:
        raise RuntimeError(f"Malformed open62541 subscription runner NOTIFY line: {line!r}") from exc


def parse_summary_line(line: str) -> ParsedSubscribeSummary:
    """Parse one ``SUB_SUMMARY`` protocol line from the open62541 runner."""

    fields = line.split("\t")
    if len(fields) not in {_SUMMARY_FIELD_COUNT, _LEGACY_SUMMARY_FIELD_COUNT} or fields[0] != _SUMMARY_PREFIX:
        raise RuntimeError(
            "Malformed open62541 subscription runner SUB_SUMMARY line: "
            f"expected {_LEGACY_SUMMARY_FIELD_COUNT} or {_SUMMARY_FIELD_COUNT} tab fields, got {len(fields)}: {line!r}"
        )
    try:
        keepalive_miss_count = int(fields[14]) if len(fields) == _SUMMARY_FIELD_COUNT else 0
        publish_timeout_index = 15 if len(fields) == _SUMMARY_FIELD_COUNT else 14
        reconnect_index = 16 if len(fields) == _SUMMARY_FIELD_COUNT else 15
        resubscribe_index = 17 if len(fields) == _SUMMARY_FIELD_COUNT else 16
        unrecovered_index = 20 if len(fields) == _SUMMARY_FIELD_COUNT else 19
        reason_index = 21 if len(fields) == _SUMMARY_FIELD_COUNT else 20
        recovery_index = 22 if len(fields) == _SUMMARY_FIELD_COUNT else 21
        max_data_age_index = 23 if len(fields) == _SUMMARY_FIELD_COUNT else 22
        max_publish_gap_index = 24 if len(fields) == _SUMMARY_FIELD_COUNT else 23
        return ParsedSubscribeSummary(
            worker_index=int(fields[1]),
            endpoint_count=int(fields[2]),
            subscription_count=int(fields[3]),
            monitored_expected=int(fields[4]),
            monitored_created=int(fields[5]),
            monitored_failed=int(fields[6]),
            notification_count=int(fields[7]),
            value_count=int(fields[8]),
            bad_count=int(fields[9]),
            missing_ts_count=int(fields[10]),
            reserved_sequence_gap_count=int(fields[11]),
            reserved_queue_overflow_count=int(fields[12]),
            keepalive_count=int(fields[13]),
            keepalive_miss_count=keepalive_miss_count,
            publish_timeout_count=int(fields[publish_timeout_index]),
            reconnect_count=int(fields[reconnect_index]),
            resubscribe_count=int(fields[resubscribe_index]),
            resubscribe_success_count=int(fields[resubscribe_index + 1]),
            resubscribe_failure_count=int(fields[resubscribe_index + 2]),
            unrecovered_endpoint_count=int(fields[unrecovered_index]),
            last_reconnect_reason="" if fields[reason_index] == "-" else fields[reason_index],
            recovery_duration_ms=float(fields[recovery_index]),
            max_data_age_ms=float(fields[max_data_age_index]),
            max_publish_gap_ms=float(fields[max_publish_gap_index]),
        )
    except ValueError as exc:
        raise RuntimeError(f"Malformed open62541 subscription runner SUB_SUMMARY line: {line!r}") from exc


def parse_endpoint_diag_line(line: str) -> ParsedSubscribeEndpointDiag:
    """Parse one ``SUB_ENDPOINT_DIAG`` protocol line from the native runner."""

    fields = line.split("\t")
    if len(fields) != _ENDPOINT_DIAG_FIELD_COUNT or fields[0] != _ENDPOINT_DIAG_PREFIX:
        raise RuntimeError(
            "Malformed open62541 subscription runner SUB_ENDPOINT_DIAG line: "
            f"expected {_ENDPOINT_DIAG_FIELD_COUNT} tab fields, got {len(fields)}: {line!r}"
        )
    try:
        return ParsedSubscribeEndpointDiag(
            worker_index=int(fields[1]),
            local_index=int(fields[2]),
            global_index=int(fields[3]),
            notification_count=int(fields[4]),
            run_iterate_count=int(fields[5]),
            max_dispatch_gap_ms=float(fields[6]),
            max_run_iterate_duration_ms=float(fields[7]),
            revised_publishing_interval_ms=float(fields[8]),
            revised_sampling_interval_ms=float(fields[9]),
        )
    except ValueError as exc:
        raise RuntimeError(f"Malformed open62541 subscription runner SUB_ENDPOINT_DIAG line: {line!r}") from exc


def _stop_process(process: subprocess.Popen[str]) -> None:
    """Stop the native runner process with graceful then forced shutdown."""

    if process.stdin is not None:
        try:
            process.stdin.write("STOP_SUBSCRIBE\nQUIT\n")
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


def _run_subscription_session(
    worker_index: int,
    specs: tuple[RunnerEndpointPlan, ...],
    *,
    config: SubscribeScanConfig,
) -> _RunnerSessionResult:
    """Run one native subscription session and capture protocol rows."""

    if not specs:
        raise ValueError("subscription session requires at least one endpoint plan")

    runner_path = _resolve_runner_path()
    if not runner_path.exists():
        raise RuntimeError(f"open62541 subscription runner executable does not exist: {runner_path}")

    with tempfile.TemporaryDirectory(prefix="source_lab_access_sub_runner_") as temp_dir:
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
        stderr_thread = start_stderr_drain_thread(process.stderr, diagnostics)
        protocol_error: RuntimeError | None = None
        notifies: list[ParsedSubscribeNotify] = []
        summary: ParsedSubscribeSummary | None = None
        endpoint_diagnostics: list[ParsedSubscribeEndpointDiag] = []
        try:
            assert process.stdin is not None
            assert process.stdout is not None
            try:
                ready_line = read_protocol_line(
                    process.stdout,
                    allowed_prefixes=(_READY_PREFIX,),
                    error_prefix=_ERROR_PREFIX,
                    diagnostics=diagnostics,
                    label="open62541 subscription runner",
                )
                if ready_line != _READY_PREFIX:
                    raise RuntimeError(
                        "unexpected subscription runner ready response: "
                        f"{ready_line!r}{diagnostics.render_context()}"
                    )

                process.stdin.write(
                    "START_SUBSCRIBE\t"
                    f"{worker_index}\t{config.publishing_interval_ms:.3f}\t{config.sampling_interval_ms:.3f}\t"
                    f"{config.duration_s:.3f}\t{config.read_timeout_s:.3f}\t{len(specs)}\t"
                    f"{config.queue_size}\t{config.startup_stagger_ms}\t{config.monitored_item_batch_size}\t"
                    f"{config.monitored_item_batch_gap_ms}\n"
                )
                for spec, node_file in zip(specs, endpoint_files):
                    source = spec.source
                    process.stdin.write(
                        "ENDPOINT\t"
                        f"{spec.global_index}\t{build_opcua_endpoint_url(source.endpoint)}\t"
                        f"{source.endpoint.namespace_uri or '-'}\t{source.endpoint.ied_name or '-'}\t"
                        f"{source.endpoint.ld_name or '-'}\t{node_file}\n"
                    )
                process.stdin.write("END_SUBSCRIBE\n")
                process.stdin.flush()

                while True:
                    line = read_protocol_line(
                        process.stdout,
                        allowed_prefixes=(
                            _NOTIFY_PREFIX,
                            _SUMMARY_PREFIX,
                            _ENDPOINT_DIAG_PREFIX,
                            _DONE_PREFIX,
                        ),
                        error_prefix=_ERROR_PREFIX,
                        diagnostics=diagnostics,
                        label="open62541 subscription runner",
                    )
                    if line.startswith(_NOTIFY_PREFIX):
                        notifies.append(parse_notify_line(line))
                        continue
                    if line.startswith(_SUMMARY_PREFIX):
                        summary = parse_summary_line(line)
                        continue
                    if line.startswith(_ENDPOINT_DIAG_PREFIX):
                        endpoint_diagnostics.append(parse_endpoint_diag_line(line))
                        continue
                    if line.startswith(_DONE_PREFIX):
                        break
            except RuntimeError as exc:
                protocol_error = exc
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
                "open62541 subscription runner exited with non-zero status "
                f"{process.returncode} for worker {worker_index}{diagnostics.render_context()}"
            )
    return _RunnerSessionResult(
        notifies=tuple(notifies),
        summary=summary,
        endpoint_diagnostics=tuple(endpoint_diagnostics),
        runner_protocol_noise_count=diagnostics.stdout_noise_count,
        runner_protocol_noise_samples=tuple(diagnostics.stdout_noise_samples),
    )


def _metadata_from_source(source: SourceRuntimeSpec) -> FieldEndpointMetadata:
    """Extract stable endpoint metadata from one runtime source."""

    if isinstance(source.runtime_handle, FieldEndpointMetadata):
        return source.runtime_handle
    return FieldEndpointMetadata(
        endpoint_id=source.endpoint.name,
        profile_id=str(source.endpoint.params.get("profile_id", "")),
        protocol=normalize_protocol(source.endpoint.protocol),
    )


def _empty_worker_stats(worker_index: int) -> SubscribeWorkerRawStats:
    """Build an empty worker stats row for buckets without endpoints."""

    return SubscribeWorkerRawStats(
        worker_index=worker_index,
        endpoint_count=0,
        expected_monitored_items=0,
        monitored_created=0,
        monitored_failed=0,
        batches=(),
        notification_count=0,
        value_count=0,
        bad_count=0,
        missing_ts_count=0,
        reserved_sequence_gap_count=0,
        reserved_queue_overflow_count=0,
        keepalive_count=0,
        keepalive_miss_count=0,
        publish_timeout_count=0,
        reconnect_count=0,
        resubscribe_count=0,
        resubscribe_success_count=0,
        resubscribe_failure_count=0,
        unrecovered_endpoint_count=0,
        recovery_duration_ms=0.0,
        last_reconnect_reason="",
        runner_protocol_noise_count=0,
        runner_protocol_noise_samples=(),
    )


def run_open62541_subscribe_worker(
    worker_index: int,
    specs: tuple[RunnerEndpointPlan, ...],
    config: SubscribeScanConfig,
) -> SubscribeWorkerRawStats:
    """Run one worker partition using the native open62541 subscription protocol."""

    if not specs:
        return _empty_worker_stats(worker_index)

    session = _run_subscription_session(worker_index, specs, config=config)
    metadata_by_local = [_metadata_from_source(spec.source) for spec in specs]
    batches: list[AccessBatch] = []
    traces: list[SubscribeRunnerTrace] = []
    expected_monitored_items = sum(len(spec.source.points) for spec in specs)

    for batch_index, notify in enumerate(session.notifies):
        if notify.local_index < 0 or notify.local_index >= len(specs):
            raise RuntimeError(
                f"open62541 subscription runner returned invalid local_index {notify.local_index}"
            )
        spec = specs[notify.local_index]
        metadata = metadata_by_local[notify.local_index]
        batch = AccessBatch(
            endpoint_id=metadata.endpoint_id,
            profile_id=metadata.profile_id,
            protocol=normalize_protocol(spec.source.endpoint.protocol),
            access_mode=AccessMode.SUBSCRIBE,
            worker_index=notify.worker_index,
            local_index=notify.local_index,
            global_index=notify.global_index,
            batch_index=batch_index,
            sequence=notify.local_notify_seq,
            scheduled_ns=None,
            started_ns=None,
            received_ns=round(notify.recv_ts_s * 1_000_000_000),
            source_timestamp_s=notify.publish_ts_s,
            server_timestamp_s=notify.publish_ts_s,
            value_count=notify.value_count,
            expected_count=len(spec.source.points),
            bad_count=notify.bad_count,
            missing_timestamp_count=notify.missing_ts_count,
            error_code=None if notify.bad_count == 0 and notify.value_count == notify.monitored_count else "notify_error",
            data_age_ms=notify.data_age_ms,
            period_ms=None,
            notify_timestamp_ns=(
                round(notify.notify_ts_s * 1_000_000_000) if notify.notify_ts_s is not None else None
            ),
            flush_timestamp_ns=(
                round(notify.flush_ts_s * 1_000_000_000) if notify.flush_ts_s is not None else None
            ),
        )
        batches.append(batch)
        if config.runner_trace_enabled:
            traces.append(
                SubscribeRunnerTrace(
                    worker_index=notify.worker_index,
                    local_index=notify.local_index,
                    global_index=notify.global_index,
                    sequence=notify.local_notify_seq,
                    value_count=notify.value_count,
                    data_age_ms=notify.data_age_ms or 0.0,
                )
            )

    summary = session.summary
    access_summary = (
        AccessRunSummary(
            access_mode=AccessMode.SUBSCRIBE,
            worker_index=worker_index,
            endpoint_count=summary.endpoint_count,
            expected_point_count=summary.monitored_expected,
            batch_count=summary.notification_count,
            value_count=summary.value_count,
            bad_count=summary.bad_count,
            missing_timestamp_count=summary.missing_ts_count,
            error_count=summary.monitored_failed + summary.publish_timeout_count,
        )
        if summary is not None
        else None
    )
    top_data_age_traces = (
        tuple(sorted(traces, key=lambda item: item.data_age_ms, reverse=True)[: config.runner_trace_top_n])
        if config.runner_trace_enabled
        else ()
    )

    return SubscribeWorkerRawStats(
        worker_index=worker_index,
        endpoint_count=len(specs),
        expected_monitored_items=expected_monitored_items if summary is None else summary.monitored_expected,
        monitored_created=expected_monitored_items if summary is None else summary.monitored_created,
        monitored_failed=0 if summary is None else summary.monitored_failed,
        batches=tuple(batches),
        notification_count=len(batches) if summary is None else summary.notification_count,
        value_count=sum(batch.value_count for batch in batches) if summary is None else summary.value_count,
        bad_count=sum(batch.bad_count for batch in batches) if summary is None else summary.bad_count,
        missing_ts_count=(
            sum(batch.missing_timestamp_count for batch in batches) if summary is None else summary.missing_ts_count
        ),
        reserved_sequence_gap_count=0 if summary is None else summary.reserved_sequence_gap_count,
        reserved_queue_overflow_count=(
            0 if summary is None else summary.reserved_queue_overflow_count
        ),
        keepalive_count=0 if summary is None else summary.keepalive_count,
        keepalive_miss_count=0 if summary is None else summary.keepalive_miss_count,
        publish_timeout_count=0 if summary is None else summary.publish_timeout_count,
        reconnect_count=0 if summary is None else summary.reconnect_count,
        resubscribe_count=0 if summary is None else summary.resubscribe_count,
        resubscribe_success_count=0 if summary is None else summary.resubscribe_success_count,
        resubscribe_failure_count=0 if summary is None else summary.resubscribe_failure_count,
        unrecovered_endpoint_count=0 if summary is None else summary.unrecovered_endpoint_count,
        recovery_duration_ms=0.0 if summary is None else summary.recovery_duration_ms,
        last_reconnect_reason="" if summary is None else summary.last_reconnect_reason,
        summary=access_summary,
        top_data_age_traces=top_data_age_traces,
        endpoint_diagnostics=tuple(
            SubscribeEndpointDispatchTrace(
                worker_index=diag.worker_index,
                local_index=diag.local_index,
                global_index=diag.global_index,
                notification_count=diag.notification_count,
                run_iterate_count=diag.run_iterate_count,
                max_dispatch_gap_ms=diag.max_dispatch_gap_ms,
                max_run_iterate_duration_ms=diag.max_run_iterate_duration_ms,
                revised_publishing_interval_ms=diag.revised_publishing_interval_ms,
                revised_sampling_interval_ms=diag.revised_sampling_interval_ms,
            )
            for diag in getattr(session, "endpoint_diagnostics", ())
        ),
        runner_protocol_noise_count=getattr(session, "runner_protocol_noise_count", 0),
        runner_protocol_noise_samples=getattr(session, "runner_protocol_noise_samples", ()),
    )
