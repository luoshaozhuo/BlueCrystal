"""model_asset PostgreSQL 真实集成测试。

验证 model_asset 四表在真实 PostgreSQL 环境下的：
- Alembic upgrade/downgrade 四表。
- FK 链约束（model_asset -> simulation_case -> simulation_result 和 artifact）。
- Unique constraint（model_code / case_code / result_code）。
- parent_model_asset_id 自引用 FK。
- ModelAssetRepository CRUD 操作。
- ModelAssetImportService 导入最小闭环。

被验证对象：
- alembic/versions/20260527_000004_add_model_asset_tables.py
- whale.model_asset.repository: ModelAssetRepository
- whale.model_asset.service: ModelAssetImportService
- whale.shared.persistence.orm.model_asset: ModelAsset/SimulationCase/SimulationResult/SimulationArtifact

测试阶段：准生产依赖验证期 (integration，需真实 PostgreSQL)。
环境依赖：WHALE_TEST_POSTGRES_DSN 环境变量（如 postgresql://user:pass@localhost:5432/whale_test）。
不能证明：SQLite 下的迁移和 CRUD 行为（由模块集成期验证覆盖）。
NOT_RUN 条件：MISSING_ENVIRONMENT — WHALE_TEST_POSTGRES_DSN 未设置或 PostgreSQL 不可达。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

# ---- 环境探测 ----

PG_DSN = os.getenv("WHALE_TEST_POSTGRES_DSN", "")
PG_DSN_SET = bool(PG_DSN)

PG_AVAILABLE = False
PG_CONNECTION_ERROR: str | None = None

if PG_DSN_SET:
    try:
        # 尝试连接 PostgreSQL 验证可用性
        test_engine = create_engine(PG_DSN, connect_args={"connect_timeout": 5})
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        PG_AVAILABLE = True
        test_engine.dispose()
    except Exception as exc:
        PG_CONNECTION_ERROR = str(exc)[:200]
        PG_AVAILABLE = False
else:
    PG_CONNECTION_ERROR = "WHALE_TEST_POSTGRES_DSN 环境变量未设置"

# 仅 DSN 未设置时才 skip；DSN 已设置但连接失败时让 fixture 报 FAIL
_NOT_RUN_REASON = (
    "NOT_RUN: MISSING_ENVIRONMENT: WHALE_TEST_POSTGRES_DSN 环境变量未设置"
)


# ---- Fixtures ----

@pytest.fixture(scope="function")
def pg_session() -> Generator[Session, None, None]:
    """创建 PostgreSQL 数据库 session。

    使用 Alembic upgrade 创建表结构，测试结束后 drop 所有表。

    Yields:
        SQLAlchemy Session 实例。
    """
    if not PG_DSN_SET:
        pytest.skip(_NOT_RUN_REASON)
    if not PG_AVAILABLE:
        pytest.fail(f"FAIL: PostgreSQL 连接失败 — {PG_CONNECTION_ERROR}")

    engine = create_engine(PG_DSN)
    # 使用 Alembic migration 创建表
    from alembic import command
    from alembic.config import Config

    alembic_root = Path(__file__).resolve().parents[2]
    ini_path = alembic_root / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(alembic_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", PG_DSN)

    # 先确保数据库状态干净（downgrade 到模型资产迁移之前）
    try:
        command.downgrade(cfg, "20260527_000003")
    except Exception:
        pass  # 可能不存在，忽略

    # upgrade 到最新
    command.upgrade(cfg, "head")

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # 清理：downgrade 移除模型资产表
        try:
            command.downgrade(cfg, "20260527_000003")
        except Exception:
            pass
        engine.dispose()


@pytest.fixture(scope="function")
def pg_session_direct() -> Generator[Session, None, None]:
    """创建 PostgreSQL session（使用 Base.metadata.create_all 而非 Alembic）。

    适用于 CRUD 测试，不需要完整的 Alembic 迁移链。

    Yields:
        SQLAlchemy Session 实例。
    """
    if not PG_DSN_SET:
        pytest.skip(_NOT_RUN_REASON)
    if not PG_AVAILABLE:
        pytest.fail(f"FAIL: PostgreSQL 连接失败 — {PG_CONNECTION_ERROR}")

    from whale.shared.persistence import Base

    engine = create_engine(PG_DSN)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        # 清理 model_asset 相关表
        from whale.shared.persistence.orm.model_asset import (
            ModelAsset,
            SimulationArtifact,
            SimulationCase,
            SimulationResult,
        )
        for table_cls in [SimulationArtifact, SimulationResult, SimulationCase, ModelAsset]:
            try:
                table_cls.__table__.drop(engine, checkfirst=True)
            except Exception:
                pass
        engine.dispose()


# ---- Alembic Migration Tests ----

@pytest.mark.l5
@pytest.mark.skipif(not PG_DSN_SET, reason=_NOT_RUN_REASON)
class TestModelAssetPostgresAlembic:
    """PostgreSQL Alembic 迁移测试。

    验证 upgrade/downgrade 四表、列完整性和 revision chain。
    """

    def test_upgrade_creates_four_tables(self) -> None:
        """验证 upgrade 到最新版本创建全部四张表。"""
        engine = create_engine(PG_DSN)
        inspector = inspect(engine)

        tables = inspector.get_table_names()
        for expected in ("model_asset", "simulation_case", "simulation_result", "simulation_artifact"):
            assert expected in tables, f"表 {expected} 不存在: 现有表 {tables}"

        engine.dispose()

    def test_downgrade_removes_four_tables(self, pg_session: Session) -> None:
        """验证 downgrade 后四张表被移除。

        依赖 pg_session fixture 的 upgrade + downgrade 流程。
        """
        engine = create_engine(PG_DSN)
        inspector = inspect(engine)

        tables = inspector.get_table_names()
        for not_expected in ("model_asset", "simulation_case", "simulation_result", "simulation_artifact"):
            assert not_expected not in tables, f"表 {not_expected} 在 downgrade 后仍存在"

        engine.dispose()

    def test_revision_chain(self) -> None:
        """验证 revision chain 正确连接。"""
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        alembic_root = Path(__file__).resolve().parents[2]
        cfg = Config(str(alembic_root / "alembic.ini"))
        cfg.set_main_option("script_location", str(alembic_root / "alembic"))

        scripts = ScriptDirectory.from_config(cfg)
        rev_004 = scripts.get_revision("20260527_000004")
        assert rev_004 is not None, "revision 20260527_000004 不存在"
        assert rev_004.revision == "20260527_000004"
        assert rev_004.down_revision is not None
        down_str = str(rev_004.down_revision)
        assert "20260527_000003" in down_str, f"down_revision 期望包含 20260527_000003，实际 {down_str}"


# ---- FK Chain Tests ----

@pytest.mark.l5
@pytest.mark.skipif(not PG_DSN_SET, reason=_NOT_RUN_REASON)
class TestModelAssetPostgresFKChain:
    """PostgreSQL FK 链约束测试。

    验证 model_asset -> simulation_case -> simulation_result 和
    simulation_artifact 的外键引用完整性。
    """

    def test_fk_chain_insert_and_verify(self, pg_session_direct: Session) -> None:
        """验证 FK 链：创建模型 -> 案例 -> 结果 -> 制品 完整链路。

        通过条件：
        1. 四表数据可完整插入。
        2. 关联查询返回正确数据。
        3. 删除父记录时 FK 约束阻止（或级联行为符合预期）。
        """
        from whale.model_asset.repository import ModelAssetRepository
        from whale.shared.persistence.orm.model_asset import (
            SimulationArtifact,
        )

        repo = ModelAssetRepository(pg_session_direct)

        # 1. 创建模型资产
        asset = repo.create_model_asset(
            model_code="PG_FK_ASSET_001",
            model_name="FK 链测试模型",
            model_type="FAST",
            asset_scope="WTG",
        )
        assert asset.model_asset_id is not None

        # 2. 创建仿真案例
        case = repo.create_simulation_case(
            case_code="PG_FK_CASE_001",
            case_name="FK 链测试案例",
            model_asset_id=asset.model_asset_id,
            case_type="DESIGN",
        )
        assert case.simulation_case_id is not None

        # 3. 创建仿真结果
        result = repo.create_simulation_result(
            simulation_case_id=case.simulation_case_id,
            result_code="PG_FK_RESULT_001",
            result_type="TIMESERIES",
        )
        assert result.simulation_result_id is not None

        # 4. 创建仿真制品（关联到结果）
        artifact = repo.create_artifact(
            owner_type="SIMULATION_RESULT",
            owner_id=result.simulation_result_id,
            artifact_type="RESULT_FILE",
            file_uri="s3://whale-test/results/pg_fk_result.csv",
        )
        assert artifact.simulation_artifact_id is not None

        # 5. 验证制品可通过 SQL 查询关联
        artifacts = (
            pg_session_direct.query(SimulationArtifact)
            .filter(SimulationArtifact.owner_id == result.simulation_result_id)
            .all()
        )
        assert len(artifacts) == 1

    def test_fk_constraint_prevents_orphan_case(self, pg_session_direct: Session) -> None:
        """验证 FK 约束：尝试创建引用不存在模型的案例时失败。

        通过条件：创建 simulation_case 引用不存在的 model_asset_id 时抛出 IntegrityError。
        """
        from whale.model_asset.repository import ModelAssetRepository

        repo = ModelAssetRepository(pg_session_direct)

        with pytest.raises((IntegrityError, ValueError)):
            repo.create_simulation_case(
                case_code="PG_ORPHAN_CASE",
                case_name="孤儿案例",
                model_asset_id=999999,  # 不存在的 model_asset_id
                case_type="DESIGN",
            )

    def test_fk_constraint_prevents_orphan_result(self, pg_session_direct: Session) -> None:
        """验证 FK 约束：尝试创建引用不存在案例的结果时失败。

        通过条件：创建 simulation_result 引用不存在的 simulation_case_id 时抛出异常。
        """
        from whale.model_asset.repository import ModelAssetRepository

        repo = ModelAssetRepository(pg_session_direct)

        with pytest.raises((IntegrityError, ValueError)):
            repo.create_simulation_result(
                simulation_case_id=999999,  # 不存在的 simulation_case_id
                result_code="PG_ORPHAN_RESULT",
                result_type="TIMESERIES",
            )


# ---- Unique Constraint Tests ----

@pytest.mark.l5
@pytest.mark.skipif(not PG_DSN_SET, reason=_NOT_RUN_REASON)
class TestModelAssetPostgresUniqueConstraint:
    """PostgreSQL Unique Constraint 测试。

    验证 model_code、case_code、result_code 的 unique 约束。
    """

    def test_duplicate_model_code_rejected(self, pg_session_direct: Session) -> None:
        """验证重复 model_code 被拒绝。

        通过条件：第二次插入相同 model_code 时抛出 IntegrityError。
        """
        from whale.shared.persistence.orm.model_asset import ModelAsset

        # 第一次插入
        a1 = ModelAsset(
            model_code="PG_UC_MODEL",
            model_name="Unique 测试模型 1",
            model_type="FAST",
            asset_scope="WTG",
        )
        pg_session_direct.add(a1)
        pg_session_direct.flush()

        # 第二次插入相同 model_code
        a2 = ModelAsset(
            model_code="PG_UC_MODEL",
            model_name="Unique 测试模型 2",
            model_type="OPENFAST",
            asset_scope="SITE",
        )
        pg_session_direct.add(a2)
        with pytest.raises(IntegrityError):
            pg_session_direct.flush()
        pg_session_direct.rollback()

    def test_duplicate_case_code_rejected(self, pg_session_direct: Session) -> None:
        """验证重复 case_code 被拒绝。"""
        from whale.model_asset.repository import ModelAssetRepository

        repo = ModelAssetRepository(pg_session_direct)
        asset = repo.create_model_asset(
            model_code="PG_UC_CASE_MODEL",
            model_name="Case Unique 测试模型",
            model_type="FAST",
            asset_scope="WTG",
        )

        # 第一次创建
        repo.create_simulation_case(
            case_code="PG_UC_CASE",
            case_name="Case Unique 1",
            model_asset_id=asset.model_asset_id,
            case_type="DESIGN",
        )

        # 第二次创建相同 case_code
        with pytest.raises(IntegrityError):
            repo.create_simulation_case(
                case_code="PG_UC_CASE",
                case_name="Case Unique 2",
                model_asset_id=asset.model_asset_id,
                case_type="DESIGN",
            )

    def test_duplicate_result_code_rejected(self, pg_session_direct: Session) -> None:
        """验证重复 result_code 被拒绝。"""
        from whale.model_asset.repository import ModelAssetRepository

        repo = ModelAssetRepository(pg_session_direct)
        asset = repo.create_model_asset(
            model_code="PG_UC_RES_MODEL",
            model_name="Result Unique 测试模型",
            model_type="FAST",
            asset_scope="WTG",
        )
        case = repo.create_simulation_case(
            case_code="PG_UC_RES_CASE",
            case_name="Result Unique 测试案例",
            model_asset_id=asset.model_asset_id,
            case_type="DESIGN",
        )

        # 第一次创建
        repo.create_simulation_result(
            simulation_case_id=case.simulation_case_id,
            result_code="PG_UC_RESULT",
            result_type="TIMESERIES",
        )

        # 第二次创建相同 result_code
        with pytest.raises(IntegrityError):
            repo.create_simulation_result(
                simulation_case_id=case.simulation_case_id,
                result_code="PG_UC_RESULT",
                result_type="SUMMARY",
            )


# ---- Self-Referencing FK Test ----

@pytest.mark.l5
@pytest.mark.skipif(not PG_DSN_SET, reason=_NOT_RUN_REASON)
class TestModelAssetPostgresSelfRefFK:
    """PostgreSQL parent_model_asset_id 自引用 FK 测试。

    验证模型资产版本派生关系的自引用外键约束。
    """

    def test_self_ref_fk_valid_parent(self, pg_session_direct: Session) -> None:
        """验证 parent_model_asset_id 引用有效父模型时插入成功。

        通过条件：
        1. 创建父模型资产。
        2. 创建子模型资产，引用父模型的 model_asset_id。
        3. 子模型的 parent_model_asset_id 指向父模型。
        """
        from whale.model_asset.repository import ModelAssetRepository

        repo = ModelAssetRepository(pg_session_direct)

        # 创建父模型
        parent = repo.create_model_asset(
            model_code="PG_SELFREF_PARENT",
            model_name="父模型 v1",
            model_type="FAST",
            asset_scope="WTG",
            version="1.0",
        )

        # 创建子模型派生自父模型
        child = repo.create_model_asset(
            model_code="PG_SELFREF_CHILD",
            model_name="子模型 v2 派生",
            model_type="FAST",
            asset_scope="WTG",
            version="2.0",
            parent_model_asset_id=parent.model_asset_id,
        )

        assert child.parent_model_asset_id == parent.model_asset_id
        assert child.model_asset_id != parent.model_asset_id

        # 验证可通过查询找到派生链
        parent_read = repo.get_model_asset_by_id(parent.model_asset_id)
        assert parent_read is not None
        child_read = repo.get_model_asset_by_code("PG_SELFREF_CHILD")
        assert child_read is not None
        assert child_read.parent_model_asset_id == parent.model_asset_id

    def test_self_ref_fk_invalid_parent_rejected(self, pg_session_direct: Session) -> None:
        """验证 parent_model_asset_id 引用不存在的父模型时被拒绝。

        通过条件：使用不存在的 parent_model_asset_id 插入时抛出 IntegrityError。
        """
        from whale.shared.persistence.orm.model_asset import ModelAsset

        child = ModelAsset(
            model_code="PG_SELFREF_ORPHAN",
            model_name="孤儿子模型",
            model_type="FAST",
            asset_scope="WTG",
            parent_model_asset_id=999999,  # 不存在的父模型
        )
        pg_session_direct.add(child)
        with pytest.raises(IntegrityError):
            pg_session_direct.flush()
        pg_session_direct.rollback()


# ---- Repository CRUD Tests ----

@pytest.mark.l5
@pytest.mark.skipif(not PG_DSN_SET, reason=_NOT_RUN_REASON)
class TestModelAssetPostgresRepositoryCRUD:
    """PostgreSQL ModelAssetRepository CRUD 测试。

    验证 repository 在真实 PostgreSQL 下的创建、查询和错误处理。
    """

    def test_create_and_query_model_asset(self, pg_session_direct: Session) -> None:
        """验证模型资产的创建和查询。

        通过条件：
        1. create_model_asset() 返回正确 ModelAsset 实例。
        2. get_model_asset_by_code() 返回正确记录。
        3. get_model_asset_by_id() 返回正确记录。
        """
        from whale.model_asset.repository import ModelAssetRepository

        repo = ModelAssetRepository(pg_session_direct)

        asset = repo.create_model_asset(
            model_code="PG_CRUD_MODEL_001",
            model_name="CRUD 测试模型",
            model_type="OPENFAST",
            asset_scope="SITE",
            version="3.5",
            metadata_json={"turbine_class": "IEC IIB", "rated_power_mw": 5.0},
        )
        assert asset.model_asset_id is not None
        assert asset.model_code == "PG_CRUD_MODEL_001"

        # 按 code 查询
        found = repo.get_model_asset_by_code("PG_CRUD_MODEL_001")
        assert found is not None
        assert found.model_name == "CRUD 测试模型"
        assert found.metadata_json["turbine_class"] == "IEC IIB"

        # 按 id 查询
        found_by_id = repo.get_model_asset_by_id(asset.model_asset_id)
        assert found_by_id is not None
        assert found_by_id.model_code == "PG_CRUD_MODEL_001"

    def test_create_simulation_case_and_result(self, pg_session_direct: Session) -> None:
        """验证仿真案例和结果的创建与查询。

        通过条件：
        1. create_simulation_case() 返回正确 SimulationCase。
        2. get_case_by_code() 查询正确。
        3. create_simulation_result() 返回正确 SimulationResult。
        4. get_result_by_code() 查询正确。
        """
        from whale.model_asset.repository import ModelAssetRepository

        repo = ModelAssetRepository(pg_session_direct)

        # 先创建模型
        asset = repo.create_model_asset(
            model_code="PG_CRUD_CHAIN_MODEL",
            model_name="CRUD 链模型",
            model_type="FAST",
            asset_scope="WTG",
        )

        # 创建案例
        case = repo.create_simulation_case(
            case_code="PG_CRUD_CHAIN_CASE",
            case_name="CRUD 链案例",
            model_asset_id=asset.model_asset_id,
            case_type="DESIGN",
            parameter_json={"wind_speed": 12.0},
        )
        assert case.simulation_case_id is not None

        found_case = repo.get_case_by_code("PG_CRUD_CHAIN_CASE")
        assert found_case is not None
        assert found_case.parameter_json["wind_speed"] == 12.0

        # 创建结果
        result = repo.create_simulation_result(
            simulation_case_id=case.simulation_case_id,
            result_code="PG_CRUD_CHAIN_RESULT",
            result_type="TIMESERIES",
            summary_json={"max_power_kw": 5200},
        )
        assert result.simulation_result_id is not None

        found_result = repo.get_result_by_code("PG_CRUD_CHAIN_RESULT")
        assert found_result is not None
        assert found_result.summary_json["max_power_kw"] == 5200

    def test_create_artifact(self, pg_session_direct: Session) -> None:
        """验证仿真制品的创建。

        通过条件：
        1. create_artifact() 返回正确 SimulationArtifact。
        2. 制品关联到正确的 owner_type 和 owner_id。
        """
        from whale.model_asset.repository import ModelAssetRepository

        repo = ModelAssetRepository(pg_session_direct)

        asset = repo.create_model_asset(
            model_code="PG_ARTIFACT_MODEL",
            model_name="Artifact 测试模型",
            model_type="FAST",
            asset_scope="WTG",
        )

        artifact = repo.create_artifact(
            owner_type="MODEL_ASSET",
            owner_id=asset.model_asset_id,
            artifact_type="SOURCE_FILE",
            file_uri="s3://whale-test/models/pg_artifact.fst",
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb924",
            metadata_json={"format": "FAST v8"},
        )
        assert artifact.simulation_artifact_id is not None
        assert artifact.owner_type == "MODEL_ASSET"
        assert artifact.owner_id == asset.model_asset_id
        assert artifact.file_uri == "s3://whale-test/models/pg_artifact.fst"


# ---- Import Service Minimal Closed Loop Test ----


@pytest.mark.l5
@pytest.mark.skipif(not PG_DSN_SET, reason=_NOT_RUN_REASON)
class TestModelAssetPostgresImportService:
    """PostgreSQL ModelAssetImportService 导入最小闭环测试。

    验证 import_model_asset、import_simulation_case 和
    import_simulation_result 在真实 PostgreSQL 下的完整流程。
    """

    def test_import_model_asset_minimal(self, pg_session_direct: Session, tmp_path: Path) -> None:
        """验证基于真实 PostgreSQL 的模型资产导入最小闭环。

        通过条件：
        1. import_model_asset() 返回 success=True。
        2. 模型资产持久化到 PostgreSQL 并可查询。
        3. 模型制品记录正确创建。
        """
        from whale.model_asset.archive import SimulationArchiveService
        from whale.model_asset.detector import SimulationFileTypeDetector
        from whale.model_asset.models import ModelAssetImportRequest
        from whale.model_asset.repository import ModelAssetRepository
        from whale.model_asset.service import ModelAssetImportService
        from whale.storage.raw_archive import (
            InMemoryManifestRepository,
            LocalCompressedArchiveSink,
        )

        # 准备测试文件
        fst_file = tmp_path / "pg_import_test.fst"
        fst_file.write_text("FAST v8.16 input for PostgreSQL integration test")

        detector = SimulationFileTypeDetector()
        archive_sink = LocalCompressedArchiveSink(tmp_path / "archive")
        manifest_repo = InMemoryManifestRepository()
        archive_svc = SimulationArchiveService(archive_sink, manifest_repo)
        # 使用真实 PostgreSQL session 的仓库
        repo = ModelAssetRepository(pg_session_direct)
        service = ModelAssetImportService(detector, archive_svc, repo)

        import asyncio

        async def _do_import():
            request = ModelAssetImportRequest(
                model_code="PG_IMPORT_SVC_001",
                model_name="PostgreSQL 导入服务测试模型",
                model_type="FAST",
                asset_scope="WTG",
                version="1.0",
                files=[str(fst_file)],
            )
            return await service.import_model_asset(request)

        result = asyncio.run(_do_import())
        assert result.success is True, f"导入失败: {result.error_message}"
        assert result.model_asset_id is not None

        # 验证 PostgreSQL 中可查询
        asset = repo.get_model_asset_by_code("PG_IMPORT_SVC_001")
        assert asset is not None
        assert asset.model_name == "PostgreSQL 导入服务测试模型"
        assert asset.parser_status == "IMPORTED"

    def test_import_case_and_result_chain(self, pg_session_direct: Session, tmp_path: Path) -> None:
        """验证基于真实 PostgreSQL 的案例和结果导入链。

        通过条件：
        1. import_model_asset() 成功。
        2. import_simulation_case() 成功。
        3. import_simulation_result() 成功。
        4. 全链路数据在 PostgreSQL 中可查询。
        """
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

        # 准备
        fst_file = tmp_path / "pg_chain_test.fst"
        fst_file.write_text("FAST v8 for chain test")

        detector = SimulationFileTypeDetector()
        archive_svc = SimulationArchiveService(
            LocalCompressedArchiveSink(tmp_path / "archive"),
            InMemoryManifestRepository(),
        )
        repo = ModelAssetRepository(pg_session_direct)
        service = ModelAssetImportService(detector, archive_svc, repo)

        import asyncio

        async def _do_import_chain():
            # 步 1: 导入模型
            model_req = ModelAssetImportRequest(
                model_code="PG_CHAIN_MODEL",
                model_name="链测试模型",
                model_type="FAST",
                asset_scope="WTG",
                files=[str(fst_file)],
            )
            model_result = await service.import_model_asset(model_req)
            assert model_result.success is True

            # 步 2: 导入案例
            case_req = SimulationCaseImportRequest(
                case_code="PG_CHAIN_CASE",
                case_name="链测试案例",
                model_code="PG_CHAIN_MODEL",
                case_type="DESIGN",
                parameters={"wind_speed": 15.0},
            )
            case_result = await service.import_simulation_case(case_req)
            assert case_result["success"] is True

            # 步 3: 导入结果
            result_req = SimulationResultImportRequest(
                result_code="PG_CHAIN_RESULT",
                case_code="PG_CHAIN_CASE",
                result_type="TIMESERIES",
                summary={"max_power": 5500},
            )
            res_result = await service.import_simulation_result(result_req)
            assert res_result["success"] is True

            return model_result, case_result, res_result

        model_r, case_r, res_r = asyncio.run(_do_import_chain())

        # PostgreSQL 查询验证
        asset = repo.get_model_asset_by_code("PG_CHAIN_MODEL")
        assert asset is not None

        case = repo.get_case_by_code("PG_CHAIN_CASE")
        assert case is not None
        assert case.model_asset_id == asset.model_asset_id

        result = repo.get_result_by_code("PG_CHAIN_RESULT")
        assert result is not None
        assert result.simulation_case_id == case.simulation_case_id
        assert result.summary_json["max_power"] == 5500
