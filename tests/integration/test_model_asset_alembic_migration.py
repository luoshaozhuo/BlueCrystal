"""model_asset Alembic migration 集成测试。

验证 model_asset、simulation_case、simulation_result、simulation_artifact
四张表的 migration 升级和降级，使用 SQLite 嵌入数据库。

被验证对象：
- alembic/versions/20260527_000004_add_model_asset_tables.py

测试阶段：模块集成期验证 (integration，使用 SQLite 嵌入数据库)。
不能证明：PostgreSQL 下的迁移行为。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


@pytest.fixture(scope="module")
def alembic_root() -> Path:
    """Alembic 项目根目录。"""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="function")
def sqlite_url(tmp_path: Path) -> str:
    """返回临时 SQLite 数据库 URL。"""
    db_path = tmp_path / "test_model_asset_alembic.db"
    return f"sqlite:///{db_path}"


@pytest.fixture(scope="function")
def alembic_cfg(alembic_root: Path, sqlite_url: str) -> Config:
    """创建 Alembic Config。"""
    # 使用项目中的 alembic.ini
    ini_path = alembic_root / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(alembic_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", sqlite_url)
    return cfg


class TestModelAssetAlembicMigration:
    """model_asset 表 Alembic migration 集成测试。"""

    def test_upgrade_all_creates_tables(self, alembic_cfg: Config, sqlite_url: str) -> None:
        """验证 upgrade 到最新版本创建所有四张表。"""
        # 从空数据库开始 upgrade 到 head
        command.upgrade(alembic_cfg, "head")

        engine = create_engine(sqlite_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # 四张表都应存在
        assert "model_asset" in tables
        assert "simulation_case" in tables
        assert "simulation_result" in tables
        assert "simulation_artifact" in tables

    def test_model_asset_columns(self, alembic_cfg: Config, sqlite_url: str) -> None:
        """验证 model_asset 表包含所有期望列。"""
        command.upgrade(alembic_cfg, "head")
        engine = create_engine(sqlite_url)
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("model_asset")}
        expected = {
            "model_asset_id", "model_code", "model_name", "model_type",
            "asset_scope", "owner_asset_instance_id", "parent_model_asset_id",
            "source_file_uri", "raw_archive_batch_id", "version",
            "checksum_sha256", "parser_status", "metadata_json",
            "created_at", "updated_at",
        }
        assert expected.issubset(columns), f"缺少列: {expected - columns}"

    def test_simulation_case_columns(self, alembic_cfg: Config, sqlite_url: str) -> None:
        """验证 simulation_case 表包含所有期望列。"""
        command.upgrade(alembic_cfg, "head")
        engine = create_engine(sqlite_url)
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("simulation_case")}
        expected = {
            "simulation_case_id", "case_code", "case_name", "model_asset_id",
            "case_type", "input_file_uri", "raw_archive_batch_id",
            "parameter_json", "scenario_json", "status", "created_by",
            "created_at", "updated_at",
        }
        assert expected.issubset(columns), f"缺少列: {expected - columns}"

    def test_simulation_result_columns(self, alembic_cfg: Config, sqlite_url: str) -> None:
        """验证 simulation_result 表包含所有期望列。"""
        command.upgrade(alembic_cfg, "head")
        engine = create_engine(sqlite_url)
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("simulation_result")}
        expected = {
            "simulation_result_id", "simulation_case_id", "result_code",
            "result_type", "result_file_uri", "raw_archive_batch_id",
            "time_series_backend", "time_series_ref", "summary_json",
            "metric_json", "status", "created_at", "updated_at",
        }
        assert expected.issubset(columns), f"缺少列: {expected - columns}"

    def test_simulation_artifact_columns(self, alembic_cfg: Config, sqlite_url: str) -> None:
        """验证 simulation_artifact 表包含所有期望列。"""
        command.upgrade(alembic_cfg, "head")
        engine = create_engine(sqlite_url)
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("simulation_artifact")}
        expected = {
            "simulation_artifact_id", "owner_type", "owner_id",
            "artifact_type", "file_uri", "raw_archive_batch_id",
            "checksum_sha256", "metadata_json", "created_at",
        }
        assert expected.issubset(columns), f"缺少列: {expected - columns}"

    def test_unique_constraints(self, alembic_cfg: Config, sqlite_url: str) -> None:
        """验证 unique 约束存在。"""
        command.upgrade(alembic_cfg, "head")

        from sqlalchemy import create_engine as ce
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.exc import IntegrityError
        from whale.shared.persistence.orm.model_asset import (
            ModelAsset,
        )

        engine = ce(sqlite_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        try:
            # 验证 model_code unique
            a1 = ModelAsset(
                model_code="UC_TEST", model_name="N1",
                model_type="FAST", asset_scope="WTG",
            )
            session.add(a1)
            session.flush()

            a2 = ModelAsset(
                model_code="UC_TEST", model_name="N2",
                model_type="FAST", asset_scope="WTG",
            )
            session.add(a2)
            with pytest.raises(IntegrityError):
                session.flush()
            session.rollback()
        finally:
            session.rollback()
            session.close()

    def test_downgrade_removes_tables(self, alembic_cfg: Config, sqlite_url: str) -> None:
        """验证 downgrade 移除全部四张表。"""
        # 先 upgrade
        command.upgrade(alembic_cfg, "head")
        # 再 downgrade
        command.downgrade(alembic_cfg, "20260527_000003")

        engine = create_engine(sqlite_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # 四张表都不应存在
        for expected_table in (
            "model_asset", "simulation_case",
            "simulation_result", "simulation_artifact",
        ):
            assert expected_table not in tables, f"{expected_table} 表在 downgrade 后仍存在"

    def test_revision_chain(self, alembic_cfg: Config) -> None:
        """验证 revision chain 正确连接。"""
        from alembic.script import ScriptDirectory

        scripts = ScriptDirectory.from_config(alembic_cfg)
        rev_004 = scripts.get_revision("20260527_000004")
        assert rev_004 is not None
        assert rev_004.revision == "20260527_000004"

        # 验证 down_revision 指向正确的前一个版本
        assert rev_004.down_revision is not None
        assert "20260527_000003" in str(rev_004.down_revision)
