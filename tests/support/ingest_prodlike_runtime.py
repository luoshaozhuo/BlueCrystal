"""Shared helpers for prodlike ingest compose, endurance, and fault tests."""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import pytest

from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    migrate_runtime_database,
)
from whale.ingest.runtime import RuntimeJob, RuntimeJobRepository
from whale.shared.persistence.orm.ingest_runtime import (
    IngestAuditEventOrm,
    IngestJobAssignment,
    IngestJobLease,
    IngestRuntimeJob,
    IngestRuntimeNode,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = PROJECT_ROOT / "deploy" / "whale" / "ingest" / "docker-compose.ingest-prodlike.yaml"
COMPOSE_PROJECT_NAME = os.environ.get("COMPOSE_PROJECT_NAME", "whale-prodlike-tests")
POSTGRES_USER = os.environ.get("WHALE_INGEST_PRODLIKE_PG_USER", "whale")
POSTGRES_PASSWORD = os.environ.get("WHALE_INGEST_PRODLIKE_PG_PASSWORD", "whale-prodlike-test")
API_BASE_URL = os.environ.get("WHALE_INGEST_PRODLIKE_API_URL", "http://127.0.0.1:18000")


def compose_env() -> dict[str, str]:
    env = os.environ.copy()
    env["WHALE_INGEST_PRODLIKE_PG_USER"] = env.get("WHALE_INGEST_PRODLIKE_PG_USER") or POSTGRES_USER
    env["WHALE_INGEST_PRODLIKE_PG_PASSWORD"] = env.get("WHALE_INGEST_PRODLIKE_PG_PASSWORD") or POSTGRES_PASSWORD
    return env


def docker_available() -> bool:
    try:
        subprocess.run(
            ["docker", "version"],
            check=True,
            capture_output=True,
            text=True,
            env=compose_env(),
        )
    except Exception:
        return False
    return True


def require_docker() -> None:
    if not docker_available():
        pytest.skip("Docker environment unavailable for prodlike ingest tests")


def compose(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "docker",
            "compose",
            "-p",
            COMPOSE_PROJECT_NAME,
            "-f",
            str(COMPOSE_FILE),
            *args,
        ],
        check=check,
        capture_output=True,
        text=True,
        env=compose_env(),
        cwd=PROJECT_ROOT,
    )


def runtime_dsn(database: str = "whale_ingest") -> str:
    return f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@127.0.0.1:5432/{database}"


_RUNTIME_ENGINE_CACHE: dict[str, tuple[Any, Any]] = {}


def clear_runtime_engine_cache() -> None:
    """Clear the cached runtime engine so the next call creates a fresh one."""
    _RUNTIME_ENGINE_CACHE.clear()


def runtime_session_factory(database: str = "whale_ingest"):
    if database in _RUNTIME_ENGINE_CACHE:
        _engine, _factory = _RUNTIME_ENGINE_CACHE[database]
        return _factory
    engine = create_runtime_engine(runtime_dsn(database))
    migrate_runtime_database(engine)
    factory = create_runtime_session_factory(engine)
    _RUNTIME_ENGINE_CACHE[database] = (engine, factory)
    return factory


def ensure_prodlike_stack(*, services: Iterable[str] | None = None) -> None:
    require_docker()
    selected = list(services or ("ingest-api", "ingest-worker-a", "ingest-worker-b", "audit-jsonl"))
    # Unset proxy vars so healthcheck urls resolve directly
    for proxy_var in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
        os.environ.pop(proxy_var, None)
    compose("build", "ingest-api", "ingest-worker-a", "ingest-worker-b")
    compose("up", "-d", "postgres", "redis", "kafka")
    migrate_prodlike_database()
    compose("up", "-d", *selected)
    wait_for_http(f"{API_BASE_URL}/healthz", contains='"status":"ok"', timeout_seconds=120)


def migrate_prodlike_database() -> None:
    require_docker()
    compose("run", "--rm", "ingest-api", "migrate")


def stop_prodlike_stack() -> None:
    if not docker_available():
        return
    compose("down", "-v", check=False)


def stop_service(service: str) -> None:
    require_docker()
    compose("stop", service)


def start_service(service: str) -> None:
    require_docker()
    compose("start", service)


def restart_service(service: str) -> None:
    require_docker()
    compose("restart", service)


def service_logs(service: str, *, tail: int = 200) -> str:
    require_docker()
    result = compose("logs", "--tail", str(tail), service)
    return result.stdout


def wait_until(
    predicate: Callable[[], bool],
    *,
    timeout_seconds: float,
    interval_seconds: float = 1.0,
    error_message: str,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval_seconds)
    raise AssertionError(error_message)


def wait_for_kafka(*, bootstrap_server: str = "127.0.0.1:9092", timeout_seconds: float = 60.0) -> None:
    """Wait until Kafka broker is reachable from the host via metadata fetch."""
    from kafka import KafkaProducer
    from kafka.errors import NoBrokersAvailable

    def _kafka_ok() -> bool:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[bootstrap_server],
                request_timeout_ms=5000,
                retries=0,
            )
            # force a real metadata request to verify broker connectivity
            future = producer.send("whale.ingest.probe", key=b"probe", value=b"probe")
            future.get(timeout=5)
            producer.flush()
            producer.close(timeout=1)
            return True
        except NoBrokersAvailable:
            return False
        except Exception:
            # send might fail if topic auto-creation is slow; try metadata instead
            try:
                producer.metrics()  # type: ignore[unreachable]
                producer.close(timeout=1)
                return True
            except Exception:
                return False

    wait_until(
        _kafka_ok,
        timeout_seconds=timeout_seconds,
        interval_seconds=3.0,
        error_message=f"Kafka broker not reachable at {bootstrap_server}",
    )


def wait_for_http(
    url: str,
    *,
    contains: str | None = None,
    timeout_seconds: float = 60.0,
) -> None:
    import urllib.request

    _opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _ok() -> bool:
        try:
            with _opener.open(url, timeout=3) as response:
                body = response.read().decode("utf-8")
        except Exception:
            return False
        return contains in body if contains else True

    wait_until(
        _ok,
        timeout_seconds=timeout_seconds,
        interval_seconds=2.0,
        error_message=f"HTTP wait timed out: {url}",
    )


def truncate_runtime_tables(database: str = "whale_ingest") -> None:
    clear_runtime_engine_cache()
    session = runtime_session_factory(database)()
    try:
        for table in (
            IngestJobAssignment,
            IngestJobLease,
            IngestAuditEventOrm,
            IngestRuntimeJob,
            IngestRuntimeNode,
        ):
            session.query(table).delete()
        session.commit()
    finally:
        session.close()


def seed_runtime_job(
    *,
    job_id: str | None = None,
    job_type: str = "noop",
    config: dict[str, object] | None = None,
    partition_key: str | None = None,
    priority: int = 100,
    enabled: bool = True,
    database: str = "whale_ingest",
) -> str:
    job_id = job_id or f"prodlike-job-{uuid.uuid4()}"
    repo = RuntimeJobRepository(runtime_session_factory(database))
    repo.upsert_job(
        RuntimeJob(
            job_id=job_id,
            job_type=job_type,
            partition_key=partition_key,
            priority=priority,
            enabled=enabled,
            config=config or {"interval_ms": 1000},
        )
    )
    return job_id


def active_assignments(database: str = "whale_ingest") -> list[IngestJobAssignment]:
    session = runtime_session_factory(database)()
    try:
        return list(session.query(IngestJobAssignment).filter_by(active=True).all())
    finally:
        session.close()


def wait_for_assignment_count(count: int, *, database: str = "whale_ingest", timeout_seconds: float = 60.0) -> None:
    wait_until(
        lambda: len(active_assignments(database)) >= count,
        timeout_seconds=timeout_seconds,
        error_message=f"Expected at least {count} active assignments",
    )


def count_audit_events(
    *,
    action: str | None = None,
    result: str | None = None,
    database: str = "whale_ingest",
) -> int:
    session = runtime_session_factory(database)()
    try:
        query = session.query(IngestAuditEventOrm)
        if action is not None:
            query = query.filter_by(action=action)
        if result is not None:
            query = query.filter_by(result=result)
        return int(query.count())
    finally:
        session.close()


def read_worker_summary(worker_service: str) -> dict[str, Any]:
    require_docker()
    result = compose("exec", "-T", "audit-jsonl", "cat", f"/audit/{worker_service}-summary.json")
    return json.loads(result.stdout)
