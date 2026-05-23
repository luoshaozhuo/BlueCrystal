"""source latest-state cache 端口定义。

本模块定义 usecase / role 依赖的 latest-state cache 写入接口。

设计约定：
- latest-state cache 保存一个 LD/source 的当前状态视图；
- cache 对外应使用 batch 级统一时间表达 LD 状态时间；
- value 级 source/server timestamp 只作为内部版本、乱序保护和诊断信息；
- update() 只负责写入一批值并刷新 LD 状态；
- mark_alive() 只刷新链路活性，不改变点位值；
- mark_unavailable() 用于将 LD 状态标记为 STALE / OFFLINE / ERROR 等，不删除最后有效值。
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch


class SourceStateCacheError(RuntimeError):
    """Base error raised by latest-state cache adapters."""


class SourceStateCacheWriteError(SourceStateCacheError):
    """Raised when a latest-state cache write cannot be completed safely.

    Args:
        error_code: Stable machine-readable error code.
        message: Optional human-readable detail for logs and diagnostics.
        retryable: Whether callers may retry the failed operation later.
    """

    def __init__(
        self,
        error_code: str,
        message: str | None = None,
        *,
        retryable: bool = True,
    ) -> None:
        detail = message or error_code
        super().__init__(detail)
        self.error_code = error_code
        self.retryable = retryable


class SourceStateCachePort(Protocol):
    """更新 source latest-state cache。"""

    def update(
        self,
        *,
        ld_name: str,
        batch: AcquiredNodeStateBatch,
    ) -> int:
        """按 batch 刷新一个 LD/source 的 latest-state。

        语义：
        - batch.values 中的点位值用于覆盖对应 node_key；
        - LD 级状态时间使用 batch.batch_observed_at；
        - 点位级 source/server timestamp 可用于乱序保护；
        - 返回实际更新的点位数量。
        """

    def mark_alive(
        self,
        *,
        ld_name: str,
        observed_at: datetime,
    ) -> None:
        """标记一个 LD/source 的采集链路仍然存活。

        只更新 last_alive_at / availability_status 等链路状态，
        不改变点位值。
        """

    def mark_unavailable(
        self,
        *,
        ld_name: str,
        status: str,
        observed_at: datetime,
        reason: str | None = None,
    ) -> None:
        """标记一个 LD/source 当前不可用或状态降级。

        status 建议使用：
        - UNKNOWN
        - STALE
        - OFFLINE
        - ERROR

        注意：
        - 不删除最后一次有效点位值；
        - publish/snapshot 后续必须读取 status，不能把旧值当作 VALID 当前值。
        """
