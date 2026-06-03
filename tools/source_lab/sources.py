"""source_lab 源定义与端口分配辅助函数。

本文件负责本地 simulator 所需的端口分配、多实例克隆和少量兼容 helper。
shared persistence 数据库读取已收敛到 provider 层，这里只保留向后兼容入口。
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from dataclasses import replace

from tools.source_lab.model import SimulatedSource, SourceConnection

_DEFAULT_PORT_START = 50000
_DEFAULT_PORT_END = 65000


def _env_int_inclusive(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _resolve_port_scan_range() -> tuple[int, int]:
    start = _env_int_inclusive("SOURCE_SIM_PORT_START", _DEFAULT_PORT_START)
    end = _env_int_inclusive("SOURCE_SIM_PORT_END", _DEFAULT_PORT_END)
    if start <= 0:
        start = _DEFAULT_PORT_START
    if end <= 0:
        end = _DEFAULT_PORT_END
    if start > end:
        start, end = _DEFAULT_PORT_START, _DEFAULT_PORT_END
    return start, end


def _resolve_bind_host(host: str) -> str:
    """把运行时 host 归一化为可 bind 的具体地址。"""

    normalized = host.strip() if host.strip() else "127.0.0.1"
    if normalized.lower() == "localhost":
        return "127.0.0.1"
    return normalized


def _is_tcp_port_available(host: str, port: int) -> bool:
    """判断给定 host/port 当前是否可绑定。"""

    bind_host = _resolve_bind_host(host)
    try:
        infos = socket.getaddrinfo(
            bind_host,
            port,
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
    except OSError:
        return False

    if not infos:
        return False

    for info in infos:
        family, sock_type, proto, _canonname, sockaddr = info
        try:
            with socket.socket(family, sock_type, proto) as sock:
                sock.bind(sockaddr)
                return True
        except OSError:
            continue

    return False


@dataclass(slots=True)
class PortAllocator:
    start: int
    end: int
    next_port: int
    used_ports: set[int]

    @classmethod
    def from_env(cls) -> "PortAllocator":
        """基于环境变量端口范围构造一次测试运行的分配器。"""

        start, end = _resolve_port_scan_range()
        return cls(start=start, end=end, next_port=start, used_ports=set())

    @classmethod
    def from_range(cls, *, start: int, end: int) -> "PortAllocator":
        """基于显式范围构造分配器，并处理非法边界回退。"""

        resolved_start = start if start > 0 else _DEFAULT_PORT_START
        resolved_end = end if end > 0 else _DEFAULT_PORT_END
        if resolved_start > resolved_end:
            resolved_start, resolved_end = _DEFAULT_PORT_START, _DEFAULT_PORT_END
        return cls(start=resolved_start, end=resolved_end, next_port=resolved_start, used_ports=set())

    def allocate_many(self, count: int, host: str = "127.0.0.1") -> tuple[int, ...]:
        """批量分配一组当前可绑定且互不冲突的 TCP 端口。"""

        if count <= 0:
            return ()

        bind_host = _resolve_bind_host(host)
        allocated: list[int] = []
        attempted = 0
        unavailable: list[int] = []

        if self.next_port < self.start or self.next_port > self.end:
            self.next_port = self.start

        capacity = self.end - self.start + 1
        candidate = self.next_port
        scanned = 0
        while scanned < capacity and len(allocated) < count:
            attempted += 1
            if candidate not in self.used_ports and _is_tcp_port_available(bind_host, candidate):
                self.used_ports.add(candidate)
                allocated.append(candidate)
            elif len(unavailable) < 12:
                unavailable.append(candidate)

            scanned += 1
            candidate += 1
            if candidate > self.end:
                candidate = self.start

        self.next_port = candidate
        if len(allocated) != count:
            raise RuntimeError(
                "Failed to allocate simulator ports: "
                f"requested_host={bind_host}, start={self.start}, end={self.end}, "
                f"needed={count}, attempted={attempted}, allocated={len(allocated)}, "
                f"next_port={self.next_port}, unavailable_sample={tuple(unavailable)}"
            )

        return tuple(allocated)


def choose_available_port(
    *,
    host: str = "127.0.0.1",
    minimum_port: int | None = None,
    maximum_port: int | None = None,
    used_ports: set[int] | None = None,
) -> int:
    """在给定范围内选择一个当前可绑定的 TCP 端口。"""
    resolved_start, resolved_end = _resolve_port_scan_range()
    minimum = resolved_start if minimum_port is None else minimum_port
    maximum = resolved_end if maximum_port is None else maximum_port
    if minimum > maximum:
        raise RuntimeError(
            "No available TCP ports found in the configured range: "
            f"start={minimum}, end={maximum}"
        )

    used = used_ports if used_ports is not None else set()
    for candidate in range(minimum, maximum + 1):
        if candidate in used:
            continue

        if _is_tcp_port_available(host, candidate):
            used.add(candidate)
            return candidate

    raise RuntimeError(
        "No available TCP ports found in the configured range: "
        f"requested_host={host}, start={minimum}, end={maximum}, "
        f"assigned_count={len(used)}"
    )


def assign_dynamic_port(source: SimulatedSource) -> SimulatedSource:
    """复制 source 并分配一个空闲高位端口。"""
    assigned_port = choose_available_port(host=source.connection.host)
    return replace(
        source,
        connection=replace(
            source.connection,
            port=assigned_port,
        ),
    )


def build_opcua_source_from_repository(
    *,
    min_expected_point_count: int,
    max_expected_point_count: int,
) -> SimulatedSource:
    """兼容旧 helper：从 shared persistence SCADA sample DB 读取一个 OPC UA 源。"""

    from tools.source_lab.access.providers.scada_profile import ScadaProfileProvider

    provider = ScadaProfileProvider()
    source = provider.load_source(protocol="opcua", access_mode="polling")
    point_count = len(source.points)

    if not min_expected_point_count <= point_count <= max_expected_point_count:
        raise AssertionError(
            f"Expected {min_expected_point_count}-{max_expected_point_count} "
            f"profile items per server, got {point_count}"
        )
    return source


def build_multi_sources(
    base_source: SimulatedSource,
    *,
    server_count: int,
    ports: tuple[int, ...] | list[int] | None = None,
) -> tuple[SimulatedSource, ...]:
    """把一个 base source 克隆为多个端口/命名空间不同的实例。"""
    sources: list[SimulatedSource] = []

    base_namespace = str(base_source.connection.namespace_uri or "urn:source-simulation")
    resolved_ports: tuple[int, ...]
    if ports is None:
        port_start, port_end = _resolve_port_scan_range()
        used_ports: set[int] = {base_source.connection.port}
        try:
            resolved_ports = tuple(
                choose_available_port(
                    host=base_source.connection.host,
                    minimum_port=port_start,
                    maximum_port=port_end,
                    used_ports=used_ports,
                )
                for _ in range(server_count)
            )
        except RuntimeError as exc:
            raise RuntimeError(
                "Failed to allocate simulator ports: "
                f"requested={server_count}, allocated={len(used_ports) - 1}, "
                f"range={port_start}-{port_end}"
            ) from exc
    else:
        if len(ports) != server_count:
            raise ValueError("ports length must equal server_count")
        resolved_ports = tuple(ports)

    for index, port in enumerate(resolved_ports):
        server_no = index + 1
        source = replace(
            base_source,
            connection=replace(
                base_source.connection,
                name=f"{base_source.connection.name}_{server_no}",
                ied_name=f"{base_source.connection.ied_name}_{server_no}",
                port=port,
                namespace_uri=f"{base_namespace}:server:{server_no}",
            ),
        )
        sources.append(source)

    return tuple(sources)


def build_opcua_endpoint(connection: SourceConnection) -> str:
    """根据连接信息构造 OPC UA endpoint URL。"""
    transport = connection.transport.strip().lower()
    scheme = "opc.tcp" if transport == "tcp" else f"opc.{transport}"
    return f"{scheme}://{connection.host}:{connection.port}"
