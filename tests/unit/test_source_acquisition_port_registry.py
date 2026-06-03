"""StaticSourceAcquisitionPortRegistry 单元测试。

验证静态 acquisition port registry 的多协议标准化解析，
包括新增的 IEC 104 协议 key 标准化和边界行为。
证据等级：L1 unit/mock。
"""

from __future__ import annotations

import pytest
from typing import cast

from whale.ingest.adapters.source.static_source_acquisition_port_registry import (
    StaticSourceAcquisitionPortRegistry,
)
from whale.ingest.ports.source.source_acquisition_port import SourceAcquisitionPort


class DummyPort:
    """用于 registry 测试的占位端口。"""


def test_protocol_keys_are_normalized() -> None:
    port = DummyPort()
    registry = StaticSourceAcquisitionPortRegistry(
        {"opcua": cast(SourceAcquisitionPort, port)}
    )

    assert registry.get("opcua") is port
    assert registry.get("OPC_UA") is port
    assert registry.get("opc-ua") is port


def test_iec104_protocol_key_is_normalized() -> None:
    """IEC 104 协议 key 应能被标准化解析。"""
    port = DummyPort()
    registry = StaticSourceAcquisitionPortRegistry(
        {"iec104": cast(SourceAcquisitionPort, port)}
    )
    assert registry.get("iec104") is port
    assert registry.get("IEC104") is port
    assert registry.get("iec-104") is port
    assert registry.get("IEC_104") is port


def test_unknown_protocol_raises_value_error() -> None:
    registry = StaticSourceAcquisitionPortRegistry({})

    with pytest.raises(ValueError, match="Unsupported acquisition protocol: modbus"):
        registry.get("modbus")
