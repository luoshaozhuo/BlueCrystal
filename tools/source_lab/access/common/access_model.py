"""接入模式数据模型，跨 read-once/polling/subscribe 共享。

负责：定义 AccessMode、AccessBatch、AccessRunSummary 等基础类型。
不负责：协议特定逻辑、扫描执行。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AccessMode(str, Enum):
    """Supported source access modes."""

    READ_ONCE = "read_once"
    POLLING = "polling"
    SUBSCRIBE = "subscribe"


@dataclass(frozen=True, slots=True)
class AccessBatch:
    """One normalized access result batch.

    Args:
        endpoint_id: Stable endpoint identifier.
        profile_id: Stable profile identifier for field-backed sources.
        protocol: Normalized protocol label.
        access_mode: Access mode that produced the batch.
        worker_index: Zero-based worker slot.
        local_index: Zero-based endpoint index inside one worker.
        global_index: Zero-based endpoint index across the whole level.
        batch_index: Zero-based emitted batch index within the worker.
        sequence: Source-mode-specific sequence number.
        scheduled_ns: Scheduled execution timestamp when relevant.
        started_ns: Start timestamp when relevant.
        received_ns: Batch receive timestamp in nanoseconds. For subscribe this
            remains the legacy receive/flush timeline and may come from a
            different clock domain than ``notify_timestamp_ns``.
        source_timestamp_s: Source timestamp in Unix seconds, when available.
        server_timestamp_s: Server timestamp in Unix seconds, when available.
        value_count: Number of values observed in the batch.
        expected_count: Expected value count for the endpoint.
        bad_count: Count of bad values in the batch.
        missing_timestamp_count: Count of values missing source or server timestamps.
        error_code: Stable error code, when the batch is not fully successful.
        data_age_ms: Age of the newest source/server timestamp in milliseconds,
            measured at receive time when available.
        period_ms: Observed period or publish gap in milliseconds, when available.
        notify_timestamp_ns: Native notify-arrival timestamp in monotonic
            nanoseconds when available. Subscribe metrics prefer this over
            ``received_ns`` so callback timing is not distorted by later flush
            or stdout delays.
        flush_timestamp_ns: Native NOTIFY-line flush timestamp in monotonic
            nanoseconds when available. Subscribe callback-to-flush lag uses
            this together with ``notify_timestamp_ns``.
    """

    endpoint_id: str
    profile_id: str
    protocol: str
    access_mode: AccessMode
    worker_index: int
    local_index: int
    global_index: int
    batch_index: int
    sequence: int
    scheduled_ns: int | None
    started_ns: int | None
    received_ns: int
    source_timestamp_s: float | None
    server_timestamp_s: float | None
    value_count: int
    expected_count: int
    bad_count: int
    missing_timestamp_count: int
    error_code: str | None
    data_age_ms: float | None
    period_ms: float | None
    notify_timestamp_ns: int | None = None
    flush_timestamp_ns: int | None = None


@dataclass(frozen=True, slots=True)
class AccessRunSummary:
    """One normalized access-mode worker summary."""

    access_mode: AccessMode
    worker_index: int
    endpoint_count: int
    expected_point_count: int
    batch_count: int
    value_count: int
    bad_count: int
    missing_timestamp_count: int
    error_count: int
