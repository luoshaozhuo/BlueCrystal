"""seahorse 核心模型 —— 场景包（ScenarioBundle）。

本模块定义 Seahorse 场景导出的完整数据包结构，聚合场景配置、
生成计划、信号值、告警和控制结果，并携带版本信息、校验和与元数据。
是导出、校验和归档的最小数据单元。

安全边界：
- 本模块不得 import whale.ingest。
- 本模块不得访问生产数据库。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from pacific.seahorse.domain.scenario import ScenarioConfig, ScenarioMetadata
from pacific.seahorse.domain.plan import SeedPlan, ServerConfig
from pacific.seahorse.domain.generation import (
    GeneratedAlarmEvent,
    GeneratedControlResult,
    GeneratedSignalValue,
)


@dataclass
class ScenarioBundle:
    """场景包 —— Seahorse 场景生成的完整数据快照。

    聚合从生成配置到最终输出结果的完整数据链，是导出、校验和
    归档的最小单元。所有数据来自确定性生成，同一 ScenarioConfig
    与同一 deterministic_seed 产生内容完全相同的 bundle。

    Attributes:
        schema_version: Bundle schema 版本号，用于序列化兼容性管理。
        scenario_version: 场景逻辑版本号，由使用方定义和管理。
        generator_version: Seahorse 生成器组件版本号。
        created_at: 生成时间戳（UTC 时区），不参与校验和计算。
        scenario_id: 场景唯一标识，必须与内部各计划的 scenario_id 一致。
        name: 场景可读名称。
        deterministic_seed: 确定性随机种子，用于重现性验证。
        synthetic: 始终为 True，标识所有数据由生成器合成而非现场采集。
        scenario_config: 场景配置完整快照。
        scenario_metadata: 生成器运行时元数据。
        seed_plan: 种子计划，包含资产、点表、端点和采集任务。
        server_config: 服务端配置，包含一组 server members 的端点与点位配置。
        generated_timeseries_sample: 生成的信号值采样序列，按时间排序。
        alarm_events: 生成的告警事件列表，按触发时间排序。
        control_results: 生成的控制回写结果列表。
        checksum: 内容确定性校验和（SHA256），相同 config+seed 产生相同值。
        replay_metadata: 可选的重放元数据（如回放文件来源、速度因子等）。
    """

    schema_version: str = "1.0.0"
    scenario_version: str = "1.0.0"
    generator_version: str = "0.2.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scenario_id: str = ""
    name: str = ""
    deterministic_seed: int = 0
    synthetic: bool = True
    scenario_config: ScenarioConfig | None = None
    scenario_metadata: ScenarioMetadata | None = None
    seed_plan: SeedPlan | None = None
    server_config: ServerConfig | None = None
    generated_timeseries_sample: list[GeneratedSignalValue] = field(default_factory=list)
    alarm_events: list[GeneratedAlarmEvent] = field(default_factory=list)
    control_results: list[GeneratedControlResult] = field(default_factory=list)
    checksum: str = ""
    replay_metadata: dict[str, Any] | None = None


def _make_serializable(obj: Any) -> Any:
    """将对象递归转换为 JSON 可序列化形式。

    处理 dataclass 实例、datetime 对象、list 和 dict 的递归转换。
    用于校验和计算和 JSON 导出阶段，确保产生稳定可重现的序列化输出。

    Args:
        obj: 任意 Python 对象，通常为 dataclass 实例或其嵌套结构。

    Returns:
        JSON 可序列化的等价表示（dict/list/str/int/float/bool/None）。
        对于非标准类型（如 bytes），转换为十六进制字符串。
    """
    from dataclasses import fields as dc_fields

    if hasattr(obj, "__dataclass_fields__"):
        result: dict[str, Any] = {}
        for f in dc_fields(obj):
            val = getattr(obj, f.name)
            result[f.name] = _make_serializable(val)
        return result
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, bytes):
        return obj.hex()
    return obj


__all__ = ["ScenarioBundle", "_make_serializable"]
