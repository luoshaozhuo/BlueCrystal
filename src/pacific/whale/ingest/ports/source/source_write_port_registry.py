"""端口接口定义。

定义调用方契约和实现方责任，相关功能。
"""

from __future__ import annotations

from typing import Protocol

from pacific.whale.ingest.ports.source.source_write_port import SourceWritePort


class SourceWritePortRegistry(Protocol):
    """根据协议解析写入端口实现。"""

    def get(self, protocol: str) -> SourceWritePort:
        """返回给定协议注册的写入端口。"""
