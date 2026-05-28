"""SQLAlchemy engine and session helpers for the ingest framework."""

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
    """Build the database URL from the configured ingest database backend."""
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
    """Yield one database session for framework-managed request scopes."""
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
