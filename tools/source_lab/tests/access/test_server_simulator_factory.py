"""ServerSimulatorFacade 工厂测试。"""

from __future__ import annotations

import pytest

from tools.source_lab.protocols.common.simulator_models import (
    SimulatorCapabilities,
)
from tools.source_lab.protocols.registry import (
    create_server_simulator,
    get_server_simulator_capabilities,
    list_server_simulator_protocols,
)


class TestCreateServerSimulator:
    """create_server_simulator 工厂测试。"""

    def test_create_opcua(self) -> None:
        from tools.source_lab.protocols.opcua.simulator import OpcUaSimulatorFacade

        facade = create_server_simulator("opcua")
        assert isinstance(facade, OpcUaSimulatorFacade)

    def test_create_modbus_tcp(self) -> None:
        from tools.source_lab.protocols.modbus.simulator import ModbusTcpSimulatorFacade

        facade = create_server_simulator("modbus_tcp")
        assert isinstance(facade, ModbusTcpSimulatorFacade)

    def test_create_modbus_rtu(self) -> None:
        from tools.source_lab.protocols.modbus.simulator import ModbusRtuSimulatorFacade

        facade = create_server_simulator("modbus_rtu")
        assert isinstance(facade, ModbusRtuSimulatorFacade)

    def test_create_iec104(self) -> None:
        from tools.source_lab.protocols.iec104.simulator import Iec104SimulatorFacade

        facade = create_server_simulator("iec104")
        assert isinstance(facade, Iec104SimulatorFacade)

    def test_create_iec61850_mms(self) -> None:
        from tools.source_lab.protocols.iec61850.simulator import Iec61850MmsSimulatorFacade

        facade = create_server_simulator("iec61850_mms")
        assert isinstance(facade, Iec61850MmsSimulatorFacade)

    def test_create_iec61850_report(self) -> None:
        from tools.source_lab.protocols.iec61850.simulator import Iec61850ReportSimulatorFacade

        facade = create_server_simulator("iec61850_report")
        assert isinstance(facade, Iec61850ReportSimulatorFacade)

    def test_create_iec61850_goose(self) -> None:
        from tools.source_lab.protocols.iec61850.simulator import Iec61850GooseSimulatorFacade

        facade = create_server_simulator("iec61850_goose")
        assert isinstance(facade, Iec61850GooseSimulatorFacade)

    def test_create_iec61850_sv(self) -> None:
        from tools.source_lab.protocols.iec61850.simulator import Iec61850SvSimulatorFacade

        facade = create_server_simulator("iec61850_sv")
        assert isinstance(facade, Iec61850SvSimulatorFacade)

    def test_create_iec101(self) -> None:
        from tools.source_lab.protocols.iec101.simulator import Iec101SimulatorFacade

        facade = create_server_simulator("iec101")
        assert isinstance(facade, Iec101SimulatorFacade)

    def test_create_mqtt(self) -> None:
        from tools.source_lab.protocols.mqtt.simulator import MqttSimulatorFacade

        facade = create_server_simulator("mqtt")
        assert isinstance(facade, MqttSimulatorFacade)

    def test_create_http_rest(self) -> None:
        from tools.source_lab.protocols.http_rest.simulator import HttpRestSimulatorFacade

        facade = create_server_simulator("http_rest")
        assert isinstance(facade, HttpRestSimulatorFacade)

    def test_create_via_alias(self) -> None:
        """别名也应能解析。"""
        facade = create_server_simulator("modbustcp")
        from tools.source_lab.protocols.modbus.simulator import ModbusTcpSimulatorFacade
        assert isinstance(facade, ModbusTcpSimulatorFacade)

    def test_unknown_protocol_raises(self) -> None:
        with pytest.raises(ValueError, match="unsupported protocol"):
            create_server_simulator("nonexistent_protocol")

    def test_facade_properties_after_create(self) -> None:
        facade = create_server_simulator("opcua")
        assert facade.protocol == "opcua"
        assert isinstance(facade.capabilities, SimulatorCapabilities)


class TestGetServerSimulatorCapabilities:
    """get_server_simulator_capabilities 测试。"""

    def test_opcua_capabilities(self) -> None:
        caps = get_server_simulator_capabilities("opcua")
        assert caps.read is True
        assert caps.subscribe is True

    def test_modbus_tcp_capabilities(self) -> None:
        caps = get_server_simulator_capabilities("modbus_tcp")
        assert caps.read is True
        assert caps.write is True, "Modbus TCP facade now supports real write via native runner"

    def test_unknown_protocol_raises(self) -> None:
        with pytest.raises(ValueError, match="unsupported protocol"):
            get_server_simulator_capabilities("unknown_protocol")


class TestListServerSimulatorProtocols:
    """list_server_simulator_protocols 测试。"""

    def test_lists_all_registered_protocols(self) -> None:
        protocols = list_server_simulator_protocols()
        assert "opcua" in protocols
        assert "modbus_tcp" in protocols
        assert "modbus_rtu" in protocols
        assert "iec101" in protocols
        assert "iec104" in protocols
        assert "iec61850_mms" in protocols
        assert "iec61850_report" in protocols
        assert "iec61850_goose" in protocols
        assert "iec61850_sv" in protocols
        assert "mqtt" in protocols
        assert "http_rest" in protocols
        assert len(protocols) >= 11

    def test_no_duplicates(self) -> None:
        protocols = list_server_simulator_protocols()
        assert len(protocols) == len(set(protocols))
