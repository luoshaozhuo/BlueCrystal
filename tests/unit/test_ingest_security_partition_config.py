"""Security partition config guard tests."""

from __future__ import annotations

from pathlib import Path


def test_security_partition_config_exists_and_contains_required_guards() -> None:
    path = Path(__file__).resolve().parents[2] / "config" / "ingest" / "security_partition.example.yaml"
    assert path.exists(), "security partition config example must exist"
    content = path.read_text(encoding="utf-8")
    assert "ingest:" in content
    assert "source:" in content
    assert "cache:" in content
    assert "mq:" in content
    assert "write_control_requires_separate_approval: true" in content
    assert "source_write_default_enabled: false" in content
    assert "simulator_forbidden_in_production: true" in content
    assert "production_forbid_tools_source_lab_import: true" in content
