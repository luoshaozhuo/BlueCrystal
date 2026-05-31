"""任务状态管理。

定义和追踪调度任务的执行状态（pending/running/success/failed）。
"""

from __future__ import annotations

from enum import StrEnum


class JobStatus(StrEnum):
    """单个调度源任务的生命周期状态。"""

    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
