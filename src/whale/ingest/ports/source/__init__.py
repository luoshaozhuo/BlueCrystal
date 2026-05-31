"""端口接口定义。

定义调用方契约和实现方责任，相关功能。
"""

from whale.ingest.ports.source.source_acquisition_definition_port import (
    SourceAcquisitionDefinitionPort,
)
from whale.ingest.ports.source.source_acquisition_port import SourceAcquisitionPort
from whale.ingest.ports.source.source_acquisition_port_registry import (
    SourceAcquisitionPortRegistry,
)

__all__ = [
    "SourceAcquisitionDefinitionPort",
    "SourceAcquisitionPort",
    "SourceAcquisitionPortRegistry",
]
