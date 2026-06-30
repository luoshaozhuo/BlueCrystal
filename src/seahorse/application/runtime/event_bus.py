"""Seahorse runtime 事件总线骨架。

当前事件总线只作为内存事件记录器，避免误表达为真实异步 bus 或
runtime scheduler。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

RuntimeEventValue = str | int | float | bool | None
"""运行时事件载荷允许的标量值。"""


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    """运行时事件。

    Attributes:
        event_type: 事件类型。
        occurred_at: 事件发生时间。
        payload: 事件载荷，限制在应用层可理解的纯数据。
    """

    event_type: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, RuntimeEventValue] = field(default_factory=dict)


@dataclass(slots=True)
class RuntimeEventBus:
    """内存事件记录器。

    仅用于未来运行时设计的强类型占位，不提供订阅线程、队列或网络传输。
    """

    events: list[RuntimeEvent] = field(default_factory=list)

    def publish(self, event: RuntimeEvent) -> None:
        """记录一个事件。

        Args:
            event: 纯内存运行时事件。
        """
        self.events.append(event)


__all__ = ["RuntimeEvent", "RuntimeEventBus", "RuntimeEventValue"]
