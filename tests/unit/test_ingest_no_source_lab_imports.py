"""Ensure ingest production code does not import tools.source_lab."""

from __future__ import annotations

import ast
from pathlib import Path


def test_ingest_production_code_does_not_import_source_lab() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "whale" / "ingest"
    offenders: list[str] = []
    for file_path in root.rglob("*.py"):
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name.startswith("tools.source_lab") for alias in node.names):
                    offenders.append(str(file_path))
            if isinstance(node, ast.ImportFrom):
                if (node.module or "").startswith("tools.source_lab"):
                    offenders.append(str(file_path))
    assert offenders == [], f"ingest production imports tools.source_lab: {sorted(set(offenders))}"
