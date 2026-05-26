from __future__ import annotations

import json
from pathlib import Path

from tools.source_lab.access.runtime.dynamic_cli import main
from tools.source_lab.tests.access._dynamic_runtime_test_utils import (
    build_http_source,
    build_registry,
    polling_config,
)


def test_dynamic_cli_export_import_accepted_state_roundtrip(tmp_path: Path, capsys) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(1, 60201)
    assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"
    export_path = tmp_path / "accepted.json"

    assert (
        main(
            [
                "--state-dir",
                str(tmp_path / "runtime"),
                "export-accepted-state",
                "--raw",
                "--output",
                str(export_path),
            ]
        )
        == 0
    )
    exported = json.loads(export_path.read_text(encoding="utf-8"))
    assert exported["redacted"] is False
    imported_path = tmp_path / "accepted-import.json"
    imported_path.write_text(json.dumps(exported), encoding="utf-8")
    assert main(["--state-dir", str(tmp_path / "runtime"), "import-accepted-state", "--file", str(imported_path)]) == 0
    out = capsys.readouterr().out
    assert "\"valid\": true" in out


def test_dynamic_cli_validate_accepted_state_rejects_invalid_schema(tmp_path: Path, capsys) -> None:
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps({"schema_version": "1.0", "endpoints": []}), encoding="utf-8")
    exit_code = main(["validate-accepted-state", "--file", str(invalid_path)])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["valid"] is False


def test_dynamic_cli_import_failure_does_not_mutate_existing_state(tmp_path: Path, capsys) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(2, 60202)
    assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"
    before = registry._state_store.load_accepted_endpoints()
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(
        json.dumps({"schema_version": "1.0", "bundle_version": "v1", "redacted": False, "checksum": "bad", "endpoints": [{"endpoint_id": "only"}]}),
        encoding="utf-8",
    )

    exit_code = main(["--state-dir", str(tmp_path / "runtime"), "import-accepted-state", "--file", str(invalid_path)])
    _ = capsys.readouterr()
    after = registry._state_store.load_accepted_endpoints()
    assert exit_code == 1
    assert after == before


def test_dynamic_cli_schema_outputs_stable_json(capsys) -> None:
    exit_code = main(["schema", "--type", "accepted-state"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema"]["type"] == "object"
    assert "checksum" in payload["schema"]["required"]


def test_dynamic_cli_dump_continuity_and_journal(tmp_path: Path) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(3, 60203)
    assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"
    continuity_path = tmp_path / "continuity.json"
    journal_path = tmp_path / "journal.jsonl"

    assert main(["--state-dir", str(tmp_path / "runtime"), "dump-continuity", "--output", str(continuity_path)]) == 0
    assert main(["--state-dir", str(tmp_path / "runtime"), "dump-journal", "--output", str(journal_path)]) == 0
    assert continuity_path.exists()
    assert journal_path.exists()


def test_dynamic_cli_redacts_sensitive_values(tmp_path: Path, capsys) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(4, 60204)
    config = polling_config(source, params={"password": "secret", "token": "abc", "username": "alice"})
    assert registry.add_endpoint(config).result == "SUCCESS"
    export_path = tmp_path / "accepted-redacted.json"

    assert main(["--state-dir", str(tmp_path / "runtime"), "export-accepted-state", "--output", str(export_path)]) == 0
    _ = capsys.readouterr()
    text = export_path.read_text(encoding="utf-8")
    assert "\"redacted\": true" in text
    assert "secret" not in text
    assert "alice" not in text
    assert "abc" not in text


def test_dynamic_cli_validate_accepted_state_rejects_duplicate_deleted_and_bad_checksum(tmp_path: Path, capsys) -> None:
    invalid_bundle = {
        "schema_version": "1.0",
        "bundle_version": "bundle-1",
        "redacted": False,
        "checksum": "broken",
        "endpoints": [
            {
                "endpoint_id": "dup",
                "protocol": "http_rest",
                "mode": "polling",
                "config_version": 1,
                "source": {
                    "endpoint": {"name": "dup", "host": "127.0.0.1", "port": 8080, "protocol": "http_rest"},
                    "points": [{"address": "a1"}],
                },
            },
            {
                "endpoint_id": "dup",
                "protocol": "http_rest",
                "mode": "polling",
                "config_version": 1,
                "state": "deleted",
                "source": {
                    "endpoint": {"name": "dup", "host": "127.0.0.1", "port": 8081, "protocol": "http_rest"},
                    "points": [{"address": "a2"}],
                },
            },
        ],
    }
    invalid_path = tmp_path / "invalid-bundle.json"
    invalid_path.write_text(json.dumps(invalid_bundle), encoding="utf-8")

    exit_code = main(["validate-accepted-state", "--file", str(invalid_path)])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert "invalid:checksum" in payload["errors"]
    assert any("duplicate:endpoint_id" in item for item in payload["errors"])
    assert any("deleted_endpoint_in_active_restore_set" in item for item in payload["errors"])


def test_dynamic_cli_import_rejects_redacted_bundle(tmp_path: Path, capsys) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(5, 60205)
    config = polling_config(source, params={"password": "secret"})
    assert registry.add_endpoint(config).result == "SUCCESS"
    export_path = tmp_path / "accepted-redacted.json"
    assert main(["--state-dir", str(tmp_path / "runtime"), "export-accepted-state", "--output", str(export_path)]) == 0
    _ = capsys.readouterr()

    exit_code = main(["--state-dir", str(tmp_path / "runtime"), "import-accepted-state", "--file", str(export_path)])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert "redacted_bundle_not_importable" in payload["errors"]
