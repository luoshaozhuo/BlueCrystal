"""写入安全配置文件。

定义设备写入操作的安全策略配置，
包括允许的写入范围、速率限制和审批要求。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ReadbackStrategy(Enum):
    """写入 readback 校验的执行方式。"""

    DISABLED = "disabled"
    IMMEDIATE_READBACK = "immediate_readback"
    ASYNC_CONFIRMATION = "async_confirmation"


@dataclass(frozen=True, slots=True)
class ProtocolWriteProfile:
    """单个协议的写入操作安全配置。"""

    allowed: bool = False
    readback_strategy: ReadbackStrategy = ReadbackStrategy.DISABLED
    required_roles: tuple[str, ...] = field(default_factory=lambda: ("admin",))
    max_items_per_write: int = 100


@dataclass(frozen=True, slots=True)
class WriteSecurityProfile:
    """写/控制操作安全策略。定义各协议写入的安全级别、确认模式和校验规则。"""

    default_readback_strategy: ReadbackStrategy = ReadbackStrategy.DISABLED
    default_required_roles: tuple[str, ...] = field(default_factory=lambda: ("admin",))
    default_max_items_per_write: int = 100
    protocols: dict[str, ProtocolWriteProfile] = field(default_factory=dict)

    def profile_for(self, protocol: str) -> ProtocolWriteProfile:
        """获取指定协议的解析后安全策略。按协议名查找配置并返回合并的策略对象。"""
        normalized = protocol.strip().lower()
        if normalized in self.protocols:
            return self.protocols[normalized]
        return ProtocolWriteProfile()

    def is_write_allowed(self, protocol: str) -> bool:
        """获取指定协议的解析后安全策略。按协议类型查找对应配置并返回合并后的安全策略。

Returns a protocol-specific entry if one is configured, otherwise
the implicit default (deny-all)."""
        return self.profile_for(protocol).allowed
