"""Standalone field endpoint probing that is independent from capacity orchestration."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import math
import socket

from tools.source_lab.access.common.io import FieldEndpointMetadata
from tools.source_lab.access.polling.model import (
    CapacityMode,
    CapacityScanConfig,
    CapacityStatus,
    ProbeConfig,
    ProbeLatencyStats,
    ProbeResult,
    ServerProbeResult,
)
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.open62541_serial_polling import run_serial_polling_probe
from tools.source_lab.access.common.utils import normalize_protocol


@dataclass(frozen=True, slots=True)
class ProbeWarning:
    """Non-fatal warning emitted during probe execution."""

    endpoint_id: str
    reason: str


def _skip_result(
    source: SourceRuntimeSpec,
    *,
    reason: str,
) -> ServerProbeResult:
    """Build one skipped probe result row for a source.

    Args:
        source: Runtime source being skipped.
        reason: Stable skip reason string.

    Returns:
        A normalized skipped probe result.
    """

    metadata = _metadata_from_source(source)
    protocol = normalize_protocol(metadata.protocol or source.endpoint.protocol)
    expected_count = len(source.points)
    return ServerProbeResult(
        endpoint_id=metadata.endpoint_id,
        profile_id=metadata.profile_id,
        protocol=protocol,
        host=source.endpoint.host,
        port=source.endpoint.port,
        point_count=expected_count,
        tcp_status="SKIP",
        protocol_status="SKIP",
        readable_count=0,
        expected_count=expected_count,
        latency=None,
        missing_ts=False,
        status=CapacityStatus.SKIP,
        reason=reason,
    )


def _probe_capacity_config(protocol: str, config: ProbeConfig) -> CapacityScanConfig:
    """Build a minimal access config for native probe calls."""

    return CapacityScanConfig(
        mode=CapacityMode.FIELD,
        protocol=protocol,
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        hz_start=1.0,
        hz_step=1.0,
        hz_max=1.0,
        process_count=1,
        warmup_s=0.0,
        level_duration_s=max(1.0, float(config.samples)),
        read_timeout_s=config.timeout_s,
        progress_enabled=False,
    )


def _metadata_from_source(source: SourceRuntimeSpec) -> FieldEndpointMetadata:
    """Extract stable field metadata from one runtime source."""

    if isinstance(source.runtime_handle, FieldEndpointMetadata):
        return source.runtime_handle
    return FieldEndpointMetadata(
        endpoint_id=source.endpoint.name,
        profile_id=str(source.endpoint.params.get("profile_id", "")),
        protocol=normalize_protocol(source.endpoint.protocol),
    )


def _tcp_reachable(host: str, port: int, timeout_s: float) -> bool:
    """Return whether one TCP endpoint accepts a connection."""

    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def _percentile(values: list[float], percentile: float) -> float:
    """Compute a simple inclusive percentile on a non-empty value list."""

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = percentile * (len(ordered) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _build_latency(latencies_ms: list[float]) -> ProbeLatencyStats | None:
    """Build latency summary stats from successful probe samples."""

    if not latencies_ms:
        return None
    return ProbeLatencyStats(
        min_ms=min(latencies_ms),
        mean_ms=sum(latencies_ms) / len(latencies_ms),
        p95_ms=_percentile(latencies_ms, 0.95),
        p99_ms=_percentile(latencies_ms, 0.99),
        max_ms=max(latencies_ms),
    )


def _probe_one_source(source: SourceRuntimeSpec, config: ProbeConfig) -> ServerProbeResult:
    """Probe one source and return a normalized per-server result.

    Args:
        source: Runtime source to probe.
        config: Requested probe configuration.

    Returns:
        One normalized probe row.
    """

    metadata = _metadata_from_source(source)
    protocol = normalize_protocol(metadata.protocol or source.endpoint.protocol)
    requested_protocol = normalize_protocol(config.protocol)
    expected_count = len(source.points)

    if protocol != requested_protocol:
        return _skip_result(source, reason="protocol_filtered")
    if requested_protocol != "opcua":
        return _skip_result(source, reason="unsupported_protocol")

    if not _tcp_reachable(source.endpoint.host, source.endpoint.port, config.tcp_timeout_s):
        return ServerProbeResult(
            endpoint_id=metadata.endpoint_id,
            profile_id=metadata.profile_id,
            protocol=protocol,
            host=source.endpoint.host,
            port=source.endpoint.port,
            point_count=expected_count,
            tcp_status="FAIL",
            protocol_status="SKIP",
            readable_count=0,
            expected_count=expected_count,
            latency=None,
            missing_ts=False,
            status=CapacityStatus.FAIL,
            reason="tcp_unreachable",
        )

    try:
        ticks = run_serial_polling_probe(
            source,
            config=_probe_capacity_config(protocol, config),
            samples=config.samples,
        )
    except Exception as exc:
        return ServerProbeResult(
            endpoint_id=metadata.endpoint_id,
            profile_id=metadata.profile_id,
            protocol=protocol,
            host=source.endpoint.host,
            port=source.endpoint.port,
            point_count=expected_count,
            tcp_status="PASS",
            protocol_status="FAIL",
            readable_count=0,
            expected_count=expected_count,
            latency=None,
            missing_ts=False,
            status=CapacityStatus.FAIL,
            reason=f"runner_exception:{type(exc).__name__}",
        )

    if not ticks:
        return ServerProbeResult(
            endpoint_id=metadata.endpoint_id,
            profile_id=metadata.profile_id,
            protocol=protocol,
            host=source.endpoint.host,
            port=source.endpoint.port,
            point_count=expected_count,
            tcp_status="PASS",
            protocol_status="FAIL",
            readable_count=0,
            expected_count=expected_count,
            latency=None,
            missing_ts=False,
            status=CapacityStatus.FAIL,
            reason="no_result",
        )

    readable_count = max((tick.value_count for tick in ticks if tick.ok), default=0)
    missing_ts = any(tick.response_timestamp_s is None for tick in ticks)
    value_count_ok = all(tick.value_count == expected_count for tick in ticks if tick.ok)
    latencies_ms = [tick.elapsed_ms for tick in ticks if tick.ok]
    latency = _build_latency(latencies_ms)

    if any(not tick.ok and tick.error == "missing_response_timestamp" for tick in ticks) or missing_ts:
        return ServerProbeResult(
            endpoint_id=metadata.endpoint_id,
            profile_id=metadata.profile_id,
            protocol=protocol,
            host=source.endpoint.host,
            port=source.endpoint.port,
            point_count=expected_count,
            tcp_status="PASS",
            protocol_status="FAIL",
            readable_count=readable_count,
            expected_count=expected_count,
            latency=latency,
            missing_ts=True,
            status=CapacityStatus.FAIL,
            reason="missing_response_timestamp",
        )

    if not value_count_ok:
        return ServerProbeResult(
            endpoint_id=metadata.endpoint_id,
            profile_id=metadata.profile_id,
            protocol=protocol,
            host=source.endpoint.host,
            port=source.endpoint.port,
            point_count=expected_count,
            tcp_status="PASS",
            protocol_status="FAIL",
            readable_count=readable_count,
            expected_count=expected_count,
            latency=latency,
            missing_ts=False,
            status=CapacityStatus.FAIL,
            reason="value_count_mismatch",
        )

    if any(not tick.ok for tick in ticks):
        first_error = next(tick.error for tick in ticks if not tick.ok)
        return ServerProbeResult(
            endpoint_id=metadata.endpoint_id,
            profile_id=metadata.profile_id,
            protocol=protocol,
            host=source.endpoint.host,
            port=source.endpoint.port,
            point_count=expected_count,
            tcp_status="PASS",
            protocol_status="FAIL",
            readable_count=readable_count,
            expected_count=expected_count,
            latency=latency,
            missing_ts=False,
            status=CapacityStatus.FAIL,
            reason=first_error or "probe_failed",
        )

    return ServerProbeResult(
        endpoint_id=metadata.endpoint_id,
        profile_id=metadata.profile_id,
        protocol=protocol,
        host=source.endpoint.host,
        port=source.endpoint.port,
        point_count=expected_count,
        tcp_status="PASS",
        protocol_status="PASS",
        readable_count=readable_count,
        expected_count=expected_count,
        latency=latency,
        missing_ts=False,
        status=CapacityStatus.PASS,
        reason="",
    )


def run_probe(config: ProbeConfig, sources: tuple[SourceRuntimeSpec, ...]) -> ProbeResult:
    """Run standalone field probes for all provided sources.

    Args:
        config: Probe configuration.
        sources: Validated runtime sources.

    Returns:
        Aggregate probe result ordered like the input sources.
    """

    if not sources:
        return ProbeResult(config=config, rows=())

    max_workers = max(1, min(config.concurrency, len(sources)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        rows = tuple(executor.map(lambda source: _probe_one_source(source, config), sources))
    return ProbeResult(config=config, rows=rows)
