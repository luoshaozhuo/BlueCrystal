"""Starfish unit 测试子树的通用 marker 约束。"""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """为本目录下所有测试统一追加 `starfish` marker。"""
    for item in items:
        item.add_marker(pytest.mark.starfish)
