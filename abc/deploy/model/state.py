"""Deploy Runtime 共享状态枚举。

这些类型只表达运行事实或生命周期，不能把 Node、Ownership 与 Runtime 生命周期
压缩为一个全局状态机；其权威来源分别是协调后端、ManagedService 和 Runtime 自身。
"""

from enum import StrEnum


class ClusterRuntimeLifecycleState(StrEnum):
    """ClusterRuntime 单次生命周期状态。"""

    CREATED = "CREATED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class NodeState(StrEnum):
    """协调后端发布的节点参与状态。"""

    JOINING = "JOINING"
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"
    LEAVING = "LEAVING"
    DOWN = "DOWN"


class ManagedServiceLifecycleState(StrEnum):
    """ManagedService 对真实运行体归一化后的生命周期状态。"""

    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    FAILED = "FAILED"


class ManagedServiceActivationState(StrEnum):
    """ManagedService 是否允许执行 Active 业务的正交状态。""

    INACTIVE = "INACTIVE"
    ACTIVATING = "ACTIVATING"
    ACTIVE = "ACTIVE"
    DEACTIVATING = "DEACTIVATING"
