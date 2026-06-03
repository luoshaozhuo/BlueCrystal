"""shared persistence SCADA sample DB 到 source_lab 模型的读取 provider。

本文件只负责在 provider 边界读取 shared persistence 数据库，并把
`CommunicationEndpoint + LDInstance + SignalProfileItem + 参数值表` 转成
`SimulatedSource/SimulatedPoint`。它不负责启动 simulator，也不直接依赖
ingest runtime repository。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from tools.source_lab.access.runners.registry import DECLARED_PROTOCOL_CAPABILITIES, normalize_protocol
from tools.source_lab.model import ProtocolValue, SimulatedPoint, SimulatedSource, SourceConnection
from whale.shared.persistence.orm import (
    CommunicationEndpoint,
    IED,
    LDInstance,
    ScadaDataType,
    ScadaEndpointParamValue,
    ScadaProtocolParamDef,
    ScadaSignalParamDef,
    ScadaSignalProfileItemParamValue,
    SignalProfileItem,
)

_ScalarParamMap = dict[str, ProtocolValue]
_TripleKey = tuple[str, str, str]


@dataclass(frozen=True, slots=True)
class _RuntimeMapping:
    """单个协议服务三元组到 source_lab runtime 的映射结果。"""

    protocol: str
    runtime_status: str
    runtime_reason: str | None = None
    backend_kind: str | None = None


@dataclass(frozen=True, slots=True)
class _ProfileItemBundle:
    """一个 profile item 及其协议参数快照。"""

    profile_item_id: int
    relative_path: str
    ln_name: str
    do_name: str
    da_name: str | None
    unit: str | None
    data_type: str
    ordinal: int
    protocol_params: _ScalarParamMap


_TRIPLE_TO_RUNTIME: dict[_TripleKey, _RuntimeMapping] = {
    ("OPC_UA", "READ", "TCP"): _RuntimeMapping("opcua", "available"),
    ("OPC_UA", "SUBSCRIBE", "TCP"): _RuntimeMapping("opcua", "available"),
    ("MODBUS", "TCP_READ", "TCP"): _RuntimeMapping("modbus_tcp", "available"),
    ("MODBUS", "RTU_READ", "SERIAL"): _RuntimeMapping("modbus_rtu", "available"),
    ("IEC101", "INTERROGATION", "SERIAL"): _RuntimeMapping("iec101", "available"),
    ("IEC101", "SPONTANEOUS", "SERIAL"): _RuntimeMapping("iec101", "available"),
    ("IEC104", "INTERROGATION", "TCP"): _RuntimeMapping("iec104", "available"),
    ("IEC104", "SPONTANEOUS", "TCP"): _RuntimeMapping("iec104", "available"),
    ("IEC61850", "MMS_READ", "TCP"): _RuntimeMapping("iec61850_mms", "available"),
    ("IEC61850", "REPORT", "TCP"): _RuntimeMapping("iec61850_report", "available"),
    ("IEC61850", "GOOSE", "ETHERNET_L2"): _RuntimeMapping("iec61850_goose", "available"),
    ("IEC61850", "SV", "ETHERNET_L2"): _RuntimeMapping("iec61850_sv", "available"),
    ("MQTT", "SUBSCRIBE", "MQTT"): _RuntimeMapping("mqtt", "available"),
    ("HTTP_REST", "REQUEST", "HTTPS"): _RuntimeMapping("http_rest", "available"),
    ("BECKHOFF_ADS", "ADS_READ_WRITE", "TCP"): _RuntimeMapping(
        "beckhoff_ads",
        "available",
        backend_kind="in_process",
    ),
    ("BECKHOFF_ADS", "ADS_NOTIFICATION", "TCP"): _RuntimeMapping(
        "beckhoff_ads",
        "available",
        "ADS notification path is not implemented in source_lab runtime",
        backend_kind="in_process",
    ),
}


def _protocol_value(
    *,
    value_text: str | None,
    value_int: int | None,
    value_float: float | None,
    value_bool: bool | None,
) -> ProtocolValue:
    """把第一范式参数值列恢复成 source_lab 可消费的标量。"""

    if value_bool is not None:
        return value_bool
    if value_int is not None:
        return value_int
    if value_float is not None:
        return value_float
    if value_text is None:
        raise ValueError("protocol param row has no populated value column")
    return value_text


def _runtime_mapping_for_triple(triple: _TripleKey) -> _RuntimeMapping:
    """解析单个协议服务三元组；未登记时立即失败。"""

    mapping = _TRIPLE_TO_RUNTIME.get(triple)
    if mapping is None:
        raise ValueError(
            "missing source_lab runtime mapping for shared persistence triple: "
            f"{triple!r}"
        )
    return mapping


def _candidate_triples(protocol: str, access_mode: str | None) -> tuple[_TripleKey, ...]:
    """根据 legacy protocol + access_mode 反查可能的 shared persistence 三元组。"""

    try:
        normalized = normalize_protocol(protocol)
    except ValueError as exc:
        raise ValueError(f"unsupported source_lab protocol: {protocol}") from exc
    cap = DECLARED_PROTOCOL_CAPABILITIES.get(normalized)
    if cap is None:
        raise ValueError(f"unsupported source_lab protocol: {protocol}")

    app_protocol = str(cap["application_protocol"])
    service_types: tuple[str, ...]
    service_type_map = cap.get("service_type_map")
    if access_mode is not None and isinstance(service_type_map, dict):
        mapped = service_type_map.get(access_mode)
        if isinstance(mapped, str):
            service_types = (mapped,)
        else:
            raw_service_types = cap.get("service_types", ())
            if not isinstance(raw_service_types, (tuple, list)):
                raw_service_types = ()
            service_types = tuple(
                str(value)
                for value in raw_service_types
                if isinstance(value, str)
            )
    else:
        raw_service_types = cap.get("service_types", ())
        if not isinstance(raw_service_types, (tuple, list)):
            raw_service_types = ()
        service_types = tuple(
            str(value)
            for value in raw_service_types
            if isinstance(value, str)
        )

    triples = tuple(
        triple
        for triple, mapping in _TRIPLE_TO_RUNTIME.items()
        if mapping.protocol == normalized
        and triple[0] == app_protocol
        and triple[1] in service_types
    )
    if not triples:
        raise ValueError(
            "no shared persistence triple matches source_lab protocol/access_mode: "
            f"protocol={protocol}, access_mode={access_mode}"
        )
    return triples


def _point_identity(item: _ProfileItemBundle) -> tuple[str, str]:
    """为不同协议生成稳定的 `ln_name/do_name`。"""

    ln_name = item.ln_name or "LN0"
    if item.da_name:
        return ln_name, f"{item.do_name}.{item.da_name}"
    return ln_name, item.do_name


def _point_address(
    *,
    triple: _TripleKey,
    path_prefix: str,
    item: _ProfileItemBundle,
) -> str:
    """按协议族为单点位构造 source_lab 可消费的地址。"""

    protocol_params = item.protocol_params
    app_protocol, _service_type, _transport = triple
    if app_protocol == "OPC_UA":
        namespace_index = int(protocol_params.get("namespace_index", 2))
        return f"ns={namespace_index};s={path_prefix}/{item.relative_path}"
    if app_protocol == "MODBUS":
        base_address = int(protocol_params.get("register_address", 0))
        register_count = max(1, int(protocol_params.get("register_count", 1)))
        return str(base_address + item.ordinal * register_count)
    if app_protocol in {"IEC101", "IEC104"}:
        return str(int(protocol_params.get("ioa", 0)) + item.ordinal)
    if app_protocol == "IEC61850":
        return f"{path_prefix}/{item.relative_path}"
    if app_protocol == "MQTT":
        return f"{protocol_params.get('payload_path', item.relative_path)}#{item.ordinal}"
    if app_protocol == "HTTP_REST":
        return f"{protocol_params.get('resource_path', '/points')}#{item.relative_path}"
    if app_protocol == "BECKHOFF_ADS":
        symbol_name = str(protocol_params.get("symbol_name", path_prefix)).strip() or path_prefix
        if item.ordinal == 0:
            return symbol_name
        return f"{symbol_name}__{item.ordinal}"
    raise ValueError(f"unsupported application protocol for point address: {triple!r}")


def _connection_params(
    *,
    triple: _TripleKey,
    ld_instance: LDInstance,
    endpoint_params: _ScalarParamMap,
    first_point: _ProfileItemBundle,
    runtime: _RuntimeMapping,
) -> _ScalarParamMap:
    """构造 SourceConnection.params，并补齐现有 runner/facade 可识别别名。"""

    params: _ScalarParamMap = {
        **endpoint_params,
        "ld_instance_id": ld_instance.ld_instance_id,
        "signal_profile_id": int(ld_instance.signal_profile_id or 0),
        "runtime_status": runtime.runtime_status,
    }
    if runtime.runtime_reason is not None:
        params["runtime_reason"] = runtime.runtime_reason
    if runtime.backend_kind is not None:
        params["backend_kind"] = runtime.backend_kind

    protocol_params = first_point.protocol_params
    app_protocol, service_type, _transport = triple
    if app_protocol == "MODBUS":
        params["modbus_unit_id"] = int(protocol_params.get("unit_id", endpoint_params.get("unit_id", 1)))
        params["modbus_start_address"] = int(protocol_params.get("register_address", 0))
    elif app_protocol == "IEC61850":
        params["ied_name"] = str(protocol_params.get("ied_name", params.get("ied_name", "")))
        params["ld_name"] = str(protocol_params.get("ld_inst", ld_instance.ld_name))
        params["fc"] = str(protocol_params.get("fc", "NONE"))
        if first_point.da_name is not None:
            params["da_name"] = first_point.da_name
        if service_type == "REPORT":
            params["rcb_ref"] = str(endpoint_params.get("report_control_block", "EventsRCB01"))
            params["use_native_report_runner"] = False
    elif app_protocol == "MQTT":
        params["mqtt_topic"] = str(protocol_params.get("topic", "source_lab/points"))
        params["mqtt_client_id"] = str(endpoint_params.get("client_id", "source-lab-runner"))
    elif app_protocol == "HTTP_REST":
        params["http_path"] = "/points"
    elif app_protocol == "BECKHOFF_ADS":
        params["ads_router_port"] = int(endpoint_params.get("ads_router_port", params.get("ads_router_port", 48898)))
        params["ads_server_port"] = int(endpoint_params.get("ads_server_port", 851))
        params["ams_net_id"] = str(endpoint_params.get("ams_net_id", ""))
    return params


class ScadaProfileProvider:
    """从 shared persistence SCADA sample DB 读取统一 `SimulatedSource`。"""

    def __init__(
        self,
        *,
        db_path: Path | str | None = None,
        database_url: str | None = None,
        engine: Engine | None = None,
    ) -> None:
        """初始化 provider。

        Args:
            db_path: 可选 SQLite 路径；提供后会创建独立 engine。
            database_url: 可选 SQLAlchemy URL，适用于 PostgreSQL 临时测试库。
            engine: 可选 SQLAlchemy engine。若提供则优先使用。
        """

        if engine is not None:
            self._engine = engine
        elif database_url is not None:
            self._engine = create_engine(
                database_url,
                echo=False,
                pool_pre_ping=True,
            )
        else:
            resolved_path = Path(db_path) if db_path is not None else None
            if resolved_path is None:
                from whale.shared.persistence.session import engine as shared_engine

                self._engine = shared_engine
            else:
                self._engine = create_engine(
                    f"sqlite:///{resolved_path}",
                    echo=False,
                    pool_pre_ping=True,
                )
        self._session_factory = sessionmaker(bind=self._engine, autoflush=False, expire_on_commit=False)

    def list_sources(self) -> tuple[SimulatedSource, ...]:
        """读取 DB 中全部 16 组协议服务样例。"""

        with self._session_factory() as session:
            return self._load_all_sources(session)

    def load_source(
        self,
        *,
        protocol: str,
        access_mode: str | None = None,
    ) -> SimulatedSource:
        """按 legacy protocol + access_mode 读取一个样例源。"""

        candidates = _candidate_triples(protocol, access_mode)
        sources = self.list_sources()
        for triple in candidates:
            for source in sources:
                current = (
                    str(source.connection.application_protocol or ""),
                    str(source.connection.service_type or ""),
                    source.connection.transport,
                )
                if current == triple:
                    return source
        raise ValueError(
            "shared persistence sample DB does not contain a source for "
            f"protocol={protocol}, access_mode={access_mode}, candidates={candidates!r}"
        )

    def _load_all_sources(self, session: Session) -> tuple[SimulatedSource, ...]:
        endpoint_rows = session.execute(
            select(LDInstance, CommunicationEndpoint, IED)
            .join(CommunicationEndpoint, CommunicationEndpoint.endpoint_id == LDInstance.endpoint_id)
            .join(IED, IED.ied_id == CommunicationEndpoint.ied_id)
            .where(LDInstance.signal_profile_id.is_not(None))
            .order_by(
                CommunicationEndpoint.application_protocol,
                CommunicationEndpoint.service_type,
                CommunicationEndpoint.transport,
                CommunicationEndpoint.endpoint_id,
            )
        ).all()
        if not endpoint_rows:
            return ()

        endpoint_ids = [endpoint.endpoint_id for _ld, endpoint, _ied in endpoint_rows]
        profile_ids = [
            int(ld.signal_profile_id)
            for ld, _endpoint, _ied in endpoint_rows
            if ld.signal_profile_id is not None
        ]
        profile_items_by_profile = self._load_profile_items(session, profile_ids)
        endpoint_params_by_endpoint = self._load_endpoint_params(session, endpoint_ids)
        all_profile_item_ids = [
            item.profile_item_id
            for bundles in profile_items_by_profile.values()
            for item in bundles
        ]
        signal_params_by_item = self._load_signal_params(session, all_profile_item_ids)

        sources: list[SimulatedSource] = []
        for ld_instance, endpoint, ied in endpoint_rows:
            if ld_instance.signal_profile_id is None:
                continue
            triple = (
                endpoint.application_protocol,
                str(endpoint.service_type or ""),
                endpoint.transport,
            )
            runtime = _runtime_mapping_for_triple(triple)
            base_items = profile_items_by_profile.get(int(ld_instance.signal_profile_id), ())
            item_bundles = tuple(
                replace(
                    item,
                    protocol_params=dict(
                        signal_params_by_item.get(item.profile_item_id, {}).get(
                            (triple[0], triple[1]),
                            {},
                        )
                    ),
                )
                for item in base_items
                if signal_params_by_item.get(item.profile_item_id, {}).get((triple[0], triple[1]))
            )
            if not item_bundles:
                raise ValueError(
                    "shared persistence sample DB profile has no signal params for triple: "
                    f"signal_profile_id={ld_instance.signal_profile_id}, triple={triple!r}"
                )

            endpoint_params = dict(endpoint_params_by_endpoint.get(endpoint.endpoint_id, {}))
            points = tuple(
                self._build_point(
                    triple=triple,
                    path_prefix=ld_instance.path_prefix or ld_instance.ld_name,
                    item=item,
                )
                for item in item_bundles
            )
            connection = SourceConnection(
                name=endpoint.endpoint_name or endpoint.access_point_name,
                ied_name=ied.ied_name,
                ld_name=ld_instance.ld_name,
                host=endpoint.host or "",
                port=int(endpoint.port or 0),
                transport=endpoint.transport,
                protocol=runtime.protocol,
                application_protocol=endpoint.application_protocol,
                service_type=endpoint.service_type,
                namespace_uri=endpoint.namespace_uri,
                params=_connection_params(
                    triple=triple,
                    ld_instance=ld_instance,
                    endpoint_params=endpoint_params,
                    first_point=item_bundles[0],
                    runtime=runtime,
                ),
            )
            sources.append(SimulatedSource(connection=connection, points=points))
        return tuple(sources)

    def _load_profile_items(
        self,
        session: Session,
        profile_ids: list[int],
    ) -> dict[int, tuple[_ProfileItemBundle, ...]]:
        rows = session.execute(
            select(SignalProfileItem, ScadaDataType)
            .join(ScadaDataType, ScadaDataType.data_type_id == SignalProfileItem.data_type_id)
            .where(SignalProfileItem.signal_profile_id.in_(profile_ids))
            .order_by(SignalProfileItem.signal_profile_id, SignalProfileItem.profile_item_id)
        ).all()
        grouped: dict[int, list[_ProfileItemBundle]] = defaultdict(list)
        profile_ordinals: dict[int, int] = defaultdict(int)
        for item, data_type in rows:
            profile_ordinals[item.signal_profile_id] += 1
            grouped[item.signal_profile_id].append(
                _ProfileItemBundle(
                    profile_item_id=item.profile_item_id,
                    relative_path=item.relative_path,
                    ln_name=item.ln_name or "",
                    do_name=item.do_name,
                    da_name=item.da_name,
                    unit=item.default_unit,
                    data_type=data_type.type_name,
                    ordinal=profile_ordinals[item.signal_profile_id] - 1,
                    protocol_params={},
                )
            )
        return {profile_id: tuple(items) for profile_id, items in grouped.items()}

    def _load_endpoint_params(
        self,
        session: Session,
        endpoint_ids: list[int],
    ) -> dict[int, _ScalarParamMap]:
        rows = session.execute(
            select(ScadaEndpointParamValue, ScadaProtocolParamDef)
            .join(
                ScadaProtocolParamDef,
                ScadaProtocolParamDef.param_def_id == ScadaEndpointParamValue.param_def_id,
            )
            .where(ScadaEndpointParamValue.endpoint_id.in_(endpoint_ids))
        ).all()
        grouped: dict[int, _ScalarParamMap] = defaultdict(dict)
        for value_row, definition in rows:
            grouped[value_row.endpoint_id][definition.param_key] = _protocol_value(
                value_text=value_row.value_text,
                value_int=value_row.value_int,
                value_float=value_row.value_float,
                value_bool=value_row.value_bool,
            )
        return grouped

    def _load_signal_params(
        self,
        session: Session,
        profile_item_ids: list[int],
    ) -> dict[int, dict[tuple[str, str | None], _ScalarParamMap]]:
        rows = session.execute(
            select(ScadaSignalProfileItemParamValue, ScadaSignalParamDef)
            .join(
                ScadaSignalParamDef,
                ScadaSignalParamDef.param_def_id == ScadaSignalProfileItemParamValue.param_def_id,
            )
            .where(ScadaSignalProfileItemParamValue.profile_item_id.in_(profile_item_ids))
        ).all()
        grouped: dict[int, dict[tuple[str, str | None], _ScalarParamMap]] = defaultdict(
            lambda: defaultdict(dict)
        )
        for value_row, definition in rows:
            grouped[value_row.profile_item_id][
                (definition.application_protocol, definition.service_type)
            ][definition.param_key] = _protocol_value(
                value_text=value_row.value_text,
                value_int=value_row.value_int,
                value_float=value_row.value_float,
                value_bool=value_row.value_bool,
            )
        return grouped

    def _build_point(
        self,
        *,
        triple: _TripleKey,
        path_prefix: str,
        item: _ProfileItemBundle,
    ) -> SimulatedPoint:
        address = _point_address(triple=triple, path_prefix=path_prefix, item=item)
        ln_name, do_name = _point_identity(item)
        if triple[0] in {"MODBUS", "IEC101", "IEC104"}:
            do_name = address
        protocol_params = dict(item.protocol_params)
        if triple[0] == "BECKHOFF_ADS":
            data_size = int(protocol_params.get("data_size", 8))
            protocol_params["symbol_name"] = address
            protocol_params["index_offset"] = int(protocol_params.get("index_offset", 0)) + item.ordinal * data_size
            protocol_params["data_size"] = data_size
        return SimulatedPoint(
            ln_name=ln_name,
            do_name=do_name,
            unit=item.unit,
            data_type=item.data_type,
            address=address,
            protocol_params=protocol_params,
        )


__all__ = ["ScadaProfileProvider"]
