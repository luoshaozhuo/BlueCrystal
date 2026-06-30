"""Seahorse driver backend 工厂。"""

from __future__ import annotations

from seahorse.infrastructure.drivers.starfish_writer_backend import InMemoryStarfishWriterBackend


def create_driver_backend() -> None:
    """返回空 backend 占位。

    Returns:
        始终为 None，表示本轮未提供真实 driver backend。
    """
    return None


def create_in_memory_starfish_writer_backend(
    *,
    fail_server_ids: frozenset[str] = frozenset(),
    fail_endpoint_ids: frozenset[str] = frozenset(),
    fail_field_ids: frozenset[str] = frozenset(),
    fail_point_ids: frozenset[str] = frozenset(),
    exception_batch_ids: frozenset[str] = frozenset(),
) -> InMemoryStarfishWriterBackend:
    """构建内存 Starfish writer backend。"""
    return InMemoryStarfishWriterBackend(
        fail_server_ids=fail_server_ids,
        fail_endpoint_ids=fail_endpoint_ids,
        fail_field_ids=fail_field_ids,
        fail_point_ids=fail_point_ids,
        exception_batch_ids=exception_batch_ids,
    )
