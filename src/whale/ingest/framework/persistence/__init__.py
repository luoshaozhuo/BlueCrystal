"""Public exports for ingest persistence helpers.

Keep this module light so importing runtime helpers does not eagerly bind one
global engine from stale environment variables.
"""

from __future__ import annotations

from whale.ingest.framework.persistence.runtime_db import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
    migrate_runtime_database,
    probe_runtime_readiness,
)

__all__ = [
    "create_runtime_engine",
    "create_runtime_session_factory",
    "initialize_runtime_database",
    "migrate_runtime_database",
    "probe_runtime_readiness",
    "Base",
    "SessionLocal",
    "engine",
    "get_session",
    "session_scope",
]


def __getattr__(name: str):
    """Lazily resolve legacy session exports when callers still need them."""

    if name == "Base":
        from whale.ingest.framework.persistence.base import Base

        return Base

    if name in {"SessionLocal", "engine", "get_session", "session_scope"}:
        from whale.ingest.framework.persistence import session as session_module

        return getattr(session_module, name)

    raise AttributeError(name)
