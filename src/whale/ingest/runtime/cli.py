"""Typer CLI for ingest runtime entrypoints."""

from __future__ import annotations

import json
import os
import signal
import time
from datetime import UTC, datetime
from pathlib import Path

import typer

from whale.ingest.api import create_app
from whale.ingest.adapters.audit import DbIngestAuditSink, DualIngestAuditSink
from whale.ingest.adapters.observability.file_sinks import JsonlIngestAuditSink
from whale.ingest.adapters.security import (
    AllowAllAccessPolicy,
    DenyAllAccessPolicy,
    FileAccessPolicy,
)
from whale.ingest.bundle.model import IngestBundle
from whale.ingest.bundle.service import BundleService
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
    migrate_runtime_database,
)
from whale.ingest.runtime import (
    FencingTokenRepository,
    JobAssignmentRepository,
    LeaseService,
    NodeRuntimeRepository,
    RuntimeJobRepository,
    RuntimeMode,
    SourceScheduler,
    WorkerRuntime,
)
from whale.ingest.runtime.scheduler_settings import SchedulerSettings
from whale.shared.persistence.orm.ingest_runtime import IngestRuntimeJob

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _build_session_factory():
    engine = create_runtime_engine()
    if engine.url.get_backend_name().startswith("sqlite"):
        initialize_runtime_database(engine)
    return engine, create_runtime_session_factory(engine)


def _build_access_policy():
    policy_mode = os.environ.get("WHALE_INGEST_ACCESS_POLICY_MODE", "allow-all").strip().lower()
    if policy_mode == "deny-all":
        return DenyAllAccessPolicy()
    if policy_mode == "file-policy":
        policy_path = os.environ.get("WHALE_INGEST_ACCESS_POLICY_FILE", "").strip()
        if not policy_path:
            raise RuntimeError(
                "WHALE_INGEST_ACCESS_POLICY_FILE is required when "
                "WHALE_INGEST_ACCESS_POLICY_MODE=file-policy."
            )
        return FileAccessPolicy(policy_path)
    return AllowAllAccessPolicy()


def _build_audit_sink(session_factory):
    db_sink = DbIngestAuditSink(session_factory)
    jsonl_path = os.environ.get("WHALE_INGEST_AUDIT_JSONL_PATH", "").strip()
    if not jsonl_path:
        return db_sink
    return DualIngestAuditSink(db_sink, JsonlIngestAuditSink(jsonl_path))


def _build_scheduler_settings(
    *,
    runtime_mode: RuntimeMode,
    node_key: str,
) -> SchedulerSettings:
    return SchedulerSettings(
        runtime_mode=runtime_mode,
        node_key=node_key,
        heartbeat_interval_seconds=int(os.environ.get("WHALE_INGEST_HEARTBEAT_INTERVAL_SECONDS", "10")),
        heartbeat_timeout_seconds=int(os.environ.get("WHALE_INGEST_HEARTBEAT_TIMEOUT_SECONDS", "30")),
        lease_ttl_seconds=int(os.environ.get("WHALE_INGEST_LEASE_TTL_SECONDS", "30")),
        pull_max_in_flight=int(os.environ.get("WHALE_INGEST_PULL_MAX_IN_FLIGHT", "8")),
        timezone=os.environ.get("WHALE_INGEST_RUNTIME_TIMEZONE", "UTC"),
    )


def _build_scheduler(runtime_mode: RuntimeMode = RuntimeMode.STANDALONE, node_key: str = "worker-1") -> SourceScheduler:
    engine, session_factory = _build_session_factory()
    lease_service = LeaseService(session_factory, FencingTokenRepository(session_factory))
    return SourceScheduler(
        settings=_build_scheduler_settings(runtime_mode=runtime_mode, node_key=node_key),
        node_repository=NodeRuntimeRepository(session_factory),
        job_repository=RuntimeJobRepository(session_factory),
        assignment_repository=JobAssignmentRepository(session_factory),
        lease_service=lease_service,
        audit_sink=_build_audit_sink(session_factory),
    )


class _NoopJobHandler:
    """Built-in handler for prodlike smoke and endurance scheduler activity."""

    def execute(self, job: IngestRuntimeJob) -> None:
        raw_sleep_ms = job.config_json.get("simulate_duration_ms")
        if raw_sleep_ms in (None, ""):
            return
        try:
            sleep_ms = max(0, int(raw_sleep_ms))
        except (TypeError, ValueError):
            return
        if sleep_ms > 0:
            time.sleep(sleep_ms / 1000.0)


def _build_worker_runtime(
    *,
    runtime_mode: RuntimeMode,
    node_key: str,
) -> WorkerRuntime:
    engine, session_factory = _build_session_factory()
    del engine
    lease_service = LeaseService(session_factory, FencingTokenRepository(session_factory))
    return WorkerRuntime(
        settings=_build_scheduler_settings(runtime_mode=runtime_mode, node_key=node_key),
        node_repository=NodeRuntimeRepository(session_factory),
        job_repository=RuntimeJobRepository(session_factory),
        assignment_repository=JobAssignmentRepository(session_factory),
        lease_service=lease_service,
        fencing_token_repository=FencingTokenRepository(session_factory),
        audit_sink=_build_audit_sink(session_factory),
        handlers={
            "noop": _NoopJobHandler(),
            "acquisition": _NoopJobHandler(),
            "publish": _NoopJobHandler(),
        },
    )


def _write_worker_summary(
    *,
    path: str | None,
    node_key: str,
    started_at: datetime,
    stopped_at: datetime,
    runtime: WorkerRuntime,
    graceful_shutdown_result: str,
) -> None:
    if not path:
        return
    summary_path = Path(path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "node_key": node_key,
        "started_at": started_at.isoformat(),
        "stopped_at": stopped_at.isoformat(),
        "uptime_seconds": max((stopped_at - started_at).total_seconds(), 0.0),
        "graceful_shutdown_result": graceful_shutdown_result,
        "restart_count": 0,
        "metrics": runtime.metrics_summary,
    }
    summary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


@app.command("migrate")
def migrate() -> None:
    """Initialize or migrate the runtime schema."""

    engine = create_runtime_engine()
    migrate_runtime_database(engine)
    typer.echo("migrate completed")


@app.command("api")
def api(smoke_exit: bool = typer.Option(False, help="Create the API app and exit.")) -> None:
    """Start or smoke the API runtime."""

    _, session_factory = _build_session_factory()
    audit_sink = _build_audit_sink(session_factory)
    access_policy = _build_access_policy()
    create_app(
        session_factory=session_factory,
        audit_sink=audit_sink,
        access_policy=access_policy,
    )
    if smoke_exit:
        typer.echo("api startup ok")
        return
    import uvicorn

    uvicorn.run(
        create_app(
            session_factory=session_factory,
            audit_sink=audit_sink,
            access_policy=access_policy,
        ),
        host="0.0.0.0",
        port=8000,
    )


@app.command("worker")
def worker(
    smoke_exit: bool = typer.Option(False, help="Bootstrap scheduler and exit."),
    runtime_mode: RuntimeMode = typer.Option(RuntimeMode.STANDALONE),
    node_key: str = typer.Option("worker-1"),
) -> None:
    """Start or smoke the worker runtime."""

    scheduler = _build_scheduler(runtime_mode=runtime_mode, node_key=node_key)
    snapshot = scheduler.bootstrap()
    if smoke_exit:
        typer.echo(f"worker startup ok {snapshot.node_key}")
        return
    runtime = _build_worker_runtime(runtime_mode=runtime_mode, node_key=node_key)
    started_at = datetime.now(tz=UTC)
    stop_requested = {"value": False}

    def _handle_signal(signum: int, frame: object | None) -> None:
        del frame
        stop_requested["value"] = True
        typer.echo(f"worker stop requested node={node_key} signal={signum}")

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    runtime.start()
    typer.echo(f"worker running {snapshot.node_key}")
    graceful_shutdown_result = "SUCCESS"
    try:
        while not stop_requested["value"]:
            time.sleep(1.0)
    except KeyboardInterrupt:
        stop_requested["value"] = True
    except Exception:
        graceful_shutdown_result = "FAILED"
        raise
    finally:
        runtime.stop(timeout_seconds=15)
        _write_worker_summary(
            path=os.environ.get("WHALE_INGEST_WORKER_SUMMARY_PATH", "").strip() or None,
            node_key=node_key,
            started_at=started_at,
            stopped_at=datetime.now(tz=UTC),
            runtime=runtime,
            graceful_shutdown_result=graceful_shutdown_result,
        )


@app.command("api-worker")
def api_worker(
    smoke_exit: bool = typer.Option(False, help="Bootstrap API and worker, then exit."),
    runtime_mode: RuntimeMode = typer.Option(RuntimeMode.STANDALONE),
    node_key: str = typer.Option("api-worker-1"),
) -> None:
    """Start or smoke the combined API/worker runtime."""

    _, session_factory = _build_session_factory()
    audit_sink = _build_audit_sink(session_factory)
    access_policy = _build_access_policy()
    create_app(
        session_factory=session_factory,
        audit_sink=audit_sink,
        access_policy=access_policy,
        node_id=node_key,
    )
    scheduler = _build_scheduler(runtime_mode=runtime_mode, node_key=node_key)
    scheduler.bootstrap()
    if smoke_exit:
        typer.echo("api-worker startup ok")
        return
    typer.echo("api-worker bootstrapped")


@app.command("export-bundle")
def export_bundle(
    path: Path = typer.Option(..., exists=False, dir_okay=False),
    redacted: bool = typer.Option(False),
) -> None:
    """Export the current acquisition-task configuration into one bundle file."""

    _, session_factory = _build_session_factory()
    service = BundleService(
        session_factory,
        audit_sink=_build_audit_sink(session_factory),
        node_id="bundle-export",
    )
    bundle = service.export_bundle(source="cli", actor="cli", redacted=redacted)
    path.write_text(json.dumps(bundle.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(path))


@app.command("import-bundle")
def import_bundle(
    path: Path = typer.Option(..., exists=True, dir_okay=False),
    dry_run: bool = typer.Option(False),
) -> None:
    """Import one bundle file into the runtime DB."""

    _, session_factory = _build_session_factory()
    service = BundleService(
        session_factory,
        audit_sink=_build_audit_sink(session_factory),
        node_id="bundle-import",
    )
    bundle = IngestBundle.model_validate_json(path.read_text(encoding="utf-8"))
    result = service.import_bundle(bundle, actor="cli", dry_run=dry_run)
    typer.echo(f"imported={result.imported_count} dry_run={result.dry_run}")
