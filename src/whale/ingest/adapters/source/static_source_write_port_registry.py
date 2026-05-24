"""Static source write port registry.

与 StaticSourceAcquisitionPortRegistry 风格对齐。
负责按标准化 protocol key 解析写端口。
"""

from __future__ import annotations

from collections.abc import Mapping

from whale.ingest.ports.source.source_write_port import SourceWritePort


class StaticSourceWritePortRegistry:
    """通过静态映射解析写端口。"""

    def __init__(self, ports_by_protocol: Mapping[str, SourceWritePort]) -> None:
        self._ports_by_protocol: dict[str, SourceWritePort] = {}
        for protocol, port in ports_by_protocol.items():
            self._ports_by_protocol[self._normalize_protocol_key(protocol)] = port

    def get(self, protocol: str) -> SourceWritePort:
        normalized = self._normalize_protocol_key(protocol)
        try:
            return self._ports_by_protocol[normalized]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported write protocol: {protocol}. "
                "Supported protocols: " + ", ".join(sorted(self._ports_by_protocol.keys()))
            ) from exc

    @staticmethod
    def _normalize_protocol_key(protocol: str) -> str:
        return protocol.strip().lower().replace("_", "").replace("-", "")
