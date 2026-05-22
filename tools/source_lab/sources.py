"""Shared source-building helpers for OPC UA load tests."""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from dataclasses import replace

from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection
from whale.ingest.adapters.config.source_runtime_config_repository import SourceRuntimeConfigRepository  # type: ignore[import-untyped]

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
    """Resolve runtime host into one concrete bind host for probing."""

    normalized = host.strip() if host.strip() else "127.0.0.1"
    if normalized.lower() == "localhost":
        return "127.0.0.1"
    return normalized


def _is_tcp_port_available(host: str, port: int) -> bool:
    """Return whether a TCP port is bindable on the given host."""

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
        """Build one test-run-scoped allocator from configured env range."""

        start, end = _resolve_port_scan_range()
        return cls(start=start, end=end, next_port=start, used_ports=set())

    @classmethod
    def from_range(cls, *, start: int, end: int) -> "PortAllocator":
        """Build allocator from explicit range with safe fallback bounds."""

        resolved_start = start if start > 0 else _DEFAULT_PORT_START
        resolved_end = end if end > 0 else _DEFAULT_PORT_END
        if resolved_start > resolved_end:
            resolved_start, resolved_end = _DEFAULT_PORT_START, _DEFAULT_PORT_END
        return cls(start=resolved_start, end=resolved_end, next_port=resolved_start, used_ports=set())

    def allocate_many(self, count: int, host: str = "127.0.0.1") -> tuple[int, ...]:
        """Allocate a batch of unique currently-bindable TCP ports."""

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
    """Pick a currently-bindable TCP port in range."""
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
    """Clone source and assign a free high-range port."""
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
    """Load one representative OPC UA source and its profile points."""
    runtime_repo = SourceRuntimeConfigRepository()

    server_rows = runtime_repo.list_servers()
    
    assert server_rows, "Expected at least one server in repository"
    server = server_rows[0]

    point_rows = runtime_repo.list_profile_items(server.signal_profile_id)
    point_count = len(point_rows)

    if not min_expected_point_count <= point_count <= max_expected_point_count:
        raise AssertionError(
            f"Expected {min_expected_point_count}-{max_expected_point_count} "
            f"profile items per server, got {point_count}"
        )

    points = tuple(
        SimulatedPoint(
            ln_name=row.ln_name,
            do_name=row.do_name,
            unit=row.unit.strip() if row.unit is not None else None,
            data_type=row.data_type,
        )
        for row in point_rows
    )

    return SimulatedSource(
        connection=SourceConnection(
            name=(
                server.asset_code
                or server.ld_name
                or server.ied_name
                or f"source_{server.endpoint_id}"
            ).strip(),
            ied_name=server.ied_name.strip(),
            ld_name=server.ld_name.strip(),
            host=server.host,
            port=int(server.port),
            transport=server.transport,
            protocol=server.application_protocol,
            namespace_uri=server.namespace_uri.strip(),
        ),
        points=points,
    )


def build_multi_sources(
    base_source: SimulatedSource,
    *,
    server_count: int,
    ports: tuple[int, ...] | list[int] | None = None,
) -> tuple[SimulatedSource, ...]:
    """Clone base source into multiple servers with unique ports/namespaces."""
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
    """Build OPC UA endpoint URL from source connection info."""
    transport = connection.transport.strip().lower()
    scheme = "opc.tcp" if transport == "tcp" else f"opc.{transport}"
    return f"{scheme}://{connection.host}:{connection.port}"
