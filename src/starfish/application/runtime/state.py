"""RuntimeState 领域状态模型。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeState:
    """DriverInstance 的可观测运行状态切片。

    Attributes:
        instance_id: DriverInstance id。
        status: CREATED / INIT / RUNNING / DEGRADED / STOPPED。
        last_error: 最近一次错误摘要；无错误时为 None。
        health_score: 轻量健康评分，范围由 runtime 维护为 0.0 到 1.0。
    """

    instance_id: str
    status: str
    last_error: str | None
    health_score: float


__all__ = ["RuntimeState"]
