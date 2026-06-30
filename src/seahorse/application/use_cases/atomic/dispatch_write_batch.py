"""WriteBatch 分发用例。

本用例只依赖 StarfishWriterPort，负责把已生成的 WriteBatch 交给写入端口。
writer 抛出的异常会收敛成稳定 WriteBatchResult，避免基础设施异常穿透
application runtime。
"""

from __future__ import annotations

from dataclasses import dataclass

from seahorse.application.ports.starfish_writer_port import StarfishWriterPort
from seahorse.domain.runtime_contract import WriteBatch, WriteBatchResult, WriteFailure


@dataclass(frozen=True, slots=True)
class DispatchWriteBatchUseCase:
    """批量分发 WriteBatch 的应用用例。"""

    writer: StarfishWriterPort

    def execute(self, batch: WriteBatch) -> WriteBatchResult:
        """分发一个 WriteBatch。

        Args:
            batch: 已生成的写入 batch。

        Returns:
            writer 返回的 WriteBatchResult；当 writer 抛出异常时，返回每个
            item 对应的 retryable failure。
        """
        try:
            return self.writer.write_batch(batch)
        except Exception as exc:
            return WriteBatchResult(
                batch_id=batch.batch_id,
                accepted_count=0,
                failures=tuple(
                    WriteFailure(
                        target=item.target,
                        reason=f"writer dispatch failed: {exc}",
                        retryable=True,
                    )
                    for item in batch.items
                ),
            )


__all__ = ["DispatchWriteBatchUseCase"]
