"""SCADA 协议端点参数展平 view 的 SQLAlchemy Core 定义。

这些定义只描述查询形状，便于 Alembic 手动管理数据库对象生命周期。
它们不创建连接、不写入数据库，也不会被加入 ORM metadata。
"""

from __future__ import annotations

from sqlalchemy import String, and_, cast, column, func, or_, select, table

from pacific.whale.shared.persistence.views.definition import ViewDefinition

scada_communication_endpoint = table(
    "scada_communication_endpoint",
    column("endpoint_id"),
    column("ied_id"),
    column("application_protocol"),
    column("service_type"),
    column("transport"),
    column("host"),
    column("port"),
    column("namespace_uri"),
    column("security_policy"),
    column("security_mode"),
    column("auth_type"),
)
scada_endpoint_param_value = table(
    "scada_endpoint_param_value",
    column("endpoint_id"),
    column("param_def_id"),
    column("value_text"),
    column("value_int"),
    column("value_float"),
    column("value_bool"),
)
scada_protocol_param_def = table(
    "scada_protocol_param_def",
    column("param_def_id"),
    column("param_key"),
)


def _param_value_expr():
    return func.coalesce(
        scada_endpoint_param_value.c.value_text,
        cast(scada_endpoint_param_value.c.value_int, String),
        cast(scada_endpoint_param_value.c.value_float, String),
        cast(scada_endpoint_param_value.c.value_bool, String),
    )


def _build_protocol_view(
    view_name: str,
    where_clause,
    *,
    include_namespace: bool = False,
    include_security: bool = False,
) -> ViewDefinition:
    ep = scada_communication_endpoint
    pv = scada_endpoint_param_value
    param = scada_protocol_param_def

    columns = [
        ep.c.endpoint_id.label("endpoint_id"),
        ep.c.ied_id.label("ied_id"),
        ep.c.application_protocol.label("application_protocol"),
        ep.c.service_type.label("service_type"),
        ep.c.transport.label("transport"),
        ep.c.host.label("host"),
        ep.c.port.label("port"),
    ]
    if include_namespace:
        columns.append(ep.c.namespace_uri.label("namespace_uri"))
    if include_security:
        columns.extend(
            [
                ep.c.security_policy.label("security_policy"),
                ep.c.security_mode.label("security_mode"),
                ep.c.auth_type.label("auth_type"),
            ]
        )
    columns.extend(
        [
            param.c.param_key.label("param_key"),
            _param_value_expr().label("param_value"),
        ]
    )

    selectable = (
        select(*columns)
        .select_from(
            ep.outerjoin(pv, pv.c.endpoint_id == ep.c.endpoint_id).outerjoin(
                param, param.c.param_def_id == pv.c.param_def_id
            )
        )
        .where(where_clause)
    )
    return ViewDefinition(view_name, selectable)


ep = scada_communication_endpoint

SCADA_PROTOCOL_VIEW_DEFINITIONS: tuple[ViewDefinition, ...] = (
    _build_protocol_view(
        "v_scada_endpoint_opcua",
        ep.c.application_protocol == "OPC_UA",
        include_namespace=True,
        include_security=True,
    ),
    _build_protocol_view(
        "v_scada_endpoint_modbus_tcp",
        and_(
            ep.c.application_protocol == "MODBUS",
            or_(ep.c.service_type.is_(None), ep.c.service_type == "TCP_READ"),
            ep.c.transport == "TCP",
        ),
    ),
    _build_protocol_view(
        "v_scada_endpoint_modbus_rtu",
        and_(
            ep.c.application_protocol == "MODBUS",
            or_(ep.c.service_type.is_(None), ep.c.service_type == "RTU_READ"),
            ep.c.transport == "SERIAL",
        ),
    ),
    _build_protocol_view("v_scada_endpoint_iec101", ep.c.application_protocol == "IEC101"),
    _build_protocol_view("v_scada_endpoint_iec104", ep.c.application_protocol == "IEC104"),
    _build_protocol_view(
        "v_scada_endpoint_iec61850_mms",
        and_(
            ep.c.application_protocol == "IEC61850",
            ep.c.service_type.in_(("MMS_READ", "REPORT")),
        ),
    ),
    _build_protocol_view(
        "v_scada_endpoint_iec61850_goose",
        and_(ep.c.application_protocol == "IEC61850", ep.c.service_type == "GOOSE"),
    ),
    _build_protocol_view(
        "v_scada_endpoint_iec61850_sv",
        and_(ep.c.application_protocol == "IEC61850", ep.c.service_type == "SV"),
    ),
    _build_protocol_view("v_scada_endpoint_mqtt", ep.c.application_protocol == "MQTT"),
    _build_protocol_view("v_scada_endpoint_http_rest", ep.c.application_protocol == "HTTP_REST"),
    _build_protocol_view(
        "v_scada_endpoint_beckhoff_ads",
        ep.c.application_protocol == "BECKHOFF_ADS",
        include_security=True,
    ),
)

SCADA_PROTOCOL_VIEW_SQL: dict[str, str] = {
    view.name: view.select_sql() for view in SCADA_PROTOCOL_VIEW_DEFINITIONS
}

__all__ = [
    "SCADA_PROTOCOL_VIEW_DEFINITIONS",
    "SCADA_PROTOCOL_VIEW_SQL",
]
