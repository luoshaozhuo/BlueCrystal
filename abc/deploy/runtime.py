"""ClusterRuntime 生命周期与一级模块的编排实现。

本模块只编排 Coordination、ManagedService Management、Coordination Maintenance 和
Reconciliation Control 的确定启动/关闭顺序；不直接调用具体运行框架，也不实现真实分布式
Failover、Failback 或多活。启动失败会保留 FAILED 事实，调用方仍可通过 ``stop`` 进入统一
资源清理路径。
"""

from __future__ import annotations

from .core.cluster_coordination import ClusterCoordination
from .core.coordination_maintenance import CoordinationMaintenance
from .core.managed_service_management import ManagedServiceManagement
from .core.reconciler import ActualFacts, DesiredState, Reconciler
from .core.reconciliation import ReconciliationControl
from .managed import ManagedService
from .model.cluster import ClusterModel
from .model.state import ClusterRuntimeLifecycleState
from .ports.coordination import CoordinationPort


class ClusterRuntime:
    """当前节点 Deploy Runtime 的单次生命周期编排器。

    Runtime 从 CREATED 只能进入一次启动路径；到达 STOPPED 后不可重启。ManagedService
    应在 ``start`` 前注册，启动顺序固定为 Coordination、Coordination Maintenance、Service
    Management、READY、Reconciliation；关闭则先停止 Reconciliation，再停用服务、释放
    Ownership、停止服务、离开集群并停止 Coordination Maintenance。
    """

    def __init__(
        self,
        cluster: ClusterModel,
        coordination_port: CoordinationPort,
        *,
        reconciler: Reconciler | None = None,
        reconciliation_interval_seconds: float = 1.0,
        coordination_maintenance_interval_seconds: float = 1.0,
    ) -> None:
        """构造未启动的 Runtime，并装配 Coordination 与两个长期控制单元。

        Args:
            cluster: 已完成基础校验的静态 Cluster 模型。
            coordination_port: 提供 Membership 与 Ownership 事实的适配器。
            reconciler: 可替换的纯决策器；默认使用第一阶段空计划实现。
            reconciliation_interval_seconds: 控制循环最长等待间隔。
            coordination_maintenance_interval_seconds: Coordination Maintenance 循环最长等待间隔。
        """
        self._cluster = cluster
        self._state = ClusterRuntimeLifecycleState.CREATED
        self._failure: Exception | None = None
        self._service_management = ManagedServiceManagement()
        self._coordination = ClusterCoordination(cluster.local_node_id, coordination_port)
        self._coordination_maintenance = CoordinationMaintenance(
            self._maintain_coordination_once,
            interval_seconds=coordination_maintenance_interval_seconds,
        )
        self._reconciler = reconciler or Reconciler()
        self._reconciliation = ReconciliationControl(
            self._reconcile_once,
            interval_seconds=reconciliation_interval_seconds,
        )

    @property
    def state(self) -> ClusterRuntimeLifecycleState:
        """返回 Runtime 自己的生命周期事实，不代表服务或 Ownership 状态。"""
        return self._state

    @property
    def failure(self) -> Exception | None:
        """返回导致 Runtime 进入 FAILED 的启动或关闭阶段异常。"""
        return self._failure

    @property
    def service_management(self) -> ManagedServiceManagement:
        """暴露服务管理门面供宿主读取受管服务快照。"""
        return self._service_management

    @property
    def coordination_maintenance_running(self) -> bool:
        """返回 Coordination Maintenance 后台任务是否仍在运行，不暴露其控制接口。"""
        return self._coordination_maintenance.is_running

    @property
    def reconciliation_running(self) -> bool:
        """返回 Reconciliation 后台任务是否仍在运行，不暴露其控制接口。"""
        return self._reconciliation.is_running

    def register(self, service: ManagedService) -> None:
        """在启动前注册一个本节点 ManagedService。

        Args:
            service: 由业务模块实现的生命周期封装实例。

        Raises:
            RuntimeError: Runtime 已开始生命周期，注册拓扑不可再变更。
            ValueError: service_id 不在 Cluster 静态服务定义内或出现重复注册。
        """
        if self._state is not ClusterRuntimeLifecycleState.CREATED:
            raise RuntimeError("只能在 ClusterRuntime.start() 前注册 ManagedService")
        configured_ids = {spec.service_id for spec in self._cluster.managed_services}
        if service.service_id not in configured_ids:
            raise ValueError(f"ManagedService 未在 ClusterModel 中定义: {service.service_id}")
        self._service_management.register(service)

    async def start(self) -> None:
        """按确定顺序启动协调、维护、服务与 Reconciliation Control。

        Raises:
            RuntimeError: 当前实例不是可启动的 CREATED 状态。
            Exception: 任一关键启动单元失败时保留 FAILED 事实后传播原异常。
        """
        if self._state is not ClusterRuntimeLifecycleState.CREATED:
            raise RuntimeError(f"不能从 {self._state} 启动 ClusterRuntime")
        self._validate_registration()
        self._state = ClusterRuntimeLifecycleState.STARTING
        try:
            await self._coordination.start()
            await self._coordination_maintenance.start()
            await self._service_management.start_all()
            await self._coordination.mark_ready()
            await self._reconciliation.start()
        except Exception as exc:
            self._failure = exc
            self._state = ClusterRuntimeLifecycleState.FAILED
            raise
        self._state = ClusterRuntimeLifecycleState.RUNNING

    async def stop(self) -> None:
        """执行统一关闭编排，并在各清理单元间继续尝试回收资源。

        关闭顺序禁止 Reconciliation 继续产生 Acquire/Activate 计划，然后依次标记节点
        LEAVING、停用服务、释放本地 Ownership、停止服务并离开协调域。清理异常会被
        聚合后传播，同时 Runtime 保持 FAILED 事实，调用方可据此人工处置。
        """
        if self._state is ClusterRuntimeLifecycleState.STOPPED:
            return
        if self._state is ClusterRuntimeLifecycleState.CREATED:
            self._state = ClusterRuntimeLifecycleState.STOPPED
            return
        self._state = ClusterRuntimeLifecycleState.STOPPING
        errors: list[Exception] = []
        for cleanup in (
            self._reconciliation.stop,
            self._coordination.begin_leaving,
            self._service_management.deactivate_active,
            self._coordination.release_local_ownerships,
            self._service_management.stop_all,
            self._coordination.leave,
            self._coordination_maintenance.stop,
        ):
            try:
                await cleanup()
            except Exception as exc:
                errors.append(exc)
        if errors:
            failure = ExceptionGroup("ClusterRuntime 关闭阶段失败", errors)
            self._failure = failure
            self._state = ClusterRuntimeLifecycleState.FAILED
            raise failure
        self._state = ClusterRuntimeLifecycleState.STOPPED

    async def close(self) -> None:
        """作为宿主程序资源清理入口调用 stop，保留同一状态机语义。"""
        await self.stop()

    async def _reconcile_once(self) -> None:
        """读取权威快照并调用纯 Reconciler；第一阶段空计划不产生控制副作用。"""
        actual = ActualFacts(
            coordination=await self._coordination.snapshot(),
            services=self._service_management.snapshots(),
        )
        self._reconciler.reconcile(DesiredState(self._cluster), actual)

    async def _maintain_coordination_once(self) -> None:
        """读取 Coordination 的权威事实，为后续维护算法保留安全生命周期入口。

        第一阶段不续租、不改变 Membership、不操作 Ownership，也不影响 ManagedService 的
        Activation；读取快照仅验证长期维护 Task 可以在 Runtime 生命周期内安全运行。
        """
        await self._coordination.snapshot()

    def _validate_registration(self) -> None:
        """确保静态模型与本节点已注册对象一一对应，避免启动半配置 Runtime。"""
        expected = {spec.service_id for spec in self._cluster.managed_services}
        actual = self._service_management.registry.service_ids()
        if expected != actual:
            missing = ", ".join(sorted(expected - actual))
            unexpected = ", ".join(sorted(actual - expected))
            details = []
            if missing:
                details.append(f"缺少注册服务: {missing}")
            if unexpected:
                details.append(f"未定义注册服务: {unexpected}")
            raise ValueError("; ".join(details))
