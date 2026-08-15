"""seahorse 生成策略注册表。

本模块提供策略注册、查找和默认实例化的能力。
支持按名称或实体类型注册 GenerationStrategy 实现，
使 SeahorseGenerator 可根据 ScenarioConfig 动态选择策略。

安全边界：
- 不得 import whale.ingest。
- 注册表本身是内存数据结构，无外部副作用。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pacific.seahorse.application.ports.generation_strategy_port import GenerationStrategy


class StrategyRegistry:
    """生成策略注册表。

    维护策略名称到实现的映射，支持按实体类型覆盖。
    所有注册的策略实例共享 deterministic_seed 语义。

    Attributes:
        _strategies: 策略名 -> 策略实例映射。
        _entity_overrides: entity_type -> 策略名映射，用于按实体类型选择策略。
        _default_name: 默认策略名（未匹配时使用）。
    """

    def __init__(self) -> None:
        """初始化空注册表。"""
        self._strategies: dict[str, "GenerationStrategy"] = {}
        self._entity_overrides: dict[str, str] = {}
        self._default_name: str | None = None

    def register(
        self,
        name: str,
        strategy: "GenerationStrategy",
        set_default: bool = False,
    ) -> None:
        """注册一个生成策略。

        Args:
            name: 策略唯一名称（如 "random"、"curve"、"replay"）。
            strategy: GenerationStrategy 实现实例。
            set_default: 是否设为默认策略。

        Raises:
            ValueError: 如果 name 已注册。
        """
        if name in self._strategies:
            raise ValueError(f"策略 '{name}' 已注册")
        self._strategies[name] = strategy
        if set_default:
            self._default_name = name

    def register_entity_override(
        self,
        entity_type: str,
        strategy_name: str,
    ) -> None:
        """为特定实体类型注册策略覆盖。

        当遇到 entity_type 匹配的实体时，优先使用覆盖的策略。

        Args:
            entity_type: 实体类型（如 "WTG"、"PV"、"SUBSTATION"）。
            strategy_name: 已注册的策略名称。

        Raises:
            KeyError: 如果 strategy_name 未在注册表中注册。
        """
        if strategy_name not in self._strategies:
            raise KeyError(f"策略 '{strategy_name}' 未注册，无法用于覆盖")
        self._entity_overrides[entity_type] = strategy_name

    def get(self, name: str) -> "GenerationStrategy":
        """按名称获取策略。

        Args:
            name: 策略名称。

        Returns:
            对应 GenerationStrategy 实例。

        Raises:
            KeyError: 如果 name 未注册。
        """
        if name not in self._strategies:
            raise KeyError(f"策略 '{name}' 未注册")
        return self._strategies[name]

    def get_for_entity(
        self,
        entity_type: str,
    ) -> "GenerationStrategy":
        """按实体类型获取策略。

        优先返回 entity_type 覆盖的策略，其次返回默认策略。

        Args:
            entity_type: 实体类型。

        Returns:
            GenerationStrategy 实例。

        Raises:
            ValueError: 如果既无覆盖也无默认策略。
        """
        if entity_type in self._entity_overrides:
            return self._strategies[self._entity_overrides[entity_type]]
        if self._default_name:
            return self._strategies[self._default_name]
        raise ValueError(f"未为实体类型 '{entity_type}' 配置策略，且无默认策略")

    @property
    def registered_names(self) -> tuple[str, ...]:
        """返回所有已注册策略名称。"""
        return tuple(self._strategies.keys())

    @property
    def default_name(self) -> str | None:
        """返回默认策略名称。"""
        return self._default_name

    def __contains__(self, name: str) -> bool:
        """检查策略是否已注册。"""
        return name in self._strategies


__all__ = ["StrategyRegistry"]
