"""数据传输对象。

定义 use case 层输入输出数据结构，与 ORM 模型解耦。
"""

from whale.ingest.usecases.dtos.acquired_node_state import (
    AcquiredNodeStateBatch,
    AcquiredNodeValue,
)
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.dtos.source_acquisition_start_result import (
    SourceAcquisitionStartResult,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData

__all__ = [
    "AcquisitionItemData",
    "AcquisitionExecutionOptions",
    "AcquiredNodeStateBatch",
    "AcquiredNodeValue",
    "SourceAcquisitionRequest",
    "SourceAcquisitionStartResult",
    "SourceConnectionData",
]
