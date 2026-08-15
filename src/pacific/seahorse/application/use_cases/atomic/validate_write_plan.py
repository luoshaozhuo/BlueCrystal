"""校验 WritePlan 的最小用例。"""

from __future__ import annotations

from dataclasses import dataclass

from pacific.seahorse.domain.runtime_contract import WritePlan, validate_write_plan


@dataclass(frozen=True, slots=True)
class WritePlanValidationResult:
    """WritePlan 校验结果。"""

    errors: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        """返回是否校验通过。"""
        return not self.errors


class ValidateWritePlanUseCase:
    """执行 WritePlan 纯内存一致性校验。"""

    def execute(self, plan: WritePlan) -> WritePlanValidationResult:
        """校验 WritePlan。

        Args:
            plan: 待校验运行计划。

        Returns:
            校验结果。
        """
        return WritePlanValidationResult(errors=validate_write_plan(plan))


__all__ = ["ValidateWritePlanUseCase", "WritePlanValidationResult"]
