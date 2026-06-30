"""seahorse 生成策略端口 —— GenerationStrategy Protocol。

定义信号、告警和控制结果的生成契约。具体实现（如随机游走、
正弦曲线、回放等）以后续扩展时注入，本轮仅定义接口边界。

安全边界：
- 策略实现不得访问生产数据库。
- 策略实现必须是确定性的：相同输入 + 相同 seed 产生相同输出。
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from seahorse.domain.generation import (
    GeneratedAlarmEvent,
    GeneratedControlResult,
    GeneratedSignalValue,
)
from seahorse.domain.plan import SeedEntity, SignalProfileItemPlan


@runtime_checkable
class GenerationStrategy(Protocol):
    """信号与事件生成策略协议。

    每个具体策略负责根据实体定义和信号规划生成时间序列数据。
    所有实现必须满足：相同输入 + 相同 deterministic_seed → 相同输出。

    本轮不实现具体策略（Random/Curve/Replay），仅定义接口边界以保证
    后续扩展的一致性。
    """

    def generate_signals(
        self,
        *,
        entity: SeedEntity,
        signal_plan: SignalProfileItemPlan,
        start_time: float,
        duration_seconds: float,
        deterministic_seed: int,
    ) -> list[GeneratedSignalValue]:
        """生成信号时间序列。

        Args:
            entity: 目标种子实体，提供实体元信息。
            signal_plan: 信号点位规划，定义单位、数据类型和生成提示。
            start_time: 起始时间（Unix 时间戳，秒）。
            duration_seconds: 生成时长（秒）。
            deterministic_seed: 确定性随机种子，保证可重现。

        Returns:
            按时间排序的生成信号值列表。
        """
        ...

    def generate_alarms(
        self,
        *,
        entity: SeedEntity,
        signal_values: list[GeneratedSignalValue],
        deterministic_seed: int,
    ) -> list[GeneratedAlarmEvent]:
        """基于信号值生成告警事件。

        Args:
            entity: 目标种子实体。
            signal_values: 已生成的信号值序列，作为告警判据输入。
            deterministic_seed: 确定性随机种子。

        Returns:
            生成的告警事件列表。
        """
        ...

    def generate_controls(
        self,
        *,
        entity: SeedEntity,
        deterministic_seed: int,
    ) -> list[GeneratedControlResult]:
        """生成控制回写结果。

        Args:
            entity: 目标种子实体。
            deterministic_seed: 确定性随机种子。

        Returns:
            生成的控制回写结果列表。
        """
        ...


__all__ = ["GenerationStrategy"]
