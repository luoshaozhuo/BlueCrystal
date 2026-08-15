"""Seahorse runtime 状态契约。

本文件只表达纯状态和合法转移，不启动线程、asyncio task 或 scheduler。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RuntimePhase(StrEnum):
    """运行态阶段枚举。"""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass(slots=True)
class RuntimeState:
    """运行态状态容器。

    Attributes:
        phase: 当前运行阶段。
        reason: 状态变化原因或失败摘要。
    """

    phase: RuntimePhase = RuntimePhase.CREATED
    reason: str = ""

    def transition_to(self, next_phase: RuntimePhase, *, reason: str = "") -> "RuntimeState":
        """返回转移后的新状态。

        Args:
            next_phase: 目标阶段。
            reason: 状态变化原因。

        Returns:
            新的 RuntimeState；原对象保持不变。

        Raises:
            ValueError: 当状态转移不被允许。
        """
        if next_phase not in _ALLOWED_TRANSITIONS[self.phase]:
            raise ValueError(f"非法 runtime 状态转移: {self.phase.value} -> {next_phase.value}")
        return RuntimeState(phase=next_phase, reason=reason)


_ALLOWED_TRANSITIONS: dict[RuntimePhase, set[RuntimePhase]] = {
    RuntimePhase.CREATED: {RuntimePhase.RUNNING, RuntimePhase.STOPPED, RuntimePhase.ERROR},
    RuntimePhase.RUNNING: {RuntimePhase.PAUSED, RuntimePhase.STOPPED, RuntimePhase.ERROR},
    RuntimePhase.PAUSED: {RuntimePhase.RUNNING, RuntimePhase.STOPPED, RuntimePhase.ERROR},
    RuntimePhase.STOPPED: set(),
    RuntimePhase.ERROR: {RuntimePhase.STOPPED},
}


__all__ = ["RuntimePhase", "RuntimeState"]
