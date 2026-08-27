"""ClusterRuntime 第一阶段生命周期的集成测试。

测试以记录调用顺序的进程内 FakeManagedService 和 FakeCoordinationPort 组装 Runtime，不访问
控制器私有字段，也不产生真实网络、Lease 或多节点通信；因此只能验证本地生命周期骨架，不能
证明 Failover、Failback 或分布式 HA。测试需在安装 pytest-asyncio 的本地开发环境执行。
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from deploy.adapters.coordination.local import LocalCoordination
from deploy.managed import ManagedServiceSnapshot
from deploy.model.cluster import ClusterModel, ManagedServiceSpec, NodeSpec
from deploy.model.ownership import CoordinationSnapshot, Ownership
from deploy.model.state import (
    ClusterRuntimeLifecycleState,
    ManagedServiceActivationState,
    ManagedServiceLifecycleState,
    NodeState,
)
from deploy.runtime import ClusterRuntime


class FakeCoordinationPort:
    """记录 Membership 调用顺序的本地 CoordinationPort 替身。"""

    def __init__(self, events: list[str], before_leaving: Callable[[], None]) -> None:
        """创建空成员事实；回调用于从公开 Runtime 状态记录控制器已停止。"""
        self._events = events
        self._before_leaving = before_leaving
        self._node_states: dict[str, NodeState] = {}

    async def join(self, node_id: str) -> None:
        """记录加入并发布 JOINING 状态。"""
        self._events.append("coordination.start")
        self._node_states[node_id] = NodeState.JOINING

    async def mark_ready(self, node_id: str) -> None:
        """记录 READY 发布。"""
        self._events.append("coordination.mark_ready")
        self._node_states[node_id] = NodeState.READY

    async def begin_leaving(self, node_id: str) -> None:
        """确认收敛循环已停止后记录 LEAVING。"""
        self._before_leaving()
        self._events.append("coordination.begin_leaving")
        self._node_states[node_id] = NodeState.LEAVING

    async def leave(self, node_id: str) -> None:
        """记录节点离开；维护循环仍应在该阶段之后才停止。"""
        self._events.append("coordination.leave")
        self._node_states.pop(node_id, None)

    async def snapshot(self) -> CoordinationSnapshot:
        """返回本地成员事实；本替身不提供 Ownership。"""
        if self._node_states.get("node-a") is NodeState.LEAVING:
            self._events.append("coordination.release_local_ownerships")
        return CoordinationSnapshot(dict(self._node_states), (), True)

    async def try_acquire(self, service_id: str, replica_slot: int, node_id: str) -> Ownership | None:
        """第一阶段测试不执行 Ownership 获取，因此固定返回 None。"""
        return None

    async def renew(self, ownership: Ownership) -> Ownership | None:
        """第一阶段测试不执行 Lease renewal，因此固定返回 None。"""
        return None

    async def release(self, ownership: Ownership) -> bool:
        """记录本地释放阶段；本替身没有 Ownership 可释放。"""
        self._events.append("coordination.release_local_ownerships")
        return False


class FakeManagedService:
    """记录 Runtime 调用的 ManagedService 替身，可模拟无效快照或启动失败。"""

    def __init__(
        self,
        service_id: str,
        events: list[str],
        *,
        on_start: Callable[[], None] | None = None,
        snapshot_state: tuple[ManagedServiceLifecycleState, ManagedServiceActivationState] | None = None,
        start_error: Exception | None = None,
    ) -> None:
        """创建服务替身；可选状态仅用于模拟 start 返回后的权威快照。"""
        self._service_id = service_id
        self._events = events
        self._on_start = on_start
        self._snapshot_state = snapshot_state
        self._start_error = start_error
        self._lifecycle_state = ManagedServiceLifecycleState.STOPPED
        self._activation_state = ManagedServiceActivationState.INACTIVE

    @property
    def service_id(self) -> str:
        """返回稳定注册标识。"""
        return self._service_id

    async def start(self) -> None:
        """记录启动，必要时模拟失败，否则转换到稳定启动状态。"""
        if self._on_start is not None:
            self._on_start()
        self._events.append(f"{self.service_id}.start")
        if self._start_error is not None:
            raise self._start_error
        self._lifecycle_state = ManagedServiceLifecycleState.RUNNING
        self._activation_state = ManagedServiceActivationState.INACTIVE

    async def activate(self, ownership: Ownership | None = None) -> None:
        """记录测试中的显式 Active 状态，以验证关闭阶段会执行 deactivate。"""
        self._events.append(f"{self.service_id}.activate")
        self._activation_state = ManagedServiceActivationState.ACTIVE

    async def deactivate(self) -> None:
        """记录关闭阶段停用，并归一化为 INACTIVE。"""
        self._events.append(f"{self.service_id}.deactivate")
        self._activation_state = ManagedServiceActivationState.INACTIVE

    async def stop(self) -> None:
        """记录 cleanup；即使未启动也安全归一化为 STOPPED。"""
        self._events.append(f"{self.service_id}.stop")
        self._lifecycle_state = ManagedServiceLifecycleState.STOPPED
        self._activation_state = ManagedServiceActivationState.INACTIVE

    async def wait(self) -> None:
        """替身没有真实后台运行体，因此立即完成。"""

    def snapshot(self) -> ManagedServiceSnapshot:
        """记录 Runtime 的实际状态确认，并返回可选的模拟快照状态。"""
        self._events.append(f"{self.service_id}.snapshot")
        lifecycle_state, activation_state = self._snapshot_state or (
            self._lifecycle_state,
            self._activation_state,
        )
        return ManagedServiceSnapshot(self.service_id, lifecycle_state, activation_state)


def make_cluster(*service_ids: str) -> ClusterModel:
    """构造单节点、指定服务集合的最小静态 ClusterModel。"""
    return ClusterModel(
        cluster_id="cluster-a",
        local_node_id="node-a",
        nodes=(NodeSpec("node-a"),),
        managed_services=tuple(ManagedServiceSpec(service_id) for service_id in service_ids),
    )


@pytest.mark.asyncio
async def test_cluster_runtime_start_and_stop_follows_lifecycle_order() -> None:
    """保护启动 READY 门槛与关闭阶段的架构顺序及后台任务退出。"""
    events: list[str] = []
    runtime: ClusterRuntime

    def record_maintenance_before_service_start() -> None:
        """通过公开只读状态确认服务启动前维护任务已经建立。"""
        assert runtime.coordination_maintenance_running is True
        events.append("coordination_maintenance.start")

    def record_reconciliation_stopped() -> None:
        """通过公开只读状态确认进入 LEAVING 前收敛循环已经退出。"""
        assert runtime.reconciliation_running is False
        events.append("reconciliation.stop")

    coordination = FakeCoordinationPort(events, record_reconciliation_stopped)
    runtime = ClusterRuntime(make_cluster("service-a", "service-b"), coordination)
    service_a = FakeManagedService("service-a", events, on_start=record_maintenance_before_service_start)
    service_b = FakeManagedService("service-b", events, on_start=record_maintenance_before_service_start)
    runtime.register(service_a)
    runtime.register(service_b)

    await runtime.start()
    events.append("reconciliation.start")
    assert runtime.state is ClusterRuntimeLifecycleState.RUNNING
    assert runtime.coordination_maintenance_running is True
    assert runtime.reconciliation_running is True

    await service_a.activate()
    await service_b.activate()
    await runtime.stop()
    events.append("coordination_maintenance.stop")

    assert runtime.state is ClusterRuntimeLifecycleState.STOPPED
    assert runtime.coordination_maintenance_running is False
    assert runtime.reconciliation_running is False
    service_b_shutdown_snapshot = len(events) - 1 - events[::-1].index("service-b.snapshot")
    service_a_shutdown_snapshot = len(events) - 1 - events[::-1].index("service-a.snapshot")
    assert events.index("coordination.start") < events.index("coordination_maintenance.start")
    assert events.index("coordination_maintenance.start") < events.index("service-a.start")
    assert events.index("service-b.start") < events.index("service-b.snapshot")
    assert events.index("service-b.snapshot") < events.index("coordination.mark_ready")
    assert events.index("coordination.mark_ready") < events.index("reconciliation.start")
    assert events.index("reconciliation.stop") < events.index("coordination.begin_leaving")
    assert events.index("coordination.begin_leaving") < service_b_shutdown_snapshot
    assert service_b_shutdown_snapshot < events.index("service-b.deactivate")
    assert events.index("service-b.deactivate") < service_a_shutdown_snapshot
    assert service_a_shutdown_snapshot < events.index("service-a.deactivate")
    assert events.index("service-a.deactivate") < events.index("coordination.release_local_ownerships")
    assert events.index("coordination.release_local_ownerships") < events.index("service-b.stop")
    assert events.index("service-b.stop") < events.index("service-a.stop")
    assert events.index("service-a.stop") < events.index("coordination.leave")
    assert events.index("coordination.leave") < events.index("coordination_maintenance.stop")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("lifecycle_state", "activation_state"),
    [
        pytest.param(ManagedServiceLifecycleState.STARTING, ManagedServiceActivationState.INACTIVE),
        pytest.param(ManagedServiceLifecycleState.RUNNING, ManagedServiceActivationState.ACTIVE),
    ],
)
async def test_cluster_runtime_does_not_mark_ready_when_service_snapshot_is_invalid(
    lifecycle_state: ManagedServiceLifecycleState,
    activation_state: ManagedServiceActivationState,
) -> None:
    """保护未满足 RUNNING 加 INACTIVE 实际状态的服务不能将节点发布为 READY。"""
    events: list[str] = []
    coordination = LocalCoordination()
    runtime = ClusterRuntime(make_cluster("service-a"), coordination)
    runtime.register(
        FakeManagedService(
            "service-a",
            events,
            snapshot_state=(lifecycle_state, activation_state),
        )
    )

    with pytest.raises(RuntimeError):
        await runtime.start()

    assert runtime.state is ClusterRuntimeLifecycleState.FAILED
    assert (await coordination.snapshot()).node_states["node-a"] is not NodeState.READY
    await runtime.stop()
    assert runtime.state is ClusterRuntimeLifecycleState.STOPPED
    assert runtime.coordination_maintenance_running is False
    assert runtime.reconciliation_running is False


@pytest.mark.asyncio
async def test_cluster_runtime_cleans_up_after_partial_start_failure() -> None:
    """保护部分启动失败后可统一停止全部注册服务而无需 Runtime 镜像状态。"""
    events: list[str] = []
    coordination = LocalCoordination()
    runtime = ClusterRuntime(make_cluster("service-a", "service-b", "service-c"), coordination)
    service_a = FakeManagedService("service-a", events)
    service_b = FakeManagedService("service-b", events, start_error=RuntimeError("expected"))
    service_c = FakeManagedService("service-c", events)
    runtime.register(service_a)
    runtime.register(service_b)
    runtime.register(service_c)

    with pytest.raises(RuntimeError, match="expected"):
        await runtime.start()

    assert runtime.state is ClusterRuntimeLifecycleState.FAILED
    assert "service-c.start" not in events

    await runtime.stop()

    assert runtime.state is ClusterRuntimeLifecycleState.STOPPED
    assert "service-a.stop" in events
    assert "service-b.stop" in events
    assert "service-c.stop" in events
    assert "node-a" not in (await coordination.snapshot()).node_states
    assert runtime.coordination_maintenance_running is False
    assert runtime.reconciliation_running is False
