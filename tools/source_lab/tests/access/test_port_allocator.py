"""Tests for simulator port probing and allocation."""

from __future__ import annotations

import socket

import pytest

from tools.source_lab.sources import PortAllocator


def test_allocate_many_skips_occupied_port() -> None:
    allocator = PortAllocator.from_range(start=53000, end=53003)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 53000))
        allocated = allocator.allocate_many(2, host="127.0.0.1")

    assert allocated == (53001, 53002)


def test_allocate_many_reports_diagnostics_when_range_exhausted() -> None:
    allocator = PortAllocator.from_range(start=53010, end=53010)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 53010))

        with pytest.raises(RuntimeError, match="Failed to allocate simulator ports") as exc_info:
            allocator.allocate_many(1, host="127.0.0.1")

    message = str(exc_info.value)
    assert "needed=1" in message
    assert "attempted=1" in message
    assert "unavailable_sample=(53010,)" in message
