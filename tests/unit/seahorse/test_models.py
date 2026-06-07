"""seahorse 核心模型序列化与确定性种子测试。

验证：
1. 所有核心模型 dataclass 可正常实例化。
2. ScenarioConfig 的 deterministic_seed 可正确保存和读取。
3. 模型序列化/反序列化一致性。
4. 模型字段默认值符合预期。

测试阶段：开发期验证 (P1)。
不能证明：模型与实际 ORM/数据库 schema 兼容性。
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from seahorse.models.scenario import ScenarioConfig, ScenarioMetadata
from seahorse.models.plan import (
    AcquisitionTaskPlan,
    EndpointPlan,
    SeedEntity,
    SeedPlan,
    ServerEndpointPlan,
    ServerPlan,
    ServerPointPlan,
    SignalProfileItemPlan,
    SignalProfilePlan,
)
from seahorse.models.generation import (
    GeneratedAlarmEvent,
    GeneratedControlResult,
    GeneratedSignalValue,
)


# ── ScenarioConfig ────────────────────────────────────────────────────────────


def test_scenario_config_defaults() -> None:
    """ScenarioConfig 默认值符合预期。"""
    cfg = ScenarioConfig(scenario_id="test_001")
    assert cfg.scenario_id == "test_001"
    assert cfg.name == ""
    assert cfg.deterministic_seed == 42
    assert cfg.duration_seconds == 3600.0
    assert cfg.sample_interval_ms == 100
    assert cfg.asset_count == 1
    assert cfg.protocol_targets == []


def test_scenario_config_deterministic_seed_preserved() -> None:
    """deterministic_seed 应正确保存。"""
    cfg = ScenarioConfig(scenario_id="seed_test", deterministic_seed=12345)
    assert cfg.deterministic_seed == 12345


def test_scenario_config_to_dict_roundtrip() -> None:
    """ScenarioConfig dataclass 可序列化为 dict 并包含所有字段。"""
    cfg = ScenarioConfig(
        scenario_id="roundtrip_001",
        name="测试场景",
        deterministic_seed=999,
        protocol_targets=["OPC_UA", "MODBUS"],
    )
    d = asdict(cfg)
    assert d["scenario_id"] == "roundtrip_001"
    assert d["name"] == "测试场景"
    assert d["deterministic_seed"] == 999
    assert d["protocol_targets"] == ["OPC_UA", "MODBUS"]


# ── ScenarioMetadata ──────────────────────────────────────────────────────────


def test_scenario_metadata_creation() -> None:
    """ScenarioMetadata 可正常创建。"""
    now = datetime.now(timezone.utc)
    meta = ScenarioMetadata(
        scenario_id="meta_001",
        generated_at=now,
        stats={"signal_count": 150, "alarm_count": 3},
    )
    assert meta.scenario_id == "meta_001"
    assert meta.seahorse_version == "0.1.0"
    assert meta.stats["signal_count"] == 150
    assert meta.stats["alarm_count"] == 3


# ── SeedPlan & sub-models ─────────────────────────────────────────────────────


def test_seed_entity_creation() -> None:
    """SeedEntity 可正常创建。"""
    entity = SeedEntity(entity_id="e001", entity_type="WTG", display_name="风机 01")
    assert entity.entity_id == "e001"
    assert entity.entity_type == "WTG"
    assert entity.parent_entity_id is None


def test_seed_plan_minimal() -> None:
    """SeedPlan 最小实例化正常（空列表）。"""
    plan = SeedPlan(plan_id="plan_001", scenario_id="sc_001")
    assert plan.plan_id == "plan_001"
    assert plan.scenario_id == "sc_001"
    assert plan.entities == []
    assert plan.signal_profiles == []
    assert plan.endpoints == []
    assert plan.acquisition_tasks == []


def test_seed_plan_with_all_sub_models() -> None:
    """SeedPlan 包含全部子模型时结构完整。"""
    entities = [SeedEntity(entity_id="e001")]
    profiles = [
        SignalProfilePlan(
            profile_id="p001",
            profile_name="点表",
            items=[SignalProfileItemPlan(signal_id="s001", signal_name="ActivePower", unit="kW")],
        )
    ]
    endpoints = [EndpointPlan(endpoint_id="ep001", application_protocol="OPC_UA")]
    tasks = [AcquisitionTaskPlan(task_id="t001", associated_endpoint_id="ep001", associated_profile_id="p001")]

    plan = SeedPlan(
        plan_id="full_plan",
        scenario_id="sc_001",
        entities=entities,
        signal_profiles=profiles,
        endpoints=endpoints,
        acquisition_tasks=tasks,
    )
    assert len(plan.entities) == 1
    assert len(plan.signal_profiles) == 1
    assert len(plan.signal_profiles[0].items) == 1
    assert plan.signal_profiles[0].items[0].signal_name == "ActivePower"
    assert plan.endpoints[0].application_protocol == "OPC_UA"
    assert plan.acquisition_tasks[0].acquisition_mode == "POLLING"


def test_signal_profile_item_plan_defaults() -> None:
    """SignalProfileItemPlan 默认值正确。"""
    item = SignalProfileItemPlan(signal_id="s001")
    assert item.signal_id == "s001"
    assert item.signal_name == ""
    assert item.unit == ""
    assert item.data_type == "FLOAT64"
    assert item.cdc == "MV"
    assert item.sample_interval_ms == 100
    assert item.generation_hint == "RANDOM"


def test_endpoint_plan_params() -> None:
    """EndpointPlan 端点参数可正常存储。"""
    ep = EndpointPlan(
        endpoint_id="ep_mqtt",
        application_protocol="MQTT",
        service_type="SUBSCRIBE",
        transport="MQTT",
        host="broker.local",
        port=1883,
        endpoint_params={"qos": 1, "topic_prefix": "whale/wtg"},
    )
    assert ep.endpoint_params["qos"] == 1
    assert ep.endpoint_params["topic_prefix"] == "whale/wtg"


# ── ServerPlan & sub-models ───────────────────────────────────────────────────


def test_server_plan_minimal() -> None:
    """ServerPlan 最小实例化正常。"""
    plan = ServerPlan(server_id="srv_001", scenario_id="sc_001")
    assert plan.server_id == "srv_001"
    assert plan.server_name == ""
    assert plan.endpoints == []
    assert plan.points == []


def test_server_endpoint_plan() -> None:
    """ServerEndpointPlan 可正常创建。"""
    ep = ServerEndpointPlan(endpoint_name="OPC_UA_SRV", protocol="OPC_UA", bind_port=4840)
    assert ep.endpoint_name == "OPC_UA_SRV"
    assert ep.protocol == "OPC_UA"
    assert ep.bind_host == "0.0.0.0"
    assert ep.bind_port == 4840


def test_server_point_plan() -> None:
    """ServerPointPlan 可正常创建。"""
    pt = ServerPointPlan(
        point_id="pt_001",
        point_name="ActivePower",
        access_mode="RO",
        associated_signal_id="sig_001",
    )
    assert pt.point_id == "pt_001"
    assert pt.access_mode == "RO"
    assert pt.data_type == "FLOAT64"


# ── Generation results ────────────────────────────────────────────────────────


def test_generated_signal_value() -> None:
    """GeneratedSignalValue 可正常创建。"""
    now = datetime.now(timezone.utc)
    sv = GeneratedSignalValue(signal_id="sig_001", timestamp=now, value=1500.5, quality=0, unit="kW")
    assert sv.signal_id == "sig_001"
    assert sv.value == 1500.5
    assert sv.quality == 0
    assert sv.unit == "kW"
    assert sv.timestamp == now


def test_generated_signal_value_backward_compatible() -> None:
    """GeneratedSignalValue 新增字段应向后兼容（旧构造代码不传新字段也不报错）。"""
    sv = GeneratedSignalValue(signal_id="sig_001")
    assert sv.signal_id == "sig_001"
    assert sv.scenario_id == ""
    assert sv.source_id == ""
    assert sv.device_id == ""
    assert sv.profile_item_id == ""
    assert sv.node_key == ""
    assert sv.variable_key == ""
    assert sv.strategy_id == ""
    assert sv.synthetic is True


def test_generated_signal_value_new_fields() -> None:
    """GeneratedSignalValue 新字段可正常赋值和读取。"""
    sv = GeneratedSignalValue(
        signal_id="sig_full",
        scenario_id="sc_001",
        source_id="OPC_UA",
        device_id="wtg_01",
        profile_item_id="pi_001",
        node_key="WTUR",
        variable_key="ActivePower",
        value=1500.0,
        quality=0,
        unit="kW",
        strategy_id="random_gen",
        synthetic=True,
    )
    assert sv.scenario_id == "sc_001"
    assert sv.source_id == "OPC_UA"
    assert sv.device_id == "wtg_01"
    assert sv.profile_item_id == "pi_001"
    assert sv.node_key == "WTUR"
    assert sv.variable_key == "ActivePower"
    assert sv.strategy_id == "random_gen"
    assert sv.synthetic is True


def test_generated_alarm_event() -> None:
    """GeneratedAlarmEvent 可正常创建。"""
    now = datetime.now(timezone.utc)
    alarm = GeneratedAlarmEvent(
        alarm_id="alarm_001",
        entity_id="e001",
        alarm_type="OVERVOLTAGE",
        severity="CRITICAL",
        timestamp=now,
        message="电压超限",
    )
    assert alarm.alarm_id == "alarm_001"
    assert alarm.severity == "CRITICAL"
    assert alarm.cleared_at is None


def test_generated_control_result() -> None:
    """GeneratedControlResult 可正常创建。"""
    now = datetime.now(timezone.utc)
    ctrl = GeneratedControlResult(
        control_id="ctrl_001",
        entity_id="e001",
        control_type="SETPOINT",
        target_value=100.0,
        result_value=99.5,
        status="SUCCESS",
        timestamp=now,
    )
    assert ctrl.control_id == "ctrl_001"
    assert ctrl.target_value == 100.0
    assert ctrl.result_value == 99.5
    assert ctrl.status == "SUCCESS"


# ── Serialization ─────────────────────────────────────────────────────────────


def test_models_serialize_to_json_safe() -> None:
    """所有核心模型应可序列化为 JSON 安全格式（通过 asdict）。"""
    import json as json_mod

    cfg = ScenarioConfig(scenario_id="json_test", deterministic_seed=42)
    plan = SeedPlan(plan_id="p001", scenario_id="json_test", entities=[SeedEntity(entity_id="e001")])

    cfg_dict = asdict(cfg)
    plan_dict = asdict(plan)

    json_mod.dumps(cfg_dict, default=str)
    json_mod.dumps(plan_dict, default=str)


def test_models_import_boundary_no_ingest() -> None:
    """核心模型模块不得 import whale.ingest。"""
    import ast
    from pathlib import Path

    models_root = Path(__file__).resolve().parents[3] / "src" / "seahorse" / "models"
    offenders = []
    for fp in models_root.rglob("*.py"):
        tree = ast.parse(fp.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("whale.ingest"):
                    offenders.append(str(fp))
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("whale.ingest"):
                        offenders.append(str(fp))
    assert offenders == [], f"seahorse models import whale.ingest: {offenders}"
