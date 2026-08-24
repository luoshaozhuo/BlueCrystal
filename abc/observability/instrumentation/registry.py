"""Instrumentation 注册表和失败回滚生命周期。"""

from __future__ import annotations

from .base import Instrumentation

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..runtime import ObservabilityRuntime


class InstrumentationRegistry:
    """按两阶段契约安装、启动、停止并卸载 instrumentation adapter。"""

    def __init__(
        self,
        runtime: ObservabilityRuntime,
    ) -> None:
        self._runtime = runtime
        self._items: list[Instrumentation] = []
        self._installed: list[Instrumentation] = []
        self._started = False

    def register(self, instrumentation: Instrumentation) -> None:
        """在宿主启动前安装并注册 adapter。

        Raises:
            ValueError: 同一 adapter 实例被重复注册。
            RuntimeError: Runtime 已启动，不能再修改宿主结构。
        """
        if instrumentation in self._items:
            raise ValueError(f"instrumentation already registered: {instrumentation.name}")
        if self._started:
            raise RuntimeError("instrumentation must be installed before runtime.start()")
        try:
            instrumentation.install(self._runtime)
        except Exception as install_error:
            # adapter 可能在抛错前已产生部分结构副作用，立即请求自身回滚。
            try:
                instrumentation.uninstall()
            except Exception as cleanup_error:
                _attach_cleanup_error(
                    install_error,
                    phase="install rollback uninstall",
                    cleanup_error=cleanup_error,
                )
            raise
        self._items.append(instrumentation)
        self._installed.append(instrumentation)

    async def start(self) -> None:
        """启动 adapter 资源；不在宿主 lifespan 内修改 route/middleware。"""
        if self._started:
            return
        started_now: list[Instrumentation] = []
        current: Instrumentation | None = None
        try:
            for item in self._installed:
                current = item
                item.start()
                started_now.append(item)
                current = None
        except Exception as startup_error:
            # 宿主启动失败时完整回滚资源和预装结构，避免残留半安装应用。
            if current is not None:
                try:
                    # start 可能在抛错前已经获取资源，因此失败项也必须先 stop。
                    current.stop()
                except Exception as exc:
                    _attach_cleanup_error(
                        startup_error,
                        phase=f"stop failed adapter {current.name}",
                        cleanup_error=exc,
                    )
            for item in reversed(started_now):
                try:
                    item.stop()
                except Exception as exc:
                    _attach_cleanup_error(
                        startup_error,
                        phase=f"stop started adapter {item.name}",
                        cleanup_error=exc,
                    )
            for item in reversed(self._installed):
                try:
                    item.uninstall()
                except Exception as exc:
                    _attach_cleanup_error(
                        startup_error,
                        phase=f"uninstall adapter {item.name}",
                        cleanup_error=exc,
                    )
            self._installed.clear()
            self._items.clear()
            raise
        self._started = True

    async def shutdown(self) -> None:
        """逆序停止资源并卸载结构；重复调用不产生额外副作用。"""
        if not self._installed:
            return
        first_error: Exception | None = None
        if self._started:
            for item in reversed(self._installed):
                try:
                    item.stop()
                except Exception as exc:
                    # 继续释放其他资源，最终向调用方报告首个清理失败。
                    if first_error is None:
                        first_error = exc
                    else:
                        _attach_cleanup_error(
                            first_error,
                            phase=f"stop adapter {item.name}",
                            cleanup_error=exc,
                        )
        for item in reversed(self._installed):
            try:
                item.uninstall()
            except Exception as exc:
                # 结构卸载失败不阻止其余 adapter 释放。
                if first_error is None:
                    first_error = exc
                else:
                    _attach_cleanup_error(
                        first_error,
                        phase=f"uninstall adapter {item.name}",
                        cleanup_error=exc,
                    )
        self._installed.clear()
        self._started = False
        if first_error is not None:
            raise first_error

    def get_instrumentations(self) -> tuple[Instrumentation, ...]:
        """返回注册顺序稳定的 adapter 快照。"""
        return tuple(self._items)


def _attach_cleanup_error(
    primary: Exception,
    *,
    phase: str,
    cleanup_error: Exception,
) -> None:
    """把清理失败附加到首要异常，同时保持调用方的异常分类不变。"""
    primary.add_note(
        f"cleanup failure during {phase}: "
        f"{type(cleanup_error).__qualname__}: {cleanup_error}"
    )
