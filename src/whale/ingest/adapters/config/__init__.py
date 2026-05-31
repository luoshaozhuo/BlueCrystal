"""配置适配器。

实现配置相关 port，从数据库加载运行时配置。
外部依赖：SQLAlchemy ORM。
"""

from whale.ingest.adapters.config.opcua_source_acquisition_definition_repository import (
    OpcUaSourceAcquisitionDefinitionRepository,
)
from whale.ingest.adapters.config.source_runtime_config_repository import (
    SourceRuntimeConfigRepository,
)

__all__ = [
    "OpcUaSourceAcquisitionDefinitionRepository",
    "SourceRuntimeConfigRepository",
]
