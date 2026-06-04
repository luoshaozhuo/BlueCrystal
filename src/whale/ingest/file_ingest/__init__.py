"""文件接入子包。

提供文件接入最小闭环的 DTO、检测器、解码器、服务和仓储实现。
支持 JSON 和二进制格式的高频采样文件接入。

本包包含：
- models: 运行期 DTO（manifest、probe、request、result、fault_event）。
- detector: 文件落地完成检测器（manifest/size stable/done flag）。
- decoder: PlcHighRateJsonDecoder / FaultRecordBinaryDecoder。
- service: FileIngestService 编排文件接入全流程。
- repository: InMemoryFaultEventRepository 故障事件仓储。
"""

from whale.ingest.file_ingest.models import (
    FaultEventMetadata,
    FileIngestManifest,
    FileIngestRequest,
    FileIngestResult,
    FileStabilityProbeResult,
)
from whale.ingest.file_ingest.detector import (
    FileCompletionDetector,
    OSStatSizeProbe,
    SizeProbeProvider,
)
from whale.ingest.file_ingest.decoder import (
    FaultRecordBinaryDecoder,
    PlcHighRateJsonDecoder,
)
from whale.ingest.file_ingest.service import FileIngestService
from whale.ingest.file_ingest.repository import (
    FaultEventRepositoryPort,
    InMemoryFaultEventRepository,
)

__all__ = [
    # models
    "FaultEventMetadata",
    "FileIngestManifest",
    "FileIngestRequest",
    "FileIngestResult",
    "FileStabilityProbeResult",
    # detector
    "FileCompletionDetector",
    "OSStatSizeProbe",
    "SizeProbeProvider",
    # decoder
    "FaultRecordBinaryDecoder",
    "PlcHighRateJsonDecoder",
    # service
    "FileIngestService",
    # repository
    "FaultEventRepositoryPort",
    "InMemoryFaultEventRepository",
]
