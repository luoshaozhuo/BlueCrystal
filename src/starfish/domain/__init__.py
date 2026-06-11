"""starfish 领域层入口。

本层承载跨入口共享的稳定契约模型与运行时抽象，不负责文件 I/O、
协议分发或 CLI 编排。
"""

from __future__ import annotations

from starfish.domain.server_config import (
    LoadResult,
    StarfishEndpointConfig,
    StarfishPointConfig,
    StarfishServerConfig,
    StarfishServerMemberConfig,
    UnsupportedOperation,
    ValidationResult,
)
from starfish.domain.driver import DriverEntry, ServerDriver

__all__ = [
    "StarfishServerConfig",
    "StarfishServerMemberConfig",
    "StarfishEndpointConfig",
    "StarfishPointConfig",
    "LoadResult",
    "ValidationResult",
    "UnsupportedOperation",
    "ServerDriver",
    "DriverEntry",
]
