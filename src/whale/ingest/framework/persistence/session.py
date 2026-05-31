"""框架基础设施。

提供持久化、数据库初始化等底层能力。
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from whale.ingest.config import (
    CONFIG,
    PostgresDatabaseConfig,
    SqliteDatabaseConfig,
    _build_config,
)


def create_db_url() -> URL:
    """根据配置的 ingest 数据库后端构造数据库 URL。"""
    config = _build_config()
    database = config.database.database
    if isinstance(config.database, SqliteDatabaseConfig):
        database_path = Path(database)
        if not database_path.is_absolute():
            database_path = (Path(__file__).resolve().parents[2] / database_path).resolve()
        database_path.parent.mkdir(parents=True, exist_ok=True)
        return URL.create(
            drivername="sqlite",
            database=str(database_path),
        )

    assert isinstance(config.database, PostgresDatabaseConfig)
    if config.database.database_url:
        return make_url(config.database.database_url)
    return URL.create(
        drivername="postgresql+psycopg",
        username=config.database.username,
        password=config.database.password,
        host=config.database.host,
        port=config.database.port,
        database=str(database),
    )


engine = create_engine(
    create_db_url(),
    pool_size=CONFIG.database_engine.pool_size,
    max_overflow=CONFIG.database_engine.max_overflow,
    pool_timeout=CONFIG.database_engine.pool_timeout,
    pool_recycle=CONFIG.database_engine.pool_recycle,
    pool_pre_ping=CONFIG.database_engine.pool_pre_ping,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_session() -> Generator[Session, None, None]:
    """为框架管理的请求作用域生成一个数据库 session。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """为本地上下文管理用途生成一个数据库 session。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def dispose_engine() -> None:
    """释放 SQLAlchemy 引擎并关闭连接池。"""
    engine.dispose()
