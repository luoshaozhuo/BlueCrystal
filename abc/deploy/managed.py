"""受管长期运行单元的公共生命周期契约。

Deploy Runtime 只通过本模块的契约控制业务模块提供的 ManagedService，不会接触
其内部的 Uvicorn、Kafka、Scheduler 或自定义 worker。具体服务必须自行归一化
真实运行体状态，并在异常退出后反映到 ``wait`` 或 ``snapshot``。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .model.ownership import Ownership
from .model.state import ManagedServiceActivationState, ManagedServiceLifecycleState


@dataclass(frozen=True, slots=True)
class ManagedServiceSnapshot:
    """ManagedService 对外声明的实际运行事实。

    Args:
        service_id: 服务的稳定注册标识。
        lifecycle_state: 已归一化的真实运行生命周期状态。
        activation_state: 是否允许发起 Active 业务的事实状态。
        error_message: 正常状态为 ``None``；异常退出时提供可安全暴露的错误摘要。
    """

    service_id: str
    lifecycle_state: ManagedServiceLifecycleState
    activation_state: ManagedServiceActivationState
    error_message: str | None = None


@runtime_checkable
class ManagedService(Protocol):
    """可独立运行或可由 Deploy Runtime 托管的长期运行单元。

    实现方负责真实运行体的创建、启动、停止和异常归一化。``activate`` 接收到的
    Ownership 是当前有效执行代次；需要保护下游副作用的实现应将 fencing token
    继续传递到受保护边界。
    """

    @property
    def service_id(self) -> str:
        """返回用于本地注册和静态配置匹配的稳定服务标识。"""

    async def start(self) -> None:
        """启动真实运行体并等待稳定初始状态。

        成功返回时，``snapshot`` 必须已报告 ``RUNNING`` 与 ``INACTIVE``。底层运行体
        若异步完成启动，实现方必须在此方法内等待，不得将该等待责任泄漏给 Deploy Runtime。
        """

    async def activate(self, ownership: Ownership | None = None) -> None:
        """允许服务发起 Active 业务；托管模式会传入已确认的 Ownership。"""

    async def deactivate(self) -> None:
        """停止发起新的 Active 业务，并保证对未激活状态幂等。

        已经 ``INACTIVE``、尚未启动或尚未进入 ``ACTIVE`` 的服务调用本方法必须安全返回；
        正常返回后，``snapshot`` 必须稳定报告 ``INACTIVE``。本方法不等同于停止真实运行体。
        """

    async def stop(self) -> None:
        """有序停止真实运行体，并保证 cleanup 对任意本地生命周期阶段幂等。

        尚未启动或已经 ``STOPPED`` 的服务调用本方法必须安全返回，重复调用不得重复破坏底层
        资源。正常返回后，``snapshot`` 必须稳定报告 ``STOPPED``；Runtime 因而无需镜像记录
        哪些服务曾成功启动。
        """

    async def wait(self) -> None:
        """等待真实运行体正常结束或异常退出；退出事实必须可由 snapshot 观察。"""

    def snapshot(self) -> ManagedServiceSnapshot:
        """返回当前实际状态，不能以控制调用成功代替实际状态。"""
