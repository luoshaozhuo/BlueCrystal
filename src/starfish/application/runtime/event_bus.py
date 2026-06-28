"""RuntimeEvent 与 RuntimeEventBus 应用层事件缓冲。

本模块提供进程内、非外部依赖的事件尾部查询能力。不负责持久化、不发送到
Prometheus / OTEL / Kafka 等外部系统，也不改变 driver 执行语义。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RuntimeEvent:
    """Starfish runtime 统一事件记录。

    Attributes:
        ts: 事件发生时间，使用 `time.time()` 秒级浮点时间戳。
        type: 事件类型，取值为 START / STOP / READ / WRITE / SWAP / ERROR。
        node_id: RuntimeGraph node id。
        instance_id: DriverInstance id。
        driver: driver 协议或运行模式标识。
        payload: 事件附加信息；仅保存轻量上下文，不承载外部 I/O 资源。
    """

    ts: float
    type: str
    node_id: str
    instance_id: str
    driver: str
    payload: dict[str, Any] = field(default_factory=dict)


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


__all__ = ["RuntimeEvent", "RuntimeEventBus"]
