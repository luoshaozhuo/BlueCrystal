"""多协议 source simulator 的测试支持 fixture。

为 source_lab simulator E2E 测试提供可复用的测试源定义。
证据等级：L3（simulator）。
"""
from __future__ import annotations

import socket

import pytest

from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection
from tools.source_lab.tests.support.sources import (
    PortAllocator,
    _is_tcp_port_available,
    build_multi_sources,
)


def _make_base_source(*, port: int = 4840) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name="WTG",
            ied_name="IED_WTG",
            ld_name="LD0",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="opcua",
            namespace_uri="urn:test:source",
        ),
        points=(
            SimulatedPoint(
                ln_name="GGIO1",
                do_name="AnIn1",
                unit=None,
                data_type="FLOAT64",
            ),
        ),
    )


def test_build_multi_sources_allocates_unique_ports_in_configured_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_SIM_PORT_START", "45000")
    monkeypatch.setenv("SOURCE_SIM_PORT_END", "45100")

    sources = build_multi_sources(_make_base_source(), server_count=50)

    ports = [source.connection.port for source in sources]
    assert len(ports) == 50
    assert len(set(ports)) == 50
    assert all(45000 <= port <= 45100 for port in ports)


def test_port_allocator_allocate_many_returns_unique_ports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_SIM_PORT_START", "45110")
    monkeypatch.setenv("SOURCE_SIM_PORT_END", "45120")

    allocator = PortAllocator.from_env()
    first = allocator.allocate_many(3)
    second = allocator.allocate_many(3)

    assert len(first) == 3
    assert len(second) == 3
    assert len(set(first + second)) == 6


def test_port_allocator_skips_temporarily_occupied_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_SIM_PORT_START", "45130")
    monkeypatch.setenv("SOURCE_SIM_PORT_END", "45135")

    allocator = PortAllocator.from_env()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 45130))
        allocated = allocator.allocate_many(2)

    assert 45130 not in allocated
    assert len(set(allocated)) == 2


def test_tcp_port_probe_detects_loopback_binding() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        assert _is_tcp_port_available("127.0.0.1", port) is False


def test_tcp_port_probe_detects_any_binding() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("0.0.0.0", 0))
        port = sock.getsockname()[1]
        assert _is_tcp_port_available("127.0.0.1", port) is False


def test_tcp_port_probe_detects_ipv6_binding_when_supported() -> None:
    if not socket.has_ipv6:
        pytest.skip("IPv6 is not available on this platform")

    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    except OSError:
        pytest.skip("IPv6 socket creation is not available on this platform")

    with sock:
        try:
            sock.bind(("::", 0))
        except OSError:
            pytest.skip("IPv6 any-address binding is not available on this platform")
        port = sock.getsockname()[1]
        assert _is_tcp_port_available("127.0.0.1", port) is False


def test_build_multi_sources_skips_temporarily_occupied_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_SIM_PORT_START", "45200")
    monkeypatch.setenv("SOURCE_SIM_PORT_END", "45205")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 45200))
        sources = build_multi_sources(_make_base_source(), server_count=3)

    ports = [source.connection.port for source in sources]
    assert 45200 not in ports
    assert len(set(ports)) == 3


def test_build_multi_sources_uses_explicit_ports() -> None:
    sources = build_multi_sources(
        _make_base_source(),
        server_count=3,
        ports=[46001, 46002, 46003],
    )

    assert [source.connection.port for source in sources] == [46001, 46002, 46003]


def test_build_multi_sources_rejects_wrong_port_count() -> None:
    with pytest.raises(ValueError, match="ports length must equal server_count"):
        build_multi_sources(_make_base_source(), server_count=3, ports=[46001, 46002])


def test_build_multi_sources_raises_when_range_is_too_small(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_SIM_PORT_START", "45300")
    monkeypatch.setenv("SOURCE_SIM_PORT_END", "45301")

    with pytest.raises(RuntimeError, match="Failed to allocate simulator ports"):
        build_multi_sources(_make_base_source(), server_count=3)


def test_build_multi_sources_reuses_range_defaults_for_invalid_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_SIM_PORT_START", "bad")
    monkeypatch.setenv("SOURCE_SIM_PORT_END", "-1")

    sources = build_multi_sources(_make_base_source(), server_count=2)

    ports = [source.connection.port for source in sources]
    assert len(set(ports)) == 2
    assert all(45000 <= port <= 65000 for port in ports)
