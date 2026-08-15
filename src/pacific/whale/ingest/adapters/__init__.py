"""适配器实现。

连接外部系统与领域层，隔离外部依赖差异。
"""

from pacific.whale.ingest.adapters.config import (
    OpcUaSourceAcquisitionDefinitionRepository,
    SourceRuntimeConfigRepository,
)

__all__ = [
    "OpcUaSourceAcquisitionDefinitionRepository",
    "SourceRuntimeConfigRepository",
]
