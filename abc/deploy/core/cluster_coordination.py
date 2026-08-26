"""Cluster Coordination 门面。

该门面将 Runtime 的启动和关闭语义映射到 CoordinationPort；它只读取或变更协调事实，
不决定 Owner、不直接激活 ManagedService，也不泄漏具体后端 SDK。
"""

from __future__ import annotations

from ..model.ownership import CoordinationSnapshot, Ownership
from ..ports.coordination import CoordinationPort


class ClusterCoordination:
    """管理当前节点 Membership 与本节点 Ownership 清理的协调门面。"""

    def __init__(self, node_id: str, port: CoordinationPort) -> None:
        """绑定当前节点标识和一个明确的协调后端 Port。"""
        self._node_id = node_id
        self._port = port
        self._started = False

    async def start(self) -> None:
        """加入 Cluster；成功后才允许 Runtime 标记节点 READY。"""
        await self._port.join(self._node_id)
        self._started = True

    async def mark_ready(self) -> None:
        """在本地 ManagedService 均完成启动后发布 READY Membership。"""
        self._ensure_started()
        await self._port.mark_ready(self._node_id)

    async def begin_leaving(self) -> None:
        """在关闭开始时停止当前节点参与新的 Ownership 竞争。"""
        if self._started:
            await self._port.begin_leaving(self._node_id)

    async def snapshot(self) -> CoordinationSnapshot:
        """读取协调后端的权威事实，供 Reconciliation 使用。"""
        return await self._port.snapshot()

    async def release_local_ownerships(self) -> None:
        """释放快照中仍属于本节点的 Ownership，不操作其他节点事实。"""
        snapshot = await self._port.snapshot()
        for ownership in snapshot.ownerships:
            if ownership.owner_node_id == self._node_id:
                await self._port.release(ownership)

    async def leave(self) -> None:
        """在服务和 Ownership 清理后离开 Cluster；重复调用保持安全。"""
        if self._started:
            await self._port.leave(self._node_id)
            self._started = False

    def _ensure_started(self) -> None:
        """保护只能在成功 join 后执行的 Membership 状态变更。"""
        if not self._started:
            raise RuntimeError("ClusterCoordination 尚未启动")
