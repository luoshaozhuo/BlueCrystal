"""source_lab 正式容量探查 CLI。

本工具读取 ``field_servers.tsv`` 与 ``signal_profile_items.tsv``，并通过正式
capacity 服务链路执行现场容量扫描。polling 模式输出统一的容量表格：
``proc srv hz period_ms value_ratio p95_ms max_ms status reason``；subscribe
模式输出统一的订阅容量表格：
``proc srv sub_hz src_hz sub_ms src_ms value_ratio p95_ms max_ms status reason``。

完整执行示例：

    python -m tools.source_lab.field_capacity \
      --access-mode polling \
      --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
      --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
      --protocol opcua \
      --process-count-start 1 \
      --process-count-step 1 \
      --process-count-max 1 \
      --server-count-start 10 \
      --server-count-step 20 \
      --server-count-max 30 \
      --hz-start 10 \
      --hz-step 20 \
      --hz-max 30 \
      --duration 6 \
      --warmup 1 \
      --source-update-enabled true \
      --output-dir tools/source_lab/tests/tmp/polling_capacity

    python -m tools.source_lab.field_capacity \
      --access-mode subscribe \
      --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
      --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
      --protocol opcua \
      --process-count-start 1 \
      --process-count-step 1 \
      --process-count-max 1 \
      --server-count-start 10 \
      --server-count-step 10 \
      --server-count-max 20 \
      --sample-hz-start 20 \
      --sample-hz-step 20 \
      --sample-hz-max 40 \
      --source-update-hz-start 10 \
      --source-update-hz-step 20 \
      --source-update-hz-max 30 \
      --duration 6 \
      --warmup 1 \
      --source-update-enabled true \
      --queue-size 1 \
      --output-dir tools/source_lab/tests/tmp/subscribe_capacity
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from tools.source_lab.access.capacity import (
    FieldCapacityRequest,
    print_capacity_summary,
    run_field_capacity_from_files,
)
from tools.source_lab.access.common.scheduling import parse_float_list_or_ramp, parse_int_list_or_ramp
from tools.source_lab.access.common.utils import normalize_protocol


def _parse_bool(value: str) -> bool:
    """Parse flexible CLI boolean text into a Python bool.

    Args:
        value: Raw CLI text value.

    Returns:
        Parsed boolean flag.
    """

    return value.strip().lower() not in {"0", "false", "no", "off"}


def _resolve_run_id(run_id: str | None) -> str:
    """Resolve the CLI run identifier.

    Args:
        run_id: Optional user-provided run id.

    Returns:
        Explicit run id or a UTC timestamp id.
    """

    return run_id or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _parse_source_update_hz_values(args: argparse.Namespace) -> tuple[float, ...] | None:
    """Parse subscribe source-update-hz inputs from list or ramp flags.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Explicit source-update-hz scan dimension when provided, otherwise ``None``.

    Raises:
        ValueError: If both the single-value and ramp/list forms are provided.
    """

    ramp_or_list_requested = any(
        value is not None
        for value in (
            args.source_update_hz_values,
            args.source_update_hz_start,
            args.source_update_hz_step,
            args.source_update_hz_max,
        )
    )
    if args.source_update_hz is not None and ramp_or_list_requested:
        raise ValueError(
            "use either --source-update-hz or --source-update-hz-start/--source-update-hz-step/--source-update-hz-max"
        )
    if not ramp_or_list_requested:
        return None
    return parse_float_list_or_ramp(
        args.source_update_hz_values,
        start=args.source_update_hz_start,
        step=args.source_update_hz_step,
        maximum=args.source_update_hz_max,
        default=(),
        value_name="source_update_hz",
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build the ``field_capacity`` CLI parser.

    Returns:
        Configured argument parser for the capacity CLI.
    """

    parser = argparse.ArgumentParser(description="Run field capacity scans from field export files.")
    parser.add_argument("--access-mode", choices=("polling", "subscribe"), required=True)
    parser.add_argument("--servers", type=Path, required=True)
    parser.add_argument("--profile-items", type=Path, required=True)
    parser.add_argument("--protocol", default="opcua")
    parser.add_argument(
        "--service-type",
        default=None,
        help="Service type for the protocol (e.g. GOOSE, SV, MMS_READ, REPORT). "
             "If omitted, derived from --protocol alone.",
    )
    parser.add_argument("--process-counts", default=None)
    parser.add_argument("--process-count-start", type=int, default=None)
    parser.add_argument("--process-count-step", type=int, default=None)
    parser.add_argument("--process-count-max", type=int, default=None)
    parser.add_argument("--server-counts", default=None)
    parser.add_argument("--server-count-start", type=int, default=None)
    parser.add_argument("--server-count-step", type=int, default=None)
    parser.add_argument("--server-count-max", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--warmup", type=float, default=10.0)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--source-update-enabled", default="true")
    parser.add_argument("--source-update-hz", type=float, default=None)
    parser.add_argument("--source-update-hz-values", default=None)
    parser.add_argument("--source-update-hz-start", type=float, default=None)
    parser.add_argument("--source-update-hz-step", type=float, default=None)
    parser.add_argument("--source-update-hz-max", type=float, default=None)
    parser.add_argument("--hz", default=None)
    parser.add_argument("--hz-start", type=float, default=None)
    parser.add_argument("--hz-step", type=float, default=None)
    parser.add_argument("--hz-max", type=float, default=None)
    parser.add_argument("--sample-hz", default=None)
    parser.add_argument("--sample-hz-start", type=float, default=None)
    parser.add_argument("--sample-hz-step", type=float, default=None)
    parser.add_argument("--sample-hz-max", type=float, default=None)
    parser.add_argument("--publishing-interval-ms", type=float, default=None)
    parser.add_argument("--sampling-interval-ms", type=float, default=None)
    parser.add_argument("--queue-size", default="1")
    parser.add_argument("--startup-stagger-ms", type=int, default=0)
    parser.add_argument("--monitored-item-batch-size", type=int, default=100)
    parser.add_argument("--monitored-item-batch-gap-ms", type=int, default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the ``field_capacity`` CLI.

    Args:
        argv: Optional argument vector override.

    Returns:
        Process exit code.
    """

    args = _build_parser().parse_args(argv)
    requested_protocol = normalize_protocol(args.protocol)
    source_update_enabled = _parse_bool(str(args.source_update_enabled))
    process_counts = parse_int_list_or_ramp(
        args.process_counts,
        start=args.process_count_start,
        step=args.process_count_step,
        maximum=args.process_count_max,
        default=(1,),
        value_name="process_count",
    )
    server_counts = parse_int_list_or_ramp(
        args.server_counts,
        start=args.server_count_start,
        step=args.server_count_step,
        maximum=args.server_count_max,
        default=(1,),
        value_name="server_count",
    )

    if args.access_mode == "polling":
        hz_values = parse_float_list_or_ramp(
            args.hz,
            start=args.hz_start,
            step=args.hz_step,
            maximum=args.hz_max,
            default=(10.0,),
            value_name="hz",
        )
        request = FieldCapacityRequest(
            access_mode="polling",
            protocol=requested_protocol,
            service_type=args.service_type,
            process_counts=process_counts,
            server_counts=server_counts,
            hz_values=hz_values,
            output_dir=args.output_dir,
            run_id=_resolve_run_id(args.run_id),
            duration_s=args.duration,
            warmup_s=args.warmup,
            timeout_s=args.timeout,
            source_update_enabled=source_update_enabled,
            source_update_hz=args.source_update_hz,
        )
    else:
        if args.sampling_interval_ms is not None:
            raise ValueError(
                "field_capacity subscribe derives sampling_interval_ms from sample_hz; "
                "use --sample-hz instead"
            )
        source_update_hz_values = _parse_source_update_hz_values(args)
        sample_hz_values = parse_float_list_or_ramp(
            args.sample_hz,
            start=args.sample_hz_start,
            step=args.sample_hz_step,
            maximum=args.sample_hz_max,
            default=(10.0,),
            value_name="sample_hz",
        )
        queue_sizes = parse_int_list_or_ramp(
            args.queue_size,
            start=None,
            step=None,
            maximum=None,
            default=(1,),
            value_name="queue_size",
        )
        request = FieldCapacityRequest(
            access_mode="subscribe",
            protocol=requested_protocol,
            service_type=args.service_type,
            process_counts=process_counts,
            server_counts=server_counts,
            sample_hz_values=sample_hz_values,
            publishing_interval_ms=args.publishing_interval_ms,
            queue_sizes=queue_sizes,
            output_dir=args.output_dir,
            run_id=_resolve_run_id(args.run_id),
            duration_s=args.duration,
            warmup_s=args.warmup,
            timeout_s=args.timeout,
            source_update_enabled=source_update_enabled,
            source_update_hz=args.source_update_hz,
            source_update_hz_values=source_update_hz_values or (),
            startup_stagger_ms=args.startup_stagger_ms,
            monitored_item_batch_size=args.monitored_item_batch_size,
            monitored_item_batch_gap_ms=args.monitored_item_batch_gap_ms,
        )

    result = run_field_capacity_from_files(
        request,
        servers_path=args.servers,
        profile_items_path=args.profile_items,
    )
    print_capacity_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
