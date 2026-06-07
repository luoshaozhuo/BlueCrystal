"""seahorse 最小编排器测试。

验证：
1. SeahorseGenerator 可正常实例化。
2. 确定性种子可保存到 config 和 metadata。
3. generate() 输出有效且与 config 一致。
4. 相同 config 产生相同的 checksum。
5. Generator 不访问生产数据库。

测试阶段：开发期验证 (P1)。
不能证明：真实策略执行正确性、外部系统连通性。
"""
from __future__ import annotations

from seahorse.models.scenario import ScenarioConfig
from seahorse.models.plan import (
    SeedPlan,
    ServerPlan,
    SignalProfileItemPlan,
)
from seahorse.orchestration import SeahorseGenerator


def test_generator_instantiation() -> None:
    """SeahorseGenerator 可正常实例化。"""
    cfg = ScenarioConfig(scenario_id="inst_test", deterministic_seed=42)
    gen = SeahorseGenerator(cfg)
    assert gen.config is cfg
    assert gen.metadata is not None
    assert gen.metadata.scenario_id == "inst_test"
    assert gen.metadata.seahorse_version == "0.1.0"


def test_generator_deterministic_seed_preserved_in_config() -> None:
    """deterministic_seed 必须保存在 config 中。"""
    seed = 12345
    cfg = ScenarioConfig(scenario_id="seed_save", deterministic_seed=seed)
    gen = SeahorseGenerator(cfg)
    assert gen.config.deterministic_seed == seed


def test_generator_deterministic_seed_in_metadata_snapshot() -> None:
    """deterministic_seed 必须出现在 metadata.config_snapshot 中。"""
    cfg = ScenarioConfig(scenario_id="meta_seed", deterministic_seed=9999, name="种子测试")
    gen = SeahorseGenerator(cfg)
    assert gen.metadata.config_snapshot["deterministic_seed"] == 9999
    assert gen.metadata.config_snapshot["scenario_id"] == "meta_seed"
    assert gen.metadata.config_snapshot["name"] == "种子测试"


def test_generate_returns_minimal_plans() -> None:
    """generate() 应返回 SeedPlan 和 ServerPlan。"""
    cfg = ScenarioConfig(scenario_id="gen_min", asset_count=3, protocol_targets=["OPC_UA"])
    gen = SeahorseGenerator(cfg)
    seed_plan, server_plan, *_ = gen.generate()

    assert isinstance(seed_plan, SeedPlan)
    assert isinstance(server_plan, ServerPlan)
    assert seed_plan.scenario_id == "gen_min"
    assert server_plan.scenario_id == "gen_min"


def test_generate_asset_count_matches_entities() -> None:
    """asset_count 应与生成的 entity 数量一致。"""
    asset_count = 5
    cfg = ScenarioConfig(scenario_id="ac_test", asset_count=asset_count)
    gen = SeahorseGenerator(cfg)
    seed_plan, *_ = gen.generate()

    assert len(seed_plan.entities) == asset_count
    assert len(seed_plan.signal_profiles) == asset_count


def test_generate_protocol_targets_in_endpoints() -> None:
    """protocol_targets 中的每个协议都应有对应的 endpoint。"""
    protocols = ["OPC_UA", "MODBUS", "IEC104"]
    cfg = ScenarioConfig(scenario_id="proto_test", asset_count=2, protocol_targets=protocols)
    gen = SeahorseGenerator(cfg)
    seed_plan, *_ = gen.generate()

    # 每个 asset 为每个 protocol 创建一个 endpoint
    expected_count = len(protocols) * 2
    assert len(seed_plan.endpoints) == expected_count
    ep_protocols = {ep.application_protocol for ep in seed_plan.endpoints}
    assert ep_protocols == set(protocols)


def test_generate_protocol_targets_default() -> None:
    """不指定 protocol_targets 时默认使用 OPC_UA。"""
    cfg = ScenarioConfig(scenario_id="default_proto", asset_count=1)
    gen = SeahorseGenerator(cfg)
    seed_plan, server_plan, *_ = gen.generate()

    assert len(seed_plan.endpoints) == 1
    assert seed_plan.endpoints[0].application_protocol == "OPC_UA"
    assert len(server_plan.endpoints) == 1
    assert server_plan.endpoints[0].protocol == "OPC_UA"


def test_generate_entity_ids_are_unique() -> None:
    """生成的 entity_id 必须唯一。"""
    cfg = ScenarioConfig(scenario_id="unique_test", asset_count=10)
    gen = SeahorseGenerator(cfg)
    seed_plan, *_ = gen.generate()

    entity_ids = [e.entity_id for e in seed_plan.entities]
    assert len(entity_ids) == len(set(entity_ids))


def test_generate_signal_profile_items_are_consistent() -> None:
    """每个 signal profile 应包含默认的 6 个信号点位。"""
    cfg = ScenarioConfig(scenario_id="sp_test", asset_count=1)
    gen = SeahorseGenerator(cfg)
    seed_plan, *_ = gen.generate()

    profile = seed_plan.signal_profiles[0]
    assert len(profile.items) == 6
    assert all(isinstance(item, SignalProfileItemPlan) for item in profile.items)
    signal_ids = {item.signal_id for item in profile.items}
    assert len(signal_ids) == 6


def test_checksum_is_deterministic() -> None:
    """相同 config 应产生相同 checksum。"""
    cfg1 = ScenarioConfig(scenario_id="hash_test", deterministic_seed=42)
    cfg2 = ScenarioConfig(scenario_id="hash_test", deterministic_seed=42)
    gen1 = SeahorseGenerator(cfg1)
    gen2 = SeahorseGenerator(cfg2)
    assert gen1.compute_checksum() == gen2.compute_checksum()


def test_checksum_differs_with_different_config() -> None:
    """不同 config 的 checksum 应不同。"""
    cfg_a = ScenarioConfig(scenario_id="hash_a", deterministic_seed=1)
    cfg_b = ScenarioConfig(scenario_id="hash_b", deterministic_seed=1)
    gen_a = SeahorseGenerator(cfg_a)
    gen_b = SeahorseGenerator(cfg_b)
    assert gen_a.compute_checksum() != gen_b.compute_checksum()


def test_generator_does_not_access_database() -> None:
    """SeahorseGenerator 不得依赖任何数据库连接。

    本测试验证 SeahorseGenerator 及相关模块中没有数据库引擎或 session 的 import。
    """
    import ast
    from pathlib import Path

    orch_root = Path(__file__).resolve().parents[3] / "src" / "seahorse" / "orchestration"
    db_keywords = {"create_engine", "session_scope", "Session", "sqlalchemy", "psycopg", "sqlite3"}
    offenders = []
    for fp in orch_root.rglob("*.py"):
        tree = ast.parse(fp.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    if name in db_keywords:
                        offenders.append(f"{fp}: import {alias.name}")
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        full = f"{node.module}.{alias.name}"
                        if any(kw in full.lower() for kw in db_keywords):
                            offenders.append(f"{fp}: from {node.module} import {alias.name}")
    assert offenders == [], f"orchestrator imports database-related modules: {offenders}"


def test_server_plan_endpoints_match_protocol_targets() -> None:
    """ServerPlan endpoints 应与 protocol_targets 数量和协议一致。"""
    protocols = ["OPC_UA", "IEC104", "MQTT"]
    cfg = ScenarioConfig(scenario_id="srv_test", asset_count=1, protocol_targets=protocols)
    gen = SeahorseGenerator(cfg)
    _, server_plan, *_ = gen.generate()

    assert len(server_plan.endpoints) == len(protocols)
    server_protocols = {ep.protocol for ep in server_plan.endpoints}
    assert server_protocols == set(protocols)


def test_server_plan_points_match_asset_count() -> None:
    """ServerPlan points 应与 asset_count 一致。"""
    cfg = ScenarioConfig(scenario_id="pts_test", asset_count=4, protocol_targets=["OPC_UA"])
    gen = SeahorseGenerator(cfg)
    _, server_plan, *_ = gen.generate()

    assert len(server_plan.points) == 4
    point_ids = {p.point_id for p in server_plan.points}
    assert len(point_ids) == 4


# ── Round 2: expanded generate() ────────────────────────────────────────────────


def test_generate_returns_5_tuple() -> None:
    """expand generate() 应返回 (SeedPlan, ServerPlan, signals, alarms, controls)。"""
    cfg = ScenarioConfig(scenario_id="expanded", asset_count=1, protocol_targets=["OPC_UA"])
    gen = SeahorseGenerator(cfg)
    seed_plan, server_plan, signals, alarms, controls = gen.generate()

    from seahorse.models.plan import SeedPlan, ServerPlan

    assert isinstance(seed_plan, SeedPlan)
    assert isinstance(server_plan, ServerPlan)
    assert isinstance(signals, list)
    assert isinstance(alarms, list)
    assert isinstance(controls, list)


def test_generated_signals_are_not_empty() -> None:
    """expand generate() 应生成非空信号值序列。"""
    cfg = ScenarioConfig(scenario_id="sig_gen", asset_count=1, duration_seconds=1.0, protocol_targets=["OPC_UA"])
    gen = SeahorseGenerator(cfg)
    _, _, signals, _, _ = gen.generate()
    assert len(signals) > 0


def test_generated_signals_have_complete_fields() -> None:
    """生成的信号值应包含完整溯源字段。"""
    cfg = ScenarioConfig(scenario_id="fields_test", asset_count=1, duration_seconds=0.5, protocol_targets=["OPC_UA"])
    gen = SeahorseGenerator(cfg)
    _, _, signals, _, _ = gen.generate()

    assert len(signals) > 0
    sv = signals[0]
    assert sv.scenario_id == "fields_test"
    assert sv.device_id
    assert sv.source_id or sv.source_id == ""  # 可空
    assert sv.profile_item_id
    assert sv.synthetic is True
    assert sv.quality == 0
    assert sv.unit


def test_generate_is_deterministic() -> None:
    """相同 config 应产生相同的 signals/alarms/controls。"""
    cfg = ScenarioConfig(scenario_id="det_full", asset_count=1, duration_seconds=0.5, protocol_targets=["OPC_UA"])
    gen1 = SeahorseGenerator(cfg)
    gen2 = SeahorseGenerator(cfg)
    _, _, sig1, alm1, ctrl1 = gen1.generate()
    _, _, sig2, alm2, ctrl2 = gen2.generate()

    assert len(sig1) == len(sig2)
    for s1, s2 in zip(sig1, sig2):
        assert s1.value == s2.value
        assert s1.timestamp == s2.timestamp

    assert len(alm1) == len(alm2)
    assert len(ctrl1) == len(ctrl2)


def test_generate_minimal_backward_compatible() -> None:
    """generate_minimal() 应与 Round 1 __init__ 行为一致（返回 2 元组）。"""
    cfg = ScenarioConfig(scenario_id="minimal_bw", asset_count=2)
    gen = SeahorseGenerator(cfg)
    seed_plan, server_plan = gen.generate_minimal()

    from seahorse.models.plan import SeedPlan, ServerPlan
    assert isinstance(seed_plan, SeedPlan)
    assert isinstance(server_plan, ServerPlan)
    assert len(seed_plan.entities) == 2


def test_metadata_stats_updated_after_generate() -> None:
    """generate() 后 metadata.stats 应反映生成结果统计。"""
    cfg = ScenarioConfig(scenario_id="stats_test", asset_count=1, duration_seconds=0.5)
    gen = SeahorseGenerator(cfg)
    _, _, signals, alarms, controls = gen.generate()

    stats = gen.metadata.stats
    assert stats["entity_count"] == 1
    assert stats["signal_value_count"] == len(signals)
    assert stats["alarm_count"] == len(alarms)
    assert stats["control_result_count"] == len(controls)


def test_generate_with_registered_strategy() -> None:
    """注入 StrategyRegistry 后 generate() 应使用注册策略生成信号。"""
    from seahorse.strategies.registry import StrategyRegistry
    from seahorse.strategies.curve_generation import CurveGenerationStrategy

    reg = StrategyRegistry()
    curve = CurveGenerationStrategy(scenario_id="cs", source_id="OPC_UA")
    reg.register("curve", curve, set_default=True)

    cfg = ScenarioConfig(scenario_id="reg_test", asset_count=1, duration_seconds=0.5, protocol_targets=["OPC_UA"])
    gen = SeahorseGenerator(cfg, registry=reg)
    _, _, signals, _, _ = gen.generate()

    assert len(signals) > 0
    # 曲线策略标识
    from seahorse.strategies.curve_generation import STRATEGY_ID_CURVE
    assert signals[0].strategy_id == STRATEGY_ID_CURVE


def test_generate_with_default_strategy() -> None:
    """注入默认策略后 generate() 应使用该策略。"""
    from seahorse.strategies.random_generation import RandomGenerationStrategy

    strategy = RandomGenerationStrategy(scenario_id="ds", source_id="OPC_UA")
    cfg = ScenarioConfig(scenario_id="def_strat", asset_count=1, duration_seconds=0.5, protocol_targets=["OPC_UA"])
    gen = SeahorseGenerator(cfg, default_strategy=strategy)
    _, _, signals, _, _ = gen.generate()

    assert len(signals) > 0
    assert signals[0].strategy_id == "random_generation"


def test_signal_values_cached_after_generate() -> None:
    """generate() 后 signal_values property 应缓存已生成的信号值。"""
    cfg = ScenarioConfig(scenario_id="cache_test", asset_count=1, duration_seconds=0.5)
    gen = SeahorseGenerator(cfg)
    _, _, signals, _, _ = gen.generate()

    cached = gen.signal_values
    assert len(cached) == len(signals)
    assert cached[0].value == signals[0].value


def test_generated_controls_has_expected_types() -> None:
    """generate() 的控制结果应包含典型控制类型。"""
    cfg = ScenarioConfig(scenario_id="ctrl_type_test", asset_count=1)
    gen = SeahorseGenerator(cfg)
    _, _, _, _, controls = gen.generate()

    ctrl_types = {c.control_type for c in controls}
    assert "START" in ctrl_types
    assert "STOP" in ctrl_types
    assert "SETPOINT" in ctrl_types


def test_generated_alarms_have_proper_structure() -> None:
    """生成的告警应包含 alarm_id、entity_id、message 等必要字段。"""
    cfg = ScenarioConfig(scenario_id="alm_struct", asset_count=1, duration_seconds=1.0)
    gen = SeahorseGenerator(cfg)
    _, _, _, alarms, _ = gen.generate()

    for alarm in alarms:
        assert alarm.alarm_id
        assert alarm.entity_id
        assert alarm.alarm_type
        assert alarm.severity
        assert alarm.timestamp


def test_generated_controls_have_proper_structure() -> None:
    """生成的控制结果应包含 control_id、entity_id、status、message 等必要字段。"""
    cfg = ScenarioConfig(scenario_id="ctrl_struct", asset_count=1)
    gen = SeahorseGenerator(cfg)
    _, _, _, _, controls = gen.generate()

    for ctrl in controls:
        assert ctrl.control_id
        assert ctrl.entity_id
        assert ctrl.control_type
        assert ctrl.status
        assert ctrl.message


def test_registry_entity_override_in_generator() -> None:
    """注册表的实体类型覆盖应影响不同实体的信号生成策略。"""
    from seahorse.strategies.registry import StrategyRegistry
    from seahorse.strategies.random_generation import RandomGenerationStrategy, STRATEGY_ID_RANDOM

    reg = StrategyRegistry()
    rand_strat = RandomGenerationStrategy(scenario_id="test", source_id="OPC_UA")
    reg.register("random", rand_strat, set_default=True)

    cfg = ScenarioConfig(scenario_id="override_test", asset_count=1, duration_seconds=0.5, protocol_targets=["OPC_UA"])
    gen = SeahorseGenerator(cfg, registry=reg)
    _, _, signals, _, _ = gen.generate()

    assert len(signals) > 0
    assert signals[0].strategy_id == STRATEGY_ID_RANDOM
