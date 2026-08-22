"""Instrumentation adapter 的最小同步生命周期协议。"""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..manager import ObservabilityRuntime


class Instrumentation(Protocol):
    """可按任意组合安装到 Runtime 的两阶段采集边界。

    ``install`` 在应用启动前修改 route/middleware/listener 结构；``start`` 只启动
    资源，不得再修改框架结构。关闭时先 ``stop`` 资源，再 ``uninstall`` 结构。
    """

    name: str

    def install(self, runtime: ObservabilityRuntime) -> None:
        """在宿主应用启动前安装结构；失败时须支持自身回滚。"""
        ...

    def start(self) -> None:
        """启动运行期资源；无资源的 adapter 实现为空操作。"""
        ...

    def stop(self) -> None:
        """停止运行期资源；必须允许重复关闭流程调用。"""
        ...

    def uninstall(self) -> None:
        """卸载结构；只会在资源停止后调用。"""
        ...
