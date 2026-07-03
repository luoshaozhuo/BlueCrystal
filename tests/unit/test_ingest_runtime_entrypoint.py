"""CLI entrypoint tests for ingest runtime."""

from __future__ import annotations

from typer.testing import CliRunner

from whale.ingest.runtime.cli import app


def test_runtime_entrypoint_rejects_invalid_command() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["invalid-command"])
    assert result.exit_code != 0


def test_runtime_entrypoint_api_smoke(tmp_path, monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setenv("WHALE_INGEST_DATABASE_BACKEND", "sqlite")
    monkeypatch.setenv("WHALE_INGEST_REDIS_HOST", "127.0.0.1")
    monkeypatch.setenv("WHALE_INGEST_REDIS_STATE_HASH_KEY", "whale:test:runtime")
    monkeypatch.setenv("WHALE_INGEST_STATION_ID", "station-runtime")
    monkeypatch.setenv("WHALE_INGEST_DB_PATH", str(tmp_path / "runtime.sqlite"))
    monkeypatch.setenv("WHALE_DB_URL", f"sqlite:///{tmp_path / 'shared.sqlite'}")

    result = runner.invoke(app, ["api", "--smoke-exit"])

    assert result.exit_code == 0
    assert "api startup ok" in result.stdout
