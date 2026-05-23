"""source_lab 正式现场探针 CLI。

本工具读取 ``field_servers.tsv`` 与 ``signal_profile_items.tsv``，执行现场连通性、
单次读取可达性与延迟采样探测。输出为以 endpoint 为单位的 TSV 报表，便于快速判断
哪些服务器可连、可读以及响应延迟区间。

完整执行示例：

    python -m tools.source_lab.field_probe \
      --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
      --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
      --protocol opcua \
      --samples 5 \
      --timeout 5 \
      --tcp-timeout 3 \
      --concurrency 16
"""

from __future__ import annotations

import argparse
from pathlib import Path

from tools.source_lab.access.common.io import build_field_runtime_sources
from tools.source_lab.access.polling.model import ProbeConfig
from tools.source_lab.access.probe import run_probe


def _build_parser() -> argparse.ArgumentParser:
    """Build the ``field_probe`` CLI parser.

    Returns:
        Configured argument parser for the probe CLI.
    """

    parser = argparse.ArgumentParser(
        description="Probe field servers from field_servers.tsv and signal_profile_items.tsv.",
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
        help="Protocol filter to execute. Unsupported protocols are reported as SKIP.",
    )
    parser.add_argument(
        "--service-type",
        default=None,
        help="Service type for the protocol (e.g. GOOSE, SV, MMS_READ, REPORT). "
             "If omitted, derived from --protocol alone.",
    )
    parser.add_argument("--samples", type=int, default=10, help="Latency sample count per endpoint.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Protocol read timeout in seconds.")
    parser.add_argument(
        "--tcp-timeout",
        type=float,
        default=3.0,
        help="TCP connect timeout in seconds.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=16,
        help="Maximum concurrent field probes.",
    )
    return parser


def _format_metric(value: float | None) -> str:
    """Format numeric output for TSV printing.

    Args:
        value: Numeric metric to render.

    Returns:
        Empty string for ``None`` or a fixed three-decimal string.
    """

    if value is None:
        return ""
    return f"{value:.3f}"


def main(argv: list[str] | None = None) -> int:
    """Run the ``field_probe`` CLI.

    Args:
        argv: Optional argument vector override.

    Returns:
        Process exit code.
    """

    args = _build_parser().parse_args(argv)
    sources = build_field_runtime_sources(args.servers, args.profile_items)
    result = run_probe(
        ProbeConfig(
            protocol=args.protocol,
            service_type=args.service_type,
            timeout_s=args.timeout,
            samples=args.samples,
            concurrency=args.concurrency,
            tcp_timeout_s=args.tcp_timeout,
        ),
        sources,
    )
    print(
        "\t".join(
            [
                "endpoint_id",
                "profile_id",
                "protocol",
                "host",
                "port",
                "point_count",
                "tcp_status",
                "protocol_status",
                "readable_count",
                "expected_count",
                "latency_min_ms",
                "latency_mean_ms",
                "latency_p95_ms",
                "latency_p99_ms",
                "latency_max_ms",
                "missing_ts",
                "status",
                "reason",
            ]
        )
    )
    for row in result.rows:
        latency = row.latency
        print(
            "\t".join(
                [
                    row.endpoint_id,
                    row.profile_id,
                    row.protocol,
                    row.host,
                    str(row.port),
                    str(row.point_count),
                    row.tcp_status,
                    row.protocol_status,
                    str(row.readable_count),
                    str(row.expected_count),
                    _format_metric(latency.min_ms if latency is not None else None),
                    _format_metric(latency.mean_ms if latency is not None else None),
                    _format_metric(latency.p95_ms if latency is not None else None),
                    _format_metric(latency.p99_ms if latency is not None else None),
                    _format_metric(latency.max_ms if latency is not None else None),
                    "true" if row.missing_ts else "false",
                    row.status.value,
                    row.reason,
                ]
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
