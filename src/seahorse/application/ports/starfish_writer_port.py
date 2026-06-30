"""Starfish writer 应用端口。

端口只定义批量和缓冲写入语义，不 import Starfish runtime，也不
实现真实 writer。本轮继续保持 Seahorse -> Starfish 纯 JSON handoff。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from seahorse.domain.runtime_contract import WriteBatch, WriteBatchResult


@runtime_checkable
class StarfishWriterPort(Protocol):
    """Starfish 写入端口。

    高频边界预留 batch/buffer 风格接口，避免未来 runtime 只能逐点写入。
    本轮没有 concrete writer。
    """

    def write_batch(self, batch: WriteBatch) -> WriteBatchResult:
        """批量写入一个 WriteBatch。

        Args:
            batch: 已在内存中构建的写入 batch。

        Returns:
            批量写入结果；本端口不提供逐点热路径。
        """
        ...

    def flush(self) -> None:
        """刷新内部缓冲；具体实现负责处理资源边界。"""
        ...
