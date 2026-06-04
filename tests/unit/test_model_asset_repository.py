"""model_asset repository 单元测试。

验证 ModelAssetRepository 的 CRUD 操作，使用 SQLite 内存数据库进行 mock。
测试模型资产、仿真案例、仿真结果和仿真制品的创建与查询。

被验证对象：
- whale.model_asset.repository: ModelAssetRepository

测试阶段：开发期验证 (unit，使用 SQLite :memory:)。
不能证明：真实 PostgreSQL 数据库下的性能和并发行为。
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from whale.shared.persistence import Base
from whale.model_asset.repository import ModelAssetRepository


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
def repo(session: Session) -> ModelAssetRepository:
    """创建 ModelAssetRepository 实例。"""
    return ModelAssetRepository(session)


class TestModelAssetRepository:
    """ModelAsset 仓库测试。"""

    def test_create_model_asset(self, repo: ModelAssetRepository) -> None:
        """验证创建模型资产并返回带 ID 的实例。"""
        asset = repo.create_model_asset(
            model_code="WF_FAST_v1",
            model_name="风场FAST模型",
            model_type="FAST",
            asset_scope="WIND_FARM",
        )
        assert asset.model_asset_id is not None
        assert asset.model_asset_id > 0
        assert asset.model_code == "WF_FAST_v1"
        assert asset.model_type == "FAST"
        assert asset.parser_status == "IMPORTED"

    def test_create_model_asset_with_all_fields(self, repo: ModelAssetRepository) -> None:
        """验证创建模型资产时所有字段正确持久化。"""
        asset = repo.create_model_asset(
            model_code="WTG_FAST_v1",
            model_name="风机FAST模型",
            model_type="FAST",
            asset_scope="WTG",
            version="2.0",
            source_file_uri="/data/test.fst",
            checksum_sha256="abc123",
            parser_status="IMPORTED",
            metadata_json={"rated_power_mw": 5.0},
        )
        assert asset.version == "2.0"
        assert asset.source_file_uri == "/data/test.fst"
        assert asset.checksum_sha256 == "abc123"
        assert asset.metadata_json["rated_power_mw"] == 5.0

    def test_get_model_asset_by_code(self, repo: ModelAssetRepository) -> None:
        """验证按 model_code 查询。"""
        repo.create_model_asset(
            model_code="MC_001", model_name="N1", model_type="FAST", asset_scope="WTG",
        )
        found = repo.get_model_asset_by_code("MC_001")
        assert found is not None
        assert found.model_code == "MC_001"
        assert found.model_name == "N1"

    def test_get_model_asset_by_code_not_found(self, repo: ModelAssetRepository) -> None:
        """验证查询不存在的 code 返回 None。"""
        found = repo.get_model_asset_by_code("NONEXISTENT")
        assert found is None

    def test_get_model_asset_by_id(self, repo: ModelAssetRepository) -> None:
        """验证按主键查询。"""
        created = repo.create_model_asset(
            model_code="MC_002", model_name="N2", model_type="FAST", asset_scope="WTG",
        )
        found = repo.get_model_asset_by_id(created.model_asset_id)
        assert found is not None
        assert found.model_asset_id == created.model_asset_id

    def test_get_model_asset_by_id_not_found(self, repo: ModelAssetRepository) -> None:
        """验证查询不存在的主键返回 None。"""
        found = repo.get_model_asset_by_id(99999)
        assert found is None

    def test_create_duplicate_model_code_raises(self, repo: ModelAssetRepository) -> None:
        """验证重复 model_code 抛出异常。"""
        repo.create_model_asset(
            model_code="DUP", model_name="N", model_type="FAST", asset_scope="WTG",
        )
        with pytest.raises(Exception):
            repo.create_model_asset(
                model_code="DUP", model_name="N2", model_type="FAST", asset_scope="WTG",
            )

    def test_parent_model_asset_relationship(self, repo: ModelAssetRepository) -> None:
        """验证父子模型资产关系。"""
        parent = repo.create_model_asset(
            model_code="PARENT", model_name="父模型", model_type="FAST", asset_scope="WTG",
        )
        child = repo.create_model_asset(
            model_code="CHILD",
            model_name="子模型",
            model_type="FAST",
            asset_scope="WTG",
            version="2.0",
            parent_model_asset_id=parent.model_asset_id,
        )
        assert child.parent_model_asset_id == parent.model_asset_id


class TestSimulationCaseRepository:
    """SimulationCase 仓库测试。"""

    def test_create_simulation_case(
        self, repo: ModelAssetRepository, session: Session,
    ) -> None:
        """验证创建仿真案例。"""
        asset = repo.create_model_asset(
            model_code="MC_CASE", model_name="N", model_type="FAST", asset_scope="WTG",
        )
        case = repo.create_simulation_case(
            case_code="CASE_001",
            case_name="DLC 1.2",
            model_asset_id=asset.model_asset_id,
            case_type="DESIGN",
            parameter_json={"ws": 12.0},
            scenario_json={"turb": "NTM"},
        )
        assert case.simulation_case_id is not None
        assert case.case_code == "CASE_001"
        assert case.case_type == "DESIGN"
        assert case.parameter_json["ws"] == 12.0

    def test_create_case_nonexistent_model_raises(
        self, repo: ModelAssetRepository,
    ) -> None:
        """验证关联不存在的模型资产抛出异常。"""
        with pytest.raises(ValueError, match="模型资产不存在"):
            repo.create_simulation_case(
                case_code="BAD", case_name="X", model_asset_id=99999, case_type="DESIGN",
            )

    def test_get_case_by_code(
        self, repo: ModelAssetRepository, session: Session,
    ) -> None:
        """验证按 case_code 查询。"""
        asset = repo.create_model_asset(
            model_code="M_C", model_name="N", model_type="FAST", asset_scope="WTG",
        )
        repo.create_simulation_case(
            case_code="C_001", case_name="X", model_asset_id=asset.model_asset_id,
            case_type="DESIGN",
        )
        found = repo.get_case_by_code("C_001")
        assert found is not None
        assert found.case_name == "X"

    def test_get_case_not_found(self, repo: ModelAssetRepository) -> None:
        """验证查询不存在的案例返回 None。"""
        assert repo.get_case_by_code("NONEXISTENT") is None

    def test_create_duplicate_case_code_raises(
        self, repo: ModelAssetRepository, session: Session,
    ) -> None:
        """验证重复 case_code 抛出异常。"""
        asset = repo.create_model_asset(
            model_code="M_DUP", model_name="N", model_type="FAST", asset_scope="WTG",
        )
        repo.create_simulation_case(
            case_code="DUP_CASE", case_name="X",
            model_asset_id=asset.model_asset_id, case_type="DESIGN",
        )
        with pytest.raises(Exception):
            repo.create_simulation_case(
                case_code="DUP_CASE", case_name="Y",
                model_asset_id=asset.model_asset_id, case_type="DESIGN",
            )


class TestSimulationResultRepository:
    """SimulationResult 仓库测试。"""

    def test_create_simulation_result(
        self, repo: ModelAssetRepository, session: Session,
    ) -> None:
        """验证创建仿真结果。"""
        asset = repo.create_model_asset(
            model_code="M_RES", model_name="N", model_type="FAST", asset_scope="WTG",
        )
        case = repo.create_simulation_case(
            case_code="C_RES", case_name="X",
            model_asset_id=asset.model_asset_id, case_type="DESIGN",
        )
        result = repo.create_simulation_result(
            simulation_case_id=case.simulation_case_id,
            result_code="RES_001",
            result_type="TIMESERIES",
            time_series_backend="FILE",
            summary_json={"max_power": 5200},
            metric_json={"aep": 22.5},
        )
        assert result.simulation_result_id is not None
        assert result.result_code == "RES_001"
        assert result.time_series_backend == "FILE"
        assert result.summary_json["max_power"] == 5200

    def test_create_result_nonexistent_case_raises(
        self, repo: ModelAssetRepository,
    ) -> None:
        """验证关联不存在的案例抛出异常。"""
        with pytest.raises(ValueError, match="仿真案例不存在"):
            repo.create_simulation_result(
                simulation_case_id=99999,
                result_code="BAD", result_type="SUMMARY",
            )

    def test_get_result_by_code(
        self, repo: ModelAssetRepository, session: Session,
    ) -> None:
        """验证按 result_code 查询。"""
        asset = repo.create_model_asset(
            model_code="M_R", model_name="N", model_type="FAST", asset_scope="WTG",
        )
        case = repo.create_simulation_case(
            case_code="C_R", case_name="X",
            model_asset_id=asset.model_asset_id, case_type="DESIGN",
        )
        repo.create_simulation_result(
            simulation_case_id=case.simulation_case_id,
            result_code="R_001", result_type="SUMMARY",
        )
        found = repo.get_result_by_code("R_001")
        assert found is not None
        assert found.result_type == "SUMMARY"

    def test_get_result_not_found(self, repo: ModelAssetRepository) -> None:
        """验证查询不存在的结果返回 None。"""
        assert repo.get_result_by_code("NONEXISTENT") is None


class TestSimulationArtifactRepository:
    """SimulationArtifact 仓库测试。"""

    def test_create_artifact(
        self, repo: ModelAssetRepository, session: Session,
    ) -> None:
        """验证创建仿真制品。"""
        asset = repo.create_model_asset(
            model_code="M_ART", model_name="N", model_type="FAST", asset_scope="WTG",
        )
        artifact = repo.create_artifact(
            owner_type="MODEL_ASSET",
            owner_id=asset.model_asset_id,
            artifact_type="SOURCE_FILE",
            file_uri="/data/test.fst",
            checksum_sha256="abc123",
        )
        assert artifact.simulation_artifact_id is not None
        assert artifact.owner_type == "MODEL_ASSET"
        assert artifact.owner_id == asset.model_asset_id
        assert artifact.file_uri == "/data/test.fst"
        assert artifact.checksum_sha256 == "abc123"

    def test_create_artifact_with_metadata(
        self, repo: ModelAssetRepository, session: Session,
    ) -> None:
        """验证创建带元数据的制品。"""
        asset = repo.create_model_asset(
            model_code="M_ART2", model_name="N", model_type="FAST", asset_scope="WTG",
        )
        artifact = repo.create_artifact(
            owner_type="MODEL_ASSET",
            owner_id=asset.model_asset_id,
            artifact_type="CONFIG",
            file_uri="/data/config.yaml",
            metadata_json={"version": "3.5"},
        )
        assert artifact.metadata_json["version"] == "3.5"
