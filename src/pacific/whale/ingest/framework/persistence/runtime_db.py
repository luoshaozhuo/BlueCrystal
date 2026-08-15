"""框架基础设施。

提供持久化、数据库初始化等底层能力。
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from pacific.whale.ingest.framework.persistence.session import create_db_url
from pacific.whale.shared.persistence import Base


def create_runtime_engine(database_url: str | URL | None = None) -> Engine:
    """创建运行时 SQLAlchemy 引擎，带连接健康检查。"""

    resolved_url = database_url or create_db_url()
    return create_engine(resolved_url, future=True, pool_pre_ping=True)


def create_runtime_session_factory(engine: Engine) -> sessionmaker[Session]:
    """从引擎创建运行时 session 工厂。"""

    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def initialize_runtime_database(engine: Engine) -> None:
    """创建所有运行时可见的表和视图。"""

    # Import ORM modules before create_all so metadata is fully populated.
    import pacific.whale.shared.persistence.orm  # noqa: F401
    import pacific.whale.ingest.framework.persistence.orm  # noqa: F401

    Base.metadata.create_all(bind=engine)


def migrate_runtime_database(engine: Engine) -> None:
    """通过 Alembic 运行当前运行时迁移策略。"""

    config = Config(str(resolve_alembic_ini_path()))
    config.set_main_option(
        "sqlalchemy.url",
        engine.url.render_as_string(hide_password=False),
    )
    command.upgrade(config, "head")


def probe_runtime_readiness(engine: Engine, timeout_seconds: int = 5) -> bool:
    """探测运行时数据库是否可接受简单查询。返回 True 表示数据库连接正常。"""

    url = make_url(engine.url)
    connect_args: dict[str, object] = {}
    engine_kwargs: dict[str, object] = {}
    if url.get_backend_name() in ("postgresql",):
        connect_args["connect_timeout"] = timeout_seconds
        engine_kwargs["pool_size"] = 1
        engine_kwargs["max_overflow"] = 0
    probe_engine = create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=False,
        **engine_kwargs,
    )
    try:
        with probe_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    finally:
        probe_engine.dispose()
    return True


def resolve_alembic_ini_path() -> Path:
    """探测运行时数据库是否可接受简单查询。返回布尔值表示数据库连接和基础功能是否正常。

Uses a short-lived engine with connect timeout so this never hangs
when PostgreSQL is unreachable (e.g. during fault injection tests)."""

    return Path(__file__).resolve().parents[5] / "alembic.ini"
