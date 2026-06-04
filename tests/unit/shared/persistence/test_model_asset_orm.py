"""model_asset ORM 表定义与约束单元测试。

验证 ModelAsset、SimulationCase、SimulationResult、SimulationArtifact
四张表的结构、字段约束、UniqueConstraint 和 FK 关系。

被验证对象：
- whale.shared.persistence.orm.model_asset: 全部四张 ORM 表

测试阶段：开发期验证 (unit，使用 SQLite :memory:，无外部依赖)。
不能证明：PostgreSQL 下的迁移兼容性和性能行为。
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from whale.shared.persistence import Base
from whale.shared.persistence.orm.model_asset import (
    ModelAsset,
    SimulationArtifact,
    SimulationCase,
    SimulationResult,
)


@pytest.fixture(scope="function")
def session() -> Session:
    """创建 SQLite 内存数据库 session，启用外键约束。"""
    from sqlalchemy import event as sa_event

    engine = create_engine("sqlite:///:memory:", echo=False)

    @sa_event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
        """SQLite 默认不启用外键约束，需手动开启。"""
        import sqlite3
        if isinstance(dbapi_connection, sqlite3.Connection):
            dbapi_connection.execute("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(engine)


# ---- 表存在性 ----

def test_model_asset_table_exists(session: Session) -> None:
    """验证 model_asset 表存在。"""
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    assert "model_asset" in tables


def test_simulation_case_table_exists(session: Session) -> None:
    """验证 simulation_case 表存在。"""
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    assert "simulation_case" in tables


def test_simulation_result_table_exists(session: Session) -> None:
    """验证 simulation_result 表存在。"""
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    assert "simulation_result" in tables


def test_simulation_artifact_table_exists(session: Session) -> None:
    """验证 simulation_artifact 表存在。"""
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    assert "simulation_artifact" in tables


# ---- ModelAsset 字段测试 ----

def test_model_asset_required_fields(session: Session) -> None:
    """验证 model_asset 必填字段不为空。"""
    asset = ModelAsset(
        model_code="MC_REQUIRED",
        model_name="必填字段测试",
        model_type="FAST",
        asset_scope="WTG",
    )
    session.add(asset)
    session.flush()
    assert asset.model_asset_id is not None
    assert asset.model_code == "MC_REQUIRED"
    assert asset.metadata_json == {}


def test_model_asset_default_values(session: Session) -> None:
    """验证 model_asset 默认值。"""
    asset = ModelAsset(
        model_code="MC_DEFAULTS",
        model_name="默认值测试",
        model_type="FAST",
        asset_scope="WTG",
    )
    session.add(asset)
    session.flush()
    assert asset.parser_status == "IMPORTED"
    assert asset.version == "1.0"
    assert asset.owner_asset_instance_id is None
    assert asset.parent_model_asset_id is None
    assert asset.created_at is not None
    assert asset.updated_at is not None


def test_model_asset_unique_code_constraint(session: Session) -> None:
    """验证 model_code UniqueConstraint 生效。"""
    a1 = ModelAsset(
        model_code="MC_UNIQUE", model_name="N1", model_type="FAST", asset_scope="WTG",
    )
    session.add(a1)
    session.flush()

    a2 = ModelAsset(
        model_code="MC_UNIQUE", model_name="N2", model_type="FAST", asset_scope="WTG",
    )
    session.add(a2)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_model_asset_nullable_fields(session: Session) -> None:
    """验证可空字段接受 None 值。"""
    asset = ModelAsset(
        model_code="MC_NULLABLE",
        model_name="可空字段",
        model_type="FAST",
        asset_scope="WTG",
        owner_asset_instance_id=None,
        parent_model_asset_id=None,
        source_file_uri=None,
        raw_archive_batch_id=None,
        checksum_sha256=None,
    )
    session.add(asset)
    session.flush()
    assert asset.owner_asset_instance_id is None
    assert asset.source_file_uri is None


def test_model_asset_self_referential_fk(session: Session) -> None:
    """验证 parent_model_asset_id 自引用外键。"""
    parent = ModelAsset(
        model_code="MC_PARENT", model_name="父", model_type="FAST", asset_scope="WTG",
    )
    session.add(parent)
    session.flush()

    child = ModelAsset(
        model_code="MC_CHILD", model_name="子", model_type="FAST", asset_scope="WTG",
        parent_model_asset_id=parent.model_asset_id,
    )
    session.add(child)
    session.flush()
    assert child.parent_model_asset_id == parent.model_asset_id


def test_model_asset_parser_status_values(session: Session) -> None:
    """验证 parser_status 接受合法值：IMPORTED / PARTIAL / UNSUPPORTED / FAILED。"""
    for status in ("IMPORTED", "PARTIAL", "UNSUPPORTED", "FAILED"):
        asset = ModelAsset(
            model_code=f"MC_PS_{status}",
            model_name=f"解析状态 {status}",
            model_type="FAST",
            asset_scope="WTG",
            parser_status=status,
        )
        session.add(asset)
        session.flush()
        assert asset.parser_status == status
    session.rollback()


# ---- SimulationCase 字段测试 ----

def test_simulation_case_required_fields(session: Session) -> None:
    """验证 simulation_case 必填字段。"""
    asset = ModelAsset(
        model_code="MC_SC1", model_name="N", model_type="FAST", asset_scope="WTG",
    )
    session.add(asset)
    session.flush()

    case = SimulationCase(
        case_code="SC_REQUIRED",
        case_name="必填",
        model_asset_id=asset.model_asset_id,
        case_type="DESIGN",
    )
    session.add(case)
    session.flush()
    assert case.simulation_case_id is not None
    assert case.status == "CREATED"
    assert case.parameter_json == {}
    assert case.scenario_json == {}


def test_simulation_case_unique_code(session: Session) -> None:
    """验证 case_code 唯一约束。"""
    asset = ModelAsset(
        model_code="MC_SC2", model_name="N", model_type="FAST", asset_scope="WTG",
    )
    session.add(asset)
    session.flush()

    c1 = SimulationCase(
        case_code="SC_UNIQUE", case_name="X",
        model_asset_id=asset.model_asset_id, case_type="DESIGN",
    )
    session.add(c1)
    session.flush()

    c2 = SimulationCase(
        case_code="SC_UNIQUE", case_name="Y",
        model_asset_id=asset.model_asset_id, case_type="DESIGN",
    )
    session.add(c2)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_simulation_case_fk_to_model_asset(session: Session) -> None:
    """验证 model_asset_id 外键约束。"""
    case = SimulationCase(
        case_code="SC_FK", case_name="X", model_asset_id=99999, case_type="DESIGN",
    )
    session.add(case)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


# ---- SimulationResult 字段测试 ----

def test_simulation_result_required_fields(session: Session) -> None:
    """验证 simulation_result 必填字段。"""
    asset = ModelAsset(
        model_code="MC_SR1", model_name="N", model_type="FAST", asset_scope="WTG",
    )
    session.add(asset)
    session.flush()
    case = SimulationCase(
        case_code="SC_SR1", case_name="X",
        model_asset_id=asset.model_asset_id, case_type="DESIGN",
    )
    session.add(case)
    session.flush()

    result = SimulationResult(
        simulation_case_id=case.simulation_case_id,
        result_code="SR_REQUIRED",
        result_type="TIMESERIES",
    )
    session.add(result)
    session.flush()
    assert result.simulation_result_id is not None
    assert result.status == "IMPORTED"
    assert result.summary_json == {}
    assert result.metric_json == {}


def test_simulation_result_unique_code(session: Session) -> None:
    """验证 result_code 唯一约束。"""
    asset = ModelAsset(
        model_code="MC_SR2", model_name="N", model_type="FAST", asset_scope="WTG",
    )
    asset2 = ModelAsset(
        model_code="MC_SR2b", model_name="N2", model_type="FAST", asset_scope="WTG",
    )
    session.add_all([asset, asset2])
    session.flush()
    case = SimulationCase(
        case_code="SC_SR2", case_name="X",
        model_asset_id=asset.model_asset_id, case_type="DESIGN",
    )
    session.add(case)
    session.flush()

    r1 = SimulationResult(
        simulation_case_id=case.simulation_case_id,
        result_code="SR_UNIQUE", result_type="TIMESERIES",
    )
    session.add(r1)
    session.flush()

    r2 = SimulationResult(
        simulation_case_id=case.simulation_case_id,
        result_code="SR_UNIQUE", result_type="SUMMARY",
    )
    session.add(r2)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_simulation_result_fk_to_case(session: Session) -> None:
    """验证 simulation_case_id 外键约束。"""
    result = SimulationResult(
        simulation_case_id=99999,
        result_code="SR_FK", result_type="SUMMARY",
    )
    session.add(result)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


# ---- SimulationArtifact 字段测试 ----

def test_simulation_artifact_required_fields(session: Session) -> None:
    """验证 simulation_artifact 必填字段。"""
    art = SimulationArtifact(
        owner_type="MODEL_ASSET",
        owner_id=1,
        artifact_type="SOURCE_FILE",
        file_uri="/data/file.fst",
    )
    session.add(art)
    session.flush()
    assert art.simulation_artifact_id is not None
    assert art.metadata_json == {}
    assert art.created_at is not None


def test_simulation_artifact_all_types(session: Session) -> None:
    """验证不同 owner_type 和 artifact_type 的制品创建。"""
    for owner_type in ("MODEL_ASSET", "SIMULATION_CASE", "SIMULATION_RESULT"):
        for artifact_type in ("SOURCE_FILE", "INPUT_FILE", "RESULT_FILE", "REPORT", "LOG", "CONFIG", "OTHER"):
            art = SimulationArtifact(
                owner_type=owner_type,
                owner_id=1,
                artifact_type=artifact_type,
                file_uri="/data/test",
            )
            session.add(art)
            session.flush()
            assert art.owner_type == owner_type
            assert art.artifact_type == artifact_type
    session.rollback()
