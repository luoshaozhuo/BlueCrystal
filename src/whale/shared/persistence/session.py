"""shared persistence 层的 SQLAlchemy engine 与 session 工具。

支持 SQLite / PostgreSQL / MySQL 三种后端，优先读取完整 URL，再回退到分散
环境变量。当前支持的环境变量如下：

    WHALE_SHARED_DB_URL        — 完整 SQLAlchemy URL，适合测试临时库
    WHALE_SHARED_DB_BACKEND    — sqlite (默认) / postgresql / mysql
    WHALE_SHARED_DB_PATH       — SQLite 数据库文件路径
    WHALE_SHARED_DB_HOST       — PostgreSQL / MySQL 主机
    WHALE_SHARED_DB_PORT       — PostgreSQL / MySQL 端口
    WHALE_SHARED_DB_NAME       — 数据库名称
    WHALE_SHARED_DB_USERNAME   — 用户名
    WHALE_SHARED_DB_PASSWORD   — 密码

本模块只负责解析连接信息和创建 engine，不负责 destructive reset 安全护栏。
"""

from __future__ import annotations

import os
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SQLITE_PATH = PROJECT_ROOT / "data" / "shared" / "whale.db"
DatabaseBackend = Literal["sqlite", "postgresql", "mysql"]
SUPPORTED_BACKENDS: frozenset[str] = frozenset({"sqlite", "postgresql", "mysql"})


# ── 后端解析 ──────────────────────────────────────────────────────────


def _resolve_backend() -> DatabaseBackend:
    raw = (os.environ.get("WHALE_SHARED_DB_BACKEND") or "sqlite").strip().lower()
    if raw not in SUPPORTED_BACKENDS:
        raise RuntimeError(
            f"不支持的 WHALE_SHARED_DB_BACKEND: {raw!r}，"
            f"可选值: {sorted(SUPPORTED_BACKENDS)}"
        )
    return raw  # type: ignore[return-value]


# ── URL 构建 ──────────────────────────────────────────────────────────


def _build_sqlite_url() -> URL:
    db_path = Path(os.environ.get("WHALE_SHARED_DB_PATH", DEFAULT_SQLITE_PATH))
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return URL.create(drivername="sqlite", database=str(db_path))


def _build_explicit_db_url() -> URL | None:
    """读取显式 `WHALE_SHARED_DB_URL`，便于测试临时库注入。"""

    raw_url = os.environ.get("WHALE_SHARED_DB_URL", "").strip()
    if not raw_url:
        return None
    return make_url(raw_url)


def _build_postgresql_url() -> URL:
    port = int(os.environ.get("WHALE_SHARED_DB_PORT", "5432"))
    return URL.create(
        drivername="postgresql+psycopg",
        host=os.environ["WHALE_SHARED_DB_HOST"],
        port=port,
        database=os.environ["WHALE_SHARED_DB_NAME"],
        username=os.environ["WHALE_SHARED_DB_USERNAME"],
        password=os.environ["WHALE_SHARED_DB_PASSWORD"],
    )


def _build_mysql_url() -> URL:
    port = int(os.environ.get("WHALE_SHARED_DB_PORT", "3306"))
    return URL.create(
        drivername="mysql+pymysql",
        host=os.environ["WHALE_SHARED_DB_HOST"],
        port=port,
        database=os.environ["WHALE_SHARED_DB_NAME"],
        username=os.environ["WHALE_SHARED_DB_USERNAME"],
        password=os.environ["WHALE_SHARED_DB_PASSWORD"],
    )


def _check_env(*names: str) -> bool:
    """检查环境变量是否齐全，返回 True 表示全部已设置."""
    return all(os.environ.get(n, "").strip() for n in names)


def _fallback_to_sqlite(backend: str, missing: list[str]) -> URL:
    warnings.warn(
        f"WHALE_SHARED_DB_BACKEND={backend} 但缺少环境变量 {', '.join(missing)}，"
        f"已回退到 sqlite ({DEFAULT_SQLITE_PATH})",
        stacklevel=2,
    )
    return _build_sqlite_url()


def _build_db_url() -> URL:
    explicit_url = _build_explicit_db_url()
    if explicit_url is not None:
        return explicit_url

    backend = _resolve_backend()
    if backend == "sqlite":
        return _build_sqlite_url()

    required = ["WHALE_SHARED_DB_HOST", "WHALE_SHARED_DB_NAME",
                "WHALE_SHARED_DB_USERNAME", "WHALE_SHARED_DB_PASSWORD"]
    if not _check_env(*required):
        missing = [n for n in required if not os.environ.get(n, "").strip()]
        return _fallback_to_sqlite(backend, missing)

    if backend == "postgresql":
        return _build_postgresql_url()
    return _build_mysql_url()


# ── Engine & Session ──────────────────────────────────────────────────


_db_url = _build_db_url()

engine = create_engine(
    _db_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    """Yield one database session for framework-managed scopes."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Yield one database session for local context-managed usage."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def dispose_engine() -> None:
    """Dispose SQLAlchemy engine and close pooled connections."""
    engine.dispose()
