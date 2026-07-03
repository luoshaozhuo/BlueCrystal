"""shared persistence SCADA sample DB 测试辅助函数。

测试阶段:
- SQLite 路径只提供跨模块联调期验证级隔离样例库,方便 source_lab
  本地测试真实消费统一输入契约。
- PostgreSQL 路径提供本轮最终验收所需的跨模块联调期验证临时测试库;它会显式
  创建带安全标识的临时数据库,并在测试结束后清理,避免误连默认库。

本文件不证明真实协议 runtime、simulator 或现场设备连通性。

环境变量约束:
- 仅通过 ``WHALE_DB_URL`` 与子进程 ``sample_data`` 通信;PostgreSQL 测试也
  仅从 ``WHALE_DB_URL`` 读取基础连接(必须是 postgresql+psycopg:// 协议),
  解析出 host / port / username / password 后,再用随机数据库名重建 URL。
- 不再使用任何散环境变量(后端 / 路径 / 主机 / 端口 / 库名 / 用户名 / 密码)。
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
from sqlalchemy.engine import Engine, make_url

_SAFE_DB_MARKERS = ("test", "tmp", "ci", "local_dev_test")
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
_DB_URL_ENV = "WHALE_DB_URL"


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
    db_url = f"sqlite:///{db_path}"
    _run_sample_data(
        env={
            **os.environ,
            "PYTHONPATH": str(_SRC_ROOT),
            _DB_URL_ENV: db_url,
        }
    )
    return db_path


@contextmanager
def postgres_scada_sample_db() -> Iterator[PostgresSampleDb]:
    """创建一份安全的 PostgreSQL 临时样例库并在退出时销毁。

    从 ``WHALE_DB_URL``(必须 postgresql+psycopg://)解析 host / port /
    username / password,在 PostgreSQL 上创建一个带安全标识的临时
    数据库,把 ``WHALE_DB_URL`` 改写为指向该临时库,运行 ``sample_data``
    初始化,退出时强制断开连接并 ``DROP DATABASE``。

    Returns:
        包含数据库名与连接 URL 的临时库句柄。

    Raises:
        RuntimeError: 当 ``WHALE_DB_URL`` 缺失 / 协议非 postgresql /
        库名不安全 / 建库或样例初始化失败时抛出。
    """

    base_settings = _resolve_postgres_settings()
    database_name = f"whale_shared_test_{uuid.uuid4().hex[:10]}"
    if not _is_safe_database_name(database_name):
        raise RuntimeError(f"generated unsafe PostgreSQL test database name: {database_name}")

    admin_engine = create_engine(base_settings.admin_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    try:
        try:
            with admin_engine.connect() as conn:
                conn.execute(text(f'CREATE DATABASE "{database_name}"'))
        except Exception as exc:
            raise RuntimeError(
                "shared persistence PostgreSQL test environment unavailable during CREATE DATABASE: "
                f"{exc}"
            ) from exc
        database_url = base_settings.database_url(database_name)
        _run_sample_data(
            env={
                **os.environ,
                "PYTHONPATH": str(_SRC_ROOT),
                _DB_URL_ENV: database_url,
            }
        )
        yield PostgresSampleDb(database_name=database_name, database_url=database_url)
    finally:
        _drop_postgres_database(admin_engine=admin_engine, database_name=database_name)
        admin_engine.dispose()


@dataclass(frozen=True, slots=True)
class _PostgresSettings:
    """shared persistence PostgreSQL 测试环境配置,全部从 ``WHALE_DB_URL`` 解析。"""

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
    """从 ``WHALE_DB_URL`` 解析 PostgreSQL 测试连接凭据。

    Returns:
        已校验的 ``_PostgresSettings``。

    Raises:
        RuntimeError: ``WHALE_DB_URL`` 未设置 / drivername 非 postgresql /
        缺 host / username 等字段时抛出。
    """

    raw = os.environ.get(_DB_URL_ENV, "").strip()
    if not raw:
        raise RuntimeError(
            "shared persistence PostgreSQL integration requires WHALE_DB_URL to be set"
            " to a postgresql+psycopg:// URL."
        )
    try:
        url = make_url(raw)
    except Exception as exc:  # noqa: BLE001 — 上抛 sqlalchemy 解析异常到稳定错误
        raise RuntimeError(f"invalid WHALE_DB_URL for PostgreSQL test: {raw!r}: {exc}") from exc

    if not url.drivername.startswith("postgresql"):
        raise RuntimeError(
            "shared persistence PostgreSQL integration requires WHALE_DB_URL drivername"
            f" to be postgresql+, got {url.drivername!r}."
        )

    host = url.host
    username = url.username
    password = url.password
    database = url.database
    missing = [
        name
        for name, value in (
            ("host", host),
            ("username", username),
            ("password", password),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "shared persistence PostgreSQL integration requires WHALE_DB_URL to contain "
            + ", ".join(missing)
        )

    try:
        port = url.port or 5432
    except ValueError as exc:
        raise RuntimeError(f"invalid port in WHALE_DB_URL: {exc}") from exc

    return _PostgresSettings(
        host=host,
        port=port,
        username=username,
        password=password,
        admin_db=database or "postgres",
    )


def _is_safe_database_name(database_name: str) -> bool:
    """判断数据库名是否包含允许的测试标识。"""

    lowered = database_name.lower()
    return any(marker in lowered for marker in _SAFE_DB_MARKERS)


def _run_sample_data(*, env: dict[str, str]) -> None:
    """执行 ``sample_data`` 子进程并在失败时抛出稳定错误。"""

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