"""Source write port registry 单元测试。"""

from __future__ import annotations

import pytest

from whale.ingest.adapters.source.static_source_write_port_registry import (
    StaticSourceWritePortRegistry,
)
from whale.ingest.ports.source.source_write_port import SourceWritePort


class _FakeWritePort(SourceWritePort):
    """假写端口，用于注册表测试。"""

    async def write(self, execution, connection, items):
        from whale.ingest.usecases.dtos.source_write_result import SourceWriteResult
        return SourceWriteResult(
            request_id="test", dry_run=True,
            success_count=0, failure_count=0,
        )


class TestStaticSourceWritePortRegistry:
    """StaticSourceWritePortRegistry 行为测试。"""

    def setup_method(self) -> None:
        self._opcua_port = _FakeWritePort()
        self._registry = StaticSourceWritePortRegistry(
            ports_by_protocol={"opcua": self._opcua_port},
        )

    def test_get_known_protocol(self) -> None:
        """已知协议应返回注册的写端口。"""
        port = self._registry.get("opcua")
        assert port is self._opcua_port

    def test_get_known_protocol_normalized(self) -> None:
        """不同格式的协议名应标准化后匹配。"""
        for alias in ("opcua", "OPCUA", "opc_ua", "opc-ua", "OPC-UA"):
            port = self._registry.get(alias)
            assert port is self._opcua_port, f"Failed for alias: {alias}"

    def test_get_unknown_protocol_raises(self) -> None:
        """未知协议应抛出 ValueError。"""
        with pytest.raises(ValueError, match="Unsupported write protocol"):
            self._registry.get("modbus_tcp")

    def test_get_empty_registry_raises(self) -> None:
        """空注册表应抛出 ValueError。"""
        empty = StaticSourceWritePortRegistry(ports_by_protocol={})
        with pytest.raises(ValueError, match="Unsupported write protocol"):
            empty.get("opcua")

    def test_protocol_normalize_key(self) -> None:
        """标准化方法应去除分隔符并转小写。"""
        assert StaticSourceWritePortRegistry._normalize_protocol_key("OPC-UA") == "opcua"
        assert StaticSourceWritePortRegistry._normalize_protocol_key("opc_ua") == "opcua"
        assert StaticSourceWritePortRegistry._normalize_protocol_key("modbus_tcp") == "modbustcp"
        assert StaticSourceWritePortRegistry._normalize_protocol_key(" IEC104 ") == "iec104"

    def test_get_iec104_protocol(self) -> None:
        """IEC 104 应能被注册和解析。"""
        iec104_port = _FakeWritePort()
        registry = StaticSourceWritePortRegistry(
            ports_by_protocol={"iec104": iec104_port},
        )
        for alias in ("iec104", "IEC104", "iec-104", "IEC_104"):
            port = registry.get(alias)
            assert port is iec104_port, f"Failed for alias: {alias}"
