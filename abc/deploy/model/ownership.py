"""Ownership、Lease 与协调快照的最小数据骨架。

这些类型保留 Epoch/Fencing 的安全语义，但第一阶段 Local Coordination 不提供跨进程
或分布式一致性保证，不能据此宣称已实现 Failover 或防脑裂闭环。
"""

from __future__ import annotations

from dataclasses import dataclass

from .state import NodeState


@dataclass(frozen=True, slots=True)
class Lease:
    """一个 Ownership 的有限有效期事实。"""

    lease_id: str
    owner_node_id: str
    expires_at_monotonic: float


@dataclass(frozen=True, slots=True)
class Ownership:
    """某个服务副本槽位的当前授权及其执行代次。"""

    service_id: str
    replica_slot: int
    owner_node_id: str
    lease: Lease
    epoch: int
    fencing_token: int


@dataclass(frozen=True, slots=True)
class CoordinationSnapshot:
    """协调后端提供的成员、Ownership、Lease 与可信度事实。"""

    node_states: dict[str, NodeState]
    ownerships: tuple[Ownership, ...]
    coordination_available: bool
