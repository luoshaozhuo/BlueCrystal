from __future__ import annotations

import json
from pathlib import Path

from tools.source_lab.access.runtime import RuntimeStateStore
from tools.source_lab.access.runtime.dynamic_cli import main


def test_dynamic_cli_inspect_state_store_outputs_snapshot_summary(tmp_path: Path, capsys) -> None:
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    store.save_registry({"ep-1": {"state": "running"}})
    output = tmp_path / "inspect.json"

    exit_code = main(["--state-dir", str(tmp_path / "runtime"), "inspect-state-store", "--output", str(output)])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["snapshots"]["registry"]["exists"] is True
    assert output.exists()


def test_dynamic_cli_repair_state_store_restores_from_backup_and_journals(tmp_path: Path, capsys) -> None:
    store = RuntimeStateStore(str(tmp_path / "runtime"))
    store.save_registry({"ep-1": {"state": "running"}})
    store.save_registry({"ep-1": {"state": "paused"}})
    store.registry_path.write_text("{bad", encoding="utf-8")

    exit_code = main(["--state-dir", str(tmp_path / "runtime"), "repair-state-store", "--from-backup"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["repair_results"]["registry"]["status"] == "SUCCESS"
    entries = store.load_journal_entries()
    assert any(entry.get("action") == "REPAIR_STATE_STORE" for entry in entries)


def test_dynamic_cli_repair_state_store_requires_from_backup_flag(capsys) -> None:
    exit_code = main(["repair-state-store"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["reason_code"] == "from_backup_flag_required"
