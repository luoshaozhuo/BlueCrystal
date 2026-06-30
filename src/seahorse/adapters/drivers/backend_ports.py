"""driver adapter 局部 backend 契约。

该契约只供 adapters/drivers 与 infrastructure/drivers 之间装配时使用，
UseCase 不得依赖本文件。本轮不提供真实 backend 实现。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from seahorse.domain.runtime_contract import WriteBatch, WriteBatchResult


@runtime_checkable
class DriverBackend(Protocol):
    """driver backend 最小生命周期契约。

    真实 backend 若后续接入，应由 ``infrastructure/drivers`` 创建并通过
    ``container.py`` 注入；adapter 不直接创建外部资源。
    """

    def close(self) -> None:
        """释放 backend 持有的外部资源。"""
        ...


@runtime_checkable
class StarfishWriterBackend(Protocol):
    """Starfish writer gateway 使用的 adapter-local backend 契约。"""

    def dispatch_batch(self, batch: WriteBatch) -> WriteBatchResult:
        """分发一个 WriteBatch 并返回稳定结果。"""
        ...
