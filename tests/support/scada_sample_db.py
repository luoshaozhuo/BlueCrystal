"""shared persistence SCADA sample DB 测试辅助函数。

证据等级：
- SQLite 路径只提供 L4 lightweight/integration 级隔离样例库，方便 source_lab
  本地测试真实消费统一输入契约。
- PostgreSQL 路径提供本轮最终验收所需的 L4 integration 临时测试库；它会显式
  创建带安全标识的临时数据库，并在测试结束后清理，避免误连默认库。

本文件不证明真实协议 runtime、simulator 或现场设备连通性。
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_SAFE_DB_MARKERS = ("test", "tmp", "ci", "local_dev_test")
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"


@dataclass(frozen=True, slots=True)
class PostgresSampleDb:
    """一份安全创建的 PostgreSQL 样例数据库句柄。"""

    database_name: str
    database_url: str


def create_isolated_scada_sample_db(tmp_path: Path) -> Path:
    """在临时目录中生成一份 shared persistence sample SQLite 数据库。

    Args:
        tmp_path: pytest 提供的临时目录。

    Returns:
        已完成初始化与样例写入的 SQLite 数据库路径。

    Raises:
        RuntimeError: 当样例初始化子进程失败时抛出。
    """

    db_path = tmp_path / "shared-persistence.sqlite"
    _run_sample_data(
        env={
            **os.environ,
            "PYTHONPATH": str(_SRC_ROOT),
            "WHALE_SHARED_DB_BACKEND": "sqlite",
            "WHALE_SHARED_DB_PATH": str(db_path),
            "WHALE_SHARED_DB_URL": "",
        }
    )
    return db_path


@contextmanager
def postgres_scada_sample_db() -> Iterator[PostgresSampleDb]:
    """创建一份安全的 PostgreSQL 临时样例库并在退出时销毁。

    Returns:
        包含数据库名与连接 URL 的临时库句柄。

    Raises:
        RuntimeError: 当 PostgreSQL 环境缺失、库名不安全、建库失败或样例初始化失败时抛出。
    """

    settings = _resolve_postgres_settings()
    database_name = f"whale_shared_test_{uuid.uuid4().hex[:10]}"
    if not _is_safe_database_name(database_name):
        raise RuntimeError(f"generated unsafe PostgreSQL test database name: {database_name}")

    admin_engine = create_engine(settings.admin_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    try:
        try:
            with admin_engine.connect() as conn:
                conn.execute(text(f'CREATE DATABASE "{database_name}"'))
        except Exception as exc:
            raise RuntimeError(
                "shared persistence PostgreSQL test environment unavailable during CREATE DATABASE: "
                f"{exc}"
            ) from exc
        database_url = settings.database_url(database_name)
        _run_sample_data(
            env={
                **os.environ,
                "PYTHONPATH": str(_SRC_ROOT),
                "WHALE_SHARED_DB_URL": database_url,
                "WHALE_SHARED_DB_BACKEND": "postgresql",
                "WHALE_SHARED_DB_HOST": settings.host,
                "WHALE_SHARED_DB_PORT": str(settings.port),
                "WHALE_SHARED_DB_NAME": database_name,
                "WHALE_SHARED_DB_USERNAME": settings.username,
                "WHALE_SHARED_DB_PASSWORD": settings.password,
            }
        )
        yield PostgresSampleDb(database_name=database_name, database_url=database_url)
    finally:
        _drop_postgres_database(admin_engine=admin_engine, database_name=database_name)
        admin_engine.dispose()


@dataclass(frozen=True, slots=True)
class _PostgresSettings:
    """shared persistence PostgreSQL 测试环境配置。"""

    host: str
    port: int
    username: str
    password: str
    admin_db: str

    @property
    def admin_url(self) -> str:
        return self.database_url(self.admin_db)

    def database_url(self, database_name: str) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.username}:{self.password}@{self.host}:{self.port}/{database_name}"
        )


def _resolve_postgres_settings() -> _PostgresSettings:
    """读取 shared persistence PostgreSQL 凭据。"""

    required = {
        "WHALE_SHARED_DB_HOST": os.environ.get("WHALE_SHARED_DB_HOST", "").strip(),
        "WHALE_SHARED_DB_USERNAME": os.environ.get("WHALE_SHARED_DB_USERNAME", "").strip(),
        "WHALE_SHARED_DB_PASSWORD": os.environ.get("WHALE_SHARED_DB_PASSWORD", "").strip(),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "shared persistence PostgreSQL integration requires env vars: "
            + ", ".join(missing)
        )

    port_raw = os.environ.get("WHALE_SHARED_DB_PORT", "5432").strip() or "5432"
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise RuntimeError(f"invalid WHALE_SHARED_DB_PORT: {port_raw!r}") from exc

    admin_db = os.environ.get("WHALE_SHARED_TEST_ADMIN_DB", "postgres").strip() or "postgres"
    return _PostgresSettings(
        host=required["WHALE_SHARED_DB_HOST"],
        port=port,
        username=required["WHALE_SHARED_DB_USERNAME"],
        password=required["WHALE_SHARED_DB_PASSWORD"],
        admin_db=admin_db,
    )


def _is_safe_database_name(database_name: str) -> bool:
    """判断数据库名是否包含允许的测试标识。"""

    lowered = database_name.lower()
    return any(marker in lowered for marker in _SAFE_DB_MARKERS)


def _run_sample_data(*, env: dict[str, str]) -> None:
    """执行 `sample_data` 子进程并在失败时抛出稳定错误。"""

    result = subprocess.run(
        [sys.executable, "-m", "whale.shared.persistence.template.sample_data"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "failed to initialize shared persistence sample DB: "
            f"returncode={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r}"
        )


def _drop_postgres_database(*, admin_engine: Engine, database_name: str) -> None:
    """终止连接并删除临时 PostgreSQL 数据库。"""

    if not _is_safe_database_name(database_name):
        raise RuntimeError(f"refusing to drop unsafe PostgreSQL database: {database_name}")

    with admin_engine.connect() as conn:
        conn.execute(
            text(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = :database_name
                  AND pid <> pg_backend_pid()
                """
            ),
            {"database_name": database_name},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))


__all__ = ["PostgresSampleDb", "create_isolated_scada_sample_db", "postgres_scada_sample_db"]
