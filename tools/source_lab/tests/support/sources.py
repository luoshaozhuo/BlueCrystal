"""source_lab 测试 source helper 兼容层。

本模块复用当前 `tools.source_lab.sources` 中的正式实现，避免旧测试在导入阶段失效。
"""

from tools.source_lab.sources import (
    PortAllocator,
    _is_tcp_port_available,
    build_multi_sources,
)

__all__ = [
    "PortAllocator",
    "_is_tcp_port_available",
    "build_multi_sources",
]
