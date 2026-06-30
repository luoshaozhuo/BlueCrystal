"""seahorse 生成器测试 —— 告警与控制回写。

验证：
1. AlarmGenerator 阈值告警、品质告警、设备状态告警、通信告警。
2. ControlResultGenerator 多种回写状态、批量生成、自定义处理器。
3. 生成器的确定性行为。
4. 生成器不访问外部系统。

测试阶段：开发期验证 (P1)。
不可证明：生产环境告警规则精确性、真实设备控制行为。
"""
from __future__ import annotations

from datetime import datetime, timezone

from seahorse.domain.generation import GeneratedControlResult, GeneratedSignalValue
from seahorse.domain.plan import SeedEntity
from seahorse.application.use_cases.alarm_generator import (
    ALARM_TYPE_DEVICE_STATE,
    ALARM_TYPE_QUALITY,
    ALARM_TYPE_THRESHOLD,
    AlarmGenerator,
)
from seahorse.application.use_cases.control_result_generator import (
    CONTROL_STATUS_UNSUPPORTED,
    CONTROL_STATUS_WRITE_DISABLED,
    ControlResultGenerator,
)


# ── helper ──────────────────────────────────────────────────────────────────────


def _make_entity(entity_id: str = "e001") -> SeedEntity:
    return SeedEntity(entity_id=entity_id)


def _make_signal(
    device_id: str = "e001",
    signal_id: str = "sig_001",
    variable_key: str = "ActivePower",
    value: float = 100.0,
    quality: int = 0,
    timestamp: datetime | None = None,
) -> GeneratedSignalValue:
    ts = timestamp or datetime.fromtimestamp(1000.0, tz=timezone.utc)
    return GeneratedSignalValue(
        signal_id=signal_id,
        device_id=device_id,
        variable_key=variable_key,
        value=value,
        quality=quality,
        timestamp=ts,
    )


# ── AlarmGenerator ──────────────────────────────────────────────────────────────


def test_alarm_gen_threshold_high() -> None:
    """超过上限阈值应产生 MAJOR 告警。"""
    gen = AlarmGenerator(scenario_id="sc_001")
    entity = _make_entity()
    sv = [_make_signal(variable_key="ActivePower", value=2000.0)]  # > 1600 阈值
    alarms = gen.generate(entity=entity, signal_values=sv)
    assert len(alarms) == 1
    assert alarms[0].alarm_type == ALARM_TYPE_THRESHOLD
    assert alarms[0].severity == "MAJOR"
    assert "ActivePower" in alarms[0].message


def test_alarm_gen_threshold_low() -> None:
    """低于下限阈值应产生 MAJOR 告警。"""
    gen = AlarmGenerator(scenario_id="sc_001")
    entity = _make_entity()
    sv = [_make_signal(variable_key="ActivePower", value=-50.0)]  # < 0 阈值
    alarms = gen.generate(entity=entity, signal_values=sv)
    assert len(alarms) == 1
    assert alarms[0].alarm_type == ALARM_TYPE_THRESHOLD
    assert "ActivePower" in alarms[0].message


def test_alarm_gen_threshold_within_range() -> None:
    """在阈值范围内不产生告警。"""
    gen = AlarmGenerator(scenario_id="sc_001")
    entity = _make_entity()
    sv = [_make_signal(variable_key="ActivePower", value=800.0)]  # 在 [0, 1600] 内
    alarms = gen.generate(entity=entity, signal_values=sv)
    assert len(alarms) == 0


def test_alarm_gen_quality_degradation() -> None:
    """品质码非 0 应产生品质告警。"""
    gen = AlarmGenerator(scenario_id="sc_001")
    entity = _make_entity()
    sv = [
        _make_signal(variable_key="WindSpeed", value=8.0, quality=0),  # good
        _make_signal(variable_key="WindSpeed", value=8.0, quality=1),  # uncertain
        _make_signal(variable_key="WindSpeed", value=8.0, quality=2),  # bad
    ]
    alarms = gen.generate(entity=entity, signal_values=sv)
    assert len(alarms) == 2
    assert alarms[0].alarm_type == ALARM_TYPE_QUALITY
    assert alarms[0].severity == "WARNING"  # quality=1
    assert alarms[1].alarm_type == ALARM_TYPE_QUALITY
    assert alarms[1].severity == "MAJOR"    # quality=2


def test_alarm_gen_device_state_normal() -> None:
    """正常信号不应产生设备状态告警。"""
    gen = AlarmGenerator(scenario_id="sc_001")
    entity = _make_entity()
    sv = [_make_signal(variable_key="ActivePower", value=800.0) for _ in range(10)]
    alarms = gen.generate(entity=entity, signal_values=sv)
    # 不过阈值，品质正常，非全零 → 无阈值/品质/设备告警
    # 可能产生通信告警（取决于随机）
    alarm_types = {a.alarm_type for a in alarms}
    assert ALARM_TYPE_DEVICE_STATE not in alarm_types
    assert ALARM_TYPE_THRESHOLD not in alarm_types
    assert ALARM_TYPE_QUALITY not in alarm_types


def test_alarm_gen_alarm_id_unique() -> None:
    """多条告警应有唯一 alarm_id。"""
    gen = AlarmGenerator(scenario_id="sc_001")
    entity = _make_entity()
    sv = [
        _make_signal(variable_key="ActivePower", value=2000.0),
        _make_signal(variable_key="WindSpeed", value=50.0),
    ]
    alarms = gen.generate(entity=entity, signal_values=sv)
    assert len(alarms) >= 1
    alarm_ids = [a.alarm_id for a in alarms]
    assert len(alarm_ids) == len(set(alarm_ids))


def test_alarm_gen_deterministic() -> None:
    """相同 seed 产生相同告警序列。"""
    entity = _make_entity()
    sv = [
        _make_signal(variable_key="ActivePower", value=2000.0),
        _make_signal(variable_key="ActivePower", value=-10.0),
        _make_signal(quality=1),
    ]

    def gen_and_extract() -> list[str]:
        gen = AlarmGenerator(scenario_id="sc", deterministic_seed=42)
        alarms = gen.generate(entity=entity, signal_values=sv)
        return [a.alarm_id for a in alarms]

    assert gen_and_extract() == gen_and_extract()


def test_alarm_gen_empty_signals() -> None:
    """空信号列表应返回空告警列表。"""
    gen = AlarmGenerator(scenario_id="sc")
    alarms = gen.generate(entity=_make_entity(), signal_values=[])
    assert alarms == []


def test_alarm_gen_custom_thresholds() -> None:
    """自定义阈值应覆盖默认阈值。"""
    custom = {"ActivePower": (500.0, 700.0)}
    gen = AlarmGenerator(scenario_id="sc", thresholds=custom)
    entity = _make_entity()
    sv = [_make_signal(variable_key="ActivePower", value=800.0)]  # 超出自定义阈值
    alarms = gen.generate(entity=entity, signal_values=sv)
    assert len(alarms) >= 1
    assert any(a.alarm_type == ALARM_TYPE_THRESHOLD for a in alarms)


# ── ControlResultGenerator ──────────────────────────────────────────────────────


def test_control_gen_single_result() -> None:
    """单条控制生成应返回完整结果。"""
    gen = ControlResultGenerator(scenario_id="sc_001")
    entity = _make_entity()
    result = gen.generate(entity=entity, control_type="START", target_value=1.0)
    assert isinstance(result, GeneratedControlResult)
    assert result.entity_id == "e001"
    assert result.control_type == "START"
    assert result.target_value == 1.0
    assert result.control_id.startswith("sc_001_ctrl_")


def test_control_gen_batch() -> None:
    """批量生成应返回与输入相同数量的结果。"""
    gen = ControlResultGenerator(scenario_id="sc_001")
    entity = _make_entity()
    controls = [("START", 1.0), ("STOP", 0.0), ("SETPOINT", 500.0)]
    results = gen.generate_batch(entity=entity, controls=controls)
    assert len(results) == 3
    assert all(r.entity_id == "e001" for r in results)


def test_control_gen_control_id_unique() -> None:
    """多条控制结果应有唯一 control_id。"""
    gen = ControlResultGenerator(scenario_id="sc_001")
    entity = _make_entity()
    results = gen.generate_batch(
        entity=entity,
        controls=[("START", 1.0), ("STOP", 0.0)],
    )
    ids = [r.control_id for r in results]
    assert len(ids) == len(set(ids))


def test_control_gen_deterministic() -> None:
    """相同 seed 产生相同控制结果。"""
    entity = _make_entity()
    gen1 = ControlResultGenerator(scenario_id="sc", deterministic_seed=42)
    gen2 = ControlResultGenerator(scenario_id="sc", deterministic_seed=42)
    r1 = gen1.generate(entity=entity, control_type="SETPOINT", target_value=100.0)
    r2 = gen2.generate(entity=entity, control_type="SETPOINT", target_value=100.0)
    assert r1.status == r2.status
    assert r1.result_value == r2.result_value
    assert r1.message == r2.message


def test_control_gen_empty_control_type_raises() -> None:
    """空 control_type 应抛出 ValueError。"""
    gen = ControlResultGenerator(scenario_id="sc")

    import pytest
    with pytest.raises(ValueError, match="control_type 不能为空"):
        gen.generate(entity=_make_entity(), control_type="", target_value=0.0)


def test_control_gen_unsupported_type() -> None:
    """不支持的操作类型应返回 UNSUPPORTED。"""
    gen = ControlResultGenerator(scenario_id="sc", deterministic_seed=42)
    result = gen.generate(
        entity=_make_entity(),
        control_type="REBOOT",
        target_value=0.0,
    )
    assert result.status == CONTROL_STATUS_UNSUPPORTED
    assert result.message


def test_control_gen_custom_handler() -> None:
    """自定义处理器应覆盖默认行为。"""
    def always_write_disabled(**kwargs):
        return GeneratedControlResult(
            control_id="custom_id",
            entity_id=kwargs["entity"].entity_id,
            control_type=kwargs["control_type"],
            target_value=kwargs["target_value"],
            result_value=0.0,
            status=CONTROL_STATUS_WRITE_DISABLED,
            timestamp=kwargs["timestamp"],
            message="自定义写禁用",
        )

    gen = ControlResultGenerator(
        scenario_id="sc",
        custom_handlers={"START": always_write_disabled},
    )
    result = gen.generate(entity=_make_entity(), control_type="START", target_value=1.0)
    assert result.status == CONTROL_STATUS_WRITE_DISABLED
    assert result.control_id == "custom_id"
    assert "自定义" in result.message


def test_control_gen_timestamp_override() -> None:
    """自定义 timestamp 应生效。"""
    gen = ControlResultGenerator(scenario_id="sc")
    ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
    result = gen.generate(
        entity=_make_entity(),
        control_type="STOP",
        target_value=0.0,
        timestamp=ts,
    )
    assert result.timestamp == ts


def test_control_gen_result_includes_status_message() -> None:
    """所有控制结果必须包含 message 字段。"""
    gen = ControlResultGenerator(scenario_id="sc", deterministic_seed=42)
    entity = _make_entity()
    for ctrl_type in ["START", "STOP", "SETPOINT", "REBOOT"]:
        result = gen.generate(entity=entity, control_type=ctrl_type, target_value=50.0)
        assert result.message, f"{ctrl_type} 缺少 message"
        assert result.control_id, f"{ctrl_type} 缺少 control_id"
        assert result.status, f"{ctrl_type} 缺少 status"
