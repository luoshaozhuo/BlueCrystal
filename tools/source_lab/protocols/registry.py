"""多协议 simulator 工厂注册表。

支持两种工厂：
1. ``get_simulator_factory`` — 旧版同步 SourceSimulator 工厂（向后兼容）。
2. ``create_server_simulator`` — 新版异步 ServerSimulatorFacade 工厂。
"""

from __future__ import annotations

from collections.abc import Callable

from tools.source_lab.access.runners.registry import normalize_protocol
from tools.source_lab.contracts import SourceSimulator
from tools.source_lab.model import SimulatedSource
from tools.source_lab.protocols.opcua.open62541_source_simulator import Open62541SourceSimulator
from tools.source_lab.protocols.common.simulator_facade import ServerSimulatorFacade
from tools.source_lab.protocols.common.simulator_models import SimulatorCapabilities
from tools.source_lab.protocols.common.simulators import build_simulator_for_protocol


# ── ServerSimulatorFacade 映射表 ──────────────────────────────────────

_SIMULATOR_FACADE_REGISTRY: dict[str, type] = {}


def _register_facade(protocol: str, facade_cls: type) -> None:
    _SIMULATOR_FACADE_REGISTRY[protocol] = facade_cls


# 延迟导入以避免循环依赖
def _lazy_register() -> None:
    if _SIMULATOR_FACADE_REGISTRY:
        return
    # pylint: disable=import-outside-toplevel
    from tools.source_lab.protocols.http_rest.simulator import HttpRestSimulatorFacade
    from tools.source_lab.protocols.iec101.simulator import Iec101SimulatorFacade
    from tools.source_lab.protocols.iec104.simulator import Iec104SimulatorFacade
    from tools.source_lab.protocols.iec61850.simulator import (
        Iec61850GooseSimulatorFacade,
        Iec61850MmsSimulatorFacade,
        Iec61850ReportSimulatorFacade,
        Iec61850SvSimulatorFacade,
    )
    from tools.source_lab.protocols.modbus.simulator import (
        ModbusRtuSimulatorFacade,
        ModbusTcpSimulatorFacade,
    )
    from tools.source_lab.protocols.mqtt.simulator import MqttSimulatorFacade
    from tools.source_lab.protocols.opcua.simulator import OpcUaSimulatorFacade

    _register_facade("opcua", OpcUaSimulatorFacade)
    _register_facade("modbus_tcp", ModbusTcpSimulatorFacade)
    _register_facade("modbus_rtu", ModbusRtuSimulatorFacade)
    _register_facade("iec101", Iec101SimulatorFacade)
    _register_facade("iec104", Iec104SimulatorFacade)
    _register_facade("iec61850_mms", Iec61850MmsSimulatorFacade)
    _register_facade("iec61850_report", Iec61850ReportSimulatorFacade)
    _register_facade("iec61850_goose", Iec61850GooseSimulatorFacade)
    _register_facade("iec61850_sv", Iec61850SvSimulatorFacade)
    _register_facade("mqtt", MqttSimulatorFacade)
    _register_facade("http_rest", HttpRestSimulatorFacade)


def create_server_simulator(
    protocol: str,
    source: SimulatedSource | None = None,
) -> ServerSimulatorFacade:
    """创建协议对应的 ServerSimulatorFacade 实例。

    Args:
        protocol: 归一化后的协议名。
        source: 可选的 SimulatedSource，start() 时需要。

    Returns:
        ServerSimulatorFacade 实例（满足 ``tools.source_lab.protocols.common.simulator_facade.ServerSimulatorFacade`` Protocol）。

    Raises:
        ValueError: 协议没有对应的 facade 实现。
    """
    _lazy_register()
    normalized = normalize_protocol(protocol)
    cls = _SIMULATOR_FACADE_REGISTRY.get(normalized)
    if cls is None:
        raise ValueError(
            f"no ServerSimulatorFacade for protocol {normalized!r} "
            f"(from input {protocol!r})"
        )
    return cls(source=source)


def get_server_simulator_capabilities(protocol: str) -> SimulatorCapabilities:
    """返回协议 simulator 的能力矩阵（无需创建实例）。"""
    _lazy_register()
    normalized = normalize_protocol(protocol)
    cls = _SIMULATOR_FACADE_REGISTRY.get(normalized)
    if cls is None:
        return SimulatorCapabilities()
    # 通过空参构造获取 capabilities
    facade: ServerSimulatorFacade = cls(source=None)  # type: ignore[call-arg]
    return facade.capabilities


def list_server_simulator_protocols() -> tuple[str, ...]:
    """返回已注册 facade 的协议名列表。"""
    _lazy_register()
    return tuple(_SIMULATOR_FACADE_REGISTRY.keys())


# ── 旧版同步工厂（向后兼容） ───────────────────────────────────────────


def _unsupported_simulator_factory(protocol: str) -> Callable[[SimulatedSource], SourceSimulator]:
    """构建不支持协议的 simulator 工厂。"""

    def _factory(source: SimulatedSource) -> SourceSimulator:
        raise ValueError(
            "source simulator not implemented for protocol: "
            f"{protocol}; endpoint={source.connection.host}:{source.connection.port}"
        )

    return _factory


def get_simulator_factory(protocol: str) -> Callable[[SimulatedSource], SourceSimulator]:
    """返回协议对应的旧版同步 simulator 工厂。"""

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
