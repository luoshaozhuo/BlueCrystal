"""SCADA 协议视图单测.

证据等级：L1 unit/mock。
这些测试只验证协议视图在本地 SQLite 中可创建、可查询，并能按协议过滤
第一范式参数值；不证明真实数据库方言兼容性，也不证明真实协议连通性。
"""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from whale.shared.persistence import Base
from whale.shared.persistence.orm import (
    AssetInstance,
    AssetType,
    CommunicationEndpoint,
    IED,
    ScadaEndpointParamValue,
    ScadaProtocolParamDef,
)
from whale.shared.persistence.template.protocol_view_defs import _PROTOCOL_VIEW_DEFS, ensure_protocol_views


def _make_engine() -> Engine:
    """创建用于视图验证的内存数据库."""

    return create_engine("sqlite:///:memory:")


def _seed_ads_endpoints(session: Session) -> tuple[int, int]:
    """写入两条可被 ADS 协议视图查询的端点和参数值."""

    asset_type = AssetType(type_code="WTG_VIEW", type_name="视图测试风机")
    session.add(asset_type)
    session.flush()

    asset = AssetInstance(
        asset_code="WTG_VIEW_001",
        asset_name="视图测试风机 001",
        asset_type_id=asset_type.asset_type_id,
        status="ACTIVE",
    )
    session.add(asset)
    session.flush()

    ied = IED(asset_instance_id=asset.asset_instance_id, ied_name="IED_WTG_VIEW_001")
    session.add(ied)
    session.flush()

    endpoint = CommunicationEndpoint(
        ied_id=ied.ied_id,
        access_point_name="ADS_AP",
        endpoint_name="ADS 视图测试端点",
        application_protocol="BECKHOFF_ADS",
        service_type="ADS_READ_WRITE",
        transport="TCP",
        host="192.168.40.51",
        port=48898,
        security_policy="PLC_ROUTE",
        security_mode="ROUTE",
        auth_type="Certificate",
        service_capabilities_json={"supports_read": True},
    )
    session.add(endpoint)
    session.flush()

    notification_endpoint = CommunicationEndpoint(
        ied_id=ied.ied_id,
        access_point_name="ADS_NOTIFY_AP",
        endpoint_name="ADS 通知视图测试端点",
        application_protocol="BECKHOFF_ADS",
        service_type="ADS_NOTIFICATION",
        transport="TCP",
        host="192.168.40.52",
        port=48898,
        security_policy="PLC_ROUTE",
        security_mode="ROUTE",
        auth_type="Certificate",
        service_capabilities_json={"supports_subscription": True},
    )
    session.add(notification_endpoint)
    session.flush()

    param_def = ScadaProtocolParamDef(
        application_protocol="BECKHOFF_ADS",
        service_type="ADS_READ_WRITE",
        transport="TCP",
        param_key="ams_net_id",
        param_name="AMS Net ID",
        data_type="STRING",
    )
    session.add(param_def)
    session.flush()

    session.add(
        ScadaEndpointParamValue(
            endpoint_id=endpoint.endpoint_id,
            param_def_id=param_def.param_def_id,
            value_text="5.32.160.1.1.1",
        )
    )
    notification_param_def = ScadaProtocolParamDef(
        application_protocol="BECKHOFF_ADS",
        service_type="ADS_NOTIFICATION",
        transport="TCP",
        param_key="ams_net_id",
        param_name="AMS Net ID",
        data_type="STRING",
    )
    session.add(notification_param_def)
    session.flush()

    session.add(
        ScadaEndpointParamValue(
            endpoint_id=notification_endpoint.endpoint_id,
            param_def_id=notification_param_def.param_def_id,
            value_text="5.32.160.1.1.2",
        )
    )
    endpoint_ids = (endpoint.endpoint_id, notification_endpoint.endpoint_id)
    session.commit()
    return endpoint_ids


def test_protocol_views_sql_registry_covers_ads() -> None:
    """协议视图注册表必须包含新增 ADS 视图定义."""

    assert "v_scada_endpoint_beckhoff_ads" in _PROTOCOL_VIEW_DEFS
    assert "BECKHOFF_ADS" in _PROTOCOL_VIEW_DEFS["v_scada_endpoint_beckhoff_ads"]


def test_protocol_views_can_be_created_and_query_ads_endpoint() -> None:
    """协议视图应能创建成功，并查询到 ADS 读写与通知端点参数值."""

    engine = _make_engine()
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        read_write_endpoint_id, notification_endpoint_id = _seed_ads_endpoints(session)

    ensure_protocol_views(bind=engine)
    with engine.connect() as conn:
        view_names = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'view' AND name LIKE 'v_scada_endpoint_%'")
            )
        }
        rows = conn.execute(
            text(
                """
                SELECT endpoint_id, application_protocol, service_type, param_key, param_value
                FROM v_scada_endpoint_beckhoff_ads
                WHERE endpoint_id IN (:read_write_endpoint_id, :notification_endpoint_id)
                ORDER BY endpoint_id
                """
            ),
            {
                "read_write_endpoint_id": read_write_endpoint_id,
                "notification_endpoint_id": notification_endpoint_id,
            },
        ).fetchall()

    assert "v_scada_endpoint_beckhoff_ads" in view_names
    assert "v_scada_endpoint_http_rest" in view_names
    assert len(rows) == 2
    assert rows[0].application_protocol == "BECKHOFF_ADS"
    assert rows[0].service_type == "ADS_READ_WRITE"
    assert rows[0].param_key == "ams_net_id"
    assert rows[0].param_value == "5.32.160.1.1.1"
    assert rows[1].service_type == "ADS_NOTIFICATION"
    assert rows[1].param_key == "ams_net_id"
    assert rows[1].param_value == "5.32.160.1.1.2"
