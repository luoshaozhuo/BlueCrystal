"""Trace 策略配置模型。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TracePolicy:
    """统一定义常规采样、错误去重和定向 Trace 策略。"""

    enabled: bool = True
    normal_sample_rate: float = 0.001
    error_dedup_ttl_seconds: float = 600.0
    error_dedup_max_entries: int = 4096
    slow_threshold_seconds: float = 5.0
    trace_http: bool = True
    trace_scheduler: bool = True
    trace_task: bool = True
    trace_protocol: bool = False
    traced_task_ids: frozenset[int] = field(default_factory=frozenset)
    traced_connection_ids: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not 0 <= self.normal_sample_rate <= 1:
            raise ValueError("normal_sample_rate must be in [0,1]")
        if self.error_dedup_ttl_seconds <= 0:
            raise ValueError("error_dedup_ttl_seconds must be > 0")
        if self.error_dedup_max_entries <= 0:
            raise ValueError("error_dedup_max_entries must be > 0")
