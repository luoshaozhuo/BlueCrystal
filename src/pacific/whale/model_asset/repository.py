"""模型资产持久化仓库。

提供模型资产、仿真案例、仿真结果和仿真制品的创建和查询操作。
所有操作通过 SQLAlchemy session 执行，不管理 session 生命周期。

不负责：
- 事务管理（由调用方控制 session 和事务边界）。
- 文件归档（由 SimulationArchiveService 负责）。
- 仿真引擎调度。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from whale.shared.persistence.orm.model_asset import (
    ModelAsset,
    SimulationArtifact,
    SimulationCase,
    SimulationResult,
)

logger = logging.getLogger(__name__)


class ModelAssetRepository:
    """模型资产仓库。

    提供模型资产、案例、结果和制品的 CRUD 操作。
    所有方法接受外部 Session 参数，不持有 session 引用。

    Attributes:
        _session: SQLAlchemy session（由调用方传入并管理生命周期）。
    """

    def __init__(self, session: Session) -> None:
        """初始化仓库。

        Args:
            session: SQLAlchemy ORM session，由调用方管理生命周期。
        """
        self._session = session

    # ---- ModelAsset ----

    def create_model_asset(
        self,
        model_code: str,
        model_name: str,
        model_type: str,
        asset_scope: str,
        *,
        version: str = "1.0",
        owner_asset_instance_id: int | None = None,
        parent_model_asset_id: int | None = None,
        source_file_uri: str | None = None,
        raw_archive_batch_id: str | None = None,
        checksum_sha256: str | None = None,
        parser_status: str = "IMPORTED",
        metadata_json: dict[str, Any] | None = None,
    ) -> ModelAsset:
        """创建模型资产记录。

        Args:
            model_code: 模型编码，全局唯一。
            model_name: 模型名称。
            model_type: 模型类型。
            asset_scope: 资产范围。
            version: 版本号。
            owner_asset_instance_id: 所属资产实例 ID。
            parent_model_asset_id: 父模型资产 ID。
            source_file_uri: 源文件 URI。
            raw_archive_batch_id: 归档批次 ID。
            checksum_sha256: 校验和。
            parser_status: 解析状态。
            metadata_json: 扩展元数据。

        Returns:
            创建的 ModelAsset 实例（已 flush，可获取 ID）。

        Raises:
            ValueError: model_code 已存在。
        """
        asset = ModelAsset(
            model_code=model_code,
            model_name=model_name,
            model_type=model_type,
            asset_scope=asset_scope,
            version=version,
            owner_asset_instance_id=owner_asset_instance_id,
            parent_model_asset_id=parent_model_asset_id,
            source_file_uri=source_file_uri,
            raw_archive_batch_id=raw_archive_batch_id,
            checksum_sha256=checksum_sha256,
            parser_status=parser_status,
            metadata_json=metadata_json or {},
        )
        self._session.add(asset)
        self._session.flush()
        logger.info("创建模型资产: model_code=%s id=%d", model_code, asset.model_asset_id)
        return asset

    def get_model_asset_by_code(self, model_code: str) -> Optional[ModelAsset]:
        """按 model_code 查询模型资产。

        Args:
            model_code: 模型编码。

        Returns:
            ModelAsset 实例，不存在时返回 None。
        """
        stmt = select(ModelAsset).where(ModelAsset.model_code == model_code)
        return self._session.scalar(stmt)

    def get_model_asset_by_id(self, model_asset_id: int) -> Optional[ModelAsset]:
        """按主键查询模型资产。

        Args:
            model_asset_id: 模型资产主键。

        Returns:
            ModelAsset 实例，不存在时返回 None。
        """
        return self._session.get(ModelAsset, model_asset_id)

    # ---- SimulationCase ----

    def create_simulation_case(
        self,
        case_code: str,
        case_name: str,
        model_asset_id: int,
        case_type: str,
        *,
        input_file_uri: str | None = None,
        raw_archive_batch_id: str | None = None,
        parameter_json: dict[str, Any] | None = None,
        scenario_json: dict[str, Any] | None = None,
        status: str = "CREATED",
        created_by: str | None = None,
    ) -> SimulationCase:
        """创建仿真案例记录。

        Args:
            case_code: 案例编码，全局唯一。
            case_name: 案例名称。
            model_asset_id: 关联模型资产 ID。
            case_type: 案例类型。
            input_file_uri: 输入文件 URI。
            raw_archive_batch_id: 归档批次 ID。
            parameter_json: 输入参数。
            scenario_json: 场景配置。
            status: 案例状态。
            created_by: 创建者标识。

        Returns:
            创建的 SimulationCase 实例。

        Raises:
            ValueError: case_code 已存在或模型资产不存在。
        """
        parent = self.get_model_asset_by_id(model_asset_id)
        if parent is None:
            raise ValueError(f"模型资产不存在: model_asset_id={model_asset_id}")

        case = SimulationCase(
            case_code=case_code,
            case_name=case_name,
            model_asset_id=model_asset_id,
            case_type=case_type,
            input_file_uri=input_file_uri,
            raw_archive_batch_id=raw_archive_batch_id,
            parameter_json=parameter_json or {},
            scenario_json=scenario_json or {},
            status=status,
            created_by=created_by,
        )
        self._session.add(case)
        self._session.flush()
        logger.info("创建仿真案例: case_code=%s id=%d", case_code, case.simulation_case_id)
        return case

    def get_case_by_code(self, case_code: str) -> Optional[SimulationCase]:
        """按 case_code 查询仿真案例。

        Args:
            case_code: 案例编码。

        Returns:
            SimulationCase 实例，不存在时返回 None。
        """
        stmt = select(SimulationCase).where(SimulationCase.case_code == case_code)
        return self._session.scalar(stmt)

    # ---- SimulationResult ----

    def create_simulation_result(
        self,
        simulation_case_id: int,
        result_code: str,
        result_type: str,
        *,
        result_file_uri: str | None = None,
        raw_archive_batch_id: str | None = None,
        time_series_backend: str | None = None,
        time_series_ref: str | None = None,
        summary_json: dict[str, Any] | None = None,
        metric_json: dict[str, Any] | None = None,
        status: str = "IMPORTED",
    ) -> SimulationResult:
        """创建仿真结果记录。

        Args:
            simulation_case_id: 关联仿真案例 ID。
            result_code: 结果编码，全局唯一。
            result_type: 结果类型。
            result_file_uri: 结果文件 URI。
            raw_archive_batch_id: 归档批次 ID。
            time_series_backend: 时序后端。
            time_series_ref: 时序数据引用。
            summary_json: 汇总结果。
            metric_json: 指标。
            status: 结果状态。

        Returns:
            创建的 SimulationResult 实例。

        Raises:
            ValueError: 仿真案例不存在。
        """
        case = self._session.get(SimulationCase, simulation_case_id)
        if case is None:
            raise ValueError(
                f"仿真案例不存在: simulation_case_id={simulation_case_id}"
            )

        result = SimulationResult(
            simulation_case_id=simulation_case_id,
            result_code=result_code,
            result_type=result_type,
            result_file_uri=result_file_uri,
            raw_archive_batch_id=raw_archive_batch_id,
            time_series_backend=time_series_backend,
            time_series_ref=time_series_ref,
            summary_json=summary_json or {},
            metric_json=metric_json or {},
            status=status,
        )
        self._session.add(result)
        self._session.flush()
        logger.info(
            "创建仿真结果: result_code=%s id=%d", result_code, result.simulation_result_id
        )
        return result

    def get_result_by_code(self, result_code: str) -> Optional[SimulationResult]:
        """按 result_code 查询仿真结果。

        Args:
            result_code: 结果编码。

        Returns:
            SimulationResult 实例，不存在时返回 None。
        """
        stmt = select(SimulationResult).where(
            SimulationResult.result_code == result_code
        )
        return self._session.scalar(stmt)

    # ---- SimulationArtifact ----

    def create_artifact(
        self,
        owner_type: str,
        owner_id: int,
        artifact_type: str,
        file_uri: str,
        *,
        raw_archive_batch_id: str | None = None,
        checksum_sha256: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> SimulationArtifact:
        """创建仿真制品记录。

        Args:
            owner_type: 所属对象类型（MODEL_ASSET / SIMULATION_CASE / SIMULATION_RESULT）。
            owner_id: 所属对象 ID。
            artifact_type: 制品类型。
            file_uri: 文件 URI。
            raw_archive_batch_id: 归档批次 ID。
            checksum_sha256: 校验和。
            metadata_json: 扩展元数据。

        Returns:
            创建的 SimulationArtifact 实例。
        """
        artifact = SimulationArtifact(
            owner_type=owner_type,
            owner_id=owner_id,
            artifact_type=artifact_type,
            file_uri=file_uri,
            raw_archive_batch_id=raw_archive_batch_id,
            checksum_sha256=checksum_sha256,
            metadata_json=metadata_json or {},
        )
        self._session.add(artifact)
        self._session.flush()
        logger.info(
            "创建仿真制品: owner_type=%s owner_id=%d type=%s id=%d",
            owner_type, owner_id, artifact_type, artifact.simulation_artifact_id,
        )
        return artifact
