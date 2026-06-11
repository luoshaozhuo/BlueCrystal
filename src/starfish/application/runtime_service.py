"""starfish 运行时应用服务。

本模块显式承担 usecase/orchestration 角色：
- 组合文件加载驱动与运行时注册驱动。
- 统一处理计划加载、校验失败和驱动装配流程。
- 为 API/CLI 提供稳定的高层调用入口。

不负责：
- CLI 参数解析与终端输出格式。
- 协议细节实现。
- 原始 JSON 解析细节本身。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from starfish.domain import StarfishServerPlan, ValidationResult
from starfish.drivers.runtime_registry import RuntimeRegistry, create_drivers
from starfish.drivers.server_plan_loader import load_server_plan


@dataclass(frozen=True)
class LoadedPlan:
    """ServerPlan 加载结果。

    Args:
        plan: 成功解析后的计划；校验失败时可能为 None。
        validation: 结构化校验明细。
    """

    plan: StarfishServerPlan | None
    validation: ValidationResult

    @property
    def is_valid(self) -> bool:
        """返回是否可进入运行时装配阶段。"""
        return self.plan is not None and self.validation.is_valid


@dataclass(frozen=True)
class BuiltRuntime:
    """运行时装配结果。

    Args:
        plan: 已通过校验的 ServerPlan。
        validation: 加载阶段校验结果。
        registry: 基于计划装配出的驱动注册表。
    """

    plan: StarfishServerPlan
    validation: ValidationResult
    registry: RuntimeRegistry


class StarfishRuntimeService:
    """Starfish 运行时用例编排服务。"""

    def load_plan(self, input_path: Path) -> LoadedPlan:
        """加载并校验 ServerPlan。

        Args:
            input_path: `starfish_server_plan.json` 文件路径。

        Returns:
            包含计划和校验结果的 `LoadedPlan`。
        """
        result = load_server_plan(input_path)
        return LoadedPlan(plan=result.plan, validation=result.validation)

    def build_runtime(self, input_path: Path) -> BuiltRuntime:
        """加载计划并创建运行时注册表。

        Args:
            input_path: `starfish_server_plan.json` 文件路径。

        Returns:
            可供 API/CLI 使用的运行时装配结果。

        Raises:
            ValueError: 校验失败或 plan 缺失，无法进入运行时阶段。
        """
        loaded = self.load_plan(input_path)
        if loaded.plan is None:
            raise ValueError("plan 为 None")
        if not loaded.validation.is_valid:
            raise ValueError(
                f"校验失败 ({len(loaded.validation.errors)} 个错误)"
            )
        return BuiltRuntime(
            plan=loaded.plan,
            validation=loaded.validation,
            registry=create_drivers(loaded.plan),
        )


__all__ = ["LoadedPlan", "BuiltRuntime", "StarfishRuntimeService"]
