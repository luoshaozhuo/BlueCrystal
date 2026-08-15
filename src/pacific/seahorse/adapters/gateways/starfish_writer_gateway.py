"""Starfish writer gateway。

gateway 实现 application StarfishWriterPort，只把 WriteBatch 委托给注入的
adapter-local backend，不创建 backend，也不导入真实 writer runtime。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pacific.seahorse.adapters.drivers.backend_ports import StarfishWriterBackend
from pacific.seahorse.application.ports.starfish_writer_port import StarfishWriterPort
from pacific.seahorse.domain.runtime_contract import WriteBatch, WriteBatchResult


@dataclass(slots=True)
class StarfishWriterGateway(StarfishWriterPort):
    """StarfishWriterPort 的 backend 委托实现。

    Attributes:
        backend: 由 container 注入的内存或本地 backend。
        history: 仅用于本地 smoke workflow 暴露 backend 已写入 batch 数量；
            生产路径不应读取该字段。当 backend 不提供 ``history`` 字段
            （例如测试替身）时，gateway 退化为 ``()``。
    """

    backend: StarfishWriterBackend
    history: tuple[WriteBatch, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """初始化时拉取 backend 当前的 history 引用。

        backend 与 gateway 共享同一份 backend.history 列表，使 gateway
        始终能在不变更端口契约的前提下，让 workflow 读取
        ``history_count``。该 list 引用不会被替换，只追加。
        """
        backend_history = getattr(self.backend, "history", None)
        if backend_history is not None:
            self.history = backend_history

    def write_batch(self, batch: WriteBatch) -> WriteBatchResult:
        """将 batch 委托给注入的 backend。"""
        return self.backend.dispatch_batch(batch)

    def flush(self) -> None:
        """内存 gateway 无额外缓冲，保留端口语义。"""
        return None


__all__ = ["StarfishWriterGateway"]
