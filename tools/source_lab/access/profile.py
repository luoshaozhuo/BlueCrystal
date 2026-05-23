"""Unified profile service and façade for single-configuration profiling."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable

from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig, CapacityStatus
from tools.source_lab.access.polling.profile import PollingProfileResult, run_polling_profile
from tools.source_lab.access.polling.reporter import print_capacity_report
from tools.source_lab.access.providers.base import SourceProvider
from tools.source_lab.access.common.io import build_field_runtime_sources
from tools.source_lab.access.common.utils import normalize_protocol
from tools.source_lab.access.runners.base import CapacityRunner, SubscriptionRunner
from tools.source_lab.access.runners.registry import (
    build_capacity_runner,
    build_subscription_runner,
    get_protocol_capability,
    supports_access_mode,
)
from tools.source_lab.access.subscribe.model import SubscribeScanConfig
from tools.source_lab.access.subscribe.profile import SubscribeProfileResult, run_subscribe_profile
from tools.source_lab.access.subscribe.reporter import print_subscribe_report
from tools.source_lab.access.providers.file_field import build_field_source_provider


@dataclass(frozen=True, slots=True)
class FieldProfileRequest:
    """Application-layer request for field profiling."""

    access_mode: str
    protocol: str
    service_type: str | None
    process_count: int
    server_count: int
    output_dir: Path | None
    run_id: str
    duration_s: float = 30.0
    warmup_s: float = 10.0
    timeout_s: float = 5.0
    source_update_enabled: bool = True
    source_update_hz: float | None = None
    runner_trace_enabled: bool = False
    runner_trace_top_n: int = 5
    pyinstrument: bool = False
    profile_max_lines: int = 80
    hz: float | None = None
    sample_hz: float | None = None
    publishing_interval_ms: float | None = None
    sampling_interval_ms: float | None = None
    queue_size: int = 1
    startup_stagger_ms: int = 0
    monitored_item_batch_size: int = 100
    monitored_item_batch_gap_ms: int = 0


@dataclass(frozen=True, slots=True)
class FieldProfileArtifacts:
    """Artifact paths emitted by field profiling."""

    report_path: Path | None
    pyinstrument_path: Path | None = None
    json_path: Path | None = None


@dataclass(frozen=True, slots=True)
class FieldProfileServiceResult:
    """Final field profile result plus emitted artifact paths."""

    access_mode: str
    protocol: str
    status: str
    reason: str
    warnings: tuple[str, ...]
    artifacts: FieldProfileArtifacts
    pyinstrument_text: str | None
    raw_result: PollingProfileResult | SubscribeProfileResult


def _resolve_run_id(run_id: str | None) -> str:
    from datetime import datetime

    return run_id or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _render_report(render: Callable[[], None]) -> str:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        render()
    return buffer.getvalue()


def _merge_warning_items(*items: tuple[str, ...] | str | None) -> tuple[str, ...]:
    warnings: list[str] = []
    for item in items:
        if not item:
            continue
        if isinstance(item, str):
            warnings.append(item)
        else:
            warnings.extend(item)
    return tuple(dict.fromkeys(warnings))


def _write_text(path: Path | None, text: str) -> None:
    if path is None:
        return
    path.write_text(text, encoding="utf-8")


def _profile_json_path(output_dir: Path | None, run_id: str) -> Path | None:
    if output_dir is None:
        return None
    return output_dir / f"field_profile_{run_id}.json"


def _profile_report_path(output_dir: Path | None, run_id: str) -> Path | None:
    if output_dir is None:
        return None
    return output_dir / f"field_profile_{run_id}.txt"


def _profile_pyinstrument_path(output_dir: Path | None, run_id: str) -> Path | None:
    if output_dir is None:
        return None
    return output_dir / f"field_profile_pyinstrument_{run_id}.txt"


def _build_polling_profile_config(request: FieldProfileRequest) -> CapacityScanConfig:
    if request.hz is None:
        raise ValueError("--hz is required for polling profile")
    source_update_hz = request.source_update_hz if request.source_update_hz is not None else request.hz
    if request.source_update_enabled and request.source_update_hz is not None and request.source_update_hz < request.hz:
        raise ValueError("source_update_hz must be greater than or equal to hz")
    return CapacityScanConfig(
        mode=CapacityMode.FIELD,
        protocol=request.protocol,
        endpoints=(),
        points=(),
        server_count_start=request.server_count,
        server_count_step=1,
        server_count_max=request.server_count,
        hz_start=request.hz,
        hz_step=request.hz,
        hz_max=request.hz,
        process_count=request.process_count,
        level_duration_s=request.duration_s,
        warmup_s=request.warmup_s,
        read_timeout_s=request.timeout_s,
        source_update_enabled=request.source_update_enabled,
        source_update_hz=source_update_hz,
        runner_trace_enabled=request.runner_trace_enabled,
        runner_trace_top_n=request.runner_trace_top_n,
    )


def _build_subscribe_profile_config(request: FieldProfileRequest) -> SubscribeScanConfig:
    if request.sample_hz is None:
        raise ValueError("--sample-hz is required for subscribe profile")
    sampling_interval_ms = request.sampling_interval_ms or (1000.0 / request.sample_hz)
    publishing_interval_ms = request.publishing_interval_ms or sampling_interval_ms
    source_update_hz = request.source_update_hz if request.source_update_hz is not None else request.sample_hz
    return SubscribeScanConfig(
        mode=CapacityMode.FIELD,
        protocol=request.protocol,
        server_count_start=request.server_count,
        server_count_step=1,
        server_count_max=request.server_count,
        process_count=request.process_count,
        publishing_interval_ms=publishing_interval_ms,
        sampling_interval_ms=sampling_interval_ms,
        nominal_sample_hz=request.sample_hz,
        queue_size=request.queue_size,
        duration_s=request.duration_s,
        read_timeout_s=request.timeout_s,
        source_update_enabled=request.source_update_enabled,
        source_update_hz=source_update_hz,
        startup_stagger_ms=request.startup_stagger_ms,
        monitored_item_batch_size=request.monitored_item_batch_size,
        monitored_item_batch_gap_ms=request.monitored_item_batch_gap_ms,
        runner_trace_enabled=request.runner_trace_enabled,
        runner_trace_top_n=request.runner_trace_top_n,
    )


def _polling_profile_details(result: PollingProfileResult) -> tuple[str, str, tuple[str, ...]]:
    level = result.result.levels[0]
    warnings = level.final_metrics.warnings
    reason = "" if level.final_status == CapacityStatus.PASS else level.final_reason or level.final_metrics.failure_reason
    return level.final_status.value, reason, warnings


def _subscribe_profile_details(result: SubscribeProfileResult) -> tuple[str, str, tuple[str, ...]]:
    level = result.result.levels[0]
    warnings = level.final_metrics.warnings
    reason = "" if level.final_status == CapacityStatus.PASS else level.final_reason or level.final_metrics.failure_reason
    return level.final_status.value, reason, warnings


def _profile_result_json(
    request: FieldProfileRequest,
    result: FieldProfileServiceResult,
) -> str:
    cap = get_protocol_capability(request.protocol)
    payload = {
        "access_mode": result.access_mode,
        "protocol": result.protocol,
        "implementation_level": cap.get("implementation_level", ""),
        "runner_backend": cap.get("backend", ""),
        "protocol_limitation": cap.get("limitation", ""),
        "process_count": request.process_count,
        "server_count": request.server_count,
        "hz": request.hz,
        "sample_hz": request.sample_hz,
        "publishing_interval_ms": request.publishing_interval_ms,
        "sampling_interval_ms": request.sampling_interval_ms,
        "queue_size": request.queue_size,
        "source_update_enabled": request.source_update_enabled,
        "source_update_hz": (
            result.raw_result.result.config.source_update_hz
            if result.access_mode == "subscribe" and isinstance(result.raw_result, SubscribeProfileResult)
            else request.source_update_hz
        ),
        "status": result.status,
        "reason": result.reason,
        "warnings": list(result.warnings),
        "report_path": None if result.artifacts.report_path is None else str(result.artifacts.report_path),
        "pyinstrument_path": None if result.artifacts.pyinstrument_path is None else str(result.artifacts.pyinstrument_path),
    }
    if request.access_mode == "subscribe" and isinstance(result.raw_result, SubscribeProfileResult):
        metrics = result.raw_result.result.levels[0].final_metrics
        payload["metrics"] = {
            "p95_ms": metrics.response_period_p95_ms,
            "max_ms": metrics.response_period_max_ms,
            "response_period_observable": metrics.response_period_observable,
            "response_period_kind": metrics.response_period_kind,
            "response_p95_ms": metrics.response_period_p95_ms,
            "response_max_ms": metrics.response_period_max_ms,
            "data_p95_ms": metrics.data_period_p95_ms,
            "data_max_ms": metrics.data_period_max_ms,
            "effective_source_update_hz": metrics.effective_source_update_hz,
            "recv_period_p95_ms": metrics.recv_period_p95_ms,
            "recv_period_max_ms": metrics.recv_period_max_ms,
            "callback_to_flush_lag_p95_ms": metrics.callback_to_flush_lag_p95_ms,
            "callback_to_flush_lag_max_ms": metrics.callback_to_flush_lag_max_ms,
            "dispatch_gap_max_ms": metrics.dispatch_gap_max_ms,
            "run_iterate_duration_max_ms": metrics.run_iterate_duration_max_ms,
            "source_period_p95_ms": metrics.source_period_p95_ms,
            "source_period_max_ms": metrics.source_period_max_ms,
            "notification_count": metrics.notification_count,
            "value_count": metrics.value_count,
            "keepalive_count": metrics.keepalive_count,
            "keepalive_miss_count": metrics.keepalive_miss_count,
            "publish_timeout_count": metrics.publish_timeout_count,
            "resubscribe_count": metrics.resubscribe_count,
            "resubscribe_success_count": metrics.resubscribe_success_count,
            "resubscribe_failure_count": metrics.resubscribe_failure_count,
            "unrecovered_endpoint_count": metrics.unrecovered_endpoint_count,
            "recovery_duration_ms": metrics.recovery_duration_ms,
            "last_reconnect_reason": metrics.last_reconnect_reason,
            "top_period_gap_traces": [
                {
                    "global_index": trace.global_index,
                    "local_index": trace.local_index,
                    "previous_notify_timestamp_ns": trace.previous_notify_timestamp_ns,
                    "notify_timestamp_ns": trace.notify_timestamp_ns,
                    "period_ms": trace.period_ms,
                }
                for trace in metrics.top_period_gap_traces
            ],
            "top_data_period_gap_traces": [
                {
                    "global_index": trace.global_index,
                    "local_index": trace.local_index,
                    "previous_notify_timestamp_ns": trace.previous_notify_timestamp_ns,
                    "notify_timestamp_ns": trace.notify_timestamp_ns,
                    "period_ms": trace.period_ms,
                }
                for trace in metrics.top_data_period_gap_traces
            ],
            "top_flush_lag_traces": [
                {
                    "global_index": trace.global_index,
                    "local_index": trace.local_index,
                    "notify_timestamp_ns": trace.notify_timestamp_ns,
                    "flush_timestamp_ns": trace.flush_timestamp_ns,
                    "lag_ms": trace.lag_ms,
                }
                for trace in metrics.top_flush_lag_traces
            ],
            "top_dispatch_gap_traces": [
                {
                    "global_index": trace.global_index,
                    "local_index": trace.local_index,
                    "notification_count": trace.notification_count,
                    "run_iterate_count": trace.run_iterate_count,
                    "max_dispatch_gap_ms": trace.max_dispatch_gap_ms,
                    "max_run_iterate_duration_ms": trace.max_run_iterate_duration_ms,
                    "revised_publishing_interval_ms": trace.revised_publishing_interval_ms,
                    "revised_sampling_interval_ms": trace.revised_sampling_interval_ms,
                }
                for trace in metrics.top_dispatch_gap_traces
            ],
        }
    return json.dumps(payload, ensure_ascii=True, indent=2) + "\n"


def write_profile_reports(
    request: FieldProfileRequest,
    result: PollingProfileResult | SubscribeProfileResult,
    *,
    output_dir: Path | None,
    run_id: str,
) -> FieldProfileArtifacts:
    """Write field-profile artifacts and return their paths."""

    report_path = _profile_report_path(output_dir, run_id)
    pyinstrument_path = _profile_pyinstrument_path(output_dir, run_id)
    json_path = _profile_json_path(output_dir, run_id)
    written_pyinstrument_path: Path | None = None
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        if isinstance(result, PollingProfileResult):
            report_text = _render_report(lambda: print_capacity_report(result.result))
        else:
            report_text = _render_report(lambda: print_subscribe_report(result.result))
        _write_text(report_path, report_text)
        if request.pyinstrument and result.pyinstrument_text:
            _write_text(pyinstrument_path, result.pyinstrument_text + "\n")
            written_pyinstrument_path = pyinstrument_path
    return FieldProfileArtifacts(report_path=report_path, pyinstrument_path=written_pyinstrument_path, json_path=json_path)


def print_profile_summary(result: FieldProfileServiceResult) -> None:
    """Print a one-line summary for field-profile CLI use."""

    warnings = ",".join(result.warnings) if result.warnings else "-"
    report_path = "-" if result.artifacts.report_path is None else str(result.artifacts.report_path)
    print(
        f"access_mode={result.access_mode} status={result.status} reason={result.reason or '-'} "
        f"warnings={warnings} report_path={report_path}",
        flush=True,
    )


def run_field_profile(
    request: FieldProfileRequest,
    *,
    provider: SourceProvider,
) -> FieldProfileServiceResult:
    """Run one field-profile configuration and persist artifacts."""

    if not supports_access_mode(request.protocol, request.access_mode):
        raise ValueError(
            "protocol/access_mode is not supported: "
            f"protocol={request.protocol}, access_mode={request.access_mode}"
        )

    if request.access_mode == "polling":
        polling_config = _build_polling_profile_config(request)
        profile_result: PollingProfileResult | SubscribeProfileResult = run_polling_profile(
            polling_config,
            provider=provider,
            runner=build_capacity_runner(request.protocol),
            pyinstrument=request.pyinstrument,
            max_lines=request.profile_max_lines,
        )
    elif request.access_mode == "subscribe":
        subscribe_config = _build_subscribe_profile_config(request)
        profile_result = run_subscribe_profile(
            subscribe_config,
            provider=provider,
            runner=build_subscription_runner(request.protocol),
            pyinstrument=request.pyinstrument,
            max_lines=request.profile_max_lines,
        )
    else:
        raise ValueError(f"unsupported access_mode: {request.access_mode}")

    if isinstance(profile_result, PollingProfileResult):
        status, reason, warnings = _polling_profile_details(profile_result)
    else:
        status, reason, warnings = _subscribe_profile_details(profile_result)
    if request.pyinstrument and profile_result.pyinstrument_text is None:
        warnings = _merge_warning_items(warnings, "pyinstrument_not_installed")

    artifacts = write_profile_reports(
        request,
        profile_result,
        output_dir=request.output_dir,
        run_id=request.run_id,
    )
    if artifacts.json_path is not None:
        _write_text(artifacts.json_path, _profile_result_json(request, FieldProfileServiceResult(
            access_mode=request.access_mode,
            protocol=request.protocol,
            status=status,
            reason=reason,
            warnings=warnings,
            artifacts=artifacts,
            pyinstrument_text=profile_result.pyinstrument_text,
            raw_result=profile_result,
        )))
    return FieldProfileServiceResult(
        access_mode=request.access_mode,
        protocol=request.protocol,
        status=status,
        reason=reason,
        warnings=warnings,
        artifacts=artifacts,
        pyinstrument_text=profile_result.pyinstrument_text,
        raw_result=profile_result,
    )


def run_field_profile_from_files(
    request: FieldProfileRequest,
    *,
    servers_path: Path,
    profile_items_path: Path,
) -> FieldProfileServiceResult:
    """Load field inputs, build the appropriate provider, and run profile."""

    sources = build_field_runtime_sources(servers_path, profile_items_path, protocol=normalize_protocol(request.protocol))
    provider = build_field_source_provider(sources, protocol=normalize_protocol(request.protocol))
    return run_field_profile(request, provider=provider)


def run_profile(
    access_mode: str,
    *,
    config: CapacityScanConfig | SubscribeScanConfig,
    provider: SourceProvider,
    runner: CapacityRunner | SubscriptionRunner,
    pyinstrument: bool = False,
    show_all: bool = False,
    max_lines: int = 80,
) -> PollingProfileResult | SubscribeProfileResult:
    """Run one single-configuration profile by access mode."""

    if access_mode == "polling":
        if not isinstance(config, CapacityScanConfig):
            raise TypeError("polling profile requires CapacityScanConfig")
        if not isinstance(runner, CapacityRunner):
            raise TypeError("polling profile requires CapacityRunner")
        return run_polling_profile(
            config,
            provider=provider,
            runner=runner,
            pyinstrument=pyinstrument,
            show_all=show_all,
            max_lines=max_lines,
        )
    if access_mode != "subscribe":
        raise ValueError(f"unsupported access_mode: {access_mode}")
    if not isinstance(config, SubscribeScanConfig):
        raise TypeError("subscribe profile requires SubscribeScanConfig")
    if not isinstance(runner, SubscriptionRunner):
        raise TypeError("subscribe profile requires SubscriptionRunner")
    return run_subscribe_profile(
        config,
        provider=provider,
        runner=runner,
        pyinstrument=pyinstrument,
        show_all=show_all,
        max_lines=max_lines,
    )
