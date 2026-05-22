"""source_lab 正式单配置诊断 CLI。

本工具读取 ``field_servers.tsv`` 与 ``signal_profile_items.tsv``，执行一组正式
field profile 诊断，并将 polling 或 subscribe 诊断报告直接输出到 stdout，
方便在 pytest ``-s`` 或手工 CLI 执行时即时观察当前开发环境表现。

完整执行示例：

    python -m tools.source_lab.field_profile \
      --access-mode polling \
      --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
      --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
      --protocol opcua \
      --process-count 1 \
      --server-count 50 \
      --hz 20 \
      --duration 10 \
      --warmup 2 \
      --runner-trace true \
      --runner-trace-top-n 5 \
      --output-dir tools/source_lab/tests/tmp/polling_profile

    python -m tools.source_lab.field_profile \
      --access-mode subscribe \
      --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
      --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
      --protocol opcua \
      --process-count 1 \
      --server-count 50 \
      --sample-hz 50 \
      --source-update-hz 50 \
      --duration 20 \
      --warmup 3 \
      --runner-trace true \
      --runner-trace-top-n 5 \
      --queue-size 1 \
      --output-dir tools/source_lab/tests/tmp/subscribe_profile
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from tools.source_lab.access.common.utils import normalize_protocol
from tools.source_lab.access.polling.profile import PollingProfileResult
from tools.source_lab.access.polling.reporter import print_capacity_report
from tools.source_lab.access.profile import FieldProfileRequest, print_profile_summary, run_field_profile_from_files
from tools.source_lab.access.subscribe.profile import SubscribeProfileResult
from tools.source_lab.access.subscribe.reporter import print_subscribe_report


def _resolve_run_id(run_id: str | None) -> str:
    """Resolve the CLI run identifier.

    Args:
        run_id: Optional user-provided run id.

    Returns:
        Explicit run id or a UTC timestamp id.
    """

    return run_id or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _parse_bool(value: str) -> bool:
    """Parse flexible CLI boolean text into a Python bool.

    Args:
        value: Raw CLI text value.

    Returns:
        Parsed boolean flag.
    """

    return value.strip().lower() not in {"0", "false", "no", "off"}


def _print_profile_report(result: PollingProfileResult | SubscribeProfileResult) -> None:
    """Print the human-readable profile diagnostics report to stdout.

    Args:
        result: Profile execution result to render.
    """

    if isinstance(result, PollingProfileResult):
        print_capacity_report(result.result)
        return
    print_subscribe_report(result.result)


def _build_parser() -> argparse.ArgumentParser:
    """Build the ``field_profile`` CLI parser.

    Returns:
        Configured argument parser for the profile CLI.
    """

    parser = argparse.ArgumentParser(description="Run single-configuration field profiling.")
    parser.add_argument("--access-mode", choices=("polling", "subscribe"), required=True)
    parser.add_argument("--servers", type=Path, required=True)
    parser.add_argument("--profile-items", type=Path, required=True)
    parser.add_argument("--protocol", default="opcua")
    parser.add_argument("--process-count", type=int, required=True)
    parser.add_argument("--server-count", type=int, required=True)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--output-dir", type=Path, required=False)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--runner-trace", default="true")
    parser.add_argument("--runner-trace-top-n", type=int, default=5)
    parser.add_argument("--pyinstrument", action="store_true")
    parser.add_argument("--profile-max-lines", type=int, default=80)
    parser.add_argument("--warmup", type=float, default=10.0)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--source-update-enabled", default="true")
    parser.add_argument("--source-update-hz", type=float, default=None)
    parser.add_argument("--hz", type=float, default=None)
    parser.add_argument("--sample-hz", type=float, default=None)
    parser.add_argument("--publishing-interval-ms", type=float, default=None)
    parser.add_argument("--sampling-interval-ms", type=float, default=None)
    parser.add_argument("--queue-size", type=int, default=1)
    parser.add_argument("--startup-stagger-ms", type=int, default=0)
    parser.add_argument("--monitored-item-batch-size", type=int, default=100)
    parser.add_argument("--monitored-item-batch-gap-ms", type=int, default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the ``field_profile`` CLI.

    Args:
        argv: Optional argument vector override.

    Returns:
        Process exit code.
    """

    args = _build_parser().parse_args(argv)
    protocol = normalize_protocol(args.protocol)
    runner_trace_enabled = _parse_bool(str(args.runner_trace))
    source_update_enabled = _parse_bool(str(args.source_update_enabled))

    request = FieldProfileRequest(
        access_mode=args.access_mode,
        protocol=protocol,
        process_count=args.process_count,
        server_count=args.server_count,
        output_dir=args.output_dir,
        run_id=_resolve_run_id(args.run_id),
        duration_s=args.duration,
        warmup_s=args.warmup,
        timeout_s=args.timeout,
        source_update_enabled=source_update_enabled,
        source_update_hz=args.source_update_hz,
        runner_trace_enabled=runner_trace_enabled,
        runner_trace_top_n=args.runner_trace_top_n,
        pyinstrument=args.pyinstrument,
        profile_max_lines=args.profile_max_lines,
        hz=args.hz,
        sample_hz=args.sample_hz,
        publishing_interval_ms=args.publishing_interval_ms,
        sampling_interval_ms=args.sampling_interval_ms,
        queue_size=args.queue_size,
        startup_stagger_ms=args.startup_stagger_ms,
        monitored_item_batch_size=args.monitored_item_batch_size,
        monitored_item_batch_gap_ms=args.monitored_item_batch_gap_ms,
    )
    result = run_field_profile_from_files(
        request,
        servers_path=args.servers,
        profile_items_path=args.profile_items,
    )
    # 先输出完整诊断报告，保持顶层 profile/load 测试的可观察性。
    _print_profile_report(result.raw_result)
    print_profile_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
