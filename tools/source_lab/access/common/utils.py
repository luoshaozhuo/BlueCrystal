"""接入层通用工具函数。

负责：协议名称归一化等跨模块共享的轻量工具。
不负责：状态管理、IO 操作。
"""

from __future__ import annotations


def normalize_protocol(value: str) -> str:
    """Normalize protocol name for robust comparisons."""

    return value.strip().lower().replace("_", "").replace("-", "")
