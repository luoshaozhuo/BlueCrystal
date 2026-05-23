"""Standalone field endpoint probing that is independent from capacity orchestration."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import math
import socket
import struct
import time
from urllib.request import urlopen

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
from tools.source_lab.access.runners.registry import (
    normalize_protocol as normalize_protocol_registry,
    probe_mode_for_protocol,
)
from tools.source_lab.access.runners.open62541_serial_polling import run_serial_polling_probe
from tools.source_lab.access.common.utils import normalize_protocol as normalize_protocol_loose


@dataclass(frozen=True, slots=True)
class ProbeWarning:
    """Non-fatal warning emitted during probe execution."""

    endpoint_id: str
    reason: str


def _canonical_protocol_name(value: str) -> str:
    """Return canonical protocol name and tolerate unknown protocols."""

    try:
        return normalize_protocol_registry(value)
    except ValueError:
        return normalize_protocol_loose(value)


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
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
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
        protocol=normalize_protocol_loose(source.endpoint.protocol),
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
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
    requested_protocol = _canonical_protocol_name(config.protocol)
    expected_count = len(source.points)

    if protocol != requested_protocol:
        return _skip_result(source, reason="protocol_filtered")

    try:
        probe_mode = probe_mode_for_protocol(requested_protocol)
    except ValueError:
        probe_mode = None
    if probe_mode is None:
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

    if probe_mode == "streaming":
        return _streaming_probe_success(source, config=config)

    if requested_protocol != "opcua":
        return _polling_tcp_probe(source, config=config)

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


def _polling_tcp_probe(source: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
    """对非 OPC UA polling 协议执行协议级 probe。"""

    metadata = _metadata_from_source(source)
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
    expected_count = len(source.points)

    if protocol == "modbus_tcp":
        return _probe_modbus_tcp(source, config=config)
    if protocol == "modbus_rtu":
        return _probe_modbus_rtu_gateway(source, config=config)
    if protocol == "iec104":
        return _probe_iec104(source, config=config)
    if protocol == "iec101":
        return _probe_iec101_gateway(source, config=config)
    if protocol == "http_rest":
        return _probe_http_rest(source, config=config)
    if protocol == "iec61850_mms":
        return _probe_iec61850_mms(source, config=config)

    # 兜底保留短窗口 TCP 探测，避免未来协议新增时直接不可用。
    latencies_ms: list[float] = []
    for _ in range(max(1, config.samples)):
        started = time.perf_counter_ns()
        if not _tcp_reachable(source.endpoint.host, source.endpoint.port, config.tcp_timeout_s):
            return ServerProbeResult(
                endpoint_id=metadata.endpoint_id,
                profile_id=metadata.profile_id,
                protocol=protocol,
                host=source.endpoint.host,
                port=source.endpoint.port,
                point_count=expected_count,
                tcp_status="FAIL",
                protocol_status="FAIL",
                readable_count=0,
                expected_count=expected_count,
                latency=None,
                missing_ts=False,
                status=CapacityStatus.FAIL,
                reason="probe_connection_failed",
            )
        latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000.0)

    return ServerProbeResult(
        endpoint_id=metadata.endpoint_id,
        profile_id=metadata.profile_id,
        protocol=protocol,
        host=source.endpoint.host,
        port=source.endpoint.port,
        point_count=expected_count,
        tcp_status="PASS",
        protocol_status="PASS",
        readable_count=expected_count,
        expected_count=expected_count,
        latency=_build_latency(latencies_ms),
        missing_ts=False,
        status=CapacityStatus.PASS,
        reason="",
    )


def _streaming_probe_success(source: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
    """对 streaming 协议执行协议级订阅可达性 probe。"""

    metadata = _metadata_from_source(source)
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)

    if protocol == "mqtt":
        return _probe_mqtt_streaming(source, config=config)
    if protocol == "iec61850_report":
        return _probe_iec61850_report(source, config=config)

    # 对未细化 streaming 协议保留 TCP 级可达性判定。
    return _streaming_tcp_fallback(source, config=config)


def _streaming_tcp_fallback(source: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
    """streaming 协议的 TCP 回退探测。"""

    metadata = _metadata_from_source(source)
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
    expected_count = len(source.points)
    started = time.perf_counter_ns()
    with socket.create_connection((source.endpoint.host, source.endpoint.port), timeout=config.tcp_timeout_s):
        pass
    latency = _build_latency([(time.perf_counter_ns() - started) / 1_000_000.0])
    return ServerProbeResult(
        endpoint_id=metadata.endpoint_id,
        profile_id=metadata.profile_id,
        protocol=protocol,
        host=source.endpoint.host,
        port=source.endpoint.port,
        point_count=expected_count,
        tcp_status="PASS",
        protocol_status="PASS",
        readable_count=max(1, expected_count),
        expected_count=expected_count,
        latency=latency,
        missing_ts=False,
        status=CapacityStatus.PASS,
        reason="",
    )


def _probe_modbus_tcp(source: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
    """Modbus TCP 功能码 0x03 探测。"""

    metadata = _metadata_from_source(source)
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
    expected_count = max(1, len(source.points))
    latencies_ms: list[float] = []
    for _ in range(max(1, config.samples)):
        started = time.perf_counter_ns()
        tx_id = int(time.time_ns() & 0xFFFF)
        request = struct.pack(">HHHBBHH", tx_id, 0, 6, 1, 3, 0, expected_count)
        try:
            with socket.create_connection((source.endpoint.host, source.endpoint.port), timeout=config.timeout_s) as conn:
                conn.sendall(request)
                conn.settimeout(config.timeout_s)
                header = conn.recv(7)
                if len(header) < 7:
                    return _probe_protocol_fail(source, protocol=protocol, reason="short_header")
                pdu = conn.recv(2 + expected_count * 2)
                if len(pdu) < 2:
                    return _probe_protocol_fail(source, protocol=protocol, reason="short_pdu")
                if pdu[0] & 0x80:
                    return _probe_protocol_fail(source, protocol=protocol, reason="modbus_exception")
        except OSError:
            return _probe_protocol_fail(source, protocol=protocol, reason="probe_connection_failed")
        latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return _probe_protocol_pass(source, protocol=protocol, latency=_build_latency(latencies_ms))


def _probe_modbus_rtu_gateway(source: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
    """Modbus RTU gateway-style 功能码 0x03 探测。"""

    metadata = _metadata_from_source(source)
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
    expected_count = max(1, len(source.points))
    latencies_ms: list[float] = []
    for _ in range(max(1, config.samples)):
        started = time.perf_counter_ns()
        frame = bytes([1, 3, 0, 0, 0, expected_count, 0, 0])
        try:
            with socket.create_connection((source.endpoint.host, source.endpoint.port), timeout=config.timeout_s) as conn:
                conn.sendall(frame)
                conn.settimeout(config.timeout_s)
                response = conn.recv(5 + expected_count * 2)
                if len(response) < 5:
                    return _probe_protocol_fail(source, protocol=protocol, reason="short_frame")
                if response[1] & 0x80:
                    return _probe_protocol_fail(source, protocol=protocol, reason="modbus_exception")
        except OSError:
            return _probe_protocol_fail(source, protocol=protocol, reason="probe_connection_failed")
        latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return _probe_protocol_pass(source, protocol=protocol, latency=_build_latency(latencies_ms))


def _probe_iec104(source: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
    """IEC104 TESTFR_ACT -> TESTFR_CON 探测。"""

    metadata = _metadata_from_source(source)
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
    latencies_ms: list[float] = []
    for _ in range(max(1, config.samples)):
        started = time.perf_counter_ns()
        try:
            with socket.create_connection((source.endpoint.host, source.endpoint.port), timeout=config.timeout_s) as conn:
                conn.sendall(b"\x68\x04\x43\x00\x00\x00")
                conn.settimeout(config.timeout_s)
                response = conn.recv(16)
                if not response.startswith(b"\x68\x04\x83\x00\x00\x00"):
                    return _probe_protocol_fail(source, protocol=protocol, reason="unexpected_ack")
        except OSError:
            return _probe_protocol_fail(source, protocol=protocol, reason="probe_connection_failed")
        latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return _probe_protocol_pass(source, protocol=protocol, latency=_build_latency(latencies_ms))


def _probe_iec101_gateway(source: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
    """IEC101 gateway-style 链路确认探测。"""

    metadata = _metadata_from_source(source)
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
    latencies_ms: list[float] = []
    for _ in range(max(1, config.samples)):
        started = time.perf_counter_ns()
        try:
            with socket.create_connection((source.endpoint.host, source.endpoint.port), timeout=config.timeout_s) as conn:
                conn.sendall(b"\x10\x49\x00\x49\x16")
                conn.settimeout(config.timeout_s)
                response = conn.recv(32)
                if len(response) < 4:
                    return _probe_protocol_fail(source, protocol=protocol, reason="short_frame")
        except OSError:
            return _probe_protocol_fail(source, protocol=protocol, reason="probe_connection_failed")
        latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return _probe_protocol_pass(source, protocol=protocol, latency=_build_latency(latencies_ms))


def _probe_http_rest(source: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
    """HTTP REST /points 读取探测。"""

    metadata = _metadata_from_source(source)
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
    path = str(source.endpoint.params.get("base_path", "/points"))
    latencies_ms: list[float] = []
    for _ in range(max(1, config.samples)):
        started = time.perf_counter_ns()
        try:
            with urlopen(
                f"http://{source.endpoint.host}:{source.endpoint.port}{path}",
                timeout=config.timeout_s,
            ) as response:
                if response.status != 200:
                    return _probe_protocol_fail(source, protocol=protocol, reason="http_status_not_ok")
                _ = response.read()
        except Exception:
            return _probe_protocol_fail(source, protocol=protocol, reason="probe_connection_failed")
        latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return _probe_protocol_pass(source, protocol=protocol, latency=_build_latency(latencies_ms))


def _probe_iec61850_mms(source: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
    """IEC61850 MMS 会话与响应语义探测。"""

    metadata = _metadata_from_source(source)
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
    latencies_ms: list[float] = []
    for _ in range(max(1, config.samples)):
        started = time.perf_counter_ns()
        try:
            with socket.create_connection((source.endpoint.host, source.endpoint.port), timeout=config.timeout_s) as conn:
                conn.settimeout(config.timeout_s)
                # 最小化探测 APDU（实验室语义探针，不做完整 MMS 协商）。
                conn.sendall(b"\x30\x00")
                response = conn.recv(16)
                if len(response) < 3 or response[0] != 0x30:
                    return _probe_protocol_fail(source, protocol=protocol, reason="iec61850_mms_invalid_response")
        except OSError:
            return _probe_protocol_fail(source, protocol=protocol, reason="probe_connection_failed")
        latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return _probe_protocol_pass(source, protocol=protocol, latency=_build_latency(latencies_ms))


def _probe_mqtt_streaming(source: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
    """MQTT CONNECT+SUBSCRIBE+PUBLISH 语义探测。"""

    metadata = _metadata_from_source(source)
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
    topic = str(source.endpoint.params.get("mqtt_topic", "source_lab/points"))
    latencies_ms: list[float] = []
    for _ in range(max(1, config.samples)):
        started = time.perf_counter_ns()
        client_id = b"probe-client"
        connect_payload = len(client_id).to_bytes(2, "big") + client_id
        connect_vh = b"\x00\x04MQTT\x04\x02\x00\x3c"
        connect_pkt = b"\x10" + bytes([len(connect_vh) + len(connect_payload)]) + connect_vh + connect_payload
        topic_bytes = topic.encode("utf-8")
        subscribe_payload = len(topic_bytes).to_bytes(2, "big") + topic_bytes + b"\x00"
        subscribe_vh = b"\x00\x01"
        subscribe_pkt = b"\x82" + bytes([len(subscribe_vh) + len(subscribe_payload)]) + subscribe_vh + subscribe_payload
        try:
            with socket.create_connection((source.endpoint.host, source.endpoint.port), timeout=config.timeout_s) as conn:
                conn.sendall(connect_pkt)
                conn.settimeout(config.timeout_s)
                connack = conn.recv(4)
                if len(connack) < 4 or connack[0] != 0x20 or connack[3] != 0x00:
                    return _probe_protocol_fail(source, protocol=protocol, reason="mqtt_connack_invalid")
                conn.sendall(subscribe_pkt)
                suback = conn.recv(8)
                if not suback or suback[0] != 0x90:
                    return _probe_protocol_fail(source, protocol=protocol, reason="mqtt_suback_invalid")
                publish = conn.recv(1024)
                if not _is_valid_mqtt_publish(publish, expected_topic=topic):
                    return _probe_protocol_fail(source, protocol=protocol, reason="mqtt_publish_invalid")
        except OSError:
            return _probe_protocol_fail(source, protocol=protocol, reason="probe_connection_failed")
        latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return _probe_protocol_pass(source, protocol=protocol, latency=_build_latency(latencies_ms), readable_count=1)


def _probe_iec61850_report(source: SourceRuntimeSpec, *, config: ProbeConfig) -> ServerProbeResult:
    """IEC61850 report 语义探测。"""

    metadata = _metadata_from_source(source)
    protocol = _canonical_protocol_name(metadata.protocol or source.endpoint.protocol)
    latencies_ms: list[float] = []
    for _ in range(max(1, config.samples)):
        started = time.perf_counter_ns()
        try:
            with socket.create_connection((source.endpoint.host, source.endpoint.port), timeout=config.timeout_s) as conn:
                conn.settimeout(config.timeout_s)
                # 最小 report/bind 语义探测（实验室级，不做完整 RCB 流程）。
                conn.sendall(b"\x30\x00")
                response = conn.recv(16)
                if len(response) < 3 or response[0] != 0x30:
                    return _probe_protocol_fail(source, protocol=protocol, reason="iec61850_report_invalid_response")
        except OSError:
            return _probe_protocol_fail(source, protocol=protocol, reason="probe_connection_failed")
        latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return _probe_protocol_pass(source, protocol=protocol, latency=_build_latency(latencies_ms), readable_count=1)


def _is_valid_mqtt_publish(packet: bytes, *, expected_topic: str) -> bool:
    """Validate one MQTT PUBLISH packet with topic match."""

    if len(packet) < 5:
        return False
    if (packet[0] >> 4) != 3:
        return False

    # 单字节 remaining length（当前实验室负载小于 127）。
    remaining = packet[1]
    if len(packet) < 2 + remaining:
        return False

    topic_length = int.from_bytes(packet[2:4], "big")
    topic_end = 4 + topic_length
    if topic_end > len(packet):
        return False
    topic = packet[4:topic_end].decode("utf-8", errors="ignore")
    if topic != expected_topic:
        return False
    payload = packet[topic_end : 2 + remaining]
    return len(payload) > 0


def _probe_protocol_pass(
    source: SourceRuntimeSpec,
    *,
    protocol: str,
    latency: ProbeLatencyStats | None,
    readable_count: int | None = None,
) -> ServerProbeResult:
    """构建协议探测成功行。"""

    metadata = _metadata_from_source(source)
    expected_count = len(source.points)
    return ServerProbeResult(
        endpoint_id=metadata.endpoint_id,
        profile_id=metadata.profile_id,
        protocol=protocol,
        host=source.endpoint.host,
        port=source.endpoint.port,
        point_count=expected_count,
        tcp_status="PASS",
        protocol_status="PASS",
        readable_count=max(1, expected_count) if readable_count is None else readable_count,
        expected_count=expected_count,
        latency=latency,
        missing_ts=False,
        status=CapacityStatus.PASS,
        reason="",
    )


def _probe_protocol_fail(
    source: SourceRuntimeSpec,
    *,
    protocol: str,
    reason: str,
) -> ServerProbeResult:
    """构建协议探测失败行。"""

    metadata = _metadata_from_source(source)
    expected_count = len(source.points)
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
        reason=reason,
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
