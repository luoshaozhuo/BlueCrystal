"""Shared access-layer utility helpers."""

from __future__ import annotations


def normalize_protocol(value: str) -> str:
    """Normalize protocol name for robust comparisons."""

    return value.strip().lower().replace("_", "").replace("-", "")
