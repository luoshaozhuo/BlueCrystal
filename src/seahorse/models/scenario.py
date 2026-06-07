"""seahorse 核心模型 —— 场景配置、元数据与种子计划。

本模块定义 Seahorse 第一阶段的核心数据结构，均为纯 dataclass，
不依赖数据库连接、ORM 或特定序列化格式。

安全边界：
- 本模块不得 import whale.ingest。
- 本模块不得访问生产数据库。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ScenarioConfig:
    """场景配置 —— Seahorse 生成器的顶层输入。

    包含场景标识、确定性种子、生成参数和协议目标。
    这是用户可编辑的入口结构，不包含运行时状态。

    Attributes:
        scenario_id: 场景唯一标识，用于日志、审计和输出文件命名。
        name: 场景可读名称。
        deterministic_seed: 确定性伪随机种子，相同的 config 与 seed 应产生相同输出。
        start_time: 模拟数据起始时间，默认使用 UTC。
        duration_seconds: 模拟总时长（秒）。
        sample_interval_ms: 信号采样间隔（毫秒）。
        asset_count: 要生成的资产数量。
        protocol_targets: 目标协议列表，例如 ["OPC_UA", "MODBUS", "IEC104"]。
    """

    scenario_id: str
    name: str = ""
    deterministic_seed: int = 42
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_seconds: float = 3600.0
    sample_interval_ms: int = 100
    asset_count: int = 1
    protocol_targets: list[str] = field(default_factory=list)


@dataclass
class ScenarioMetadata:
    """场景元数据 —— 记录生成器运行时的版本、参数和统计信息。

    用于追踪生成历史、重现结果和审计。
    不包含实际生成数据，仅保留参数快照与统计摘要。

    Attributes:
        scenario_id: 关联的场景 ID。
        generated_at: 生成时间戳。
        seahorse_version: Seahorse 组件版本。
        config_snapshot: 生成时使用的完整配置快照。
        stats: 统计摘要，例如 {"signal_count": 150, "alarm_count": 3}。
    """

    scenario_id: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    seahorse_version: str = "0.1.0"
    config_snapshot: dict[str, Any] = field(default_factory=dict)
    stats: dict[str, int] = field(default_factory=dict)
