"""Helpers for ingest runtime DB initialization and migration smoke."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from whale.ingest.framework.persistence.session import create_db_url
from whale.shared.persistence import Base


def create_runtime_engine(database_url: str | URL | None = None) -> Engine:
    """Create one runtime SQLAlchemy engine with connection health check."""

    resolved_url = database_url or create_db_url()
    return create_engine(resolved_url, future=True, pool_pre_ping=True)


def create_runtime_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create one runtime session factory from an engine."""

    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def initialize_runtime_database(engine: Engine) -> None:
    """Create all runtime-visible tables and views."""

    # Import ORM modules before create_all so metadata is fully populated.
    import whale.shared.persistence.orm  # noqa: F401
    import whale.ingest.framework.persistence.orm  # noqa: F401

    Base.metadata.create_all(bind=engine)


def migrate_runtime_database(engine: Engine) -> None:
    """Run the current runtime migration strategy via Alembic."""

    config = Config(str(resolve_alembic_ini_path()))
    config.set_main_option(
        "sqlalchemy.url",
        engine.url.render_as_string(hide_password=False),
    )
    command.upgrade(config, "head")


def probe_runtime_readiness(engine: Engine, timeout_seconds: int = 5) -> bool:
    """Return whether the runtime database accepts a trivial query.

    Uses a short-lived engine with connect timeout so this never hangs
    when PostgreSQL is unreachable (e.g. during fault injection tests).
    """

    url = make_url(engine.url)
    probe_engine = create_engine(
        url,
        connect_args={"connect_timeout": timeout_seconds},
        pool_pre_ping=False,
        pool_size=1,
        max_overflow=0,
    )
    try:
        with probe_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    finally:
        probe_engine.dispose()
    return True


def resolve_alembic_ini_path() -> Path:
    """Return the repository-local alembic.ini path."""

    return Path(__file__).resolve().parents[5] / "alembic.ini"
