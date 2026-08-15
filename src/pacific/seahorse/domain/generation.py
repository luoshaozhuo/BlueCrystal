"""seahorse 核心模型 —— 生成结果值。

本模块定义 Seahorse 生成的信号值、告警事件和控制回写结果的数据结构。
这些是生成器的输出类型，不包含生成逻辑本身。

安全边界：
- 本模块不得 import whale.ingest。
- 本模块不得访问生产数据库。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class GeneratedSignalValue:
    """生成的信号值 —— 单时刻、单个点位的采样结果。

    携带完整溯源信息，包括场景、设备、节点、变量标识及生成策略标识。
    默认 synthetic=True，表示由生成器合成而非真实采集。

    Attributes:
        signal_id: 关联的信号点位 ID（保持向后兼容）。
        scenario_id: 场景唯一标识，用于关联生成上下文。
        source_id: 数据源标识（如协议名称 "OPC_UA"）。
        device_id: 设备唯一标识，对应 SeedEntity.entity_id。
        profile_item_id: 信号点位规划 ID，对应 SignalProfileItemPlan.signal_id。
        node_key: 逻辑节点标识（如 "WTUR"、"WGEN"）。
        variable_key: 变量标识（如 "Ww"、"WindSpeed"）。
        timestamp: 采样时间戳。
        value: 信号值（数值型）。
        quality: 质量码，0=good, 1=uncertain, 2=bad。
        unit: 工程单位。
        strategy_id: 生成策略标识，用于追溯生成来源。
        synthetic: 是否为合成数据，默认 True 表示由生成器生成。
    """

    signal_id: str
    scenario_id: str = ""
    source_id: str = ""
    device_id: str = ""
    profile_item_id: str = ""
    node_key: str = ""
    variable_key: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    value: float = 0.0
    quality: int = 0
    unit: str = ""
    strategy_id: str = ""
    synthetic: bool = True


@dataclass
class GeneratedAlarmEvent:
    """生成的告警事件 —— 描述某类设备在特定时间触发的告警。

    Attributes:
        alarm_id: 告警唯一标识。
        entity_id: 触发告警的实体 ID。
        alarm_type: 告警类型（如 "OVERVOLTAGE"、"OVERCURRENT"）。
        severity: 严重等级（"CRITICAL"、"MAJOR"、"MINOR"、"WARNING"）。
        timestamp: 告警触发时间。
        cleared_at: 告警清除时间（None 表示未清除）。
        message: 告警描述信息。
    """

    alarm_id: str
    entity_id: str = ""
    alarm_type: str = ""
    severity: str = "WARNING"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cleared_at: datetime | None = None
    message: str = ""


@dataclass
class GeneratedControlResult:
    """生成的控制回写结果 —— 描述控制命令执行后的反馈。

    Attributes:
        control_id: 控制唯一标识。
        entity_id: 目标实体 ID。
        control_type: 控制类型（如 "START"、"STOP"、"SETPOINT"）。
        target_value: 目标值。
        result_value: 执行结果值。
        status: 执行状态（"SUCCESS"、"FAILURE"、"TIMEOUT"）。
        timestamp: 执行时间戳。
        message: 结果描述信息。
    """

    control_id: str
    entity_id: str = ""
    control_type: str = ""
    target_value: float = 0.0
    result_value: float = 0.0
    status: str = "SUCCESS"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message: str = ""
