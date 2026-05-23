"""OPC UA adapter 地址解析单元测试。"""

from __future__ import annotations

from typing import Any

from whale.ingest.adapters.source.opcua_source_acquisition_adapter import (
    OpcUaSourceAcquisitionAdapter,
    _build_endpoint,
)
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData


def _mk_conn(**params: Any) -> SourceConnectionData:
    return SourceConnectionData(
        host=str(params.get("host", "")),
        port=int(params.get("port", 0)),
        ied_name=str(params.get("ied_name", "IED_01")),
        ld_name=str(params.get("ld_name", "LD_01")),
        namespace_uri=str(params.get("namespace_uri", "")),
    )


def _mk_execution() -> AcquisitionExecutionOptions:
    return AcquisitionExecutionOptions(
        protocol="opcua",
        transport="tcp",
        acquisition_mode="ONCE",
        interval_ms=1000,
        max_iteration=1,
        request_timeout_ms=500,
        freshness_timeout_ms=30000,
        alive_timeout_ms=60000,
    )


def test_resolve_endpoint_from_protocol_transport_host_and_port() -> None:
    conn = _mk_conn(host="192.168.1.1", port=4840)

    assert _build_endpoint(_mk_execution(), conn) == "opc.tcp://192.168.1.1:4840"


def test_resolve_endpoint_empty_when_host_or_port_is_missing() -> None:
    assert _build_endpoint(_mk_execution(), _mk_conn(host="", port=0)) == ""


def test_resolve_node_paths_adds_namespace_uri_for_relative_paths() -> None:
    conn = _mk_conn(namespace_uri="urn:windfarm:2wtg")
    item = AcquisitionItemData(
        key="TotW",
        profile_item_id=1,
        relative_path="WTG_001/MMXU1.TotW.mag.f",
    )

    assert OpcUaSourceAcquisitionAdapter._resolve_node_paths(conn, [item]) == [
        "nsu=urn:windfarm:2wtg;s=WTG_001/MMXU1.TotW.mag.f"
    ]


def test_resolve_node_paths_without_namespace_uri_uses_string_nodeid() -> None:
    item = AcquisitionItemData(
        key="Spd",
        profile_item_id=2,
        relative_path="MMXU1.Spd.mag.f",
    )

    assert OpcUaSourceAcquisitionAdapter._resolve_node_paths(_mk_conn(), [item]) == [
        "s=MMXU1.Spd.mag.f"
    ]


def test_resolve_node_paths_preserves_prequalified_path() -> None:
    conn = _mk_conn(namespace_uri="urn:windfarm:2wtg")
    item = AcquisitionItemData(
        key="TotW",
        profile_item_id=1,
        relative_path="nsu=urn:other;s=Custom.Val",
    )

    assert OpcUaSourceAcquisitionAdapter._resolve_node_paths(conn, [item]) == [
        "nsu=urn:other;s=Custom.Val"
    ]
