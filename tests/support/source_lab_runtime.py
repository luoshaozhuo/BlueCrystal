"""Helpers for using source_lab runtime modules without package-level side effects."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_LAB_ROOT = PROJECT_ROOT / "tools" / "source_lab"


def _ensure_namespace_package(name: str, path: Path) -> None:
    """Register a namespace-like package stub for one source_lab package path."""

    if name in sys.modules:
        return
    module = types.ModuleType(name)
    module.__path__ = [str(path)]  # type: ignore[attr-defined]
    sys.modules[name] = module


def prepare_source_lab_runtime_imports() -> None:
    """Install lightweight package stubs before importing source_lab submodules.

    The current source_lab package `__init__` eagerly imports capacity/profile
    modules. Ingest integration tests only need the simulator/runtime modules,
    so they register package stubs here and import concrete submodules directly.
    """

    _ensure_namespace_package("tools.source_lab", SOURCE_LAB_ROOT)
    _ensure_namespace_package("tools.source_lab.access", SOURCE_LAB_ROOT / "access")
    _ensure_namespace_package(
        "tools.source_lab.access.runners",
        SOURCE_LAB_ROOT / "access" / "runners",
    )
    _ensure_namespace_package("tools.source_lab.opcua", SOURCE_LAB_ROOT / "opcua")


def import_source_lab_module(module_name: str) -> Any:
    """Import one source_lab submodule after preparing stub packages."""

    prepare_source_lab_runtime_imports()
    return importlib.import_module(module_name)
