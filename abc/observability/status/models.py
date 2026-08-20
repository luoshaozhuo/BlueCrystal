"""当前运行状态数据模型。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RuntimeState(StrEnum):
    """运行实例状态。"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"


class TaskScheduleState(StrEnum):
    """任务调度状态。"""

    UNKNOWN = "unknown"
    SCHEDULED = "scheduled"
    PAUSED = "paused"
    REMOVED = "removed"


class TaskExecutionState(StrEnum):
    """任务执行状态。"""

    IDLE = "idle"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    """可序列化异常摘要。"""

    error_type: str
    message: str

    @classmethod
    def from_exception(cls, exc: BaseException) -> ErrorInfo:
        """从异常创建错误摘要。"""
        return cls(type(exc).__qualname__, str(exc))


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    """运行实例当前状态。"""

    runtime_id: str | None = None
    node_id: str | None = None
    state: RuntimeState = RuntimeState.STOPPED
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error: ErrorInfo | None = None


@dataclass(frozen=True, slots=True)
class SchedulerStatus:
    """调度器当前状态。"""

    running: bool = False
    last_started_at: datetime | None = None
    last_stopped_at: datetime | None = None
    misfire_count: int = 0
    max_instances_skip_count: int = 0
    last_issue_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class TaskStatus:
    """单个任务的当前调度与执行状态。"""

    task_id: int
    schedule_state: TaskScheduleState = TaskScheduleState.UNKNOWN
    execution_state: TaskExecutionState = TaskExecutionState.IDLE
    last_scheduled_at: datetime | None = None
    last_removed_at: datetime | None = None
    last_paused_at: datetime | None = None
    last_resumed_at: datetime | None = None
    last_run_requested_at: datetime | None = None
    last_started_at: datetime | None = None
    last_finished_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_cancelled_at: datetime | None = None
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    cancellation_count: int = 0
    misfire_count: int = 0
    max_instances_skip_count: int = 0
    last_duration_seconds: float | None = None
    last_error: ErrorInfo | None = None
