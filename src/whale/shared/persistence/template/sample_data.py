"""全套风电场样本数据生成脚本 — GB/T 30966.2 全量测点覆盖.

Usage: python -m whale.shared.persistence.template.sample_data
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from whale.shared.persistence.orm import (
    AcquisitionTask,
    AssetInstance,
    AssetModel,
    AssetType,
    CDCDict,
    CommunicationEndpoint,
    FCDict,
    IED,
    LDInstance,
    Organization,
    ScadaDataType,
    SignalProfile,
    SignalProfileItem,
)
from whale.shared.persistence.session import session_scope

TURBINE_COUNT = 10


def generate_all_sample_data() -> None:
    with session_scope() as session:
        print("=" * 60)
        print("  张北风电场 GB/T 30966.2 样本数据生成")
        print("=" * 60)

        org = _create_org(session)
        session.flush()
        print("✓ 组织")

        data_types = _create_data_types(session)
        session.flush()
        print(f"✓ 数据类型: {len(data_types)} 种")

        wtg_type, model = _create_asset_types_and_models(session)
        session.flush()
        print("✓ 资产类型 + 型号")

        turbines = _create_turbines(session, wtg_type, model, org)
        session.flush()
        print(f"✓ 资产实例: {len(turbines)} 台风机")

        _create_cdc_fc(session)
        session.flush()
        print("✓ CDC/FC 字典")

        profile = _create_signal_profile(session, wtg_type, data_types)
        session.flush()
        print(f"✓ 点位方案: {len(profile.items)} 个采集点")

        ieds = _create_ieds(session, turbines, profile)
        session.flush()
        print(f"✓ IED + Endpoint + LD: {len(ieds)} 套")

        # Collect all LD instances and pass to task creation
        all_lds = [ld for ied in ieds for ep in ied.endpoints for ld in ep.ld_instances]
        tasks = _create_acquisition_tasks(session, all_lds)
        session.flush()
        print(f"✓ 采集任务: {len(tasks)} 个")

        session.commit()
        print("=" * 60)
        print("  样本数据生成完毕")
        print("=" * 60)


# ══════════════════════════════════════════════════════════════════════

def _create_org(session: Session) -> Organization:
    org = Organization(org_name="张北风电场")
    session.add(org)
    return org


def _create_data_types(session: Session) -> dict[str, ScadaDataType]:
    types = {}
    for name, enc, bits, constraint in [
        ("BOOLEAN", "IEC61850_BASIC", 1, "CHECK(value IN (0,1))"),
        ("INT32", "IEC61850_BASIC", 32, "CHECK(value BETWEEN -2147483648 AND 2147483647)"),
        ("INT64", "IEC61850_BASIC", 64, "CHECK(value BETWEEN -9223372036854775808 AND 9223372036854775807)"),
        ("FLOAT32", "IEC61850_BASIC", 32, "CHECK(value BETWEEN -3.4E38 AND 3.4E38)"),
        ("FLOAT64", "IEC61850_BASIC", 64, "CHECK(value BETWEEN -1.7E308 AND 1.7E308)"),
        ("STRING", "IEC61850_BASIC", None, "CHECK(LENGTH(value) <= 255)"),
        ("DATETIME", "IEC61850_BASIC", None, ""),
        ("VisString255", "IEC61850_BASIC", None, "CHECK(LENGTH(value) <= 255)"),
    ]:
        dt = ScadaDataType(type_name=name, encoding=enc, size_bits=bits, constraint_expr=constraint or None)
        types[name] = dt
        session.add(dt)
        types[name] = dt
    return types


def _create_asset_types_and_models(session: Session) -> tuple[AssetType, AssetModel]:
    wtg_type = AssetType(
        type_code="WTG", type_name="风力发电机组",
        category="GENERATION_DEVICE", description="双馈异步风力发电机组",
    )
    session.add(wtg_type)
    session.flush()

    model = AssetModel(
        asset_type_id=wtg_type.asset_type_id,
        model_code="WTG_5MW_GW121", model_name="金风 GW121 5MW",
        manufacturer="Goldwind",
        specifications={"rated_power_kw": 5000, "hub_height_m": 120, "rotor_diameter_m": 190},
    )
    session.add(model)
    return wtg_type, model


def _create_turbines(session: Session, wtg_type: AssetType,
                     model: AssetModel, org: Organization) -> list[AssetInstance]:
    turbines = []
    for i in range(1, TURBINE_COUNT + 1):
        code = f"ZB-WTG-{i:03d}"
        t = AssetInstance(
            asset_code=code, asset_name=f"{i}号风机",
            asset_type_id=wtg_type.asset_type_id,
            model_id=model.model_id,
            org_id=org.org_id,
            location=f"{i}号机位",
            longitude=114.5 + i * 0.01, latitude=41.0 + i * 0.005,
            status="ACTIVE",
        )
        session.add(t)
        turbines.append(t)
    return turbines


def _create_cdc_fc(session: Session) -> None:
    cdc_list = [
        ("MV", "Measured Value", "测量值"),
        ("SPS", "Single Point Status", "单点状态"),
        ("INS", "Integer Status", "整数状态"),
        ("ENS", "Enabled State", "使能状态"),
        ("ACT", "Activation Info", "动作信息"),
        ("ACD", "Directional Protection Activation Info", "方向保护动作信息"),
        ("INC", "Integer Controlled Step Position Info", "整数控制阶位信息"),
        ("BCR", "Binary Counter Reading", "二进制计数器读数"),
        ("ENC", "Enumerated Status", "枚举状态"),
        ("ENG", "Enumerated Status Setting", "枚举状态定值"),
        ("DPL", "Double Point Status", "双点状态"),
        ("DPC", "Double Point Controllable Status", "双点可控状态"),
        ("SPC", "Single Point Controllable Status", "单点可控状态"),
        ("HMV", "Harmonic Value", "谐波值"),
        ("HST", "Harmonic Value Setting", "谐波定值"),
        ("CSD", "Curve Shape Description", "曲线形状描述"),
        ("CST", "Curve Shape Setting", "曲线形状定值"),
        ("ISC", "Integer Status Setting", "整数状态定值"),
        ("LPL", "Logical Node Name Plate", "逻辑节点铭牌"),
        ("LPC", "Logical Node Name Plate Setting", "逻辑节点铭牌定值"),
    ]
    for code, name, desc in cdc_list:
        session.add(CDCDict(cdc_code=code, cdc_name=name, description=desc))
    fc_list = [
        ("ST", "Status", "状态"),
        ("MX", "Measurand", "测量量"),
        ("SP", "Setpoint", "设定值"),
        ("SV", "Substitution Value", "替代值"),
        ("CF", "Configuration", "配置"),
        ("DC", "Description", "描述"),
        ("EX", "Extended Definition", "扩展定义"),
    ]
    for code, name, desc in fc_list:
        session.add(FCDict(fc_code=code, fc_name=name, description=desc))


def _create_signal_profile(session: Session, wtg_type: AssetType,
                           data_types: dict[str, ScadaDataType]) -> SignalProfile:
    from whale.shared.persistence.template.gbt_30966_fields import ALL_LOGICAL_NODES

    profile = SignalProfile(
        profile_code="WTG_GB_T_30966_2_FULL_V1",
        profile_name="风机 GB/T 30966.2 全量采集点位方案 V1",
        asset_type_id=wtg_type.asset_type_id,
        standard_family="GB_T_30966",
        vendor="STANDARD",
        version="1.0",
        description="覆盖 GB/T 30966.2-2022 全部 19 个逻辑节点 / 416 个 DO 测点",
    )
    session.add(profile)
    session.flush()

    for node_def in ALL_LOGICAL_NODES:
        for field in node_def.fields:
            # Resolve data type
            type_name = field.data_type
            dt = data_types.get(type_name)
            if dt is None:
                dt = data_types.get("FLOAT64")

            ln_name = f"{node_def.name}1"
            da = "mag.f"
            if field.cdc in ("SPS", "SPC", "ENS", "ACT", "ACD", "DPL", "DPC"):
                da = "stVal"
            elif field.cdc in ("INS", "INC", "ENC", "ENG", "BCR", "ISC"):
                da = "stVal"
            elif field.cdc in ("CSD", "CST", "LPL", "LPC"):
                da = "stVal"

            fc = "MX"
            if field.cdc in ("SPS", "ENS", "ACT", "ACD", "DPL", "DPC", "SPC"):
                fc = "ST"
            elif field.cdc in ("INS", "INC", "ENC", "ENG", "ISC"):
                fc = "ST"
            elif field.cdc in ("CSD", "CST", "LPL", "LPC", "BCR"):
                fc = "CF"

            constraint = None
            if field.unit in ("kW", "kWh", "kVAr", "kVArh", "A", "V"):
                constraint = ">= 0"
            elif field.unit in ("Hz",):
                constraint = "BETWEEN 45 AND 55"
            elif field.unit in ("deg C",):
                constraint = "BETWEEN -40 AND 80"
            elif field.unit in ("m/s",):
                constraint = "BETWEEN 0 AND 75"
            elif field.unit in ("deg",):
                constraint = "BETWEEN 0 AND 360"
            elif field.unit in ("%",):
                constraint = "BETWEEN 0 AND 100"

            item = SignalProfileItem(
                signal_profile_id=profile.signal_profile_id,
                ln_class=node_def.name, ln_name=ln_name,
                do_name=field.key, da_name=da,
                relative_path=f"{ln_name}.{field.key}.{da}",
                fc=fc, cdc=field.cdc,
                data_type_id=dt.data_type_id,
                default_unit=field.unit if field.unit else None,
                display_name=field.desc,
                default_sample_mode="SUBSCRIPTION",
                default_sample_interval_ms=100,
                default_constraint_expr=constraint,
                quality_supported=True,
                timestamp_supported=True,
                description=f"{node_def.desc} — {field.desc}",
            )
            session.add(item)

    return profile


def _create_ieds(session: Session, turbines: list[AssetInstance],
                 profile: SignalProfile) -> list[IED]:
    ieds = []
    for i, t in enumerate(turbines):
        ied = IED(
            asset_instance_id=t.asset_instance_id,
            ied_name=f"IED_{t.asset_code}",
            ied_code=f"{t.asset_code}_CTRL_IED",
            ied_type="WTG_CONTROLLER",
            standard_family="IEC61400_25",
        )
        session.add(ied)
        session.flush()

        endpoint = CommunicationEndpoint(
            ied_id=ied.ied_id,
            access_point_name="OPCUA_AP",
            endpoint_name=f"{t.asset_code} OPC UA 端点",
            application_protocol="OPC_UA",
            transport="TCP",
            host="127.0.0.1", port=40001 + i,
            namespace_uri="urn:windfarm:2wtg",
            security_policy="None", security_mode="None",
        )
        session.add(endpoint)
        session.flush()

        ld = LDInstance(
            endpoint_id=endpoint.endpoint_id,
            asset_instance_id=t.asset_instance_id,
            signal_profile_id=profile.signal_profile_id,
            ld_name=t.asset_code,
            ld_type="WIND_TURBINE",
            path_prefix=t.asset_code,
        )
        session.add(ld)
        ieds.append(ied)

    return ieds


def _create_acquisition_tasks(
    session: Session,
    ld_instances: list[LDInstance],
) -> list[AcquisitionTask]:
    tasks = []
    for ld in ld_instances:
        asset = session.get(AssetInstance, ld.asset_instance_id)
        if asset is None:
            raise LookupError(
                f"AssetInstance `{ld.asset_instance_id}` not found for LD `{ld.ld_name}`."
            )

    task = AcquisitionTask(
        task_name=f"task_{asset.asset_code}",
        ld_instance_id=ld.ld_instance_id,
        acquisition_mode="SUBSCRIBE",
        poll_interval_ms=100,
        request_timeout_ms=500,
        freshness_timeout_ms=30000,
        alive_timeout_ms=60000,

        polling_max_concurrent_connections=4,
        polling_connection_start_interval_ms=25,

        subscription_start_interval_ms=25,
        subscription_notification_queue_size=4096,
        subscription_notification_max_lag_ms=200,

        protocol_params={},
    )
    session.add(task)
    tasks.append(task)

    return tasks


if __name__ == "__main__":
    from whale.shared.persistence.init_db import init_db as _init_db
    _init_db(force=True)
    generate_all_sample_data()
