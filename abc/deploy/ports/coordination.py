"""协调后端的稳定 Port 契约。

Core 仅依赖这里的成员与 Ownership 语义，具体 etcd、Redis 或平台 SDK 必须由 Adapter
隔离。第一阶段先由进程内 Local 实现满足单节点生命周期，不提供分布式安全承诺。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..model.ownership import CoordinationSnapshot, Ownership


@runtime_checkable
class CoordinationPort(Protocol):
    """提供 Membership、Ownership 与 Lease 事实的异步协调边界。"""

    async def join(self, node_id: str) -> None:
        """将节点加入协调域，初始状态由实现定义为 JOINING。"""

    async def mark_ready(self, node_id: str) -> None:
        """确认节点本地服务可运行后将 Membership 更新为 READY。"""

    async def begin_leaving(self, node_id: str) -> None:
        """阻止节点继续参与新 Ownership 竞争并标记为 LEAVING。"""

    async def leave(self, node_id: str) -> None:
        """移除节点 Membership；调用方必须先完成本地服务和 Ownership 清理。"""

    async def snapshot(self) -> CoordinationSnapshot:
        """返回当前协调事实及其是否可用于证明本地 Ownership。"""

    async def try_acquire(self, service_id: str, replica_slot: int, node_id: str) -> Ownership | None:
        """原子尝试取得副本槽位 Ownership；失败返回 None。"""

    async def renew(self, ownership: Ownership) -> Ownership | None:
        """只在 Owner、Lease 与 Epoch 全部匹配时续租；失效返回 None。"""

    async def release(self, ownership: Ownership) -> bool:
        """只释放仍由相同 Owner、Lease 与 Epoch 持有的 Ownership。"""
