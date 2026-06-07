"""Shared pytest fixtures for ingest integration tests.

Round 12: dead OPC UA simulator fixtures removed (tools/opcua_sim and
tools/source_simulation deleted in Round 11).  Kept: Redis infrastructure
and env-sanitisation hooks.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

_VALID_STATE_CACHE_BACKENDS = frozenset({"redis"})
_VALID_MESSAGE_BACKENDS = frozenset({"relational_outbox", "redis_streams", "kafka"})
_VALID_DATABASE_BACKENDS = frozenset({"sqlite", "postgresql"})
_ROOT_OUTPUT_ARTIFACTS = (
    "all_test_output.txt",
    "compile_output.txt",
    "fail_fast_output.txt",
    "mypy_output.txt",
    "profile_test_output.txt",
    "pytest_out.txt",
    "test_output.txt",
    "output.log",
    "pytest_output.log",
    "pytest_output_v2.log",
    "test_out.log",
    "test_output.log",
)


def _cleanup_root_output_artifacts() -> None:
    """Remove known root-level test/output artifacts to keep repo clean."""

    for name in _ROOT_OUTPUT_ARTIFACTS:
        path = PROJECT_ROOT / name
        if path.is_file():
            path.unlink()


def pytest_configure(config: pytest.Config) -> None:
    """Ensure valid ingest backend env vars before test collection.

    Shell-level env vars may carry stale or invalid values from previous
    experiments. This hook corrects any invalid backend selections to safe
    lightweight defaults before whale.ingest.config is first imported.
    """
    if os.environ.get("WHALE_INGEST_DATABASE_BACKEND", "") not in _VALID_DATABASE_BACKENDS:
        os.environ["WHALE_INGEST_DATABASE_BACKEND"] = "sqlite"
    if os.environ.get("WHALE_INGEST_STATE_CACHE_BACKEND", "") not in _VALID_STATE_CACHE_BACKENDS:
        os.environ["WHALE_INGEST_STATE_CACHE_BACKEND"] = "redis"
    os.environ.setdefault("WHALE_INGEST_REDIS_HOST", "127.0.0.1")
    os.environ.setdefault("WHALE_INGEST_REDIS_PORT", "6379")
    os.environ.setdefault("WHALE_INGEST_REDIS_DB", "0")
    os.environ.setdefault("WHALE_INGEST_REDIS_STATE_HASH_KEY", "whale:test:state")
    os.environ.setdefault("WHALE_INGEST_STATION_ID", "station-test-default")
    if os.environ.get("WHALE_INGEST_MESSAGE_BACKEND", "") not in _VALID_MESSAGE_BACKENDS:
        os.environ["WHALE_INGEST_MESSAGE_BACKEND"] = "relational_outbox"


def pytest_sessionstart(session: pytest.Session) -> None:
    """Clean root-level output artifacts before tests start."""

    _cleanup_root_output_artifacts()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean root-level output artifacts when tests finish."""

    _cleanup_root_output_artifacts()


@pytest.fixture(scope="session")
def real_redis_url() -> str:
    """Return the Redis URL used by integration tests that require a real service."""

    host = os.environ.get("WHALE_TEST_REDIS_HOST", "127.0.0.1")
    port = int(os.environ.get("WHALE_TEST_REDIS_PORT", "16379"))
    db = int(os.environ.get("WHALE_TEST_REDIS_DB", "15"))
    return f"redis://{host}:{port}/{db}"


@pytest.fixture()
def real_redis_client(real_redis_url: str):
    """Provide a real Redis client or skip with an explicit integration reason."""

    redis_module = pytest.importorskip("redis")
    client = redis_module.Redis.from_url(real_redis_url, decode_responses=True)
    try:
        client.ping()
    except Exception as exc:
        pytest.skip(
            "real Redis service is required for ingest Redis integration test: "
            f"{exc}"
        )
    if "fakeredis" in type(client).__module__.lower():
        raise AssertionError("integration tests require a real Redis client, not fakeredis")

    yield client

    try:
        client.flushdb()
    finally:
        client.close()


@pytest.fixture()
def real_redis_hash_key() -> str:
    """Return one isolated Redis hash key for the current test."""

    return f"whale:test:{uuid.uuid4()}"
