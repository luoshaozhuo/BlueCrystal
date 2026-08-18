"""进程内 Diagnostics Store."""

from __future__ import annotations

from threading import RLock

from ..models import RuntimeDiagnostic, SchedulerDiagnostic, TaskDiagnostic


class InMemoryDiagnosticStore:
    """线程安全的 P0 当前状态 Store."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._runtime: RuntimeDiagnostic | None = None
        self._scheduler: SchedulerDiagnostic | None = None
        self._tasks: dict[int, TaskDiagnostic] = {}

    def get_runtime(self) -> RuntimeDiagnostic | None:
        with self._lock:
            return self._runtime

    def set_runtime(self, diagnostic: RuntimeDiagnostic) -> None:
        with self._lock:
            self._runtime = diagnostic

    def get_scheduler(self) -> SchedulerDiagnostic | None:
        with self._lock:
            return self._scheduler

    def set_scheduler(self, diagnostic: SchedulerDiagnostic) -> None:
        with self._lock:
            self._scheduler = diagnostic

    def get_task(self, task_id: int) -> TaskDiagnostic | None:
        with self._lock:
            return self._tasks.get(task_id)

    def set_task(self, diagnostic: TaskDiagnostic) -> None:
        with self._lock:
            self._tasks[diagnostic.task_id] = diagnostic

    def list_tasks(self) -> tuple[TaskDiagnostic, ...]:
        with self._lock:
            return tuple(self._tasks[key] for key in sorted(self._tasks))

    def clear(self) -> None:
        with self._lock:
            self._runtime = None
            self._scheduler = None
            self._tasks.clear()
