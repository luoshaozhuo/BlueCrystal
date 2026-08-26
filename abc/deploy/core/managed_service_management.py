"""ManagedService Management 门面。

本模块按确定顺序调用受管服务的公共契约并读取实际快照；它不决定 Active 节点、不调用
具体框架 API，也不把一次控制调用成功当作真实运行状态。
"""

from __future__ import annotations

from ..managed import ManagedService, ManagedServiceSnapshot
from ..model.ownership import Ownership
from ..model.state import ManagedServiceActivationState
from .managed_service_registry import ManagedServiceRegistry


class ManagedServiceManagement:
    """封装本节点受管服务的注册、控制与状态观察入口。"""

    def __init__(self, registry: ManagedServiceRegistry | None = None) -> None:
        """创建服务管理门面；未传入时创建私有空注册表。"""
        self._registry = registry or ManagedServiceRegistry()

    @property
    def registry(self) -> ManagedServiceRegistry:
        """暴露注册表供 Runtime 在启动前完成注册和校验。"""
        return self._registry

    def register(self, service: ManagedService) -> None:
        """注册本节点受管服务；仅转发注册表的重复标识保护。"""
        self._registry.add(service)

    async def start_all(self) -> None:
        """按注册顺序启动所有服务；任一失败立即传播供 Runtime 进入 FAILED。"""
        for service in self._registry.list():
            await service.start()

    async def stop_all(self) -> None:
        """按逆注册顺序停止服务，降低依赖服务先被销毁的风险。"""
        for service in reversed(self._registry.list()):
            await service.stop()

    async def activate(self, service_id: str, ownership: Ownership | None = None) -> None:
        """激活一个指定服务；Ownership 由后续协调与 Reconciler 阶段提供。"""
        await self._registry.get(service_id).activate(ownership)

    async def deactivate(self, service_id: str) -> None:
        """停用一个指定服务，但不停止其真实运行体。"""
        await self._registry.get(service_id).deactivate()

    async def deactivate_active(self) -> None:
        """对快照仍非 INACTIVE 的服务执行关闭阶段停用动作。"""
        for service in reversed(self._registry.list()):
            if service.snapshot().activation_state is not ManagedServiceActivationState.INACTIVE:
                await service.deactivate()

    def snapshots(self) -> tuple[ManagedServiceSnapshot, ...]:
        """读取所有服务的权威实际快照，不缓存或推断状态。"""
        return tuple(service.snapshot() for service in self._registry.list())
