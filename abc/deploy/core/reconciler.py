"""纯 Reconciler 骨架。

本阶段只固定输入输出边界，并返回空计划。Ownership、Lease、Fail-Closed、Failover 和
Failback 的真实决策将在后续阶段加入，不能在此阶段用推测状态驱动服务激活。
"""

from __future__ import annotations

from dataclasses import dataclass

from ..managed import ManagedServiceSnapshot
from ..model.cluster import ClusterModel
from ..model.ownership import CoordinationSnapshot
from .plan import RuntimePlan


@dataclass(frozen=True, slots=True)
class DesiredState:
    """Reconciler 所需的静态期望状态输入。"""

    cluster: ClusterModel


@dataclass(frozen=True, slots=True)
class ActualFacts:
    """Reconciler 所需的、来自权威边界的当前事实。"""

    coordination: CoordinationSnapshot
    services: tuple[ManagedServiceSnapshot, ...]


class Reconciler:
    """根据 Desired State 和 Actual Facts 计算下一轮 RuntimePlan 的纯决策器。"""

    def reconcile(self, desired: DesiredState, actual: ActualFacts) -> RuntimePlan:
        """返回第一阶段空计划，不推断尚未实现的 Ownership 状态。

        Args:
            desired: Cluster 的静态期望状态。
            actual: ManagedService 与 Coordination 的权威快照。

        Returns:
            不包含外部控制动作的 RuntimePlan。
        """
        del desired, actual
        return RuntimePlan.empty()
