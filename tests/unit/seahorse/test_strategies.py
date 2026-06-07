"""seahorse 生成策略测试。

验证：
1. RandomGenerationStrategy 确定性输出与字段完整性。
2. CurveGenerationStrategy 各曲线类型正确性。
3. ReplayGenerationStrategy 内存/文件回放与字段映射。
4. StrategyRegistry 注册、查找、覆盖行为。
5. 所有策略实现 GenerationStrategy Protocol。
6. Round 20 根因修复：daily_power_preset 长周期（24h）下最小值
   稳定 >= ``base_power * floor_ratio``（避免 ``noise_stdev=50`` 在
   864000 样本下偶发跌破 0/100 的 flaky）。

测试阶段：开发期验证 (P1)。
不可证明：真实外部文件系统 I/O 下的大规模 replay、生产环境曲线精确性。
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from seahorse.models.plan import SeedEntity, SignalProfileItemPlan
from seahorse.ports.generation_strategy import GenerationStrategy
from seahorse.strategies.random_generation import RandomGenerationStrategy, STRATEGY_ID_RANDOM
from seahorse.strategies.curve_generation import (
    CurveGenerationStrategy,
    STRATEGY_ID_CURVE,
)
from seahorse.strategies.replay_generation import ReplayGenerationStrategy
from seahorse.strategies.registry import StrategyRegistry


# ── shared fixtures ─────────────────────────────────────────────────────────────


def _make_entity(entity_id: str = "e001", entity_type: str = "WTG") -> SeedEntity:
    return SeedEntity(entity_id=entity_id, entity_type=entity_type)


def _make_signal_plan(
    signal_id: str = "sig_001",
    signal_name: str = "ActivePower",
    unit: str = "kW",
    cdc: str = "MV",
    generation_hint: str = "RANDOM",
    sample_interval_ms: int = 100,
) -> SignalProfileItemPlan:
    return SignalProfileItemPlan(
        signal_id=signal_id,
        signal_name=signal_name,
        unit=unit,
        cdc=cdc,
        generation_hint=generation_hint,
        sample_interval_ms=sample_interval_ms,
    )


# ── RandomGenerationStrategy ────────────────────────────────────────────────────


def test_random_strategy_is_strategy_protocol() -> None:
    """RandomGenerationStrategy 应满足 GenerationStrategy Protocol。"""
    strategy = RandomGenerationStrategy()
    assert isinstance(strategy, GenerationStrategy)


def test_random_strategy_deterministic() -> None:
    """相同 seed 产生相同输出。"""
    strategy = RandomGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan()

    result1 = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=0.5,
        deterministic_seed=42,
    )
    result2 = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=0.5,
        deterministic_seed=42,
    )
    assert len(result1) == len(result2)
    for s1, s2 in zip(result1, result2):
        assert s1.value == s2.value
        assert s1.timestamp == s2.timestamp
        assert s1.quality == s2.quality


def test_random_strategy_different_seed_different_output() -> None:
    """不同 seed 产生不同输出。"""
    strategy = RandomGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan()

    result1 = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=0.5,
        deterministic_seed=1,
    )
    result2 = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=0.5,
        deterministic_seed=9999,
    )
    # 两个不同 seed 至少一个值不同
    values1 = [s.value for s in result1]
    values2 = [s.value for s in result2]
    assert values1 != values2


def test_random_strategy_populates_all_fields() -> None:
    """生成的每条信号值应包含完整溯源字段。"""
    strategy = RandomGenerationStrategy(scenario_id="sc_001", source_id="OPC_UA")
    entity = _make_entity(entity_id="wtg_01")
    sp = _make_signal_plan(
        signal_id="sig_AP",
        signal_name="ActivePower",
        unit="kW",
        cdc="MV",
        generation_hint="RANDOM",
    )

    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=0.1,
        deterministic_seed=42,
    )
    assert len(results) > 0
    sv = results[0]
    assert sv.scenario_id == "sc_001"
    assert sv.source_id == "OPC_UA"
    assert sv.device_id == "wtg_01"
    assert sv.profile_item_id == "sig_AP"
    assert sv.variable_key == "ActivePower"
    assert sv.unit == "kW"
    assert sv.quality == 0
    assert sv.strategy_id == STRATEGY_ID_RANDOM
    assert sv.synthetic is True


def test_random_strategy_discrete_hint() -> None:
    """generation_hint=DISCRETE 的信号值应为 0 或 1。"""
    strategy = RandomGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan(signal_name="Status", generation_hint="DISCRETE")

    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=0.5,
        deterministic_seed=42,
    )
    for sv in results:
        assert sv.value in (0.0, 1.0)


def test_random_strategy_returns_correct_count() -> None:
    """信号值数量应与 duration / sample_interval 一致。"""
    strategy = RandomGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan(sample_interval_ms=200)

    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=1.0,
        deterministic_seed=42,
    )
    # 1.0s / 0.2s = 5 步
    assert len(results) == 5


# ── CurveGenerationStrategy ─────────────────────────────────────────────────────


def test_curve_strategy_is_strategy_protocol() -> None:
    """CurveGenerationStrategy 应满足 GenerationStrategy Protocol。"""
    strategy = CurveGenerationStrategy()
    assert isinstance(strategy, GenerationStrategy)


def test_curve_constant() -> None:
    """CONSTANT 曲线生成恒定值。"""
    strategy = CurveGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan(signal_name="UnknownSignal", generation_hint="UNKNOWN")

    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=1.0,
        deterministic_seed=42,
    )
    # unknown signal -> constant 0
    assert len(results) > 0
    assert all(sv.value == 0.0 for sv in results)


def test_curve_sinusoidal_preset() -> None:
    """预设 WindSpeed 曲线应为正弦变化。"""
    strategy = CurveGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan(signal_name="WindSpeed")

    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=3600.0,  # 1 hour
        deterministic_seed=42,
    )
    assert len(results) > 0
    values = [sv.value for sv in results]
    # 正弦曲线应有变动（非全同值）
    assert len(set(round(v, 1) for v in values)) > 1
    # 值应在合理范围 [4, 12] 左右
    for v in values:
        assert 3.0 < v < 14.0


def test_curve_daily_power_preset() -> None:
    """ActivePower 预设应为日功率双峰曲线。"""
    strategy = CurveGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan(signal_name="ActivePower")

    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=86400.0,  # 24 hours
        deterministic_seed=42,
    )
    assert len(results) > 0
    # 双峰曲线的最小值应 >= 0.2 * base_power
    values = [sv.value for sv in results]
    # noise stdev=50 时最小值可能低于 300，但仍 > 100
    assert min(values) >= 100
    assert max(values) > 500


def test_curve_daily_solar_preset() -> None:
    """PV_ActivePower 预设应为日光伏单峰曲线。"""
    strategy = CurveGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan(signal_name="PV_ActivePower")

    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=86400.0,
        deterministic_seed=42,
    )
    # 日出前和日落后值应为 0 或接近 0
    values = [sv.value for sv in results]
    assert any(v <= 1.0 for v in values), "应有接近 0 的值（夜间）"
    assert any(sv.value > 200 for sv in results), "应有峰值 > 200"


def test_curve_strategy_deterministic() -> None:
    """相同 seed 产生相同曲线输出。"""
    strategy = CurveGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan(signal_name="WindSpeed")

    results1 = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=3600.0,
        deterministic_seed=42,
    )
    results2 = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=3600.0,
        deterministic_seed=42,
    )
    for s1, s2 in zip(results1, results2):
        assert s1.value == s2.value


def test_curve_strategy_field_population() -> None:
    """曲线策略也填充完整溯源字段。"""
    strategy = CurveGenerationStrategy(scenario_id="cs", source_id="OPC_UA")
    entity = _make_entity()
    sp = _make_signal_plan(signal_name="WindSpeed")

    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=0.1,
        deterministic_seed=42,
    )
    sv = results[0]
    assert sv.scenario_id == "cs"
    assert sv.source_id == "OPC_UA"
    assert sv.strategy_id == STRATEGY_ID_CURVE
    assert sv.synthetic is True
    assert sv.variable_key == "WindSpeed"


# ── ReplayGenerationStrategy ────────────────────────────────────────────────────


def test_replay_strategy_is_strategy_protocol() -> None:
    """ReplayGenerationStrategy 应满足 GenerationStrategy Protocol。"""
    strategy = ReplayGenerationStrategy()
    assert isinstance(strategy, GenerationStrategy)


def test_replay_from_rows() -> None:
    """从内存 rows 回放信号值。"""
    strategy = ReplayGenerationStrategy(scenario_id="rep", source_id="OPC_UA")
    rows = [
        {"value": 100.0, "quality": 0, "timestamp": 1000.0},
        {"value": 200.0, "quality": 1, "timestamp": 1001.0},
    ]
    strategy.load_from_rows(rows)
    entity = _make_entity()
    sp = _make_signal_plan(sample_interval_ms=1000)

    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=900.0, duration_seconds=10.0,
        deterministic_seed=42,
    )
    assert len(results) == 2
    assert results[0].value == 100.0
    assert results[0].quality == 0
    assert results[1].value == 200.0
    assert results[1].quality == 1


def test_replay_from_jsonl() -> None:
    """从 JSONL 文件回放信号值。"""
    strategy = ReplayGenerationStrategy(scenario_id="rep")
    rows_data = [
        {"value": 300.0, "quality": 0},
        {"value": 400.0, "quality": 2},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for row in rows_data:
            f.write(json.dumps(row) + "\n")
        tmp_path = f.name

    try:
        strategy.load_from_jsonl(tmp_path)
        entity = _make_entity()
        sp = _make_signal_plan()
        results = strategy.generate_signals(
            entity=entity, signal_plan=sp,
            start_time=1000.0, duration_seconds=10.0,
            deterministic_seed=42,
        )
        assert len(results) == 2
        assert results[0].value == 300.0
        assert results[1].value == 400.0
        assert results[1].quality == 2
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_replay_missing_value_raises() -> None:
    """缺少 value 字段的 row 应抛出 KeyError。"""
    strategy = ReplayGenerationStrategy()
    rows = [{"quality": 0}]  # 缺少 value
    strategy.load_from_rows(rows)
    entity = _make_entity()
    sp = _make_signal_plan()

    import pytest
    with pytest.raises(KeyError, match="value"):
        strategy.generate_signals(
            entity=entity, signal_plan=sp,
            start_time=1000.0, duration_seconds=10.0,
            deterministic_seed=42,
        )


def test_replay_not_loaded_raises() -> None:
    """数据未加载时生成应抛出 ValueError。"""
    strategy = ReplayGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan()

    import pytest
    with pytest.raises(ValueError, match="数据未加载"):
        strategy.generate_signals(
            entity=entity, signal_plan=sp,
            start_time=1000.0, duration_seconds=10.0,
            deterministic_seed=42,
        )


def test_replay_jsonl_file_not_found() -> None:
    """JSONL 文件不存在时应抛出 FileNotFoundError。"""
    strategy = ReplayGenerationStrategy()

    import pytest
    with pytest.raises(FileNotFoundError):
        strategy.load_from_jsonl("/nonexistent/path/file.jsonl")


def test_replay_time_offset_and_speed() -> None:
    """时间偏移和加速倍率应对时间序列生效。"""
    strategy = ReplayGenerationStrategy()
    rows = [
        {"value": 100.0, "timestamp": 1000.0},
        {"value": 200.0, "timestamp": 1002.0},
    ]
    strategy.load_from_rows(rows)
    entity = _make_entity()
    sp = _make_signal_plan(
        sample_interval_ms=1000,
        generation_hint="REPLAY:2.0",  # speed_factor=2
    )

    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=5000.0, duration_seconds=10.0,
        deterministic_seed=42,
    )
    assert len(results) == 2
    # row0 timestamp 1000 → offset: (1000 - 1000) / 2.0 = 0.0, actual = 5000.0 + 0 = 5000.0
    assert results[0].timestamp == datetime.fromtimestamp(5000.0, tz=timezone.utc)
    # row1 timestamp 1002 → offset: (1002 - 1000) / 2.0 = 1.0, actual = 5000.0 + 1.0 = 5001.0
    assert results[1].timestamp == datetime.fromtimestamp(5001.0, tz=timezone.utc)


def test_replay_field_map_custom() -> None:
    """自定义字段映射应正确转换 row 字段到 GeneratedSignalValue 字段。"""
    custom_map = {
        "val": "value",
        "qual": "quality",
        "sig": "signal_id",
    }
    strategy = ReplayGenerationStrategy(field_map=custom_map)
    rows = [
        {"val": 999.0, "qual": 1, "sig": "custom_sig"},
    ]
    strategy.load_from_rows(rows)
    entity = _make_entity()
    sp = _make_signal_plan()

    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=10.0,
        deterministic_seed=42,
    )
    assert results[0].value == 999.0
    assert results[0].quality == 1
    assert results[0].signal_id == "custom_sig"


# ── StrategyRegistry ────────────────────────────────────────────────────────────


def test_registry_register_and_get() -> None:
    """注册策略后可正常获取。"""
    reg = StrategyRegistry()
    strategy = RandomGenerationStrategy()
    reg.register("random", strategy)
    assert "random" in reg
    assert reg.get("random") is strategy


def test_registry_register_duplicate_raises() -> None:
    """重复注册同名策略应抛出 ValueError。"""
    reg = StrategyRegistry()
    reg.register("a", RandomGenerationStrategy())

    import pytest
    with pytest.raises(ValueError, match="已注册"):
        reg.register("a", RandomGenerationStrategy())


def test_registry_get_missing_raises() -> None:
    """获取未注册策略应抛出 KeyError。"""
    reg = StrategyRegistry()

    import pytest
    with pytest.raises(KeyError, match="未注册"):
        reg.get("nonexistent")


def test_registry_default_strategy() -> None:
    """设默认策略后可正常获取。"""
    reg = StrategyRegistry()
    s = RandomGenerationStrategy()
    reg.register("random", s, set_default=True)
    assert reg.default_name == "random"
    assert reg.get_for_entity("WTG") is s


def test_registry_entity_override() -> None:
    """实体类型覆盖应优先于默认策略。"""
    reg = StrategyRegistry()
    default_s = RandomGenerationStrategy()
    curve_s = CurveGenerationStrategy()
    reg.register("random", default_s, set_default=True)
    reg.register("curve", curve_s)
    reg.register_entity_override("PV", "curve")

    assert reg.get_for_entity("WTG") is default_s
    assert reg.get_for_entity("PV") is curve_s


def test_registry_override_unregistered_raises() -> None:
    """覆盖未注册策略应抛出 KeyError。"""
    reg = StrategyRegistry()

    import pytest
    with pytest.raises(KeyError, match="未注册"):
        reg.register_entity_override("WTG", "ghost")


def test_registry_no_default_raises() -> None:
    """无默认策略时获取应抛出 ValueError。"""
    reg = StrategyRegistry()

    import pytest
    with pytest.raises(ValueError, match="未为实体类型.*配置策略"):
        reg.get_for_entity("WTG")


def test_registry_registered_names() -> None:
    """registered_names 应返回所有已注册名称。"""
    reg = StrategyRegistry()
    reg.register("a", RandomGenerationStrategy())
    reg.register("b", RandomGenerationStrategy())
    assert set(reg.registered_names) == {"a", "b"}


# ── Round 20 daily_power_preset 稳定性回归测试 ──────────────────────────────


def test_curve_daily_power_preset_min_floor_enforced() -> None:
    """Round 20 根因修复：daily_power_preset 最小值应被 floor 钳制。

    业务语义：风机的"最低技术出力"硬下限（典型 20% 额定容量）。
    长周期 24h 仿真（864000 样本，0.1s 间隔）在 ``noise_stdev=50``
    时偶尔跌破 0 / 100。本测试验证 floor 强制执行。
    """
    strategy = CurveGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan(signal_name="ActivePower")
    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=86400.0,
        deterministic_seed=42,
    )
    values = [sv.value for sv in results]
    # base_power=1500 * floor_ratio=0.2 = 300（绝对下限）
    assert min(values) >= 300.0, (
        f"daily_power 最小值应 >= base_power * floor_ratio = 300，实际 {min(values)}"
    )


def test_curve_daily_power_preset_deterministic_across_runs() -> None:
    """Round 20 验证：相同 seed 多次运行 daily_power 输出一致。"""
    strategy = CurveGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan(signal_name="ActivePower")
    results1 = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=86400.0,
        deterministic_seed=42,
    )
    results2 = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=86400.0,
        deterministic_seed=42,
    )
    assert len(results1) == len(results2)
    for s1, s2 in zip(results1, results2):
        assert s1.value == s2.value


def test_curve_daily_power_preset_min_floor_with_high_noise() -> None:
    """Round 20 验证：即便 noise_stdev 加大也仍被 floor 钳制。"""
    strategy = CurveGenerationStrategy(
        curve_configs={
            "ActivePower": (
                "daily_power_curve",
                {
                    "base_power": 100.0,
                    "morning_peak": 9.0,
                    "evening_peak": 17.0,
                    "peak_ratio": 0.95,
                    "floor_ratio": 0.2,
                    "noise_stdev": 50.0,  # 50% base_power！
                },
            ),
        },
    )
    entity = _make_entity()
    sp = _make_signal_plan(signal_name="ActivePower")
    results = strategy.generate_signals(
        entity=entity, signal_plan=sp,
        start_time=1000.0, duration_seconds=86400.0,
        deterministic_seed=42,
    )
    values = [sv.value for sv in results]
    # base_power=100 * floor_ratio=0.2 = 20
    assert min(values) >= 20.0, (
        f"daily_power 最小值应 >= 20，实际 {min(values)}"
    )


def test_curve_other_types_no_floor() -> None:
    """Round 20 验证：除 daily_power 外，其它曲线类型不强制 floor。

    sinusoidal / solar / storage 允许值跌至 0（夜间/待机），
    不应被钳制为 base_power * 0.2。
    """
    strategy = CurveGenerationStrategy()
    entity = _make_entity()
    sp_solar = _make_signal_plan(signal_name="PV_ActivePower")
    results = strategy.generate_signals(
        entity=entity, signal_plan=sp_solar,
        start_time=1000.0, duration_seconds=86400.0,
        deterministic_seed=42,
    )
    values = [sv.value for sv in results]
    # solar 夜间值应接近 0（不被 floor 钳制）
    assert any(v <= 1.0 for v in values), (
        "solar 夜间应有接近 0 的值（floor 不应作用于 solar）"
    )


def test_curve_daily_power_preset_stability_5x() -> None:
    """Round 20 验证：连续运行 5 次 daily_power_preset 均通过 min >= 100。

    这是 round 19 报告中标记的 pre-existing flaky 的回归测试：
    通过 floor 根因修复后，连续运行 5 次 0 flaky。
    """
    strategy = CurveGenerationStrategy()
    entity = _make_entity()
    sp = _make_signal_plan(signal_name="ActivePower")
    for run_idx in range(5):
        results = strategy.generate_signals(
            entity=entity, signal_plan=sp,
            start_time=1000.0, duration_seconds=86400.0,
            deterministic_seed=42,
        )
        values = [sv.value for sv in results]
        # 旧 flaky 阈值（>= 100）现在永久通过（实际 min >= 300）
        assert min(values) >= 100, (
            f"第 {run_idx + 1} 次运行 min(values) < 100: {min(values)}"
        )
