"""seahorse 确定性随机值生成策略。

基于 deterministic_seed 和 profile_item 元信息生成稳定、
可重现的信号值序列。每条信号值携带完整溯源信息，
包括 scenario_id、source_id、device_id、profile_item_id、
node_key、variable_key、timestamp、value、quality_code、
strategy_id 和 synthetic 标识。

安全边界：
- 不得 import whale.ingest。
- 确定性：相同输入 + 相同 deterministic_seed → 相同输出。
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from seahorse.models.generation import GeneratedAlarmEvent, GeneratedControlResult, GeneratedSignalValue
from seahorse.models.plan import SeedEntity, SignalProfileItemPlan

# 策略标识常量
STRATEGY_ID_RANDOM = "random_generation"


class RandomGenerationStrategy:
    """确定性随机值生成策略。

    基于 signal_plan 中的 generation_hint 选择不同的随机分布行为，
    确保相同 (entity, signal_plan, start_time, duration_seconds, deterministic_seed)
    总是产生相同的信号值序列。

    generation_hint 支持：
    - RANDOM / RANDOM_WALK: 高斯噪声叠加基线值。
    - DISCRETE: 离散整数随机值（用于状态信号）。
    - CONSTANT: 恒定 baseline 值。
    - 其他: 按 RANDOM 处理。

    所有生成信号值的 quality 均为 0 (good)，synthetic=True。

    Attributes:
        _scenario_id: 场景标识。
        _source_id: 数据源标识。
    """

    def __init__(self, *, scenario_id: str = "", source_id: str = "") -> None:
        """初始化随机生成策略。

        Args:
            scenario_id: 场景唯一标识。
            source_id: 数据源标识（如协议名称）。
        """
        self._scenario_id = scenario_id
        self._source_id = source_id

    @property
    def strategy_id(self) -> str:
        """返回策略标识字符串。"""
        return STRATEGY_ID_RANDOM

    def generate_signals(
        self,
        *,
        entity: SeedEntity,
        signal_plan: SignalProfileItemPlan,
        start_time: float,
        duration_seconds: float,
        deterministic_seed: int,
    ) -> list[GeneratedSignalValue]:
        """基于确定性随机算法生成信号值序列。

        使用 deterministic_seed 初始化 RNG，保证相同输入产生相同序列。
        生成步长由 signal_plan.sample_interval_ms 决定。

        Args:
            entity: 目标种子实体。
            signal_plan: 信号点位规划。
            start_time: 起始 Unix 时间戳（秒）。
            duration_seconds: 生成时长（秒）。
            deterministic_seed: 确定性随机种子。

        Returns:
            GeneratedSignalValue 列表，按时间升序排列。
            长度由 duration_seconds / (signal_plan.sample_interval_ms / 1000) 决定。
        """
        rng = random.Random(deterministic_seed)

        # 按实体和信号维度混合 seed，保证不同实体/信号的可区分性
        composite_seed = deterministic_seed ^ hash(entity.entity_id) ^ hash(signal_plan.signal_id)
        rng = random.Random(composite_seed)

        interval_s = signal_plan.sample_interval_ms / 1000.0
        if interval_s <= 0:
            interval_s = 0.1  # 默认 100ms

        step_count = max(1, int(duration_seconds / interval_s))
        results: list[GeneratedSignalValue] = []

        base_time = datetime.fromtimestamp(start_time, tz=timezone.utc)
        generation_hint = signal_plan.generation_hint.upper()

        for step in range(step_count):
            ts = base_time + timedelta(seconds=step * interval_s)
            value = self._compute_value(
                rng=rng,
                signal_plan=signal_plan,
                generation_hint=generation_hint,
                step=step,
                step_count=step_count,
            )

            results.append(GeneratedSignalValue(
                signal_id=signal_plan.signal_id,
                scenario_id=self._scenario_id,
                source_id=self._source_id,
                device_id=entity.entity_id,
                profile_item_id=signal_plan.signal_id,
                node_key=signal_plan.ln_class,
                variable_key=signal_plan.signal_name,
                timestamp=ts,
                value=value,
                quality=0,
                unit=signal_plan.unit,
                strategy_id=STRATEGY_ID_RANDOM,
                synthetic=True,
            ))

        return results

    def _compute_value(
        self,
        *,
        rng: random.Random,
        signal_plan: SignalProfileItemPlan,
        generation_hint: str,
        step: int,
        step_count: int,
    ) -> float:
        """根据 generation_hint 计算单点值。

        Args:
            rng: 确定性随机数生成器。
            signal_plan: 信号点位规划。
            generation_hint: 标准化后的生成提示（大写）。
            step: 当前步数索引。
            step_count: 总步数。

        Returns:
            计算得到的信号值（float）。
        """
        if generation_hint == "CONSTANT":
            # 恒定值：从 signal_id hash 派生固定 baseline
            const_hash = hash(signal_plan.signal_id) & 0x7FFFFFFF
            return (const_hash % 1000) / 10.0  # 0~99.9

        if generation_hint in ("DISCRETE", "SPS", "STV", "CMD", "INS", "INC", "ENC", "SPC"):
            # 离散值：返回 0 或 1 的整数（模拟状态位）
            return float(rng.randint(0, 1))

        if generation_hint == "RANDOM_WALK":
            # 随机游走：base ± random drift
            base = self._baseline_from_signal_id(signal_plan.signal_id)
            drift = rng.gauss(0.0, base * 0.02)  # 2% stdev
            return round(base + drift, 3)

        # 默认 RANDOM: 高斯噪声叠加基线值（模拟稳定读数）
        base = self._baseline_from_signal_id(signal_plan.signal_id)
        noise = rng.gauss(0.0, base * 0.05)  # 5% stdev
        return round(max(0.0, base + noise), 3)

    @staticmethod
    def _baseline_from_signal_id(signal_id: str) -> float:
        """从 signal_id 计算出确定性基线值。

        使用 hash 派生，保证不同 signal_id 有不同的 baseline，
        且相同 signal_id 总是得到相同 baseline。

        Args:
            signal_id: 信号标识。

        Returns:
            基线值（float），范围 [0.1, 1000.0]。
        """
        h = hash(signal_id) & 0x7FFFFFFF
        # 映射到合理范围: 非零正数
        return (h % 10000) / 10.0 + 0.1  # 0.1 ~ 1000.0

    def generate_alarms(
        self,
        *,
        entity: SeedEntity,
        signal_values: list[GeneratedSignalValue],
        deterministic_seed: int,
    ) -> list[GeneratedAlarmEvent]:
        """生成告警事件（随机策略最小实现）。

        随机策略默认不生成告警事件，返回空列表。
        告警事件由 SeahorseGenerator 通过 AlarmGenerator 统一管理。

        Args:
            entity: 目标实体。
            signal_values: 信号值序列。
            deterministic_seed: 确定性随机种子。

        Returns:
            空列表（随机策略不负责告警生成）。
        """
        return []

    def generate_controls(
        self,
        *,
        entity: SeedEntity,
        deterministic_seed: int,
    ) -> list[GeneratedControlResult]:
        """生成控制回写结果（随机策略最小实现）。

        随机策略默认不生成控制结果，返回空列表。
        控制结果由 SeahorseGenerator 通过 ControlResultGenerator 统一管理。

        Args:
            entity: 目标实体。
            deterministic_seed: 确定性随机种子。

        Returns:
            空列表（随机策略不负责控制生成）。
        """
        return []


__all__ = ["STRATEGY_ID_RANDOM", "RandomGenerationStrategy"]
