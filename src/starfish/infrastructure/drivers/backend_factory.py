"""Starfish driver backend 创建与探测入口。

本模块集中处理真实 backend 创建、native runner、PTY、环境变量和二进制
文件探测。adapters 只依赖其 Protocol，不直接 import 本模块。
"""

from __future__ import annotations

from typing import Callable

from starfish.infrastructure.drivers.ads.ads_backend import AdsBackend
from starfish.infrastructure.drivers.ads.ads_backend import probe_ads_binary
from starfish.infrastructure.drivers.iec.goose_backend import GooseBackend
from starfish.infrastructure.drivers.iec.goose_backend import probe_goose_binary
from starfish.infrastructure.drivers.iec.iec101_backend import Iec101Backend
from starfish.infrastructure.drivers.iec.iec101_backend import (
    probe_iec101_binary,
    probe_iec101_codec,
    probe_iec101_codec_enhanced,
    probe_iec101_codec_enhanced_plus,
)
from starfish.infrastructure.drivers.iec.sv_backend import SvBackend
from starfish.infrastructure.drivers.iec.sv_backend import probe_sv_binary
from starfish.infrastructure.drivers.modbus.modbus_rtu_pty_backend import ModbusRtuPtyBackend
from starfish.infrastructure.drivers.modbus.modbus_rtu_pty_backend import probe_modbus_rtu_binary
from starfish.infrastructure.drivers.modbus.modbus_tcp_server_backend import ModbusTcpServerBackend
from starfish.infrastructure.drivers.native.iec.iec104_native_backend import Iec104NativeBackend
from starfish.infrastructure.drivers.native.iec.iec104_native_backend import probe_iec104_binary
from starfish.infrastructure.drivers.native.iec.iec61850_mms_native_backend import (
    Iec61850MmsNativeBackend,
)
from starfish.infrastructure.drivers.native.iec.iec61850_mms_native_backend import (
    probe_iec61850_mms_binary,
)
from starfish.infrastructure.drivers.native.iec.iec61850_report_native_backend import (
    Iec61850ReportNativeBackend,
)
from starfish.infrastructure.drivers.native.iec.iec61850_report_native_backend import (
    probe_iec61850_report_binary,
)
from starfish.infrastructure.drivers.native.opcua.opcua_native_backend import OpcUaNativeBackend
from starfish.infrastructure.drivers.native.opcua.opcua_native_backend import probe_opcua_binary
from starfish.infrastructure.drivers.protocol.http.http_rest_server_backend import HttpRestServerBackend
from starfish.infrastructure.drivers.protocol.mqtt.mqtt_server_backend import MqttServerBackend
from starfish.infrastructure.drivers.simulator.server_simulator_backend import ServerSimulatorBackend


class StarfishBackendFactory:
    """默认 infrastructure backend factory。"""

    _PROBES: dict[str, Callable[[], tuple[bool, str]]] = {
        "OPC_UA": probe_opcua_binary,
        "IEC104": probe_iec104_binary,
        "IEC_104": probe_iec104_binary,
        "IEC61850_MMS": probe_iec61850_mms_binary,
        "IEC61850_REPORT": probe_iec61850_report_binary,
        "MODBUS_RTU": probe_modbus_rtu_binary,
        "IEC101": probe_iec101_binary,
        "IEC_101": probe_iec101_binary,
        "ADS": probe_ads_binary,
        "BECKHOFF_ADS": probe_ads_binary,
        "GOOSE": probe_goose_binary,
        "SV": probe_sv_binary,
    }

    def create_http_rest_backend(self) -> HttpRestServerBackend:
        """创建 HTTP REST backend。"""
        return HttpRestServerBackend()

    def create_modbus_tcp_backend(self) -> ModbusTcpServerBackend:
        """创建 Modbus TCP backend。"""
        return ModbusTcpServerBackend()

    def create_mqtt_backend(self) -> MqttServerBackend:
        """创建 MQTT-like backend。"""
        return MqttServerBackend()

    def create_opcua_backend(self) -> OpcUaNativeBackend:
        """创建 OPC UA backend。"""
        return OpcUaNativeBackend()

    def create_iec104_backend(self) -> Iec104NativeBackend:
        """创建 IEC104 backend。"""
        return Iec104NativeBackend()

    def create_iec61850_mms_backend(self) -> Iec61850MmsNativeBackend:
        """创建 IEC61850 MMS backend。"""
        return Iec61850MmsNativeBackend()

    def create_iec61850_report_backend(self) -> Iec61850ReportNativeBackend:
        """创建 IEC61850 Report backend。"""
        return Iec61850ReportNativeBackend()

    def create_iec101_backend(self) -> Iec101Backend:
        """创建 IEC101 backend。"""
        return Iec101Backend()

    def create_modbus_rtu_backend(self, *, mode: str) -> ModbusRtuPtyBackend:
        """创建 Modbus RTU backend。"""
        return ModbusRtuPtyBackend(mode=mode)

    def create_ads_backend(self) -> AdsBackend:
        """创建 ADS backend。"""
        return AdsBackend()

    def create_goose_backend(self) -> GooseBackend:
        """创建 GOOSE backend。"""
        return GooseBackend()

    def create_sv_backend(self) -> SvBackend:
        """创建 SV backend。"""
        return SvBackend()

    def create_simulator_backend(self) -> ServerSimulatorBackend:
        """创建未知协议 fallback backend。"""
        return ServerSimulatorBackend()

    def probe_binary(self, name: str) -> tuple[bool, str]:
        """按协议名执行 backend 环境探测。"""
        probe = self._PROBES.get(name.strip().upper())
        if probe is None:
            return False, f"无 backend probe: {name}"
        return probe()

__all__ = [
    "StarfishBackendFactory",
    "probe_ads_binary",
    "probe_goose_binary",
    "probe_iec101_binary",
    "probe_iec101_codec",
    "probe_iec101_codec_enhanced",
    "probe_iec101_codec_enhanced_plus",
    "probe_iec104_binary",
    "probe_iec61850_mms_binary",
    "probe_iec61850_report_binary",
    "probe_modbus_rtu_binary",
    "probe_opcua_binary",
    "probe_sv_binary",
]
