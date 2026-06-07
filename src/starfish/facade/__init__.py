"""starfish 协议 server 模拟门面。

提供 ServerSimulatorFacade（in-memory stub）和协议专用 facade：
- ServerSimulatorFacade: 通用 in-memory stub（fallback）。
- HttpRestFacade: HTTP REST 真实 server（GET /points）。
- ModbusTcpFacade: Modbus TCP 真实 server（FC03/FC06）。
- MqttFacade: MQTT 轻量级端点（TCP JSON 行协议，subscribe 轮询队列）。
- OpcUaFacade: OPC UA 门面（依赖 open62541 C runner，real/unavailable 模式）。
- Iec104Facade: IEC104 门面（依赖 iec104_simulator_server C runner，real/unavailable 模式）。
- Iec61850MmsFacade: IEC61850 MMS 门面（依赖 iec61850_simulator_server C runner，real/unavailable 模式）。
- Iec61850ReportFacade: IEC61850 Report 门面（依赖 iec61850_simulator_server + iec61850_report_runner，real/report-lightweight 模式；ReportQueue 事件队列）。
- Iec101Facade: IEC101 门面（codebase-pending stub，串口链路未就绪）。
- ModbusRtuFacade: Modbus RTU 门面（codebase-pending stub，串口/PTY 链路未就绪）。
- AdsFacade: Beckhoff ADS 门面（codebase-pending stub，.NET/TwinCAT runtime 未就绪）。
- GooseFacade: GOOSE 门面（environment-pending stub，L2 veth 网络未就绪）。
- SvFacade: SV 门面（environment-pending stub，L2 veth + PTP 时间同步未就绪）。

stub facade 作为不支持协议的 fallback。
real facade 启动真实 TCP server 进程（Python 原生或 C runner 子进程）。

安全边界：
- 不得 import seahorse。
- 不得 import whale.ingest / whale.shared.source。
- 所有数据标注 synthetic。
"""

from __future__ import annotations

from starfish.facade.server_simulator_facade import ServerSimulatorFacade
from starfish.facade.http_rest_facade import HttpRestFacade
from starfish.facade.modbus_tcp_facade import ModbusTcpFacade
from starfish.facade.mqtt_facade import MqttFacade, SubscriptionQueue
from starfish.facade.opcua_facade import OpcUaFacade, probe_opcua_binary
from starfish.facade.iec104_facade import Iec104Facade, probe_iec104_binary
from starfish.facade.iec61850_mms_facade import (
    Iec61850MmsFacade,
    probe_iec61850_mms_binary,
)
from starfish.facade.iec61850_report_facade import (
    Iec61850ReportFacade,
    ReportQueue,
    probe_iec61850_report_binary,
)
from starfish.facade.iec101_facade import Iec101Facade, probe_iec101_binary
from starfish.facade.modbus_rtu_facade import ModbusRtuFacade, probe_modbus_rtu_binary
from starfish.facade.ads_facade import AdsFacade, probe_ads_binary
from starfish.facade.goose_facade import GooseFacade, probe_goose_binary
from starfish.facade.sv_facade import SvFacade, probe_sv_binary

__all__ = [
    "ServerSimulatorFacade",
    "HttpRestFacade",
    "ModbusTcpFacade",
    "MqttFacade",
    "SubscriptionQueue",
    "OpcUaFacade",
    "Iec104Facade",
    "Iec61850MmsFacade",
    "Iec61850ReportFacade",
    "ReportQueue",
    "Iec101Facade",
    "ModbusRtuFacade",
    "AdsFacade",
    "GooseFacade",
    "SvFacade",
    "probe_opcua_binary",
    "probe_iec104_binary",
    "probe_iec61850_mms_binary",
    "probe_iec61850_report_binary",
    "probe_iec101_binary",
    "probe_modbus_rtu_binary",
    "probe_ads_binary",
    "probe_goose_binary",
    "probe_sv_binary",
]
