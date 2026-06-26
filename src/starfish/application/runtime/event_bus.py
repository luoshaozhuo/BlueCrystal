"""RuntimeEventBus 应用层事件缓冲。

本模块提供进程内、非外部依赖的事件尾部查询能力。不负责持久化、不发送到
Prometheus / OTEL / Kafka 等外部系统，也不改变 driver 执行语义。
"""

from __future__ import annotations

from starfish.application.runtime.event import RuntimeEvent


class RuntimeEventBus:
    """Starfish runtime 进程内事件总线。"""

    def __init__(self) -> None:
        """初始化空事件列表。"""
        self._events: list[RuntimeEvent] = []

    def emit(self, event: RuntimeEvent) -> None:
        """追加一条 runtime event。

        Args:
            event: 已构造好的 RuntimeEvent。
        """
        self._events.append(event)

    def tail(self, n: int = 100) -> list[RuntimeEvent]:
        """返回最近 n 条事件。

        Args:
            n: 需要返回的尾部事件数。

        Returns:
            RuntimeEvent 列表副本。
        """
        return list(self._events[-n:])


__all__ = ["RuntimeEventBus"]
