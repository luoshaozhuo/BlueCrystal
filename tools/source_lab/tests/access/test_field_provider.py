"""Tests for file-backed field source loading and provider behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.source_lab.access.io import build_field_runtime_sources
from tools.source_lab.access.model import CapacityMode, CapacityScanConfig
from tools.source_lab.access.providers.file_field import FieldFileSourceProvider


def _write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _config(protocol: str = "opcua") -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.FIELD,
        protocol=protocol,
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=3,
        hz_start=10.0,
        hz_step=10.0,
        hz_max=10.0,
        process_count=1,
    )


def test_field_provider_builds_sources_from_profile_binding(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport\tnamespace_uri\tied_name\tld_instance_id
        ep-1\tpf-1\topc-ua\ttcp\t127.0.0.1\t4840\turn:test\tIED1\tLD1
        """,
    )
    _write(
        items,
        """
        profile_id\taddress\tdata_type\tpoint_name\tprotocol
        pf-1\ts=Node1\tFLOAT64\tp1\topcua
        pf-1\ts=Node2\tBOOLEAN\tp2\topcua
        """,
    )

    sources = build_field_runtime_sources(servers, items)
    provider = FieldFileSourceProvider(sources, protocol="opcua")

    built = provider.build_sources(_config(), server_count=1)

    assert len(built) == 1
    assert built[0].endpoint.protocol == "opcua"
    assert len(built[0].points) == 2
    with provider.started(built):
        pass


def test_multiple_servers_can_share_one_profile_id(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport
        ep-1\tpf-1\topcua\ttcp\t127.0.0.1\t4840
        ep-2\tpf-1\topcua\ttcp\t127.0.0.1\t4841
        """,
    )
    _write(
        items,
        """
        profile_id\taddress\tdata_type
        pf-1\ts=Node1\tFLOAT64
        """,
    )

    sources = build_field_runtime_sources(servers, items)

    assert len(sources) == 2
    assert tuple(len(source.points) for source in sources) == (1, 1)


def test_different_servers_can_use_different_profile_ids(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport
        ep-1\tpf-1\topcua\ttcp\t127.0.0.1\t4840
        ep-2\tpf-2\topcua\ttcp\t127.0.0.1\t4841
        """,
    )
    _write(
        items,
        """
        profile_id\taddress\tdata_type
        pf-1\ts=Node1\tFLOAT64
        pf-2\ts=Node2\tBOOLEAN
        """,
    )

    sources = build_field_runtime_sources(servers, items)

    assert sources[0].points[0].address == "s=Node1"
    assert sources[1].points[0].address == "s=Node2"


def test_missing_profile_reference_raises_error(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport
        ep-1\tpf-missing\topcua\ttcp\t127.0.0.1\t4840
        """,
    )
    _write(
        items,
        """
        profile_id\taddress\tdata_type
        pf-1\ts=Node1\tFLOAT64
        """,
    )

    with pytest.raises(ValueError, match="references missing profile_id"):
        build_field_runtime_sources(servers, items)


def test_profile_with_no_enabled_items_raises_error(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport
        ep-1\tpf-1\topcua\ttcp\t127.0.0.1\t4840
        """,
    )
    _write(
        items,
        """
        profile_id\taddress\tdata_type\tenabled
        pf-1\ts=Node1\tFLOAT64\tfalse
        """,
    )

    with pytest.raises(ValueError, match="has no enabled items"):
        build_field_runtime_sources(servers, items)


def test_non_opcua_protocol_can_load_and_provider_filters_by_protocol(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport
        ep-1\tpf-1\tmodbus-tcp\ttcp\t127.0.0.1\t502
        ep-2\tpf-2\topc-ua\ttcp\t127.0.0.1\t4840
        """,
    )
    _write(
        items,
        """
        profile_id\taddress\tdata_type\tprotocol
        pf-1\t40001\tINT32\tmodbus_tcp
        pf-2\ts=Node1\tFLOAT64\topcua
        """,
    )

    sources = build_field_runtime_sources(servers, items)
    provider = FieldFileSourceProvider(sources, protocol="opcua")

    built = provider.build_sources(_config(protocol="opcua"), server_count=1)

    assert len(sources) == 2
    assert len(built) == 1
    assert built[0].endpoint.protocol == "opcua"


def test_protocol_mismatch_is_reported(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport
        ep-1\tpf-1\topcua\ttcp\t127.0.0.1\t4840
        """,
    )
    _write(
        items,
        """
        profile_id\taddress\tdata_type\tprotocol
        pf-1\ts=Node1\tFLOAT64\tmodbus
        """,
    )

    with pytest.raises(ValueError, match="protocol mismatch"):
        build_field_runtime_sources(servers, items)


def test_provider_raises_when_server_count_exceeds_filtered_sources(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport
        ep-1\tpf-1\tmodbus-tcp\ttcp\t127.0.0.1\t502
        ep-2\tpf-2\topcua\ttcp\t127.0.0.1\t4840
        """,
    )
    _write(
        items,
        """
        profile_id\taddress\tdata_type\tprotocol
        pf-1\t40001\tINT32\tmodbus_tcp
        pf-2\ts=Node1\tFLOAT64\topcua
        """,
    )

    sources = build_field_runtime_sources(servers, items)
    provider = FieldFileSourceProvider(sources, protocol="opcua")

    with pytest.raises(ValueError, match="server_count exceeds available endpoints"):
        provider.build_sources(_config(protocol="opcua"), server_count=2)


def test_provider_raises_on_config_protocol_mismatch(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport
        ep-1\tpf-1\topcua\ttcp\t127.0.0.1\t4840
        """,
    )
    _write(
        items,
        """
        profile_id\taddress\tdata_type\tprotocol
        pf-1\ts=Node1\tFLOAT64\topcua
        """,
    )

    sources = build_field_runtime_sources(servers, items)
    provider = FieldFileSourceProvider(sources, protocol="opcua")

    with pytest.raises(ValueError, match="protocol mismatch"):
        provider.build_sources(_config(protocol="modbus"), server_count=1)
