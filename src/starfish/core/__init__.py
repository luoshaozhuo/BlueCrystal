"""Starfish 核心运行时模型。

本包是 Hexagonal Architecture 的 core。它定义 simulator server 的纯
definition、生命周期 port 和 manager 编排逻辑，不直接依赖 DB view、
CLI、IEC104 native runner 或其他外部 adapter。
"""

from __future__ import annotations

from starfish.core.definitions import (
    PointItemDefinition,
    ServerDefinition,
    ServerStatus,
    TaskDefinition,
)
from starfish.core.manager import StarfishServerManager

__all__ = [
    "PointItemDefinition",
    "ServerDefinition",
    "ServerStatus",
    "TaskDefinition",
    "StarfishServerManager",
]
