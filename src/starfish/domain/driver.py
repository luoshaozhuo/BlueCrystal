"""starfish driver entry 领域值对象。

本模块只定义 endpoint 与运行时 driver 的装配结果，不定义运行时接口、
协议选择或外部 I/O 行为。driver 字段作为外部边界对象由 application
ports 约束，domain 层保持纯 dataclass/value object。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from starfish.domain.server_config import (
    StarfishEndpointConfig,
    StarfishServerMemberConfig,
)


@dataclass
class DriverEntry:
    """单个 endpoint 的驱动装配结果。"""

    server: StarfishServerMemberConfig
    endpoint: StarfishEndpointConfig
    driver: Any = None
    available: bool = True
    reason: str = ""
    mode: str = "stub"


__all__ = ["DriverEntry"]
