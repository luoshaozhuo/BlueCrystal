"""静态 source acquisition port registry。

本模块负责按标准化 protocol key 解析采集端口。
"""

from __future__ import annotations

from collections.abc import Mapping

from whale.ingest.ports.source.source_acquisition_port import SourceAcquisitionPort


class StaticSourceAcquisitionPortRegistry:
    """通过静态映射解析采集端口。"""

    def __init__(self, ports_by_protocol: Mapping[str, SourceAcquisitionPort]) -> None:
        """保存按协议配置的端口映射。"""

        self._ports_by_protocol = {
            self._normalize_protocol_key(protocol): port
            for protocol, port in ports_by_protocol.items()
        }

    def get(self, protocol: str) -> SourceAcquisitionPort:
        """返回指定协议的采集端口。"""

        normalized = self._normalize_protocol_key(protocol)
        try:
            return self._ports_by_protocol[normalized]
        except KeyError as exc:
            raise ValueError(f"Unsupported acquisition protocol: {protocol}") from exc

    @staticmethod
    def _normalize_protocol_key(protocol: str) -> str:
        """标准化协议 key。"""

        return protocol.strip().lower().replace("_", "").replace("-", "")
