"""协议采集适配器。

实现 SourceAcquisitionPort / SourceWritePort，
封装特定协议（工业协议）的采集或写入逻辑。
外部依赖边界：lib60870 C 库（ctypes）、asyncio stream（MQTT/HTTP REST）。

包含多协议调度适配器 DispatchSourceAcquisitionAdapter，
作为 composition root 中多协议采集链的调度入口。
"""

from pacific.whale.ingest.adapters.source.dispatch_source_acquisition_adapter import (
    DispatchSourceAcquisitionAdapter,
)
from pacific.whale.ingest.adapters.source.http_rest_source_acquisition_adapter import (
    HttpRestSourceAcquisitionAdapter,
)
from pacific.whale.ingest.adapters.source.iec101_source_acquisition_adapter import (
    Iec101SourceAcquisitionAdapter,
)
from pacific.whale.ingest.adapters.source.iec104_source_acquisition_adapter import (
    Iec104SourceAcquisitionAdapter,
)
from pacific.whale.ingest.adapters.source.modbus_rtu_source_acquisition_adapter import (
    ModbusRtuSourceAcquisitionAdapter,
)
from pacific.whale.ingest.adapters.source.mqtt_source_acquisition_adapter import (
    MqttSourceAcquisitionAdapter,
)
from pacific.whale.ingest.adapters.source.opcua_source_acquisition_adapter import (
    OpcUaSourceAcquisitionAdapter,
)

__all__ = [
    "DispatchSourceAcquisitionAdapter",
    "HttpRestSourceAcquisitionAdapter",
    "Iec101SourceAcquisitionAdapter",
    "Iec104SourceAcquisitionAdapter",
    "ModbusRtuSourceAcquisitionAdapter",
    "MqttSourceAcquisitionAdapter",
    "OpcUaSourceAcquisitionAdapter",
]
