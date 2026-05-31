"""端口接口定义。

定义调用方契约和实现方责任，相关功能。
"""

from __future__ import annotations

from typing import Protocol

from whale.ingest.ports.source.source_acquisition_port import SourceAcquisitionPort


class SourceAcquisitionPortRegistry(Protocol):
    """根据协议解析采集端口实现。"""

    def get(self, protocol: str) -> SourceAcquisitionPort:
        """返回给定协议注册的采集端口。"""
