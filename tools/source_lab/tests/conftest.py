"""Pytest bootstrap for source_simulation tests.

Auto-skips @pytest.mark.load tests unless -m load is explicitly requested.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SRC_ROOT = _PROJECT_ROOT / "src"

for _path in (str(_PROJECT_ROOT), str(_SRC_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip @pytest.mark.load tests unless -m load is explicitly passed."""
    user_marker = config.getoption("-m") or ""
    if "load" in user_marker:
        return  # User explicitly requested load tests, don't skip

    for item in items:
        if item.get_closest_marker("load"):
            item.add_marker(
                pytest.mark.skip(reason="load test: use `pytest -m load` to run")
            )