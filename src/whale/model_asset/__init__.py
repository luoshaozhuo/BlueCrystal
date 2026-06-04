"""模型资产子包 — 仿真模型资产的导入、检测、归档与服务。

本包包含：
- models: DTO 和数据模型定义。
- detector: 仿真文件类型检测器。
- archive: 仿真归档服务（复用 storage.raw_archive 的 FileArchiveSinkPort）。
- repository: 模型资产持久化仓库。
- service: 模型资产导入编排服务。

不负责：
- 仿真引擎调度与执行（由 Dolphin/simulation engine 负责）。
- 时序数据的深度存储（由 storage.simulation_result 端口负责）。
- 协议采集和消息管道（由 ingest/message_pipeline 负责）。
"""

from whale.model_asset.models import (
    SimulationCaseImportRequest,
    SimulationFileType,
    SimulationImportManifest,
    SimulationResultImportRequest,
    ModelAssetImportRequest,
    ModelAssetImportResult,
)
from whale.model_asset.detector import SimulationFileTypeDetector
from whale.model_asset.archive import SimulationArchiveService
from whale.model_asset.repository import ModelAssetRepository
from whale.model_asset.service import ModelAssetImportService

__all__ = [
    "SimulationFileType",
    "ModelAssetImportRequest",
    "ModelAssetImportResult",
    "SimulationCaseImportRequest",
    "SimulationResultImportRequest",
    "SimulationImportManifest",
    "SimulationFileTypeDetector",
    "SimulationArchiveService",
    "ModelAssetRepository",
    "ModelAssetImportService",
]
