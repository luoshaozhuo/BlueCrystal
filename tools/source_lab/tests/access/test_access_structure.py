"""Tests for access package structure and entrypoint imports."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path


def test_legacy_access_shim_files_do_not_exist() -> None:
    """Old flat access shim modules should not exist after regrouping."""

    root = Path("tools/source_lab/access")
    legacy_files = (
        "capacity_model.py",
        "capacity_progress.py",
        "capacity_reporter.py",
        "capacity_rows.py",
        "model.py",
        "metrics.py",
        "worker.py",
        "reporter.py",
        "subscription.py",
        "subscription_model.py",
        "subscription_metrics.py",
        "subscription_reporter.py",
        "subscription_worker.py",
    )

    assert all(not (root / name).exists() for name in legacy_files)
    assert (root / "field_capacity.py").exists()
    assert (root / "common" / "progress.py").exists()
    assert (root / "common" / "table.py").exists()
    assert (root / "subscribe" / "capacity.py").exists()
    assert (root / "subscribe" / "capacity_model.py").exists()
    assert (root / "subscribe" / "capacity_plan.py").exists()
    assert (root / "subscribe" / "capacity_rows.py").exists()
    assert (root / "subscribe" / "capacity_scan.py").exists()
    assert (root / "polling" / "capacity.py").exists()
    assert (root / "polling" / "capacity_rows.py").exists()


def test_common_package_does_not_host_mode_specific_capacity_rows() -> None:
    """Mode-specific row builders should stay under polling/subscribe packages."""

    root = Path("tools/source_lab/access")
    common = root / "common"

    forbidden_common_files = (
        "capacity_rows.py",
        "subscribe_capacity_rows.py",
        "polling_capacity_rows.py",
        "subscribe_rows.py",
        "polling_rows.py",
    )

    assert all(not (common / name).exists() for name in forbidden_common_files)


def test_cli_entrypoints_import_after_access_regrouping() -> None:
    """Field CLIs should import cleanly through the regrouped access packages."""

    modules = (
        "tools.source_lab.field_probe",
        "tools.source_lab.field_capacity",
        "tools.source_lab.field_profile",
    )

    for module_name in modules:
        module = import_module(module_name)
        assert module is not None
