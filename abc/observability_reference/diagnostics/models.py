"""Diagnostics 当前状态模型."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RuntimeDiagnosticState(StrEnum):
    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class TaskScheduleState(StrEnum):
    UNKNOWN = "unknown"
    SCHEDULED = "scheduled"
    PAUSED = "paused"
    REMOVED = "removed"


class TaskExecutionState(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class DiagnosticError:
    type: str
    message: str

    @classmethod
    def from_exception(cls, exception: BaseException) -> "DiagnosticError":
        return cls(
            type=type(exception).__name__,
            message=_bounded_text(str(exception)),
        )


@dataclass(frozen=True, slots=True)
class RuntimeDiagnostic:
    runtime_id: str | None = None
    node_id: str | None = None
    state: RuntimeDiagnosticState = RuntimeDiagnosticState.UNKNOWN
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error: DiagnosticError | None = None


@dataclass(frozen=True, slots=True)
class SchedulerDiagnostic:
    running: bool = False
    last_started_at: datetime | None = None
    last_stopped_at: datetime | None = None
    misfire_count: int = 0
    max_instances_skip_count: int = 0
    last_issue_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class TaskDiagnostic:
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
    last_error: DiagnosticError | None = None
    last_missed_scheduled_at: datetime | None = None


_MAX_ERROR_LENGTH = 4096


def _bounded_text(value: str) -> str:
    if len(value) <= _MAX_ERROR_LENGTH:
        return value
    return value[:_MAX_ERROR_LENGTH] + "…<truncated>"
