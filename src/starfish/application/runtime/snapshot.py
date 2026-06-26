"""RuntimeSnapshot 领域快照模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from starfish.application.runtime.event import RuntimeEvent
from starfish.application.runtime.state import RuntimeState


@dataclass(frozen=True)
class RuntimeSnapshot:
    """Starfish runtime 的只读系统切片。

    Attributes:
        timestamp: 快照生成时间，使用 `time.time()` 秒级浮点时间戳。
        graph: 当前 RuntimeGraph；为避免领域模型循环 import，此处保持运行图对象引用。
        states: 当前 DriverInstance 状态列表。
        events_tail: 最近事件列表。
    """

    timestamp: float
    graph: Any
    states: list[RuntimeState] = field(default_factory=list)
    events_tail: list[RuntimeEvent] = field(default_factory=list)


__all__ = ["RuntimeSnapshot"]
