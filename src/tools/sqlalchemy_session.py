"""跨模块 SQLAlchemy engine 与 session 工具。

本模块不归属任何具体业务子包，是横切基础设施。连接配置通过环境变量
``WHALE_DB_URL`` 注入完整 SQLAlchemy URL；**未设置时模块级立即 ``KeyError``，
不再提供默认 SQLite fallback** —— 让运维、CI、测试显式声明连接目标，
避免把"忘记配置"伪装成"本地开发能用"。
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from os import environ

from sqlalchemy import create_engine, make_url
from sqlalchemy.orm import Session, sessionmaker

# 唯一受支持的环境变量名；Alembic、测试 fixture、部署 compose 都按此名称注入。
DB_URL_ENV = "WHALE_DB_URL"

# 强制读取环境变量；未设即 KeyError，与原 fallback 行为有意不同。
_db_url = make_url(environ[DB_URL_ENV])

engine = create_engine(
    _db_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Yield one database session for local context-managed usage.

    Yields:
        ``sqlalchemy.orm.Session``；调用方只写业务逻辑，不手动提交
        ``close()`` 由本 contextmanager 的 ``finally`` 兜底。
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()