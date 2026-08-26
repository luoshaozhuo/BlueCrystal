"""Cluster 的最小静态定义。

本阶段只校验当前节点、服务规范和副本数的基本一致性；复杂 placement、标签和
failover/failback 策略留给后续 Reconciler 实现，不在此处伪造调度能力。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True, slots=True)
class NodeSpec:
    """Cluster 中一个可参与协调的节点定义。

    Args:
        node_id: 节点稳定标识。
        priority: 后续 Ownership 候选排序可使用的静态优先级。
        labels: 后续 placement 规则可使用的不可变节点标签。
    """

    node_id: str
    priority: int = 0
    labels: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ManagedServiceSpec:
    """期望由 Cluster 托管的运行单元静态定义。

    Args:
        service_id: 与实际 ManagedService 相匹配的稳定标识。
        active_replicas: 后续 Reconciler 需要维持的 Active 副本数。
    """

    service_id: str
    active_replicas: int = 1

    def __post_init__(self) -> None:
        """拒绝不能表达有效期望状态的副本数。"""
        if not self.service_id:
            raise ValueError("service_id 不能为空")
        if self.active_replicas < 1:
            raise ValueError("active_replicas 必须大于零")


@dataclass(frozen=True, slots=True)
class ClusterModel:
    """ClusterRuntime 启动时使用的最小静态模型。

    Args:
        cluster_id: Cluster 的稳定标识。
        local_node_id: 当前进程代表的节点标识，必须出现在 ``nodes`` 中。
        nodes: 参与 Cluster 的静态节点列表。
        managed_services: 需要由本 Runtime 识别的服务规范列表。
    """

    cluster_id: str
    local_node_id: str
    nodes: tuple[NodeSpec, ...]
    managed_services: tuple[ManagedServiceSpec, ...]

    def __post_init__(self) -> None:
        """在启动前冻结可安全检查的模型约束。"""
        if not self.cluster_id:
            raise ValueError("cluster_id 不能为空")
        node_ids = [node.node_id for node in self.nodes]
        service_ids = [service.service_id for service in self.managed_services]
        if not node_ids or self.local_node_id not in node_ids:
            raise ValueError("local_node_id 必须存在于 nodes")
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("nodes 包含重复 node_id")
        if len(service_ids) != len(set(service_ids)):
            raise ValueError("managed_services 包含重复 service_id")
