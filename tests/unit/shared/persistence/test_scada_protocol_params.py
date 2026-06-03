"""SCADA 协议参数模板与 ORM 单测.

证据等级：L1 unit/mock。
这些测试验证模板注册、ORM 建表、注释语义和第一范式参数值的本地存取，
不证明真实协议连通性，也不证明生产环境配置正确。
"""

from __future__ import annotations

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from whale.shared.persistence import Base
from whale.shared.persistence.orm import (
    AssetInstance,
    AssetType,
    CommunicationEndpoint,
    IED,
    LDInstance,
    ScadaDataType,
    ScadaEndpointParamValue,
    ScadaProtocolParamDef,
    ScadaSignalParamDef,
    ScadaSignalProfileItemParamValue,
    SignalProfile,
    SignalProfileItem,
)
from whale.shared.persistence.template.protocol_param_data import ENDPOINT_PARAM_DEFS, SIGNAL_PARAM_DEFS, get_endpoint_params, get_signal_params


def _make_engine() -> Engine:
    """创建内存 SQLite 引擎."""

    return create_engine("sqlite:///:memory:")


def _init_tables(engine: Engine) -> None:
    """初始化测试所需全部 ORM 表."""

    Base.metadata.create_all(bind=engine)


def _create_minimal_scada_context(session: Session) -> tuple[CommunicationEndpoint, SignalProfileItem]:
    """创建参数值测试需要的最小资产、IED、Endpoint 与点位上下文."""

    asset_type = AssetType(type_code="WTG_TEST", type_name="测试风机")
    session.add(asset_type)
    session.flush()

    asset = AssetInstance(
        asset_code="WTG_TEST_001",
        asset_name="测试风机 001",
        asset_type_id=asset_type.asset_type_id,
        status="ACTIVE",
    )
    session.add(asset)
    session.flush()

    ied = IED(asset_instance_id=asset.asset_instance_id, ied_name="IED_WTG_TEST_001")
    session.add(ied)
    session.flush()

    endpoint = CommunicationEndpoint(
        ied_id=ied.ied_id,
        access_point_name="AP1",
        application_protocol="OPC_UA",
        service_type="READ",
        transport="TCP",
        host="127.0.0.1",
        port=4840,
        service_capabilities_json={"supports_read": True},
    )
    session.add(endpoint)
    session.flush()

    data_type = ScadaDataType(type_name="FLOAT64")
    session.add(data_type)
    session.flush()

    profile = SignalProfile(profile_code="PROFILE_TEST", profile_name="测试点表")
    session.add(profile)
    session.flush()

    item = SignalProfileItem(
        signal_profile_id=profile.signal_profile_id,
        do_name="TotW",
        relative_path="MMXU1.TotW.mag.f",
        data_type_id=data_type.data_type_id,
    )
    session.add(item)
    session.flush()

    ld_instance = LDInstance(
        endpoint_id=endpoint.endpoint_id,
        asset_instance_id=asset.asset_instance_id,
        signal_profile_id=profile.signal_profile_id,
        ld_name="LD0",
    )
    session.add(ld_instance)
    session.flush()
    return endpoint, item


def test_protocol_param_tables_created() -> None:
    """协议参数相关表必须被 ORM 元数据创建."""

    engine = _make_engine()
    _init_tables(engine)
    names = set(inspect(engine).get_table_names())
    assert "scada_protocol_param_def" in names
    assert "scada_endpoint_param_value" in names
    assert "scada_signal_param_def" in names
    assert "scada_signal_profile_item_param_value" in names


def test_endpoint_param_registry_covers_expected_protocol_matrix() -> None:
    """端点参数模板必须覆盖 handoff 要求的协议矩阵."""

    expected = {
        ("OPC_UA", "READ"),
        ("OPC_UA", "SUBSCRIBE"),
        ("MODBUS", "TCP_READ"),
        ("MODBUS", "RTU_READ"),
        ("IEC101", "INTERROGATION"),
        ("IEC101", "SPONTANEOUS"),
        ("IEC104", "INTERROGATION"),
        ("IEC104", "SPONTANEOUS"),
        ("IEC61850", "MMS_READ"),
        ("IEC61850", "REPORT"),
        ("IEC61850", "GOOSE"),
        ("IEC61850", "SV"),
        ("MQTT", "SUBSCRIBE"),
        ("HTTP_REST", "REQUEST"),
        ("BECKHOFF_ADS", "ADS_READ_WRITE"),
        ("BECKHOFF_ADS", "ADS_NOTIFICATION"),
    }
    registered = {(protocol, service) for protocol, services in ENDPOINT_PARAM_DEFS.items() for service in services}
    assert registered == expected


def test_signal_param_registry_covers_expected_protocol_matrix() -> None:
    """点位参数模板必须覆盖与端点一致的协议矩阵."""

    expected = {
        ("OPC_UA", "READ"),
        ("OPC_UA", "SUBSCRIBE"),
        ("MODBUS", "TCP_READ"),
        ("MODBUS", "RTU_READ"),
        ("IEC101", "INTERROGATION"),
        ("IEC101", "SPONTANEOUS"),
        ("IEC104", "INTERROGATION"),
        ("IEC104", "SPONTANEOUS"),
        ("IEC61850", "MMS_READ"),
        ("IEC61850", "REPORT"),
        ("IEC61850", "GOOSE"),
        ("IEC61850", "SV"),
        ("MQTT", "SUBSCRIBE"),
        ("HTTP_REST", "REQUEST"),
        ("BECKHOFF_ADS", "ADS_READ_WRITE"),
        ("BECKHOFF_ADS", "ADS_NOTIFICATION"),
    }
    registered = {(protocol, service) for protocol, services in SIGNAL_PARAM_DEFS.items() for service in services}
    assert registered == expected


def test_new_protocol_endpoint_params_are_defined() -> None:
    """新增协议的端点参数模板必须完整可查."""

    assert {"endpoint_url", "application_uri", "connect_timeout_ms", "request_timeout_ms"} <= {
        param.key for param in get_endpoint_params("OPC_UA", "READ")
    }
    assert {"client_id", "topic_prefix", "keepalive_seconds", "username_ref", "password_ref"} <= {
        param.key for param in get_endpoint_params("MQTT", "SUBSCRIBE")
    }
    assert {"base_path", "method", "auth_header_ref", "verify_tls"} <= {
        param.key for param in get_endpoint_params("HTTP_REST", "REQUEST")
    }
    assert {"ams_net_id", "ads_router_port", "ads_server_port", "request_timeout_ms"} <= {
        param.key for param in get_endpoint_params("BECKHOFF_ADS", "ADS_READ_WRITE")
    }
    assert {"ams_net_id", "ads_router_port", "ads_server_port", "request_timeout_ms"} <= {
        param.key for param in get_endpoint_params("BECKHOFF_ADS", "ADS_NOTIFICATION")
    }


def test_new_protocol_signal_params_are_defined() -> None:
    """新增协议的点位参数模板必须完整可查."""

    assert {"namespace_index", "node_id", "browse_path", "attribute_id"} <= {
        param.key for param in get_signal_params("OPC_UA", "READ")
    }
    assert {"topic", "payload_path", "payload_type", "retain"} <= {
        param.key for param in get_signal_params("MQTT", "SUBSCRIBE")
    }
    assert {"resource_path", "json_path", "method", "value_field"} <= {
        param.key for param in get_signal_params("HTTP_REST", "REQUEST")
    }
    assert {"symbol_name", "index_group", "index_offset", "data_size", "ads_data_type"} <= {
        param.key for param in get_signal_params("BECKHOFF_ADS", "ADS_READ_WRITE")
    }
    assert {
        "symbol_name",
        "index_group",
        "index_offset",
        "data_size",
        "ads_data_type",
        "notification_mode",
        "cycle_time_ms",
        "max_delay_ms",
    } <= {param.key for param in get_signal_params("BECKHOFF_ADS", "ADS_NOTIFICATION")}


def test_endpoint_comments_explain_protocol_fill_rules() -> None:
    """CommunicationEndpoint 列注释应包含新增协议与填写指引."""

    mapper = inspect(CommunicationEndpoint)
    columns = {column.name: column.comment or "" for column in mapper.columns}
    assert "BECKHOFF_ADS" in columns["application_protocol"]
    assert "推荐组合" in columns["service_type"]
    assert "推荐组合" in columns["transport"]
    assert "串口设备、网卡等正式参数写入参数值表" in columns["host"]
    assert "AMS Port" in columns["port"]
    assert "主要用于 OPC_UA" in columns["namespace_uri"]
    assert "认证方式摘要" in columns["auth_type"]
    assert "正式参数" in columns["service_capabilities_json"]


def test_protocol_param_model_docstrings_explain_table_purpose() -> None:
    """参数模型 docstring 必须明确值表用途与禁止事项."""

    assert "metadata_json" in (ScadaProtocolParamDef.__doc__ or "")
    assert "ScadaEndpointParamValue" in (ScadaProtocolParamDef.__doc__ or "")
    assert "scada_signal_profile_item" in (ScadaSignalParamDef.__doc__ or "")
    assert "共享点表" in (ScadaSignalParamDef.__doc__ or "")
    assert "第一范式" in (ScadaEndpointParamValue.__doc__ or "")
    assert "第一范式" in (ScadaSignalProfileItemParamValue.__doc__ or "")


def test_protocol_param_values_can_be_inserted_and_queried() -> None:
    """端点参数值与点位参数值必须能按定义落库和查询."""

    engine = _make_engine()
    _init_tables(engine)
    with Session(engine) as session:
        endpoint, item = _create_minimal_scada_context(session)

        endpoint_def = ScadaProtocolParamDef(
            application_protocol="OPC_UA",
            service_type="READ",
            transport="TCP",
            param_key="session_name",
            param_name="会话名称",
            data_type="STRING",
        )
        signal_def = ScadaSignalParamDef(
            application_protocol="OPC_UA",
            service_type="READ",
            param_key="node_id",
            param_name="NodeId",
            data_type="STRING",
        )
        session.add_all([endpoint_def, signal_def])
        session.flush()

        session.add(
            ScadaEndpointParamValue(
                endpoint_id=endpoint.endpoint_id,
                param_def_id=endpoint_def.param_def_id,
                value_text="whale-opcua-test",
            )
        )
        session.add(
            ScadaSignalProfileItemParamValue(
                profile_item_id=item.profile_item_id,
                param_def_id=signal_def.param_def_id,
                value_text="ns=2;s=WTG_TEST_001/MMXU1.TotW.mag.f",
            )
        )
        session.commit()

        stored_endpoint_value = session.query(ScadaEndpointParamValue).one()
        stored_signal_value = session.query(ScadaSignalProfileItemParamValue).one()
        assert stored_endpoint_value.value_text == "whale-opcua-test"
        assert stored_signal_value.value_text == "ns=2;s=WTG_TEST_001/MMXU1.TotW.mag.f"
