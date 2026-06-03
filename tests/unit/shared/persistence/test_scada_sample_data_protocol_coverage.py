"""SCADA 多协议样例数据覆盖单测.

证据等级：L1 unit/mock。
这些测试只验证样例数据装配逻辑、共享点表与参数值落库，不证明真实设备、
真实协议驱动或现场连通性。
"""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from whale.shared.persistence import Base
from whale.shared.persistence.orm import CommunicationEndpoint, ScadaEndpointParamValue, ScadaSignalProfileItemParamValue, SignalProfile
from whale.shared.persistence.template.sample_data import (
    PROTOCOL_SAMPLE_SPECS,
    _create_acquisition_tasks,
    _create_asset_types_and_models,
    _create_cdc_fc,
    _create_data_types,
    _create_org,
    _create_protocol_samples,
    _create_signal_profile,
    _seed_protocol_param_defs,
)


def _make_engine() -> Engine:
    """创建用于样例数据单测的内存数据库."""

    return create_engine("sqlite:///:memory:")


def _build_sample_dataset(session: Session) -> None:
    """按样例模块内部步骤装配共享点表和多协议端点."""

    org = _create_org(session)
    data_types = _create_data_types(session)
    wtg_type, model = _create_asset_types_and_models(session)
    _create_cdc_fc(session)
    session.flush()

    profile, profile_items = _create_signal_profile(session, wtg_type, data_types)
    endpoint_defs, signal_defs = _seed_protocol_param_defs(session)
    session.flush()

    ld_instances = _create_protocol_samples(
        session,
        org=org,
        wtg_type=wtg_type,
        model=model,
        profile=profile,
        profile_items=profile_items[:3],
        endpoint_param_defs=endpoint_defs,
        signal_param_defs=signal_defs,
    )
    session.flush()
    _create_acquisition_tasks(session, ld_instances)
    session.commit()


def test_sample_data_reuses_one_signal_profile_across_16_protocol_endpoints() -> None:
    """样例数据应复用同一套点表并覆盖 16 组协议服务端点."""

    engine = _make_engine()
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        _build_sample_dataset(session)

        profiles = session.query(SignalProfile).all()
        endpoints = session.query(CommunicationEndpoint).all()
        profile_ids = {
            row[0]
            for row in session.execute(text("SELECT DISTINCT signal_profile_id FROM scada_ld_instance")).all()
        }
        task_count = session.execute(text("SELECT COUNT(*) FROM acq_task")).scalar_one()

        assert len(profiles) == 1
        assert len(endpoints) == len(PROTOCOL_SAMPLE_SPECS) == 16
        assert len(profile_ids) == 1
        assert task_count == len(PROTOCOL_SAMPLE_SPECS)
        assert sum(1 for spec in PROTOCOL_SAMPLE_SPECS if spec.application_protocol == "OPC_UA") == 2
        assert any(spec.service_type == "ADS_READ_WRITE" for spec in PROTOCOL_SAMPLE_SPECS)
        assert any(spec.service_type == "ADS_NOTIFICATION" for spec in PROTOCOL_SAMPLE_SPECS)
        assert any(spec.service_type == "SPONTANEOUS" and spec.application_protocol == "IEC101" for spec in PROTOCOL_SAMPLE_SPECS)
        assert any(spec.service_type == "SPONTANEOUS" and spec.application_protocol == "IEC104" for spec in PROTOCOL_SAMPLE_SPECS)
        assert {endpoint.application_protocol for endpoint in endpoints} == {
            "OPC_UA",
            "MODBUS",
            "IEC101",
            "IEC104",
            "IEC61850",
            "MQTT",
            "HTTP_REST",
            "BECKHOFF_ADS",
        }


def test_sample_data_writes_queryable_endpoint_and_signal_param_values() -> None:
    """样例数据必须把端点参数值和点位参数值写入第一范式表."""

    engine = _make_engine()
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        _build_sample_dataset(session)

        endpoint_param_count = session.query(ScadaEndpointParamValue).count()
        signal_param_count = session.query(ScadaSignalProfileItemParamValue).count()
        mqtt_topic_prefix = session.execute(
            text(
                """
                SELECT epv.value_text
                FROM scada_endpoint_param_value AS epv
                JOIN scada_protocol_param_def AS def
                    ON def.param_def_id = epv.param_def_id
                JOIN scada_communication_endpoint AS ep
                    ON ep.endpoint_id = epv.endpoint_id
                WHERE ep.application_protocol = 'MQTT'
                  AND def.param_key = 'topic_prefix'
                """
            )
        ).scalar_one()
        ads_symbol_names = session.execute(
            text(
                """
                SELECT DISTINCT spv.value_text
                FROM scada_signal_profile_item_param_value AS spv
                JOIN scada_signal_param_def AS def
                    ON def.param_def_id = spv.param_def_id
                WHERE def.application_protocol = 'BECKHOFF_ADS'
                  AND def.param_key = 'symbol_name'
                """
            )
        ).scalars().all()
        mapped_profile_item_count = session.execute(
            text(
                """
                SELECT COUNT(DISTINCT spv.profile_item_id)
                FROM scada_signal_profile_item_param_value AS spv
                JOIN scada_signal_param_def AS def
                    ON def.param_def_id = spv.param_def_id
                WHERE def.application_protocol = 'OPC_UA'
                  AND def.service_type = 'READ'
                """
            )
        ).scalar_one()

        assert endpoint_param_count > len(PROTOCOL_SAMPLE_SPECS)
        assert signal_param_count >= len(PROTOCOL_SAMPLE_SPECS) * 3
        assert mqtt_topic_prefix == "whale/wtg/001"
        assert ads_symbol_names == [
            "MAIN.WTG_ADS_001.ActivePower",
            "MAIN.WTG_ADS_SUB_001.ActivePower",
        ]
        assert mapped_profile_item_count == 3


def test_sample_data_creates_acquisition_tasks_matching_service_semantics() -> None:
    """采集任务模式必须与 service_type 语义一致，且每个 LD 都有任务."""

    engine = _make_engine()
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        _build_sample_dataset(session)

        mode_rows = session.execute(
            text(
                """
                SELECT ep.application_protocol, ep.service_type, task.acquisition_mode
                FROM acq_task AS task
                JOIN scada_ld_instance AS ld
                    ON ld.ld_instance_id = task.ld_instance_id
                JOIN scada_communication_endpoint AS ep
                    ON ep.endpoint_id = ld.endpoint_id
                ORDER BY ep.application_protocol, ep.service_type
                """
            )
        ).fetchall()

        assert len(mode_rows) == len(PROTOCOL_SAMPLE_SPECS)
        mode_map = {(row.application_protocol, row.service_type): row.acquisition_mode for row in mode_rows}
        assert mode_map[("OPC_UA", "READ")] == "POLLING"
        assert mode_map[("OPC_UA", "SUBSCRIBE")] == "SUBSCRIBE"
        assert mode_map[("IEC101", "INTERROGATION")] == "POLLING"
        assert mode_map[("IEC101", "SPONTANEOUS")] == "SUBSCRIBE"
        assert mode_map[("IEC104", "INTERROGATION")] == "POLLING"
        assert mode_map[("IEC104", "SPONTANEOUS")] == "SUBSCRIBE"
        assert mode_map[("IEC61850", "REPORT")] == "REPORT"
        assert mode_map[("IEC61850", "GOOSE")] == "SUBSCRIBE"
        assert mode_map[("IEC61850", "SV")] == "SUBSCRIBE"
        assert mode_map[("BECKHOFF_ADS", "ADS_READ_WRITE")] == "POLLING"
        assert mode_map[("BECKHOFF_ADS", "ADS_NOTIFICATION")] == "SUBSCRIBE"
