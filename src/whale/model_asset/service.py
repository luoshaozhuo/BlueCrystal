"""模型资产导入编排服务。

协调 detector、archive、repository 完成模型资产、仿真案例和仿真结果的导入流程。
不调用 Dolphin，不运行仿真，仅完成元数据和文件的导入。

导入流程：
1. detect: 使用 SimulationFileTypeDetector 检测文件类型。
2. archive: 通过 SimulationArchiveService 归档文件。
3. persist: 通过 ModelAssetRepository 写入数据库元数据。
4. artifact: 创建仿真制品关联记录。

不负责：
- 仿真引擎调度和执行。
- 仿真结果的时序数据写入（由 SimulationResultTimeSeriesSinkPort 负责）。
- 消息管道和实时采集。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from whale.model_asset.archive import SimulationArchiveService
from whale.model_asset.detector import SimulationFileTypeDetector
from whale.model_asset.models import (
    ModelAssetImportRequest,
    ModelAssetImportResult,
    SimulationCaseImportRequest,
    SimulationResultImportRequest,
)
from whale.model_asset.repository import ModelAssetRepository

logger = logging.getLogger(__name__)


class ModelAssetImportService:
    """模型资产导入编排服务。

    协调检测器、归档服务和仓库完成资产导入全流程。

    Attributes:
        _detector: 文件类型检测器。
        _archive_svc: 文件归档服务。
        _repo: 持久化仓库。
    """

    def __init__(
        self,
        detector: SimulationFileTypeDetector,
        archive_svc: SimulationArchiveService,
        repo: ModelAssetRepository,
    ) -> None:
        """初始化导入服务。

        Args:
            detector: 仿真文件类型检测器。
            archive_svc: 仿真归档服务。
            repo: 模型资产仓库。
        """
        self._detector = detector
        self._archive_svc = archive_svc
        self._repo = repo

    async def import_model_asset(
        self,
        request: ModelAssetImportRequest,
    ) -> ModelAssetImportResult:
        """导入模型资产。

        流程：
        1. 检测文件类型（按 request.files 中每个文件的扩展名）。
        2. 如果 parent_model_code 不为空，查找父模型资产。
        3. 归档文件到 raw_archive。
        4. 创建 ModelAsset 记录。
        5. 为每个文件创建 SimulationArtifact。

        Args:
            request: 模型资产导入请求。

        Returns:
            ModelAssetImportResult 包含导入结果信息。
        """
        # 步 1: 检测文件类型
        file_types = [self._detector.detect(f) for f in request.files]
        detected_type = self._resolve_model_type(request.model_type, file_types)

        # 如果全部 UNSUPPORTED，标记为 UNSUPPORTED
        if all(ft.value in ("UNSUPPORTED",) for ft in file_types):
            return ModelAssetImportResult(
                success=False,
                model_code=request.model_code,
                parser_status="UNSUPPORTED",
                error_message="所有文件类型无法识别",
            )

        # 步 2: 查找父模型资产
        parent_id: Optional[int] = None
        if request.parent_model_code:
            parent = self._repo.get_model_asset_by_code(request.parent_model_code)
            parent_id = parent.model_asset_id if parent else None

        # 步 3: 归档文件
        batch_id = SimulationArchiveService.generate_batch_id(request.model_code)
        archive_result: dict[str, Any] = {
            "batch_id": batch_id,
            "file_count": 0,
            "file_uris": [],
            "checksums": [],
        }
        try:
            archive_result = await self._archive_svc.archive_files(
                batch_id=batch_id,
                files=request.files,
                metadata={"model_code": request.model_code},
            )
        except Exception as exc:
            logger.warning("文件归档失败，继续导入: %s", exc)

        # 步 4: 创建模型资产记录
        try:
            asset = self._repo.create_model_asset(
                model_code=request.model_code,
                model_name=request.model_name,
                model_type=detected_type,
                asset_scope=request.asset_scope,
                version=request.version,
                parent_model_asset_id=parent_id,
                source_file_uri=(
                    archive_result["file_uris"][0]
                    if archive_result["file_uris"]
                    else None
                ),
                raw_archive_batch_id=batch_id,
                checksum_sha256=request.checksum_sha256,
                parser_status="IMPORTED",
                metadata_json=request.metadata,
            )
        except Exception as exc:
            logger.exception("创建模型资产记录失败")
            return ModelAssetImportResult(
                success=False,
                model_code=request.model_code,
                error_message=str(exc),
            )

        # 步 5: 创建制品
        artifact_ids: list[int] = []
        for i, (uri, chk) in enumerate(
            zip(archive_result["file_uris"], archive_result["checksums"])
        ):
            try:
                artifact = self._repo.create_artifact(
                    owner_type="MODEL_ASSET",
                    owner_id=asset.model_asset_id,
                    artifact_type="SOURCE_FILE",
                    file_uri=uri,
                    raw_archive_batch_id=batch_id,
                    checksum_sha256=chk,
                )
                artifact_ids.append(artifact.simulation_artifact_id)
            except Exception as exc:
                logger.warning("制品创建失败 file=%s: %s", uri, exc)

        return ModelAssetImportResult(
            success=True,
            model_code=request.model_code,
            model_asset_id=asset.model_asset_id,
            parser_status="IMPORTED",
            artifact_ids=artifact_ids,
        )

    async def import_simulation_case(
        self,
        request: SimulationCaseImportRequest,
    ) -> dict[str, Any]:
        """导入仿真案例。

        先查找关联的模型资产，再创建案例记录。

        Args:
            request: 仿真案例导入请求。

        Returns:
            导入结果字典，包含 case_code、simulation_case_id 和 status。

        Raises:
            ValueError: 关联的模型资产不存在。
        """
        model = self._repo.get_model_asset_by_code(request.model_code)
        if model is None:
            raise ValueError(f"模型资产不存在: model_code={request.model_code}")

        case = self._repo.create_simulation_case(
            case_code=request.case_code,
            case_name=request.case_name,
            model_asset_id=model.model_asset_id,
            case_type=request.case_type,
            input_file_uri=request.input_file_uri,
            parameter_json=request.parameters,
            scenario_json=request.scenario,
            created_by=request.created_by,
        )
        return {
            "success": True,
            "case_code": case.case_code,
            "simulation_case_id": case.simulation_case_id,
            "status": case.status,
        }

    async def import_simulation_result(
        self,
        request: SimulationResultImportRequest,
    ) -> dict[str, Any]:
        """导入仿真结果。

        先查找关联的仿真案例，再归档结果文件并创建结果记录。

        Args:
            request: 仿真结果导入请求。

        Returns:
            导入结果字典。

        Raises:
            ValueError: 关联的仿真案例不存在。
        """
        case = self._repo.get_case_by_code(request.case_code)
        if case is None:
            raise ValueError(f"仿真案例不存在: case_code={request.case_code}")

        # 归档结果文件
        batch_id = SimulationArchiveService.generate_batch_id(request.result_code)
        if request.files:
            try:
                await self._archive_svc.archive_files(
                    batch_id=batch_id,
                    files=request.files,
                    metadata={
                        "result_code": request.result_code,
                        "case_code": request.case_code,
                    },
                )
            except Exception as exc:
                logger.warning("结果文件归档失败: %s", exc)

        result = self._repo.create_simulation_result(
            simulation_case_id=case.simulation_case_id,
            result_code=request.result_code,
            result_type=request.result_type,
            result_file_uri=request.result_file_uri,
            raw_archive_batch_id=batch_id,
            time_series_backend=request.time_series_backend,
            time_series_ref=request.time_series_ref,
            summary_json=request.summary,
            metric_json=request.metrics,
            status=request.status,
        )

        # 为每个结果文件创建制品
        artifact_ids: list[int] = []
        for fp in request.files:
            try:
                art = self._repo.create_artifact(
                    owner_type="SIMULATION_RESULT",
                    owner_id=result.simulation_result_id,
                    artifact_type="RESULT_FILE",
                    file_uri=str(fp),
                    raw_archive_batch_id=batch_id,
                )
                artifact_ids.append(art.simulation_artifact_id)
            except Exception as exc:
                logger.warning("制品创建失败 file=%s: %s", fp, exc)

        return {
            "success": True,
            "result_code": result.result_code,
            "simulation_result_id": result.simulation_result_id,
            "status": result.status,
            "artifact_ids": artifact_ids,
        }

    @staticmethod
    def _resolve_model_type(
        declared_type: str,
        detected_types: list[Any],
    ) -> str:
        """综合声明类型和检测到的文件类型，确定最终模型类型。

        优先使用声明类型；如果声明类型为 OTHER，尝试从检测类型推断。

        Args:
            declared_type: 在 import request 中声明的模型类型。
            detected_types: 检测器对各文件的分类结果。

        Returns:
            最终确定的模型类型字符串。
        """
        if declared_type and declared_type != "OTHER":
            return declared_type
        # 从检测结果中选择出现频率最高的非 OTHER/UNSUPPORTED 类型
        for ft in detected_types:
            val = ft.value if hasattr(ft, "value") else str(ft)
            if val not in ("OTHER", "UNSUPPORTED"):
                return val
        return declared_type or "OTHER"
