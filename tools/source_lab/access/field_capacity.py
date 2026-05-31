"""现场容量测试编排与报告行渲染辅助。

负责：按 polling/subscribe 两种接入模式执行现场容量扫描，汇总为 FieldCapacityRow 并输出 CSV/JSONL 报告。
不负责：协议级连接管理与数据源发现（由 provider 层负责）。
数据流：FieldCapacityRequest -> provider 提供模拟/文件数据源 -> scan_capacity -> FieldCapacityRow -> CSV/JSONL。
"""

from __future__ import annotations

import csv
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
import json
import os
from pathlib import Path
import sys
from typing import Protocol, cast

from tools.source_lab.access.common.cpu import CpuSampler
from tools.source_lab.access.common.io import build_field_runtime_sources
from tools.source_lab.access.common.progress import CapacityProgressBar
from tools.source_lab.access.common.table import render_fixed_width_table
from tools.source_lab.access.common.utils import normalize_protocol
from tools.source_lab.access.polling.capacity import scan_source_capacity
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig, CapacityScanResult, CapacityStatus
from tools.source_lab.access.providers.base import SourceProvider
from tools.source_lab.access.providers.file_field import build_field_source_provider
from tools.source_lab.access.runners.registry import (
    build_capacity_runner,
    build_subscription_runner,
    get_protocol_capability,
    supports_access_mode,
)
from tools.source_lab.access.subscribe.capacity_model import (
    SubscribeCapacityComboResult,
    SubscribeCapacityLimitSummary,
    SubscribeCapacityResult,
)
from tools.source_lab.access.subscribe.model import SubscribeScanConfig

@dataclass(frozen=True, slots=True)
class FieldCapacityRow:
    """One normalized field-capacity report row."""

    access_mode: str
    process_count: int
    server_count: int
    protocol: str
    mode: str = ""
    hz: float = 0.0
    sample_hz: float = 0.0
    period_ms: float = 0.0
    points_per_server: int = 0
    point_total: int = 0
    expected_values: int = 0
    values: int = 0
    value_ratio: float = 0.0
    value_miss: int = 0
    bad: int = 0
    miss_ts: int = 0
    noise: int = 0
    notify: int = 0
    expected_notifications: int = 0
    expected_items: int = 0
    created_items: int = 0
    reads: int = 0
    batches: int = 0
    publishing_interval_ms: float = 0.0
    sampling_interval_ms: float = 0.0
    effective_source_update_hz: float = 0.0
    queue_size: int = 0
    publish_gap_p95_ms: float = 0.0
    publish_gap_max_ms: float = 0.0
    data_age_p95_ms: float = 0.0
    data_age_max_ms: float = 0.0
    response_period_p95_ms: float = 0.0
    response_period_max_ms: float = 0.0
    data_period_p95_ms: float = 0.0
    data_period_max_ms: float = 0.0
    source_period_p95_ms: float = 0.0
    source_period_max_ms: float = 0.0
    point_count: int = 0
    cpu_mean_pct: float = 0.0
    cpu_max_pct: float = 0.0
    rss_mb: float = 0.0
    status: str = CapacityStatus.SKIP.value
    reason: str = ""
    warnings: str = ""
    runner_protocol_noise_count: int = 0
    sub_hz: float = 0.0
    src_hz: float = 0.0
    sub_ms: float = 0.0
    src_ms: float = 0.0
    implementation_level: str = ""
    runner_backend: str = ""
    protocol_limitation: str = ""


@dataclass(frozen=True, slots=True)
class FieldCapacityRequest:
    """Application-layer request for field-capacity execution."""

    access_mode: str
    protocol: str
    service_type: str | None
    process_counts: tuple[int, ...]
    server_counts: tuple[int, ...]
    output_dir: Path
    run_id: str
    duration_s: float = 30.0
    warmup_s: float = 10.0
    timeout_s: float = 5.0
    source_update_enabled: bool = True
    source_update_hz: float | None = None
    source_update_hz_values: tuple[float, ...] = ()
    hz_values: tuple[float, ...] = ()
    sample_hz_values: tuple[float, ...] = ()
    publishing_interval_ms: float | None = None
    sampling_interval_ms: float | None = None
    queue_sizes: tuple[int, ...] = (1,)
    startup_stagger_ms: int = 0
    monitored_item_batch_size: int = 100
    monitored_item_batch_gap_ms: int = 0


@dataclass(frozen=True, slots=True)
class FieldCapacityArtifacts:
    """Report artifact paths emitted by field-capacity execution."""

    csv_path: Path
    jsonl_path: Path
    limit_csv_path: Path | None = None


@dataclass(frozen=True, slots=True)
class FieldCapacityServiceResult:
    """Final field-capacity report plus written artifact paths."""

    rows: tuple[FieldCapacityRow, ...]
    artifacts: FieldCapacityArtifacts
    limit_summaries: tuple[SubscribeCapacityLimitSummary, ...] = ()


class CpuSnapshot(Protocol):
    @property
    def cpu_mean_pct(self) -> float: ...

    @property
    def cpu_max_pct(self) -> float: ...

    @property
    def rss_mb(self) -> float: ...

    @property
    def warning(self) -> str: ...


_SUMMARY_HEADERS = (
    "proc",
    "srv",
    "hz",
    "period_ms",
    "value_ratio",
    "p95_ms",
    "max_ms",
    "status",
    "reason",
)
_SUBSCRIBE_SUMMARY_HEADERS = (
    "proc",
    "srv",
    "sub_hz",
    "src_hz",
    "sub_ms",
    "src_ms",
    "value_ratio",
    "p95_ms",
    "max_ms",
    "status",
    "reason",
)
_ROW_ATTRS = {
    "mode": "mode",
    "proc": "process_count",
    "srv": "server_count",
    "hz": "hz",
    "sub_hz": "sub_hz",
    "src_hz": "src_hz",
    "period_ms": "period_ms",
    "sub_ms": "sub_ms",
    "src_ms": "src_ms",
    "points_per_srv": "points_per_server",
    "point_total": "point_total",
    "expected_values": "expected_values",
    "values": "values",
    "value_ratio": "value_ratio",
    "p95_ms": "data_period_p95_ms",
    "max_ms": "data_period_max_ms",
    "value_miss": "value_miss",
    "bad": "bad",
    "miss_ts": "miss_ts",
    "noise": "noise",
    "expected_items": "expected_items",
    "created_items": "created_items",
    "notify": "notify",
    "reads": "reads",
    "batches": "batches",
    "queue": "queue_size",
    "publish_gap_p95_ms": "publish_gap_p95_ms",
    "publish_gap_max_ms": "publish_gap_max_ms",
    "data_age_p95_ms": "data_age_p95_ms",
    "data_age_max_ms": "data_age_max_ms",
    "response_period_p95_ms": "response_period_p95_ms",
    "response_period_max_ms": "response_period_max_ms",
    "data_period_p95_ms": "data_period_p95_ms",
    "data_period_max_ms": "data_period_max_ms",
    "source_period_p95_ms": "source_period_p95_ms",
    "source_period_max_ms": "source_period_max_ms",
    "status": "status",
    "reason": "reason",
}
_DETAIL_MODE_WARNING = (
    "SOURCE_LAB_CAPACITY_TABLE_MODE is deprecated; use profile for diagnostics"
)
_FLOAT_PRECISION = {
    "hz": 1,
    "sub_hz": 1,
    "src_hz": 1,
    "period_ms": 1,
    "sub_ms": 1,
    "src_ms": 1,
    "value_ratio": 3,
    "p95_ms": 2,
    "max_ms": 2,
    "publish_gap_p95_ms": 2,
    "publish_gap_max_ms": 2,
    "data_age_p95_ms": 2,
    "data_age_max_ms": 2,
    "response_period_p95_ms": 2,
    "response_period_max_ms": 2,
    "data_period_p95_ms": 2,
    "data_period_max_ms": 2,
    "source_period_p95_ms": 2,
    "source_period_max_ms": 2,
}
_DEFAULT_WIDTHS = {
    "mode": 10,
    "proc": 5,
    "srv": 5,
    "hz": 6,
    "sub_hz": 6,
    "src_hz": 6,
    "period_ms": 9,
    "sub_ms": 8,
    "src_ms": 8,
    "points_per_srv": 14,
    "point_total": 10,
    "expected_values": 15,
    "values": 8,
    "value_ratio": 11,
    "p95_ms": 8,
    "max_ms": 8,
    "value_miss": 10,
    "bad": 5,
    "miss_ts": 7,
    "noise": 5,
    "expected_items": 14,
    "created_items": 13,
    "notify": 8,
    "reads": 7,
    "batches": 8,
    "queue": 5,
    "publish_gap_p95_ms": 19,
    "publish_gap_max_ms": 19,
    "data_age_p95_ms": 16,
    "data_age_max_ms": 16,
    "response_period_p95_ms": 19,
    "response_period_max_ms": 19,
    "data_period_p95_ms": 19,
    "data_period_max_ms": 19,
    "source_period_p95_ms": 18,
    "source_period_max_ms": 18,
    "status": 7,
    "reason": 7,
}

_detail_mode_warned = False


def _warn_deprecated_detail_mode() -> None:
    global _detail_mode_warned
    raw = os.environ.get("SOURCE_LAB_CAPACITY_TABLE_MODE", "").strip().lower()
    if raw != "detail" or _detail_mode_warned:
        return
    print(_DETAIL_MODE_WARNING, file=sys.stderr, flush=True)
    _detail_mode_warned = True


def _format_cell(header: str, row: FieldCapacityRow) -> str:
    attribute_name = _ROW_ATTRS[header]
    value = getattr(row, attribute_name)
    if header == "reason":
        return row.reason or "-"
    if isinstance(value, float):
        precision = _FLOAT_PRECISION.get(header, 0)
        return f"{value:.{precision}f}" if precision > 0 else str(int(value))
    return str(value)


def _summary_headers(rows: tuple[FieldCapacityRow, ...]) -> tuple[str, ...]:
    if rows and all(row.access_mode == "subscribe" for row in rows):
        return _SUBSCRIBE_SUMMARY_HEADERS
    return _SUMMARY_HEADERS


def print_capacity_table(rows: tuple[FieldCapacityRow, ...]) -> None:
    """Print the fixed summary table used by capacity output."""

    if not rows:
        print("[source-lab] capacity table: no rows", flush=True)
        return

    _warn_deprecated_detail_mode()
    table = render_fixed_width_table(
        headers=_summary_headers(rows),
        rows=rows,
        format_cell=cast(Callable[[str, object], str], _format_cell),
        default_widths=_DEFAULT_WIDTHS,
    )
    print(table, flush=True)


def _write_rows(path: Path, rows: tuple[FieldCapacityRow, ...]) -> None:
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(FieldCapacityRow.__dataclass_fields__.keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _write_jsonl(path: Path, rows: tuple[FieldCapacityRow, ...]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), ensure_ascii=True) + "\n")


def _write_limit_summaries(
    path: Path,
    summaries: tuple[SubscribeCapacityLimitSummary, ...],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "process_count",
                "server_count",
                "queue_size",
                "effective_source_update_hz",
                "max_pass_sample_hz",
                "first_fail_sample_hz",
                "reason",
            ],
        )
        writer.writeheader()
        for summary in summaries:
            writer.writerow(asdict(summary))


def write_capacity_reports(
    output_dir: Path,
    *,
    run_id: str,
    rows: tuple[FieldCapacityRow, ...],
    limit_summaries: tuple[SubscribeCapacityLimitSummary, ...] = (),
) -> FieldCapacityArtifacts:
    """Write field-capacity report artifacts and return their paths."""

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"field_capacity_{run_id}.csv"
    jsonl_path = output_dir / f"field_capacity_{run_id}.jsonl"
    _write_rows(csv_path, rows)
    _write_jsonl(jsonl_path, rows)
    limit_csv_path: Path | None = None
    if limit_summaries:
        limit_csv_path = output_dir / f"field_capacity_limits_{run_id}.csv"
        _write_limit_summaries(limit_csv_path, limit_summaries)
    return FieldCapacityArtifacts(csv_path=csv_path, jsonl_path=jsonl_path, limit_csv_path=limit_csv_path)


def print_capacity_summary(result: FieldCapacityServiceResult) -> None:
    """Print the summary table plus artifact locations."""

    print_capacity_table(result.rows)
    print(f"csv_path={result.artifacts.csv_path}", flush=True)
    print(f"jsonl_path={result.artifacts.jsonl_path}", flush=True)
    if result.artifacts.limit_csv_path is not None:
        print(f"limit_csv_path={result.artifacts.limit_csv_path}", flush=True)


def build_polling_capacity_rows(
    result: CapacityScanResult | tuple[CapacityScanResult, ...],
) -> tuple[FieldCapacityRow, ...]:
    """Forward polling row building without a module-level cycle."""

    from tools.source_lab.access.polling.capacity_rows import build_polling_capacity_rows as _build

    return _build(result)


def build_subscribe_capacity_rows(
    result: SubscribeCapacityResult,
    *,
    protocol: str,
) -> tuple[FieldCapacityRow, ...]:
    """Forward subscribe row building without a module-level cycle."""

    from tools.source_lab.access.subscribe.capacity_rows import build_subscribe_capacity_rows as _build

    return _build(result, protocol=protocol)


def _run_polling_field_capacity(
    request: FieldCapacityRequest,
    *,
    provider: SourceProvider,
    point_count_per_server: int,
) -> tuple[FieldCapacityRow, ...]:
    from tools.source_lab.access.polling.capacity_rows import polling_row

    runner = build_capacity_runner(request.protocol).runner
    rows: list[FieldCapacityRow] = []
    progress = CapacityProgressBar(
        "polling",
        total=len(request.process_counts) * len(request.server_counts) * len(request.hz_values),
    )
    current = 0
    cap = get_protocol_capability(request.protocol)
    try:
        for process_count in request.process_counts:
            for server_count in request.server_counts:
                for hz in request.hz_values:
                    config = CapacityScanConfig(
                        mode=CapacityMode.FIELD,
                        protocol=normalize_protocol(request.protocol),
                        endpoints=(),
                        points=(),
                        server_count_start=server_count,
                        server_count_step=1,
                        server_count_max=server_count,
                        hz_start=hz,
                        hz_step=hz,
                        hz_max=hz,
                        process_count=process_count,
                        level_duration_s=request.duration_s,
                        warmup_s=request.warmup_s,
                        read_timeout_s=request.timeout_s,
                        source_update_enabled=request.source_update_enabled,
                        source_update_hz=request.source_update_hz or hz,
                        progress_enabled=False,
                        runner_trace_enabled=False,
                    )
                    sampler = CpuSampler(interval_s=1.0)
                    sampler.start()
                    result = scan_source_capacity(config, provider=provider, runner=runner)
                    cpu = sampler.stop()
                    row = polling_row(
                        result,
                        process_count=process_count,
                        point_count=point_count_per_server * server_count,
                        cpu=cpu,
                        source_update_enabled=request.source_update_enabled,
                    )
                    rows.append(replace(
                        row,
                        implementation_level=str(cap.get("implementation_level", "")),
                        runner_backend=str(cap.get("backend", "")),
                        protocol_limitation=str(cap.get("limitation", "")),
                    ))
                    current += 1
                    progress.update(
                        process_count=process_count,
                        process_max=request.process_counts[-1],
                        server_count=server_count,
                        server_max=request.server_counts[-1],
                        hz=hz,
                        hz_max=request.hz_values[-1],
                        current=current,
                    )
    finally:
        progress.close()
    return tuple(rows)


def _run_subscribe_field_capacity(
    request: FieldCapacityRequest,
    *,
    provider: SourceProvider,
    point_count_per_server: int,
) -> tuple[tuple[FieldCapacityRow, ...], tuple[SubscribeCapacityLimitSummary, ...]]:
    from tools.source_lab.access.capacity import scan_capacity
    from tools.source_lab.access.subscribe.capacity_rows import sample_hz_to_interval_ms, subscribe_row

    runner = build_subscription_runner(request.protocol)
    rows: list[FieldCapacityRow] = []
    limit_summaries: list[SubscribeCapacityLimitSummary] = []
    resolved_source_update_hz_values = request.source_update_hz_values or (
        (request.source_update_hz,) if request.source_update_hz is not None else ()
    )
    for server_count in request.server_counts:
        base_sample_hz = min(request.sample_hz_values)
        base_interval_ms = sample_hz_to_interval_ms(base_sample_hz)
        base_source_update_hz = (
            resolved_source_update_hz_values[0]
            if resolved_source_update_hz_values
            else (request.source_update_hz or base_sample_hz)
        )
        config = SubscribeScanConfig(
            mode=CapacityMode.FIELD,
            protocol=normalize_protocol(request.protocol),
            server_count_start=server_count,
            server_count_step=1,
            server_count_max=server_count,
            process_count=request.process_counts[0],
            publishing_interval_ms=request.publishing_interval_ms or base_interval_ms,
            sampling_interval_ms=base_interval_ms,
            queue_size=request.queue_sizes[0],
            duration_s=request.duration_s,
            read_timeout_s=request.timeout_s,
            source_update_enabled=request.source_update_enabled,
            source_update_hz=base_source_update_hz,
            source_update_hz_explicit=bool(resolved_source_update_hz_values) or request.source_update_hz is not None,
            startup_stagger_ms=request.startup_stagger_ms,
            monitored_item_batch_size=request.monitored_item_batch_size,
            monitored_item_batch_gap_ms=request.monitored_item_batch_gap_ms,
        )
        sampler = CpuSampler(interval_s=1.0)
        sampler.start()
        result = scan_capacity(
            "subscribe",
            config=config,
            provider=provider,
            runner=runner,
            process_counts=request.process_counts,
            sample_hz_values=request.sample_hz_values,
            queue_sizes=request.queue_sizes,
            source_update_hz_values=resolved_source_update_hz_values or None,
            explicit_publishing_interval_ms=request.publishing_interval_ms,
            explicit_source_update_hz=request.source_update_hz,
            stop_on_first_fail_per_server=False,
        )
        cpu = sampler.stop()
        if not isinstance(result, SubscribeCapacityResult):
            raise RuntimeError("subscribe capacity returned unexpected result type")
        cap = get_protocol_capability(request.protocol)
        for combo in result.combos:
            row = subscribe_row(
                combo,
                protocol=normalize_protocol(request.protocol),
                point_count_per_server=point_count_per_server,
                cpu=cpu,
                source_update_enabled=request.source_update_enabled,
            )
            rows.append(replace(
                row,
                implementation_level=str(cap.get("implementation_level", "")),
                runner_backend=str(cap.get("backend", "")),
                protocol_limitation=str(cap.get("limitation", "")),
            ))
        limit_summaries.extend(result.limit_summaries)
    return tuple(rows), tuple(limit_summaries)


def run_field_capacity(
    request: FieldCapacityRequest,
    *,
    provider: SourceProvider,
    point_count_per_server: int,
) -> FieldCapacityServiceResult:
    """Run field-capacity workloads and persist report artifacts."""

    if not supports_access_mode(request.protocol, request.access_mode):
        raise ValueError(
            "protocol/access_mode is not supported: "
            f"protocol={request.protocol}, access_mode={request.access_mode}"
        )

    if request.access_mode == "polling":
        rows = _run_polling_field_capacity(
            request,
            provider=provider,
            point_count_per_server=point_count_per_server,
        )
        artifacts = write_capacity_reports(request.output_dir, run_id=request.run_id, rows=rows)
        return FieldCapacityServiceResult(rows=rows, artifacts=artifacts)

    if request.access_mode != "subscribe":
        raise ValueError(f"unsupported access_mode: {request.access_mode}")

    rows, limit_summaries = _run_subscribe_field_capacity(
        request,
        provider=provider,
        point_count_per_server=point_count_per_server,
    )
    artifacts = write_capacity_reports(
        request.output_dir,
        run_id=request.run_id,
        rows=rows,
        limit_summaries=limit_summaries,
    )
    return FieldCapacityServiceResult(rows=rows, artifacts=artifacts, limit_summaries=limit_summaries)


def run_field_capacity_from_files(
    request: FieldCapacityRequest,
    *,
    servers_path: Path,
    profile_items_path: Path,
) -> FieldCapacityServiceResult:
    """Load field inputs, resolve the appropriate provider, and run capacity."""

    sources = build_field_runtime_sources(servers_path, profile_items_path, protocol=request.protocol)
    provider = build_field_source_provider(sources, protocol=request.protocol)
    point_count_per_server = len(sources[0].points) if sources else 0
    return run_field_capacity(
        request,
        provider=provider,
        point_count_per_server=point_count_per_server,
    )


__all__ = [
    "FieldCapacityArtifacts",
    "FieldCapacityRequest",
    "FieldCapacityRow",
    "FieldCapacityServiceResult",
    "SubscribeCapacityComboResult",
    "SubscribeCapacityLimitSummary",
    "SubscribeCapacityResult",
    "build_polling_capacity_rows",
    "build_subscribe_capacity_rows",
    "print_capacity_summary",
    "print_capacity_table",
    "run_field_capacity",
    "run_field_capacity_from_files",
    "write_capacity_reports",
]
