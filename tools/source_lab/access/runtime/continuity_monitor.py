"""Continuity monitor for endpoint-level dynamic runtime validation."""

from __future__ import annotations

import threading
import time

from tools.source_lab.access.runtime.continuity_model import EndpointContinuityMetrics


class ContinuityMonitor:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._metrics: dict[str, EndpointContinuityMetrics] = {}
        self._started_ns: dict[str, int] = {}
        self._last_sample_ms: dict[str, float] = {}
        self._last_event_ms: dict[str, float] = {}
        self._tracked_unaffected_ops: dict[str, str] = {}

    def ensure_endpoint(
        self,
        endpoint_id: str,
        *,
        config_version: int,
        stagger_offset_ns: int,
        stagger_offset_changed: bool,
    ) -> None:
        with self._lock:
            metrics = self._metrics.setdefault(endpoint_id, EndpointContinuityMetrics())
            metrics.endpoint_config_version = config_version
            metrics.stagger_offset_changed = stagger_offset_changed
            metrics.stagger_offset_ns = stagger_offset_ns

    def bind_runtime(
        self,
        endpoint_id: str,
        *,
        runtime_backend: str,
        runner_handle_id: str | None,
        runner_pid: int | None = None,
        permission_status: str | None = None,
    ) -> None:
        with self._lock:
            metrics = self._metrics.setdefault(endpoint_id, EndpointContinuityMetrics())
            metrics.endpoint_runtime_backend = runtime_backend
            metrics.endpoint_runner_handle_id = runner_handle_id
            metrics.endpoint_runner_pid = runner_pid
            if permission_status is not None:
                metrics.endpoint_permission_status = permission_status

    def record_start(self, endpoint_id: str, *, config_version: int, stagger_offset_ns: int) -> None:
        with self._lock:
            metrics = self._metrics.setdefault(endpoint_id, EndpointContinuityMetrics())
            metrics.endpoint_restart_count += 1
            metrics.endpoint_stream_restart_count += 1
            metrics.endpoint_config_version = config_version
            metrics.stagger_offset_ns = stagger_offset_ns
            self._started_ns[endpoint_id] = time.monotonic_ns()

    def record_stop(self, endpoint_id: str) -> None:
        with self._lock:
            started_ns = self._started_ns.get(endpoint_id)
            if started_ns is None:
                return
            uptime_ms = (time.monotonic_ns() - started_ns) / 1_000_000.0
            self._metrics.setdefault(endpoint_id, EndpointContinuityMetrics()).endpoint_uptime_ms += uptime_ms
            self._started_ns.pop(endpoint_id, None)
            self._last_sample_ms.pop(endpoint_id, None)
            self._last_event_ms.pop(endpoint_id, None)

    def record_pause(self, endpoint_id: str) -> None:
        with self._lock:
            metrics = self._metrics.setdefault(endpoint_id, EndpointContinuityMetrics())
            metrics.endpoint_pause_count += 1

    def record_expected_tick(self, endpoint_id: str) -> None:
        with self._lock:
            metrics = self._metrics.setdefault(endpoint_id, EndpointContinuityMetrics())
            metrics.endpoint_expected_samples += 1

    def record_stream_drop(self, endpoint_id: str) -> None:
        with self._lock:
            metrics = self._metrics.setdefault(endpoint_id, EndpointContinuityMetrics())
            metrics.endpoint_stream_drop_count += 1

    def record_sample(
        self,
        endpoint_id: str,
        *,
        timestamp_ms: float,
        expected_period_ms: float,
        successful: bool,
    ) -> None:
        with self._lock:
            metrics = self._metrics.setdefault(endpoint_id, EndpointContinuityMetrics())
            if not successful:
                metrics.endpoint_missed_tick_count += 1
                return

            last_sample_ms = self._last_sample_ms.get(endpoint_id)
            if last_sample_ms is not None:
                gap_ms = timestamp_ms - last_sample_ms
                if gap_ms > expected_period_ms * 1.5:
                    metrics.endpoint_gap_count += 1
                    metrics.endpoint_max_gap_ms = max(metrics.endpoint_max_gap_ms, gap_ms)
                    metrics.endpoint_missed_tick_count += max(
                        0,
                        int(round(gap_ms / max(1.0, expected_period_ms))) - 1,
                    )
            self._last_sample_ms[endpoint_id] = timestamp_ms
            metrics.endpoint_actual_samples += 1
            metrics.endpoint_sample_count += 1

            if endpoint_id in self._tracked_unaffected_ops:
                metrics.unaffected_endpoint_samples += 1
                metrics.unaffected_endpoint_continuity_breaks = metrics.endpoint_gap_count

    def record_event(
        self,
        endpoint_id: str,
        *,
        timestamp_ms: float,
        expected_period_ms: float,
        successful: bool,
    ) -> None:
        with self._lock:
            metrics = self._metrics.setdefault(endpoint_id, EndpointContinuityMetrics())
            if not successful:
                metrics.endpoint_stream_drop_count += 1
                return

            last_event_ms = self._last_event_ms.get(endpoint_id)
            if last_event_ms is not None:
                gap_ms = timestamp_ms - last_event_ms
                if gap_ms > expected_period_ms * 1.5:
                    metrics.endpoint_callback_gap_count += 1
                    metrics.endpoint_callback_max_gap_ms = max(
                        metrics.endpoint_callback_max_gap_ms,
                        gap_ms,
                    )
            self._last_event_ms[endpoint_id] = timestamp_ms
            metrics.endpoint_last_event_at = time.strftime(
                "%Y-%m-%dT%H:%M:%S",
                time.gmtime(timestamp_ms / 1000.0),
            )
            metrics.endpoint_event_count += 1
            metrics.endpoint_sample_count += 1
            metrics.endpoint_actual_samples += 1

            if endpoint_id in self._tracked_unaffected_ops:
                metrics.unaffected_endpoint_samples += 1
                metrics.unaffected_endpoint_continuity_breaks = (
                    metrics.endpoint_gap_count + metrics.endpoint_callback_gap_count
                )

    def tag_operation(
        self,
        *,
        operation_id: str,
        result: str,
        affected_endpoints: tuple[str, ...],
        unaffected_endpoints: tuple[str, ...],
    ) -> None:
        with self._lock:
            for endpoint_id in affected_endpoints + unaffected_endpoints:
                metrics = self._metrics.setdefault(endpoint_id, EndpointContinuityMetrics())
                metrics.dynamic_operation_id = operation_id
                metrics.dynamic_operation_result = result
            for endpoint_id in unaffected_endpoints:
                self._tracked_unaffected_ops[endpoint_id] = operation_id
                metrics = self._metrics.setdefault(endpoint_id, EndpointContinuityMetrics())
                metrics.unaffected_endpoint_continuity_breaks = metrics.endpoint_gap_count

    def snapshot(self) -> dict[str, EndpointContinuityMetrics]:
        with self._lock:
            return {
                endpoint_id: EndpointContinuityMetrics.from_dict(metrics.to_dict())
                for endpoint_id, metrics in self._metrics.items()
            }

    def load_snapshot(self, data: dict[str, dict[str, object]]) -> None:
        with self._lock:
            self._metrics = {
                endpoint_id: EndpointContinuityMetrics.from_dict(payload)
                for endpoint_id, payload in data.items()
            }
