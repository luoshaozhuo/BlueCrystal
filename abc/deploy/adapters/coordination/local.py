"""单进程 Cluster 的 Local Coordination 适配器。

适配器以 asyncio lock 原子保护本进程内成员和 Ownership 状态，并生成递增 Epoch。
它只能支撑单节点或单进程测试装配，不具有跨进程 Lease、故障恢复或防脑裂能力。
"""

from __future__ import annotations

import asyncio
import time
import uuid

from ...model.ownership import CoordinationSnapshot, Lease, Ownership
from ...model.state import NodeState


class LocalCoordination:
    """在一个 Python 进程内实现 CoordinationPort 的最小事实存储。"""

    def __init__(self, lease_seconds: float = 30.0) -> None:
        """创建空协调状态。

        Args:
            lease_seconds: Local Ownership 的名义 lease 时长，必须为正数。
        """
        if lease_seconds <= 0:
            raise ValueError("lease_seconds 必须大于零")
        self._lease_seconds = lease_seconds
        self._lock = asyncio.Lock()
        self._node_states: dict[str, NodeState] = {}
        self._ownerships: dict[tuple[str, int], Ownership] = {}
        self._epoch = 0

    async def join(self, node_id: str) -> None:
        """将节点标记为 JOINING；重复 join 保持幂等。"""
        async with self._lock:
            self._node_states[node_id] = NodeState.JOINING

    async def mark_ready(self, node_id: str) -> None:
        """把已加入的节点标记为 READY，拒绝无 Membership 更新。"""
        async with self._lock:
            if node_id not in self._node_states:
                raise ValueError(f"节点尚未 join: {node_id}")
            self._node_states[node_id] = NodeState.READY

    async def begin_leaving(self, node_id: str) -> None:
        """将节点标记为 LEAVING，表示不应再竞争新的 Ownership。"""
        async with self._lock:
            if node_id in self._node_states:
                self._node_states[node_id] = NodeState.LEAVING

    async def leave(self, node_id: str) -> None:
        """移除 Membership，并丢弃仍属于该节点的 Local Ownership。"""
        async with self._lock:
            self._node_states.pop(node_id, None)
            self._ownerships = {
                key: ownership
                for key, ownership in self._ownerships.items()
                if ownership.owner_node_id != node_id
            }

    async def snapshot(self) -> CoordinationSnapshot:
        """返回当前进程内事实；始终只声明本地协调可用。"""
        async with self._lock:
            self._discard_expired_locked()
            return CoordinationSnapshot(
                node_states=dict(self._node_states),
                ownerships=tuple(self._ownerships.values()),
                coordination_available=True,
            )

    async def try_acquire(self, service_id: str, replica_slot: int, node_id: str) -> Ownership | None:
        """在本进程内原子尝试占有一个 READY 节点可持有的副本槽位。"""
        async with self._lock:
            self._discard_expired_locked()
            if self._node_states.get(node_id) is not NodeState.READY:
                return None
            key = (service_id, replica_slot)
            existing = self._ownerships.get(key)
            if existing is not None:
                return existing if existing.owner_node_id == node_id else None
            self._epoch += 1
            lease = Lease(str(uuid.uuid4()), node_id, time.monotonic() + self._lease_seconds)
            ownership = Ownership(service_id, replica_slot, node_id, lease, self._epoch, self._epoch)
            self._ownerships[key] = ownership
            return ownership

    async def renew(self, ownership: Ownership) -> Ownership | None:
        """仅对精确匹配的本地 Ownership 续租，旧 Owner 不可影响新代次。"""
        async with self._lock:
            self._discard_expired_locked()
            key = (ownership.service_id, ownership.replica_slot)
            current = self._ownerships.get(key)
            if current != ownership:
                return None
            renewed = Ownership(
                ownership.service_id,
                ownership.replica_slot,
                ownership.owner_node_id,
                Lease(ownership.lease.lease_id, ownership.owner_node_id, time.monotonic() + self._lease_seconds),
                ownership.epoch,
                ownership.fencing_token,
            )
            self._ownerships[key] = renewed
            return renewed

    async def release(self, ownership: Ownership) -> bool:
        """仅当所有身份字段仍匹配时释放 Ownership，避免误删新 Owner。"""
        async with self._lock:
            key = (ownership.service_id, ownership.replica_slot)
            if self._ownerships.get(key) != ownership:
                return False
            del self._ownerships[key]
            return True

    def _discard_expired_locked(self) -> None:
        """在持锁条件下删除过期 lease；仅用于 Local 状态卫生。"""
        now = time.monotonic()
        self._ownerships = {
            key: ownership
            for key, ownership in self._ownerships.items()
            if ownership.lease.expires_at_monotonic > now
        }
