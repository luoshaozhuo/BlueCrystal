"""Worker 执行状态的线程安全聚合器。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from .models import WorkerStatus


@dataclass(slots=True)
class _WorkerState:
    """仅在锁内读写的 Worker 当前状态。"""

    in_flight: int = 0
    last_result: str | None = None
    last_finished_at: datetime | None = None


class WorkerStatusTracker:
    """聚合 Worker 状态；不保存请求、身份、异常文本或业务载荷。"""

    def __init__(self) -> None:
        """创建空状态容器。"""
        self._lock = Lock()
        self._workers: dict[str, _WorkerState] = {}

    def worker_started(self, operation: str) -> None:
        """登记一次 Worker 开始执行。"""
        with self._lock:
            self._workers.setdefault(operation, _WorkerState()).in_flight += 1

    def worker_finished(self, operation: str, result: str) -> None:
        """登记一次 Worker 结束执行，并更新最近结果。

        Raises:
            ValueError: 结果类型不受支持。
            RuntimeError: 当前 operation 没有对应的运行中执行。
        """
        with self._lock:
            if result not in {"success", "failure", "cancelled"}:
                raise ValueError(f"unsupported worker result: {result!r}")
            state = self._workers.get(operation)
            if state is None or state.in_flight == 0:
                raise RuntimeError(
                    f"worker {operation!r} finished without matching start"
                )
            state.in_flight -= 1
            state.last_result = result
            state.last_finished_at = datetime.now(timezone.utc)

    def worker_statuses(self) -> tuple[WorkerStatus, ...]:
        """返回按 operation 稳定排序的 Worker 状态快照。"""
        with self._lock:
            return tuple(
                WorkerStatus(
                    operation=operation,
                    in_flight=state.in_flight,
                    last_result=state.last_result,
                    last_finished_at=state.last_finished_at,
                )
                for operation, state in sorted(self._workers.items())
            )
