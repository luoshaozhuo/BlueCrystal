"""本地 ManagedService 注册表。

注册表只维护当前进程中 ``service_id → ManagedService`` 的引用关系，不负责服务发现、
Ownership 仲裁或真实运行体的构造。注册在 Runtime 启动前完成，避免运行期拓扑歧义。
"""

from __future__ import annotations

from ..managed import ManagedService


class ManagedServiceRegistry:
    """按稳定 service_id 保存本节点已注册的 ManagedService。"""

    def __init__(self) -> None:
        """初始化空注册表；字典插入顺序定义确定性的启动顺序。"""
        self._services: dict[str, ManagedService] = {}

    def add(self, service: ManagedService) -> None:
        """注册一个服务，并拒绝重复标识覆盖既有实例。

        Args:
            service: 将由 Runtime 统一托管的服务实例。

        Raises:
            ValueError: service_id 为空或已经被其他实例注册。
        """
        service_id = service.service_id
        if not service_id:
            raise ValueError("ManagedService.service_id 不能为空")
        if service_id in self._services:
            raise ValueError(f"ManagedService 已注册: {service_id}")
        self._services[service_id] = service

    def get(self, service_id: str) -> ManagedService:
        """根据 service_id 返回已注册实例；不存在时传播 KeyError。"""
        return self._services[service_id]

    def list(self) -> tuple[ManagedService, ...]:
        """按注册顺序返回服务快照，防止调用方修改注册表。"""
        return tuple(self._services.values())

    def service_ids(self) -> frozenset[str]:
        """返回当前注册的稳定标识集合，用于启动前一致性校验。"""
        return frozenset(self._services)
