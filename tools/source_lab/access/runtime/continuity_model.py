"""Continuity metric models for endpoint-level runtime validation."""

from __future__ import annotations

from dataclasses import dataclass


def _as_float(value: object, default: float) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _as_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


@dataclass(slots=True)
class EndpointContinuityMetrics:
    """Endpoint 连续性指标数据模型。

    记录单个 endpoint 在运行时采集周期中的连续性统计信息，
    包括采样次数、间隔异常、丢包、重启次数、权限状态等。
    支持 to_dict/from_dict 序列化，用于持久化快照和恢复。

    不负责：连续性判定阈值（由 ContinuityMonitor 根据业务规则计算）。
    """
    endpoint_uptime_ms: float = 0.0
    endpoint_gap_count: int = 0
    endpoint_max_gap_ms: float = 0.0
    endpoint_expected_samples: int = 0
    endpoint_actual_samples: int = 0
    endpoint_missed_tick_count: int = 0
    endpoint_restart_count: int = 0
    endpoint_pause_count: int = 0
    endpoint_config_version: int = 1
    endpoint_last_event_at: str | None = None
    endpoint_event_count: int = 0
    endpoint_sample_count: int = 0
    endpoint_callback_gap_count: int = 0
    endpoint_callback_max_gap_ms: float = 0.0
    endpoint_stream_restart_count: int = 0
    endpoint_stream_drop_count: int = 0
    endpoint_permission_status: str | None = None
    endpoint_runtime_backend: str | None = None
    endpoint_runner_pid: int | None = None
    endpoint_runner_handle_id: str | None = None
    stagger_offset_ns: int = 0
    stagger_offset_changed: bool = False
    unaffected_endpoint_samples: int = 0
    unaffected_endpoint_continuity_breaks: int = 0
    dynamic_operation_id: str | None = None
    dynamic_operation_result: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "endpoint_uptime_ms": self.endpoint_uptime_ms,
            "endpoint_gap_count": self.endpoint_gap_count,
            "endpoint_max_gap_ms": self.endpoint_max_gap_ms,
            "endpoint_expected_samples": self.endpoint_expected_samples,
            "endpoint_actual_samples": self.endpoint_actual_samples,
            "endpoint_missed_tick_count": self.endpoint_missed_tick_count,
            "endpoint_restart_count": self.endpoint_restart_count,
            "endpoint_pause_count": self.endpoint_pause_count,
            "endpoint_config_version": self.endpoint_config_version,
            "endpoint_last_event_at": self.endpoint_last_event_at,
            "endpoint_event_count": self.endpoint_event_count,
            "endpoint_sample_count": self.endpoint_sample_count,
            "endpoint_callback_gap_count": self.endpoint_callback_gap_count,
            "endpoint_callback_max_gap_ms": self.endpoint_callback_max_gap_ms,
            "endpoint_stream_restart_count": self.endpoint_stream_restart_count,
            "endpoint_stream_drop_count": self.endpoint_stream_drop_count,
            "endpoint_permission_status": self.endpoint_permission_status,
            "endpoint_runtime_backend": self.endpoint_runtime_backend,
            "endpoint_runner_pid": self.endpoint_runner_pid,
            "endpoint_runner_handle_id": self.endpoint_runner_handle_id,
            "stagger_offset_ns": self.stagger_offset_ns,
            "stagger_offset_changed": self.stagger_offset_changed,
            "unaffected_endpoint_samples": self.unaffected_endpoint_samples,
            "unaffected_endpoint_continuity_breaks": self.unaffected_endpoint_continuity_breaks,
            "dynamic_operation_id": self.dynamic_operation_id,
            "dynamic_operation_result": self.dynamic_operation_result,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "EndpointContinuityMetrics":
        return cls(
            endpoint_uptime_ms=_as_float(data.get("endpoint_uptime_ms", 0.0), 0.0),
            endpoint_gap_count=_as_int(data.get("endpoint_gap_count", 0), 0),
            endpoint_max_gap_ms=_as_float(data.get("endpoint_max_gap_ms", 0.0), 0.0),
            endpoint_expected_samples=_as_int(data.get("endpoint_expected_samples", 0), 0),
            endpoint_actual_samples=_as_int(data.get("endpoint_actual_samples", 0), 0),
            endpoint_missed_tick_count=_as_int(data.get("endpoint_missed_tick_count", 0), 0),
            endpoint_restart_count=_as_int(data.get("endpoint_restart_count", 0), 0),
            endpoint_pause_count=_as_int(data.get("endpoint_pause_count", 0), 0),
            endpoint_config_version=_as_int(data.get("endpoint_config_version", 1), 1),
            endpoint_last_event_at=(
                str(data["endpoint_last_event_at"])
                if data.get("endpoint_last_event_at") is not None
                else None
            ),
            endpoint_event_count=_as_int(data.get("endpoint_event_count", 0), 0),
            endpoint_sample_count=_as_int(data.get("endpoint_sample_count", 0), 0),
            endpoint_callback_gap_count=_as_int(data.get("endpoint_callback_gap_count", 0), 0),
            endpoint_callback_max_gap_ms=_as_float(
                data.get("endpoint_callback_max_gap_ms", 0.0),
                0.0,
            ),
            endpoint_stream_restart_count=_as_int(data.get("endpoint_stream_restart_count", 0), 0),
            endpoint_stream_drop_count=_as_int(data.get("endpoint_stream_drop_count", 0), 0),
            endpoint_permission_status=(
                str(data["endpoint_permission_status"])
                if data.get("endpoint_permission_status") is not None
                else None
            ),
            endpoint_runtime_backend=(
                str(data["endpoint_runtime_backend"])
                if data.get("endpoint_runtime_backend") is not None
                else None
            ),
            endpoint_runner_pid=(
                _as_int(data["endpoint_runner_pid"], 0)
                if data.get("endpoint_runner_pid") is not None
                else None
            ),
            endpoint_runner_handle_id=(
                str(data["endpoint_runner_handle_id"])
                if data.get("endpoint_runner_handle_id") is not None
                else None
            ),
            stagger_offset_ns=_as_int(data.get("stagger_offset_ns", 0), 0),
            stagger_offset_changed=bool(data.get("stagger_offset_changed", False)),
            unaffected_endpoint_samples=_as_int(data.get("unaffected_endpoint_samples", 0), 0),
            unaffected_endpoint_continuity_breaks=_as_int(
                data.get("unaffected_endpoint_continuity_breaks", 0)
                ,
                0,
            ),
            dynamic_operation_id=(
                str(data["dynamic_operation_id"])
                if data.get("dynamic_operation_id") is not None
                else None
            ),
            dynamic_operation_result=(
                str(data["dynamic_operation_result"])
                if data.get("dynamic_operation_result") is not None
                else None
            ),
        )
