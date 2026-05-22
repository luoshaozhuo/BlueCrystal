"""Tests for file-backed field source loading and provider behavior."""

from __future__ import annotations

from typing import Any, cast

from pathlib import Path
import socket

import pytest

from tools.source_lab.access.common.io import build_field_runtime_sources
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig
from tools.source_lab.access.providers.expanded_field import ExpandedFieldSourceProvider
from tools.source_lab.access.providers.file_field import FieldFileSourceProvider, build_field_source_provider
from tools.source_lab.access.subscribe.model import SubscribeScanConfig
from tools.source_lab.sources import PortAllocator


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


def _subscribe_config(*, sample_hz: float, source_update_hz: float) -> SubscribeScanConfig:
    return SubscribeScanConfig(
        mode=CapacityMode.FIELD,
        protocol="opcua",
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        process_count=1,
        publishing_interval_ms=1000.0 / sample_hz,
        sampling_interval_ms=1000.0 / sample_hz,
        nominal_sample_hz=sample_hz,
        queue_size=1,
        source_update_enabled=True,
        source_update_hz=source_update_hz,
        progress_enabled=False,
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


def test_relative_path_takes_precedence_over_legacy_address(tmp_path: Path) -> None:
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
        profile_id\trelative_path\taddress\tdata_type
        pf-1\tIED1.LD0.WPPD1.TotW\ts=LegacyNode\tFLOAT64
        """,
    )

    sources = build_field_runtime_sources(servers, items)

    assert sources[0].points[0].address == "IED1.LD0.WPPD1.TotW"


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


def test_server_and_item_signal_profile_id_aliases_are_supported(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id\tsignal_profile_id\tapplication_protocol\ttransport\thost\tport\tendpoint_name\taccess_point_name
        ep-1\tpf-1\topcua\ttcp\t127.0.0.1\t4840\tIED1\tLD0
        """,
    )
    _write(
        items,
        """
        signal_profile_id\trelative_path\tdata_type_id\tln_name\tdo_name
        pf-1\tIED1.LD0.WPPD1.TotW\tFLOAT64\tWPPD1\tTotW
        """,
    )

    sources = build_field_runtime_sources(servers, items)

    assert sources[0].endpoint.params["profile_id"] == "pf-1"
    assert sources[0].points[0].address == "IED1.LD0.WPPD1.TotW"


def test_expanded_field_provider_overrides_host_and_skips_occupied_ports(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport\tendpoint_name\taccess_point_name
        ep-1\tpf-1\topcua\ttcp\tfield.example\t4840\tIED1\tLD0
        """,
    )
    _write(
        items,
        """
        profile_id\trelative_path\tdata_type_id\tln_name\tdo_name
        pf-1\tIED1.LD0.WPPD1.TotW\tFLOAT64\tWPPD1\tTotW
        """,
    )

    base_sources = build_field_runtime_sources(servers, items)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 52000))
        provider = ExpandedFieldSourceProvider(
            base_sources,
            port_start=52000,
            port_end=52003,
            port_allocator=PortAllocator.from_range(start=52000, end=52003),
        )

        built = provider.build_sources(_config(), server_count=3)

    assert tuple(source.endpoint.host for source in built) == ("127.0.0.1", "127.0.0.1", "127.0.0.1")
    assert tuple(source.endpoint.port for source in built) == (52001, 52002, 52003)
    assert all(len(source.points) == 1 for source in built)


def test_build_field_source_provider_uses_expanded_provider_for_simulator_runtime(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id	profile_id	application_protocol	transport	host	port	source_lab_runtime
        ep-1	pf-1	opcua	tcp	127.0.0.1	45000	simulator
        """,
    )
    _write(
        items,
        """
        profile_id	relative_path	data_type_id	ln_name	do_name
        pf-1	IED1.LD0.WPPD1.TotW	FLOAT64	WPPD1	TotW
        """,
    )

    sources = build_field_runtime_sources(servers, items, protocol="opcua")
    provider = build_field_source_provider(sources, protocol="opcua")

    assert isinstance(provider, ExpandedFieldSourceProvider)


def test_build_field_source_provider_keeps_real_field_provider_for_default_runtime(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id	profile_id	application_protocol	transport	host	port
        ep-1	pf-1	opcua	tcp	127.0.0.1	4840
        """,
    )
    _write(
        items,
        """
        profile_id	relative_path	data_type_id	ln_name	do_name
        pf-1	IED1.LD0.WPPD1.TotW	FLOAT64	WPPD1	TotW
        """,
    )

    sources = build_field_runtime_sources(servers, items, protocol="opcua")
    provider = build_field_source_provider(sources, protocol="opcua")

    assert isinstance(provider, FieldFileSourceProvider)


def test_expanded_field_provider_started_cleans_up_on_success(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id	profile_id	application_protocol	transport	host	port
        ep-1	pf-1	opcua	tcp	field.example	4840
        """,
    )
    _write(
        items,
        """
        profile_id	relative_path	data_type_id	ln_name	do_name
        pf-1	IED1.LD0.WPPD1.TotW	FLOAT64	WPPD1	TotW
        """,
    )
    events: list[object] = []
    fleet_args: dict[str, object] = {}

    class _FakeFleet:
        def __enter__(self) -> "_FakeFleet":
            events.append("enter")
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            events.append(("exit", exc_type))

    def _fleet_factory(*, sources: tuple, update_config: object, startup_timeout_seconds: float) -> _FakeFleet:
        fleet_args["sources"] = sources
        fleet_args["update_config"] = update_config
        fleet_args["startup_timeout_seconds"] = startup_timeout_seconds
        return _FakeFleet()

    fleet_factory: Any = _fleet_factory
    provider = ExpandedFieldSourceProvider(
        build_field_runtime_sources(servers, items),
        port_start=52000,
        fleet_factory=fleet_factory,
    )
    built = provider.build_sources(_config(), server_count=2)

    with provider.started(built):
        events.append("body")

    assert events == ["enter", "body", ("exit", None)]
    assert len(cast(tuple[object, ...], fleet_args["sources"])) == 2
    assert getattr(fleet_args["update_config"], "enabled") is True


def test_expanded_field_provider_started_passes_effective_source_update_rate(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id	profile_id	application_protocol	transport	host	port
        ep-1	pf-1	opcua	tcp	field.example	4840
        """,
    )
    _write(
        items,
        """
        profile_id	relative_path	data_type_id	ln_name	do_name
        pf-1	IED1.LD0.WPPD1.TotW	FLOAT64	WPPD1	TotW
        """,
    )
    fleet_args: dict[str, object] = {}

    class _FakeFleet:
        def __enter__(self) -> "_FakeFleet":
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    def _fleet_factory(*, sources: tuple, update_config: object, startup_timeout_seconds: float) -> _FakeFleet:
        fleet_args["sources"] = sources
        fleet_args["update_config"] = update_config
        fleet_args["startup_timeout_seconds"] = startup_timeout_seconds
        return _FakeFleet()

    provider = ExpandedFieldSourceProvider(
        build_field_runtime_sources(servers, items),
        port_start=52000,
        fleet_factory=cast(Any, _fleet_factory),
    )
    built = provider.build_sources(_subscribe_config(sample_hz=20.0, source_update_hz=20.0), server_count=1)

    with provider.started(built):
        pass

    fleet_sources = cast(tuple[object, ...], fleet_args["sources"])
    params = fleet_sources[0].connection.params
    assert params["source_update_hz"] == 20.0
    assert params["open62541_internal_update_enabled"] is True
    assert params["open62541_internal_update_interval_ms"] == 50


def test_expanded_field_provider_started_cleans_up_on_exception(tmp_path: Path) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        """
        endpoint_id	profile_id	application_protocol	transport	host	port
        ep-1	pf-1	opcua	tcp	field.example	4840
        """,
    )
    _write(
        items,
        """
        profile_id	relative_path	data_type_id	ln_name	do_name
        pf-1	IED1.LD0.WPPD1.TotW	FLOAT64	WPPD1	TotW
        """,
    )
    events: list[object] = []

    class _FakeFleet:
        def __enter__(self) -> "_FakeFleet":
            events.append("enter")
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            events.append(("exit", exc_type))

    fleet_factory: Any = lambda **kwargs: _FakeFleet()
    provider = ExpandedFieldSourceProvider(
        build_field_runtime_sources(servers, items),
        port_start=52000,
        fleet_factory=fleet_factory,
    )
    built = provider.build_sources(_config(), server_count=1)

    with pytest.raises(RuntimeError, match="boom"):
        with provider.started(built):
            raise RuntimeError("boom")

    assert events == ["enter", ("exit", RuntimeError)]
