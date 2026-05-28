"""CLI smoke tests for ingest runtime entrypoints."""

from __future__ import annotations

from typer.testing import CliRunner

from whale.ingest.runtime.cli import app


def test_runtime_entrypoints_smoke(tmp_path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setenv("WHALE_INGEST_DATABASE_BACKEND", "sqlite")
    monkeypatch.setenv("WHALE_INGEST_REDIS_HOST", "127.0.0.1")
    monkeypatch.setenv("WHALE_INGEST_REDIS_STATE_HASH_KEY", "whale:test:runtime")
    monkeypatch.setenv("WHALE_INGEST_STATION_ID", "station-runtime")
    monkeypatch.setenv("WHALE_INGEST_DB_PATH", str(tmp_path / "runtime.sqlite"))
    monkeypatch.setenv("WHALE_SHARED_DB_BACKEND", "sqlite")
    monkeypatch.setenv("WHALE_SHARED_DB_PATH", str(tmp_path / "shared.sqlite"))

    migrate_result = runner.invoke(app, ["migrate"])
    worker_result = runner.invoke(app, ["worker", "--smoke-exit"])
    api_worker_result = runner.invoke(app, ["api-worker", "--smoke-exit"])

    assert migrate_result.exit_code == 0
    assert worker_result.exit_code == 0
    assert api_worker_result.exit_code == 0
