"""model_asset service 单元测试。

验证 ModelAssetImportService 的导入编排逻辑，包括模型资产、仿真案例和
仿真结果的导入流程。使用 SQLite 内存数据库和 InMemory archive。

被验证对象：
- whale.model_asset.service: ModelAssetImportService

测试阶段：开发期验证 (unit，使用 SQLite :memory: + InMemory archive)。
不能证明：真实文件归档、大文件性能、PostgreSQL 并发行为。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from whale.shared.persistence import Base
from whale.model_asset.archive import SimulationArchiveService
from whale.model_asset.detector import SimulationFileTypeDetector
from whale.model_asset.models import (
    ModelAssetImportRequest,
    SimulationCaseImportRequest,
    SimulationResultImportRequest,
)
from whale.model_asset.repository import ModelAssetRepository
from whale.model_asset.service import ModelAssetImportService
from whale.storage.raw_archive import (
    InMemoryManifestRepository,
    LocalCompressedArchiveSink,
)


@pytest.fixture(scope="function")
def session() -> Session:
    """创建 SQLite 内存数据库 session。"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def service(session: Session, tmp_path: Path) -> ModelAssetImportService:
    """创建完整的 ModelAssetImportService 及其依赖。"""
    detector = SimulationFileTypeDetector()
    archive_sink = LocalCompressedArchiveSink(tmp_path / "archive")
    manifest_repo = InMemoryManifestRepository()
    archive_svc = SimulationArchiveService(archive_sink, manifest_repo)
    repo = ModelAssetRepository(session)
    return ModelAssetImportService(detector, archive_svc, repo)


class TestModelAssetImportService:
    """ModelAssetImportService 导入编排测试。"""

    @pytest.mark.asyncio
    async def test_import_model_asset(
        self, service: ModelAssetImportService, tmp_path: Path,
    ) -> None:
        """验证完整的模型资产导入流程：文件归档 -> 元数据写入 -> 制品创建。"""
        # 创建临时 FAST 文件
        fst_file = tmp_path / "test_model.fst"
        fst_file.write_text("FAST v8 input file")

        request = ModelAssetImportRequest(
            model_code="WF_IMPORT_001",
            model_name="导入测试模型",
            model_type="FAST",
            asset_scope="WIND_FARM",
            version="1.0",
            files=[str(fst_file)],
        )
        result = await service.import_model_asset(request)
        assert result.success is True
        assert result.model_code == "WF_IMPORT_001"
        assert result.model_asset_id is not None
        assert result.parser_status == "IMPORTED"
        assert len(result.artifact_ids) >= 1

    @pytest.mark.asyncio
    async def test_import_model_asset_with_parent(
        self, service: ModelAssetImportService, tmp_path: Path,
    ) -> None:
        """验证带父模型的资产导入。"""
        f1 = tmp_path / "parent.fst"
        f1.write_text("parent")
        f2 = tmp_path / "child.fst"
        f2.write_text("child")

        # 先导入父模型
        parent_req = ModelAssetImportRequest(
            model_code="PARENT_001", model_name="父", model_type="FAST",
            asset_scope="WTG", files=[str(f1)],
        )
        parent_result = await service.import_model_asset(parent_req)
        assert parent_result.success

        # 再导入子模型（引用父）
        child_req = ModelAssetImportRequest(
            model_code="CHILD_001", model_name="子", model_type="FAST",
            asset_scope="WTG", version="2.0",
            parent_model_code="PARENT_001", files=[str(f2)],
        )
        child_result = await service.import_model_asset(child_req)
        assert child_result.success
        assert child_result.model_asset_id != parent_result.model_asset_id

    @pytest.mark.asyncio
    async def test_import_model_asset_file_not_found(
        self, service: ModelAssetImportService,
    ) -> None:
        """验证文件不存在时仍能成功导入（归档失败不影响元数据写入）。"""
        request = ModelAssetImportRequest(
            model_code="NOFILE_001",
            model_name="无文件模型",
            model_type="FAST",
            asset_scope="WTG",
            files=["/nonexistent/file.fst"],
        )
        result = await service.import_model_asset(request)
        # 归档失败但 metadata 创建应成功
        assert result.success is True
        assert result.model_asset_id is not None

    @pytest.mark.asyncio
    async def test_import_model_asset_duplicate_code(
        self, service: ModelAssetImportService, tmp_path: Path,
    ) -> None:
        """验证重复 model_code 导入失败。"""
        f = tmp_path / "dup.fst"
        f.write_text("test")

        req = ModelAssetImportRequest(
            model_code="DUP_001", model_name="第一次",
            model_type="FAST", asset_scope="WTG", files=[str(f)],
        )
        result1 = await service.import_model_asset(req)
        assert result1.success is True

        result2 = await service.import_model_asset(req)
        assert result2.success is False

    @pytest.mark.asyncio
    async def test_import_unsupported_files(
        self, service: ModelAssetImportService, tmp_path: Path,
    ) -> None:
        """验证不支持的文件类型返回失败。"""
        txt = tmp_path / "data.txt"
        txt.write_text("not a simulation file")

        request = ModelAssetImportRequest(
            model_code="UNSUPP_001",
            model_name="不支持的类型",
            model_type="OTHER",
            asset_scope="WTG",
            files=[str(txt)],
        )
        result = await service.import_model_asset(request)
        # 全部文件 UNSUPPORTED 应返回失败
        assert result.success is False
        assert result.parser_status == "UNSUPPORTED"

    @pytest.mark.asyncio
    async def test_import_simulation_case(
        self, service: ModelAssetImportService, tmp_path: Path,
    ) -> None:
        """验证仿真案例导入。"""
        # 先导入模型
        f = tmp_path / "model.fst"
        f.write_text("model")
        import_req = ModelAssetImportRequest(
            model_code="MC_CASE", model_name="N", model_type="FAST",
            asset_scope="WTG", files=[str(f)],
        )
        await service.import_model_asset(import_req)

        case_req = SimulationCaseImportRequest(
            case_code="CASE_IMP_001",
            case_name="DLC 1.2",
            model_code="MC_CASE",
            case_type="DESIGN",
            parameters={"ws": 12.0},
            created_by="tester",
        )
        result = await service.import_simulation_case(case_req)
        assert result["success"] is True
        assert result["case_code"] == "CASE_IMP_001"
        assert result["simulation_case_id"] is not None

    @pytest.mark.asyncio
    async def test_import_simulation_case_missing_model(
        self, service: ModelAssetImportService,
    ) -> None:
        """验证导入案例时模型不存在则报错。"""
        case_req = SimulationCaseImportRequest(
            case_code="BAD_CASE", case_name="X",
            model_code="NONEXISTENT", case_type="DESIGN",
        )
        with pytest.raises(ValueError, match="模型资产不存在"):
            await service.import_simulation_case(case_req)

    @pytest.mark.asyncio
    async def test_import_simulation_result(
        self, service: ModelAssetImportService, tmp_path: Path,
    ) -> None:
        """验证仿真结果导入。"""
        # 先导入模型和案例
        f = tmp_path / "model.fst"
        f.write_text("model")
        await service.import_model_asset(ModelAssetImportRequest(
            model_code="MC_RES", model_name="N", model_type="FAST",
            asset_scope="WTG", files=[str(f)],
        ))
        await service.import_simulation_case(SimulationCaseImportRequest(
            case_code="CASE_RES", case_name="X",
            model_code="MC_RES", case_type="DESIGN",
        ))

        result_req = SimulationResultImportRequest(
            result_code="RES_IMP_001",
            case_code="CASE_RES",
            result_type="TIMESERIES",
            summary={"max": 100},
            metrics={"aep": 20},
        )
        result = await service.import_simulation_result(result_req)
        assert result["success"] is True
        assert result["result_code"] == "RES_IMP_001"
        assert result["simulation_result_id"] is not None

    @pytest.mark.asyncio
    async def test_import_simulation_result_missing_case(
        self, service: ModelAssetImportService,
    ) -> None:
        """验证导入结果时案例不存在则报错。"""
        result_req = SimulationResultImportRequest(
            result_code="BAD_RES", case_code="NONEXISTENT", result_type="SUMMARY",
        )
        with pytest.raises(ValueError, match="仿真案例不存在"):
            await service.import_simulation_result(result_req)
