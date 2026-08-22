"""可选 instrumentation 的框架无关公共契约。

具体框架 adapter 应通过其子模块或 ``ObservabilityRuntime`` 按需加载。
"""

from .base import Instrumentation
from .registry import InstrumentationRegistry
from .task_scheduler import observe_scheduler_action

__all__ = [
    "Instrumentation",
    "InstrumentationRegistry",
    "observe_scheduler_action",
]
