"""协调后端适配器；第一阶段仅提供进程内 Local 实现。"""

from .local import LocalCoordination

__all__ = ["LocalCoordination"]
