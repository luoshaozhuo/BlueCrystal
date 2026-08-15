"""Seahorse runtime 最小骨架。

本包定义运行态上下文、状态、图、事件总线、快照和同步 tick executor。
executor 只在内存中生成 WriteBatch，不实现真实 50Hz 性能、Starfish writer
或 Whale->WritePlan 读取链路。
"""

from pacific.seahorse.application.runtime.context import RuntimeContext
from pacific.seahorse.application.runtime.event_bus import RuntimeEvent, RuntimeEventBus
from pacific.seahorse.application.runtime.executor import RuntimeExecutor, RuntimeExecutorDiagnostics
from pacific.seahorse.application.runtime.graph import RuntimeGraph, RuntimeNode, RuntimeNodeKind
from pacific.seahorse.application.runtime.snapshot import RuntimeSnapshot
from pacific.seahorse.application.runtime.state import RuntimePhase, RuntimeState

__all__ = [
    "RuntimeContext",
    "RuntimeEvent",
    "RuntimeEventBus",
    "RuntimeExecutor",
    "RuntimeExecutorDiagnostics",
    "RuntimeGraph",
    "RuntimeNode",
    "RuntimeNodeKind",
    "RuntimePhase",
    "RuntimeSnapshot",
    "RuntimeState",
]
