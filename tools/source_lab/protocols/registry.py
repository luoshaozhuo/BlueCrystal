"""多协议 simulator 工厂注册表。"""

from __future__ import annotations

from collections.abc import Callable

from tools.source_lab.access.runners.registry import normalize_protocol
from tools.source_lab.contracts import SourceSimulator
from tools.source_lab.model import SimulatedSource
from tools.source_lab.opcua.open62541_source_simulator import Open62541SourceSimulator
from tools.source_lab.protocols.common.simulators import build_simulator_for_protocol


def _unsupported_simulator_factory(protocol: str) -> Callable[[SimulatedSource], SourceSimulator]:
    """构建不支持协议的 simulator 工厂。

    Args:
        protocol: 归一化后的协议名。

    Returns:
        抛出明确错误的工厂函数。
    """

    def _factory(source: SimulatedSource) -> SourceSimulator:
        raise ValueError(
            "source simulator not implemented for protocol: "
            f"{protocol}; endpoint={source.connection.host}:{source.connection.port}"
        )

    return _factory


def get_simulator_factory(protocol: str) -> Callable[[SimulatedSource], SourceSimulator]:
    """返回协议对应的 simulator 工厂。"""

    normalized = normalize_protocol(protocol)
    if normalized == "opcua":
        return Open62541SourceSimulator
    if normalized in {
        "modbus_tcp",
        "modbus_rtu",
        "iec101",
        "iec104",
        "iec61850_mms",
        "iec61850_report",
        "mqtt",
        "http_rest",
    }:
        return lambda source: build_simulator_for_protocol(normalized, source)
    return _unsupported_simulator_factory(normalized)
