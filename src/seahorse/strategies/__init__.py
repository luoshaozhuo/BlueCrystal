"""seahorse 生成策略层。

本层包含信号生成策略的具体实现，包括随机值生成、
曲线生成和回放生成。所有策略实现 `GenerationStrategy` Protocol，
保证确定性：相同输入 + 相同 deterministic_seed → 相同输出。

安全边界：
- 不得 import whale.ingest。
- 不得访问生产数据库。
"""
from __future__ import annotations

from seahorse.strategies.random_generation import (
    STRATEGY_ID_RANDOM,
    RandomGenerationStrategy,
)
from seahorse.strategies.curve_generation import (
    CURVE_TYPE_CONSTANT,
    CURVE_TYPE_DAILY_POWER,
    CURVE_TYPE_DAILY_SOLAR,
    CURVE_TYPE_DAILY_STORAGE,
    CURVE_TYPE_LINEAR,
    CURVE_TYPE_SINUSOIDAL,
    STRATEGY_ID_CURVE,
    CurveGenerationStrategy,
)
from seahorse.strategies.replay_generation import (
    STRATEGY_ID_REPLAY,
    ReplayGenerationStrategy,
)
from seahorse.strategies.registry import StrategyRegistry

__all__ = [
    "STRATEGY_ID_RANDOM",
    "RandomGenerationStrategy",
    "CURVE_TYPE_CONSTANT",
    "CURVE_TYPE_LINEAR",
    "CURVE_TYPE_SINUSOIDAL",
    "CURVE_TYPE_DAILY_POWER",
    "CURVE_TYPE_DAILY_SOLAR",
    "CURVE_TYPE_DAILY_STORAGE",
    "STRATEGY_ID_CURVE",
    "CurveGenerationStrategy",
    "STRATEGY_ID_REPLAY",
    "ReplayGenerationStrategy",
    "StrategyRegistry",
]
