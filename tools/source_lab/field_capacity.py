"""CLI entrypoint for field capacity scans backed by field TSV/CSV inputs."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path

from tools.source_lab.access.capacity import scan_source_capacity
from tools.source_lab.access.cpu import CpuSampler
from tools.source_lab.access.io import build_field_runtime_sources
from tools.source_lab.access.model import CapacityMode, CapacityScanConfig, CapacityStatus
from tools.source_lab.access.providers.file_field import FieldFileSourceProvider
from tools.source_lab.access.runners.open62541_serial_polling import OpcUaOpen62541CapacityRunner
from tools.source_lab.access.utils import normalize_protocol


@dataclass(frozen=True, slots=True)
class FieldCapacityRow:
    """One output row produced by ``field_capacity``."""

    process_count: int
    server_count: int
    protocol: str
    hz: float
    period_ms: float
    cpu_mean_pct: float
    cpu_max_pct: float
    rss_mb: float
    bad: int
    read_errors: int
    missing_ts: int
    missed: int
    p_n: int
    p_mean: float
    p_max: float
    mean_err: float
    runner_max_lag: float
    runner_max_read: float
    status: str
    reason: str


def _parse_int_list(value: str) -> list[int]:
    """Parse a comma-separated integer list."""

    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _parse_float_list(value: str) -> list[float]:
    """Parse a comma-separated float list."""

    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _build_parser() -> argparse.ArgumentParser:
    """Build the ``field_capacity`` CLI parser.

    Returns:
        Configured argument parser for field capacity scans.
    """

    parser = argparse.ArgumentParser(
        description="Run field capacity scans from field_servers.tsv and signal_profile_items.tsv.",
    )
    parser.add_argument("--servers", type=Path, required=True, help="Path to field_servers TSV/CSV.")
    parser.add_argument(
        "--profile-items",
        type=Path,
        required=True,
        help="Path to signal_profile_items TSV/CSV.",
    )
    parser.add_argument(
        "--protocol",
        default="opcua",
        help="Protocol group to execute. Non-OPC UA groups are reported as SKIP.",
    )
    parser.add_argument(
        "--process-counts",
        required=True,
        help="Comma-separated process counts, for example: 1,2,4,8.",
    )
    parser.add_argument(
        "--hz",
        required=True,
        help="Comma-separated polling rates in Hz, for example: 10,20,30.",
    )
    parser.add_argument("--duration", type=float, default=60.0, help="Per-level measurement duration in seconds.")
    parser.add_argument("--warmup", type=float, default=10.0, help="Per-level warmup in seconds.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Protocol read timeout in seconds.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where CSV and JSONL reports will be written.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run identifier used in output filenames. Defaults to a UTC timestamp.",
    )
    return parser


def _build_config(
    *,
    protocol: str,
    server_count: int,
    process_count: int,
    hz: float,
    duration_s: float,
    warmup_s: float,
    timeout_s: float,
) -> CapacityScanConfig:
    """Build one single-level capacity config."""

    return CapacityScanConfig(
        mode=CapacityMode.FIELD,
        protocol=protocol,
        endpoints=(),
        points=(),
        server_count_start=server_count,
        server_count_step=1,
        server_count_max=server_count,
        hz_start=hz,
        hz_step=hz,
        hz_max=hz,
        process_count=process_count,
        level_duration_s=duration_s,
        warmup_s=warmup_s,
        read_timeout_s=timeout_s,
        progress_enabled=True,
    )


def _skip_row(process_count: int, server_count: int, protocol: str, hz: float, reason: str) -> FieldCapacityRow:
    """Build one skipped capacity row.

    Args:
        process_count: Process count for the scan slot.
        server_count: Number of servers represented by the row.
        protocol: Protocol label for the row.
        hz: Requested polling rate.
        reason: Stable skip reason.

    Returns:
        A normalized skipped row.
    """

    return FieldCapacityRow(
        process_count=process_count,
        server_count=server_count,
        protocol=protocol,
        hz=hz,
        period_ms=round(1000.0 / hz, 1),
        cpu_mean_pct=0.0,
        cpu_max_pct=0.0,
        rss_mb=0.0,
        bad=0,
        read_errors=0,
        missing_ts=0,
        missed=0,
        p_n=0,
        p_mean=0.0,
        p_max=0.0,
        mean_err=0.0,
        runner_max_lag=0.0,
        runner_max_read=0.0,
        status=CapacityStatus.SKIP.value,
        reason=reason,
    )


def _resolve_run_id(run_id: str | None) -> str:
    """Resolve the output run identifier.

    Args:
        run_id: Optional caller-provided identifier.

    Returns:
        A non-empty identifier safe for file naming.
    """

    return run_id or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _write_reports(output_dir: Path, rows: tuple[FieldCapacityRow, ...], *, run_id: str) -> None:
    """Write field capacity rows to CSV and JSONL.

    Args:
        output_dir: Report directory.
        rows: Rows to persist.
        run_id: Unique run identifier used in filenames.
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"field_capacity_{run_id}.csv"
    jsonl_path = output_dir / f"field_capacity_{run_id}.jsonl"
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(FieldCapacityRow.__dataclass_fields__.keys())
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), ensure_ascii=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    """Run the ``field_capacity`` CLI.

    Args:
        argv: Optional argument vector override.

    Returns:
        Process exit code.
    """

    args = _build_parser().parse_args(argv)
    requested_protocol = normalize_protocol(args.protocol)
    run_id = _resolve_run_id(args.run_id)
    sources = build_field_runtime_sources(args.servers, args.profile_items)
    process_counts = _parse_int_list(args.process_counts)
    hz_values = _parse_float_list(args.hz)
    grouped: dict[str, tuple] = {}
    for source in sources:
        protocol = normalize_protocol(source.endpoint.protocol)
        grouped.setdefault(protocol, tuple())
    for protocol in tuple(grouped):
        grouped[protocol] = tuple(source for source in sources if normalize_protocol(source.endpoint.protocol) == protocol)

    rows: list[FieldCapacityRow] = []
    runner = OpcUaOpen62541CapacityRunner()
    for protocol, protocol_sources in grouped.items():
        for process_count in process_counts:
            for hz in hz_values:
                if protocol != requested_protocol:
                    reason = "unsupported_protocol" if protocol != "opcua" else "protocol_filtered"
                    rows.append(_skip_row(process_count, len(protocol_sources), protocol, hz, reason))
                    continue
                if requested_protocol != "opcua":
                    rows.append(_skip_row(process_count, len(protocol_sources), protocol, hz, "unsupported_protocol"))
                    continue
                if protocol != "opcua":
                    rows.append(_skip_row(process_count, len(protocol_sources), protocol, hz, "unsupported_protocol"))
                    continue
                config = _build_config(
                    protocol=protocol,
                    server_count=len(protocol_sources),
                    process_count=process_count,
                    hz=hz,
                    duration_s=args.duration,
                    warmup_s=args.warmup,
                    timeout_s=args.timeout,
                )
                provider = FieldFileSourceProvider(protocol_sources, protocol=protocol)
                sampler = CpuSampler(interval_s=1.0)
                sampler.start()
                result = scan_source_capacity(config, provider=provider, runner=runner)
                cpu = sampler.stop()
                level = result.levels[0]
                metrics = level.primary
                rows.append(
                    FieldCapacityRow(
                        process_count=process_count,
                        server_count=metrics.server_count,
                        protocol=protocol,
                        hz=metrics.target_hz,
                        period_ms=metrics.target_period_ms,
                        cpu_mean_pct=round(cpu.cpu_mean_pct, 3),
                        cpu_max_pct=round(cpu.cpu_max_pct, 3),
                        rss_mb=round(cpu.rss_mb, 3),
                        bad=metrics.batch_mismatches,
                        read_errors=metrics.read_errors,
                        missing_ts=metrics.missing_response_timestamps,
                        missed=metrics.missed_ticks,
                        p_n=metrics.period_samples,
                        p_mean=metrics.period_mean_ms,
                        p_max=metrics.period_max_ms,
                        mean_err=metrics.period_mean_abs_error_ms,
                        runner_max_lag=metrics.runner_max_lag_ms,
                        runner_max_read=metrics.runner_max_read_ms,
                        status=level.final_status.value,
                        reason=cpu.warning or level.final_reason or metrics.failure_reason,
                    )
                )

    if not rows and requested_protocol != "opcua":
        for process_count in process_counts:
            for hz in hz_values:
                rows.append(_skip_row(process_count, 0, requested_protocol, hz, "unsupported_protocol"))

    print(
        "\t".join(
            [
                "process_count",
                "server_count",
                "protocol",
                "hz",
                "period_ms",
                "cpu_mean_pct",
                "cpu_max_pct",
                "rss_mb",
                "bad",
                "read_errors",
                "missing_ts",
                "missed",
                "p_n",
                "p_mean",
                "p_max",
                "mean_err",
                "runner_max_lag",
                "runner_max_read",
                "status",
                "reason",
            ]
        )
    )
    for row in rows:
        print(
            "\t".join(
                [
                    str(row.process_count),
                    str(row.server_count),
                    row.protocol,
                    f"{row.hz:.3f}",
                    f"{row.period_ms:.3f}",
                    f"{row.cpu_mean_pct:.3f}",
                    f"{row.cpu_max_pct:.3f}",
                    f"{row.rss_mb:.3f}",
                    str(row.bad),
                    str(row.read_errors),
                    str(row.missing_ts),
                    str(row.missed),
                    str(row.p_n),
                    f"{row.p_mean:.3f}",
                    f"{row.p_max:.3f}",
                    f"{row.mean_err:.3f}",
                    f"{row.runner_max_lag:.3f}",
                    f"{row.runner_max_read:.3f}",
                    row.status,
                    row.reason,
                ]
            )
        )
    _write_reports(args.output_dir, tuple(rows), run_id=run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
