"""Deploy Runtime 第一阶段公共 API。

本包提供当前节点集群运行时的生命周期骨架、受管服务契约和进程内协调适配器。
它不提供具体 Web、消息或调度框架的集成，也不把 Local Coordination 误作分布式
HA 控制面。
"""

from .managed import ManagedService, ManagedServiceSnapshot
from .runtime import ClusterRuntime

__all__ = ["ClusterRuntime", "ManagedService", "ManagedServiceSnapshot"]
