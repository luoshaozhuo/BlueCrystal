from __future__ import annotations

import json

from tools.source_lab.access.runtime.dynamic_cli import main


class _FakeRuntime:
    def __init__(self, endpoint_id: str) -> None:
        self.endpoint_id = endpoint_id

    def to_dict(self) -> dict[str, object]:
        return {"endpoint_id": self.endpoint_id, "state": "running", "params": {"password": "***REDACTED***"}}


class _FakeResult:
    def __init__(self, result: str, decision: str = "ALLOW", reason_code: str = "ok", runtime=None) -> None:
        self.operation_id = "op-1"
        self.result = result
        self.decision = decision
        self.reason_code = reason_code
        self.runtime = runtime


class _FakeRegistry:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def list_status(self) -> list[_FakeRuntime]:
        self.calls.append(("list_status", ()))
        return [_FakeRuntime("ep-1"), _FakeRuntime("ep-2")]

    def add_endpoint(self, config: object) -> _FakeResult:
        self.calls.append(("add_endpoint", (config,)))
        return _FakeResult("SUCCESS")

    def update_endpoint(self, endpoint_id: str, patch: dict[str, object], expected_version: int) -> _FakeResult:
        self.calls.append(("update_endpoint", (endpoint_id, patch, expected_version)))
        result = "CONFLICT" if expected_version != 1 else "SUCCESS"
        return _FakeResult(result, decision="DENY" if result == "CONFLICT" else "ALLOW", reason_code=result.lower())

    def pause_endpoint(self, endpoint_id: str) -> _FakeResult:
        self.calls.append(("pause_endpoint", (endpoint_id,)))
        return _FakeResult("SUCCESS")

    def resume_endpoint(self, endpoint_id: str) -> _FakeResult:
        self.calls.append(("resume_endpoint", (endpoint_id,)))
        return _FakeResult("SUCCESS")

    def stop_endpoint(self, endpoint_id: str) -> _FakeResult:
        self.calls.append(("stop_endpoint", (endpoint_id,)))
        return _FakeResult("SUCCESS")

    def delete_endpoint(self, endpoint_id: str) -> _FakeResult:
        self.calls.append(("delete_endpoint", (endpoint_id,)))
        return _FakeResult("SUCCESS")

    def replace_points(self, endpoint_id: str, points: tuple[object, ...], expected_version: int) -> _FakeResult:
        self.calls.append(("replace_points", (endpoint_id, points, expected_version)))
        result = "CONFLICT" if expected_version != 1 else "SUCCESS"
        return _FakeResult(result, decision="DENY" if result == "CONFLICT" else "ALLOW", reason_code=result.lower())

    def status(self, endpoint_id: str) -> _FakeResult:
        self.calls.append(("status", (endpoint_id,)))
        return _FakeResult("STATUS_SUCCESS", runtime=_FakeRuntime(endpoint_id))

    def recover(self) -> list[_FakeRuntime]:
        self.calls.append(("recover", ()))
        return [_FakeRuntime("ep-1")]


def test_dynamic_cli_list_status(monkeypatch, capsys) -> None:
    registry = _FakeRegistry()
    monkeypatch.setattr("tools.source_lab.access.runtime.dynamic_cli.build_registry", lambda state_dir=None: registry)
    exit_code = main(["list-status"])
    captured = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert captured["command"] == "list-status"
    assert [runtime["endpoint_id"] for runtime in captured["runtimes"]] == ["ep-1", "ep-2"]


def test_dynamic_cli_add_update_pause_resume_stop_delete_endpoint(monkeypatch, capsys) -> None:
    registry = _FakeRegistry()
    monkeypatch.setattr("tools.source_lab.access.runtime.dynamic_cli.build_registry", lambda state_dir=None: registry)
    config_json = json.dumps(
        {
            "endpoint_id": "ep-1",
            "protocol": "http_rest",
            "mode": "polling",
            "target_hz": 5.0,
            "source": {
                "endpoint": {
                    "name": "ep-1",
                    "host": "127.0.0.1",
                    "port": 8080,
                    "protocol": "http_rest",
                    "transport": "tcp",
                    "params": {"http_path": "/points", "password": "secret"},
                },
                "points": [{"address": "a1", "name": "a1"}],
            },
        }
    )
    assert main(["add", config_json]) == 0
    assert main(["update", "ep-1", "1", json.dumps({"host": "127.0.0.2"})]) == 0
    assert main(["pause", "ep-1"]) == 0
    assert main(["resume", "ep-1"]) == 0
    assert main(["stop", "ep-1"]) == 0
    assert main(["delete", "ep-1"]) == 0

    out = capsys.readouterr().out
    assert "secret" not in out


def test_dynamic_cli_replace_points_expected_version_conflict(monkeypatch, capsys) -> None:
    registry = _FakeRegistry()
    monkeypatch.setattr("tools.source_lab.access.runtime.dynamic_cli.build_registry", lambda state_dir=None: registry)
    exit_code = main(
        [
            "replace-points",
            "ep-1",
            "2",
            json.dumps([{"address": "a1", "name": "a1", "data_type": "INT32"}]),
        ]
    )
    captured = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert captured["result"] == "CONFLICT"


def test_dynamic_cli_recover_writes_journal(monkeypatch, capsys) -> None:
    registry = _FakeRegistry()
    monkeypatch.setattr("tools.source_lab.access.runtime.dynamic_cli.build_registry", lambda state_dir=None: registry)
    exit_code = main(["recover", "--print-runtime"])
    captured = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert captured["recovered_count"] == 1
    assert captured["runtimes"][0]["endpoint_id"] == "ep-1"
