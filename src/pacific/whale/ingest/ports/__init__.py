"""端口接口定义。

定义调用方契约和实现方责任，相关功能。
"""

from pacific.whale.ingest.ports.diagnostics import IngestRuntimeDiagnosticsPort
from pacific.whale.ingest.ports.message import MessagePublisherPort
from pacific.whale.ingest.ports.metrics import IngestMetricEvent, IngestMetricsPort
from pacific.whale.ingest.ports.runtime.source_runtime_config_port import (
    SourceRuntimeConfigPort,
)
from pacific.whale.ingest.ports.source import (
    SourceAcquisitionDefinitionPort,
    SourceAcquisitionPort,
)
from pacific.whale.ingest.ports.state import (
    SourceStateCacheError,
    SourceStateCachePort,
    SourceStateSnapshotReaderPort,
    SourceStateCacheWriteError,
)

__all__ = [
    "IngestRuntimeDiagnosticsPort",
    "MessagePublisherPort",
    "IngestMetricEvent",
    "IngestMetricsPort",
    "SourceAcquisitionDefinitionPort",
    "SourceAcquisitionPort",
    "SourceRuntimeConfigPort",
    "SourceStateCacheError",
    "SourceStateCachePort",
    "SourceStateSnapshotReaderPort",
    "SourceStateCacheWriteError",
]
