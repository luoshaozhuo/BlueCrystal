"""Starfish writer 内存 backend。

本 backend 只在内存中记录 batch 历史并返回稳定 WriteBatchResult，服务
Seahorse runtime dispatch 链路测试；不连接外部 writer。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from seahorse.domain.runtime_contract import WriteBatch, WriteBatchResult, WriteFailure, WriteTarget


@dataclass(slots=True)
class InMemoryStarfishWriterBackend:
    """可配置部分失败的内存 Starfish writer backend。"""

    fail_server_ids: frozenset[str] = frozenset()
    fail_endpoint_ids: frozenset[str] = frozenset()
    fail_field_ids: frozenset[str] = frozenset()
    fail_point_ids: frozenset[str] = frozenset()
    exception_batch_ids: frozenset[str] = frozenset()
    history: list[WriteBatch] = field(default_factory=list)

    def dispatch_batch(self, batch: WriteBatch) -> WriteBatchResult:
        """记录 batch 并返回配置化分发结果。

        Args:
            batch: 待分发的 WriteBatch。

        Returns:
            稳定 WriteBatchResult。命中失败配置的 item 会生成 failure，
            未命中的 item 计入 accepted_count。

        Raises:
            RuntimeError: batch_id 命中 exception_batch_ids 时，用于验证用例
                异常收敛。
        """
        if batch.batch_id in self.exception_batch_ids:
            raise RuntimeError(f"writer backend rejected batch {batch.batch_id}")

        self.history.append(batch)
        failures = tuple(
            WriteFailure(
                target=item.target,
                reason=f"configured writer failure for {item.target.stable_key()}",
                retryable=True,
            )
            for item in batch.items
            if self._matches_failure(item.target)
        )
        return WriteBatchResult(
            batch_id=batch.batch_id,
            accepted_count=len(batch.items) - len(failures),
            failures=failures,
        )

    def close(self) -> None:
        """内存 backend 无资源需要释放。"""
        return None

    def _matches_failure(self, target: WriteTarget) -> bool:
        """判断 target 是否命中配置化失败条件。"""
        return (
            target.server_id in self.fail_server_ids
            or target.endpoint_id in self.fail_endpoint_ids
            or target.point_id in self.fail_point_ids
            or target.field_name in self.fail_field_ids
            or target.stable_key() in self.fail_field_ids
        )


__all__ = ["InMemoryStarfishWriterBackend"]
