"""Load test fixtures: PostgreSQL + Redis + Kafka, large NodeSets."""

from __future__ import annotations

import os
from contextlib import contextmanager

import pytest

from tests.e2e.helpers import (
    PG_DB,
    PG_HOST,
    PG_PASSWORD,
    PG_PORT,
    PG_USER,
    REDIS_HOST,
    REDIS_PORT,
    KAFKA_BOOTSTRAP_SERVER,
    wait_for_kafka,
    wait_for_redis,
)


def pytest_configure(config: pytest.Config) -> None:
    os.environ["WHALE_INGEST_DATABASE_BACKEND"] = "postgresql"
    os.environ["WHALE_INGEST_STATE_CACHE_BACKEND"] = "redis"
    os.environ["WHALE_INGEST_MESSAGE_BACKEND"] = "kafka"
    os.environ["WHALE_INGEST_DB_HOST"] = PG_HOST
    os.environ["WHALE_INGEST_DB_PORT"] = str(PG_PORT)
    os.environ["WHALE_INGEST_DB_NAME"] = PG_DB
    os.environ["WHALE_INGEST_DB_USERNAME"] = PG_USER
    os.environ["WHALE_INGEST_DB_PASSWORD"] = PG_PASSWORD
    os.environ["WHALE_INGEST_REDIS_HOST"] = REDIS_HOST
    os.environ["WHALE_INGEST_REDIS_PORT"] = str(REDIS_PORT)
    os.environ["WHALE_INGEST_REDIS_DB"] = "0"
    os.environ["WHALE_INGEST_REDIS_STATE_HASH_KEY"] = "whale:ingest:state"
    os.environ["WHALE_INGEST_STATION_ID"] = "station-load-001"
    os.environ["WHALE_INGEST_KAFKA_BOOTSTRAP_SERVERS"] = KAFKA_BOOTSTRAP_SERVER
    os.environ["WHALE_INGEST_KAFKA_TOPIC"] = "whale.ingest.state_snapshot.v1"
    os.environ["WHALE_INGEST_KAFKA_ACK_TIMEOUT_SECONDS"] = "5.0"


@pytest.fixture(scope="session")
def pg_db_url() -> str:
    return f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"


@pytest.fixture(scope="session")
def pg_engine(pg_db_url: str):
    from sqlalchemy import create_engine

    eng = create_engine(pg_db_url, pool_size=20, max_overflow=40, pool_pre_ping=True)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def _pg_tables_created(pg_engine):
    from importlib import import_module

    import_module("whale.ingest.framework.persistence.orm")
    from whale.ingest.framework.persistence.base import Base

    Base.metadata.create_all(bind=pg_engine)


@pytest.fixture()
def pg_session(pg_engine, _pg_tables_created):
    """Function-scoped session, cleans up before each test."""
    from sqlalchemy.orm import Session

    session = Session(bind=pg_engine, autoflush=False, expire_on_commit=False)
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def session_factory(pg_engine, _pg_tables_created):
    @contextmanager
    def _factory():
        from sqlalchemy.orm import Session

        session = Session(bind=pg_engine, autoflush=False, expire_on_commit=False)
        try:
            yield session
        finally:
            session.rollback()
            session.close()

    return _factory


@pytest.fixture()
def redis_client():
    from redis import Redis

    client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    wait_for_redis(client)
    yield client
    client.close()


@pytest.fixture(scope="session")
def _kafka_ready():
    wait_for_kafka()
