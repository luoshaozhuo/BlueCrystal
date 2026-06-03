"""Helpers for creating isolated shared persistence sample databases in tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def create_shared_persistence_sample_db(tmp_path: Path) -> Path:
    """Create one isolated SQLite DB populated by sample_data."""

    repo_root = Path(__file__).resolve().parents[2]
    db_path = tmp_path / "shared-persistence-source-lab.sqlite"
    env = {
        **os.environ,
        "PYTHONPATH": str(repo_root / "src"),
        "WHALE_SHARED_DB_BACKEND": "sqlite",
        "WHALE_SHARED_DB_PATH": str(db_path),
    }
    subprocess.run(
        [sys.executable, "-m", "whale.shared.persistence.template.sample_data"],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return db_path
