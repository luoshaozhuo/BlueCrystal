"""协议采集适配器。

实现 SourceAcquisitionPort / SourceWritePort，
封装特定协议（工业协议）的采集或写入逻辑。
外部依赖边界：ctypes C 库。
"""

from whale.ingest.adapters.source.opcua_source_acquisition_adapter import (
    OpcUaSourceAcquisitionAdapter,
)

__all__ = ["OpcUaSourceAcquisitionAdapter"]
