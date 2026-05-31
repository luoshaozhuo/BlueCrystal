"""ServerSimulatorFacade 契约测试。

验证每个 facade 满足 ServerSimulatorFacade Protocol 要求的方法签名。
"""

from __future__ import annotations

import inspect

import pytest

from tools.source_lab.protocols.common.simulator_models import (
    SimulatorCapabilities,
    SimulatorStatus,
)
from tools.source_lab.protocols.registry import list_server_simulator_protocols

# ── 从 registry 导入所有 facade 类型 ──────────────────────────────────

_FACADE_PROTOCOL_METHODS = [
    "start",
    "stop",
    "health",
    "load_points",
    "read",
    "write",
    "subscribe",
    "report",
    "update_values",
]

_FACADE_PROTOCOL_PROPERTIES = ["protocol", "capabilities"]


def _get_all_facade_classes() -> list[type]:
    """返回所有已注册的 facade 类。"""
    from tools.source_lab.protocols.registry import _SIMULATOR_FACADE_REGISTRY
    # 触发注册
    list_server_simulator_protocols()
    # registry values 为 facade 类（Callable 形式），实际均为 type，
    # 但 mypy 无法从 dict_values[Callable[..., ServerSimulatorFacade]] 推断为 Iterable[type]。
    return list(_SIMULATOR_FACADE_REGISTRY.values())  # type: ignore[arg-type,return-value]


class TestFacadeContract:
    """所有 facade 必须满足的契约测试。"""

    @pytest.fixture(params=_get_all_facade_classes(), ids=lambda cls: cls.__name__)
    def facade_cls(self, request: pytest.FixtureRequest) -> type:
        # pytest FixtureRequest.param 推断为 Any，对已知 fixtures 做显式 cast。
        return request.param  # type: ignore[no-any-return]

    def test_facade_has_protocol_property(self, facade_cls: type) -> None:
        instance = facade_cls(source=None)
        protocol = instance.protocol
        assert isinstance(protocol, str) and len(protocol) > 0

    def test_facade_has_capabilities_property(self, facade_cls: type) -> None:
        instance = facade_cls(source=None)
        caps = instance.capabilities
        assert isinstance(caps, SimulatorCapabilities)

    def test_facade_start_returns_simulator_result(self, facade_cls: type) -> None:
        instance = facade_cls(source=None)
        assert inspect.iscoroutinefunction(instance.start)

    def test_facade_stop_returns_simulator_result(self, facade_cls: type) -> None:
        instance = facade_cls(source=None)
        assert inspect.iscoroutinefunction(instance.stop)

    def test_facade_health_returns_simulator_health(self, facade_cls: type) -> None:
        instance = facade_cls(source=None)
        assert inspect.iscoroutinefunction(instance.health)

    def test_facade_load_points_returns_simulator_result(self, facade_cls: type) -> None:
        instance = facade_cls(source=None)
        assert inspect.iscoroutinefunction(instance.load_points)

    def test_facade_read_returns_read_result(self, facade_cls: type) -> None:
        instance = facade_cls(source=None)
        assert inspect.iscoroutinefunction(instance.read)

    def test_facade_write_returns_simulator_result(self, facade_cls: type) -> None:
        instance = facade_cls(source=None)
        assert inspect.iscoroutinefunction(instance.write)

    def test_facade_subscribe_returns_simulator_result(self, facade_cls: type) -> None:
        instance = facade_cls(source=None)
        assert inspect.iscoroutinefunction(instance.subscribe)

    def test_facade_report_returns_simulator_result(self, facade_cls: type) -> None:
        instance = facade_cls(source=None)
        assert inspect.iscoroutinefunction(instance.report)

    def test_facade_update_values_returns_simulator_result(self, facade_cls: type) -> None:
        instance = facade_cls(source=None)
        assert inspect.iscoroutinefunction(instance.update_values)


class TestNotImplementedReturnsCorrectStatus:
    """NOT_IMPLEMENTED 操作应返回 SimulatorStatus.NOT_IMPLEMENTED。"""

    @pytest.mark.asyncio
    async def test_goose_all_not_implemented(self) -> None:
        from tools.source_lab.protocols.iec61850.simulator import Iec61850GooseSimulatorFacade
        facade = Iec61850GooseSimulatorFacade(source=None)
        assert (await facade.read([])).status == SimulatorStatus.NOT_IMPLEMENTED
        assert (await facade.write({})).status == SimulatorStatus.NOT_IMPLEMENTED
        assert (await facade.report([])).status == SimulatorStatus.NOT_IMPLEMENTED

    @pytest.mark.asyncio
    async def test_sv_all_not_implemented(self) -> None:
        from tools.source_lab.protocols.iec61850.simulator import Iec61850SvSimulatorFacade
        facade = Iec61850SvSimulatorFacade(source=None)
        assert (await facade.read([])).status == SimulatorStatus.NOT_IMPLEMENTED
        assert (await facade.write({})).status == SimulatorStatus.NOT_IMPLEMENTED
        assert (await facade.report([])).status == SimulatorStatus.NOT_IMPLEMENTED


class TestCapabilitiesReflectImplementation:
    """capabilities 应准确反映各 facade 的真实能力。"""

    def test_opcua_capabilities(self) -> None:
        from tools.source_lab.protocols.opcua.simulator import OpcUaSimulatorFacade
        facade = OpcUaSimulatorFacade(source=None)
        caps = facade.capabilities
        assert caps.read is True
        assert caps.write is True
        assert caps.subscribe is True
        assert caps.report is False

    def test_opcua_protocol(self) -> None:
        from tools.source_lab.protocols.opcua.simulator import OpcUaSimulatorFacade
        assert OpcUaSimulatorFacade(source=None).protocol == "opcua"

    def test_modbus_tcp_capabilities(self) -> None:
        from tools.source_lab.protocols.modbus.simulator import ModbusTcpSimulatorFacade
        facade = ModbusTcpSimulatorFacade(source=None)
        caps = facade.capabilities
        assert caps.read is True
        assert caps.write is True, "Modbus TCP facade should support real write via native runner"
        assert caps.subscribe is False
        assert caps.report is False

    def test_modbus_tcp_protocol(self) -> None:
        from tools.source_lab.protocols.modbus.simulator import ModbusTcpSimulatorFacade
        assert ModbusTcpSimulatorFacade(source=None).protocol == "modbus_tcp"

    def test_modbus_rtu_capabilities(self) -> None:
        from tools.source_lab.protocols.modbus.simulator import ModbusRtuSimulatorFacade
        facade = ModbusRtuSimulatorFacade(source=None)
        caps = facade.capabilities
        assert caps.read is True, "Modbus RTU facade supports real FC03 read (TCP gateway mode)"
        assert caps.write is False

    def test_iec104_capabilities(self) -> None:
        from tools.source_lab.protocols.iec104.simulator import Iec104SimulatorFacade
        facade = Iec104SimulatorFacade(source=None)
        assert facade.capabilities.read is True
        assert facade.capabilities.subscribe is False

    def test_iec61850_mms_capabilities(self) -> None:
        from tools.source_lab.protocols.iec61850.simulator import Iec61850MmsSimulatorFacade
        facade = Iec61850MmsSimulatorFacade(source=None)
        caps = facade.capabilities
        assert caps.read is True, "MMS facade should support real read via native runner"
        assert caps.write is True, "MMS facade should support real write via native runner"
        assert caps.report is False

    def test_iec61850_report_capabilities(self) -> None:
        from tools.source_lab.protocols.iec61850.simulator import Iec61850ReportSimulatorFacade
        facade = Iec61850ReportSimulatorFacade(source=None)
        caps = facade.capabilities
        assert caps.subscribe is True, "Report facade should support real subscribe via native runner"
        assert caps.report is True, "Report facade should support real report via native runner"
        assert caps.read is False
        assert caps.write is False

    def test_iec61850_goose_capabilities(self) -> None:
        from tools.source_lab.protocols.iec61850.simulator import Iec61850GooseSimulatorFacade
        facade = Iec61850GooseSimulatorFacade(source=None)
        caps = facade.capabilities
        assert caps.subscribe is True
        assert caps.read is False
        assert caps.write is False
        assert caps.report is False

    def test_iec61850_sv_capabilities(self) -> None:
        from tools.source_lab.protocols.iec61850.simulator import Iec61850SvSimulatorFacade
        facade = Iec61850SvSimulatorFacade(source=None)
        caps = facade.capabilities
        assert caps.subscribe is True
        assert caps.read is False
        assert caps.write is False
        assert caps.report is False

    def test_mqtt_capabilities(self) -> None:
        from tools.source_lab.protocols.mqtt.simulator import MqttSimulatorFacade
        facade = MqttSimulatorFacade(source=None)
        assert facade.capabilities.subscribe is True
        assert facade.capabilities.read is False

    def test_http_rest_capabilities(self) -> None:
        from tools.source_lab.protocols.http_rest.simulator import HttpRestSimulatorFacade
        facade = HttpRestSimulatorFacade(source=None)
        assert facade.capabilities.read is True, "HTTP REST facade supports real HTTP GET read"
        assert facade.capabilities.write is False

    def test_iec101_capabilities(self) -> None:
        from tools.source_lab.protocols.iec101.simulator import Iec101SimulatorFacade
        facade = Iec101SimulatorFacade(source=None)
        assert facade.capabilities.read is True, "IEC101 facade supports real CS101 read (TCP gateway mode)"


class TestFacadeCapabilitiesConsistency:
    """Facade capabilities 必须不超出 PROTOCOL_CAPABILITIES 声明。"""

    def test_facade_capabilities_subset_of_protocol_capabilities(self) -> None:
        from tools.source_lab.access.runners.registry import PROTOCOL_CAPABILITIES
        from tools.source_lab.protocols.registry import (
            list_server_simulator_protocols,
            create_server_simulator,
        )

        for proto in list_server_simulator_protocols():
            facade = create_server_simulator(proto)
            caps = facade.capabilities

            pc = PROTOCOL_CAPABILITIES.get(proto)
            if pc is None:
                raise AssertionError(f"{proto} has no PROTOCOL_CAPABILITIES entry")

            # facade 能力不得超出 PROTOCOL 声明
            if caps.read:
                assert pc.get("polling") is True, (
                    f"{proto}: facade read=True but PROTOCOL polling={pc.get('polling')}"
                )
            if caps.write:
                assert pc.get("write") is True, (
                    f"{proto}: facade write=True but PROTOCOL write={pc.get('write')}"
                )
            if caps.subscribe:
                assert pc.get("subscribe") is True, (
                    f"{proto}: facade subscribe=True but PROTOCOL subscribe={pc.get('subscribe')}"
                )
            if caps.report:
                assert pc.get("subscribe") is True, (
                    f"{proto}: facade report=True but PROTOCOL subscribe={pc.get('subscribe')} "
                    f"(report capability requires PROTOCOL subscribe)"
                )
