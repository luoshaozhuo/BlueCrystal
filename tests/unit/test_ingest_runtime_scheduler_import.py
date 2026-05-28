"""Import smoke for the ingest runtime scheduler package."""

from __future__ import annotations

import importlib


def test_runtime_scheduler_module_imports() -> None:
    module = importlib.import_module("whale.ingest.runtime.scheduler")
    assert hasattr(module, "SourceScheduler")
