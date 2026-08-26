"""Reconciler 与执行控制器之间传递的最小运行计划模型。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RuntimeActionKind(StrEnum):
    """后续阶段可由 Runtime Core 执行的控制动作类别。"""

    ACQUIRE_OWNERSHIP = "ACQUIRE_OWNERSHIP"
    RELEASE_OWNERSHIP = "RELEASE_OWNERSHIP"
    ACTIVATE_SERVICE = "ACTIVATE_SERVICE"
    DEACTIVATE_SERVICE = "DEACTIVATE_SERVICE"
    RENEW_LEASE = "RENEW_LEASE"


@dataclass(frozen=True, slots=True)
class RuntimeAction:
    """一个最多改变一项外部事实的后续控制动作。"""

    kind: RuntimeActionKind
    service_id: str


@dataclass(frozen=True, slots=True)
class RuntimePlan:
    """一次 Reconciliation 计算出的有序本地动作计划。"""

    actions: tuple[RuntimeAction, ...] = ()

    @classmethod
    def empty(cls) -> RuntimePlan:
        """构造不改变任何外部事实的第一阶段空计划。"""
        return cls()
