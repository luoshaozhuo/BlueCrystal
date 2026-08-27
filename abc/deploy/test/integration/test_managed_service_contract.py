"""ManagedService cleanup 幂等契约的集成测试。

本文件使用严格的进程内 FakeManagedService 表达公共 Protocol 的生命周期事实，不依赖真实
Uvicorn、APScheduler 或外部资源；它只能证明 Deploy 所需的接口契约，不能证明具体运行体
的资源释放实现。测试需在安装 pytest-asyncio 的本地开发环境执行。
"""

from __future__ import annotations

import pytest

from deploy.managed import ManagedServiceSnapshot
from deploy.model.ownership import Ownership
from deploy.model.state import ManagedServiceActivationState, ManagedServiceLifecycleState


class FakeManagedService:
    """以内存状态实现 cleanup 幂等契约的 ManagedService 测试替身。"""

    def __init__(self, service_id: str) -> None:
        """创建初始为 STOPPED 与 INACTIVE 的服务替身。"""
        self._service_id = service_id
        self._lifecycle_state = ManagedServiceLifecycleState.STOPPED
        self._activation_state = ManagedServiceActivationState.INACTIVE

    @property
    def service_id(self) -> str:
        """返回注册与 snapshot 共用的稳定服务标识。"""
        return self._service_id

    async def start(self) -> None:
        """把替身转换到第一阶段要求的稳定启动状态。"""
        self._lifecycle_state = ManagedServiceLifecycleState.RUNNING
        self._activation_state = ManagedServiceActivationState.INACTIVE

    async def activate(self, ownership: Ownership | None = None) -> None:
        """仅为完整 Protocol 提供最小激活行为；本测试不验证重复激活语义。"""
        del ownership
        self._activation_state = ManagedServiceActivationState.ACTIVE

    async def deactivate(self) -> None:
        """无条件归一化为 INACTIVE，模拟接口要求的幂等 cleanup。"""
        self._activation_state = ManagedServiceActivationState.INACTIVE

    async def stop(self) -> None:
        """无条件归一化为 STOPPED 与 INACTIVE，模拟接口要求的幂等 cleanup。"""
        self._lifecycle_state = ManagedServiceLifecycleState.STOPPED
        self._activation_state = ManagedServiceActivationState.INACTIVE

    async def wait(self) -> None:
        """替身没有真实后台运行体，因此立即完成等待。"""

    def snapshot(self) -> ManagedServiceSnapshot:
        """返回当前内存生命周期事实，不复制外部运行体状态。"""
        return ManagedServiceSnapshot(self.service_id, self._lifecycle_state, self._activation_state)


@pytest.mark.asyncio
async def test_managed_service_stop_and_deactivate_are_idempotent() -> None:
    """保护未启动、已停止及正常生命周期中的 cleanup 均可重复调用。"""
    service = FakeManagedService("service-a")

    await service.deactivate()
    await service.deactivate()
    assert service.snapshot().activation_state is ManagedServiceActivationState.INACTIVE

    await service.stop()
    await service.stop()
    assert service.snapshot().lifecycle_state is ManagedServiceLifecycleState.STOPPED
    assert service.snapshot().activation_state is ManagedServiceActivationState.INACTIVE

    await service.start()
    await service.deactivate()
    await service.deactivate()
    await service.stop()
    await service.stop()
    assert service.snapshot().lifecycle_state is ManagedServiceLifecycleState.STOPPED
    assert service.snapshot().activation_state is ManagedServiceActivationState.INACTIVE
