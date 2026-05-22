"""Models for protocol-agnostic subscription scans and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field

from tools.source_lab.access.common.access_model import AccessBatch, AccessMode, AccessRunSummary
from tools.source_lab.access.polling.model import CapacityMode, CapacityStatus


@dataclass(frozen=True, slots=True)
class SubscribeRunnerTrace:
    """One retained subscribe runner trace entry."""

    worker_index: int
    local_index: int
    global_index: int
    sequence: int
    value_count: int
    data_age_ms: float


@dataclass(frozen=True, slots=True)
class SubscribePeriodGapTrace:
    """One retained subscribe notify-period gap trace."""

    worker_index: int
    local_index: int
    global_index: int
    previous_notify_timestamp_ns: int
    notify_timestamp_ns: int
    period_ms: float


@dataclass(frozen=True, slots=True)
class SubscribeFlushLagTrace:
    """One retained subscribe callback-to-flush lag trace."""

    worker_index: int
    local_index: int
    global_index: int
    notify_timestamp_ns: int
    flush_timestamp_ns: int
    lag_ms: float


@dataclass(frozen=True, slots=True)
class SubscribeEndpointDispatchTrace:
    """One retained native-runner endpoint dispatch diagnostic."""

    worker_index: int
    local_index: int
    global_index: int
    notification_count: int
    run_iterate_count: int
    max_dispatch_gap_ms: float
    max_run_iterate_duration_ms: float
    revised_publishing_interval_ms: float
    revised_sampling_interval_ms: float


@dataclass(frozen=True, slots=True)
class SubscribeWorkerRawStats:
    """Raw metrics emitted by one subscription worker."""

    worker_index: int
    endpoint_count: int
    expected_monitored_items: int
    monitored_created: int
    monitored_failed: int
    batches: tuple[AccessBatch, ...]
    notification_count: int
    value_count: int
    bad_count: int
    missing_ts_count: int
    reserved_sequence_gap_count: int
    reserved_queue_overflow_count: int
    keepalive_count: int
    publish_timeout_count: int
    reconnect_count: int
    keepalive_miss_count: int = 0
    resubscribe_count: int = 0
    resubscribe_success_count: int = 0
    resubscribe_failure_count: int = 0
    unrecovered_endpoint_count: int = 0
    recovery_duration_ms: float = 0.0
    last_reconnect_reason: str = ""
    summary: AccessRunSummary | None = None
    top_data_age_traces: tuple[SubscribeRunnerTrace, ...] = ()
    endpoint_diagnostics: tuple[SubscribeEndpointDispatchTrace, ...] = ()
    runner_protocol_noise_count: int = 0
    runner_protocol_noise_samples: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SubscribeScanConfig:
    """Protocol-agnostic subscription scan configuration."""

    mode: CapacityMode
    protocol: str
    server_count_start: int
    server_count_step: int
    server_count_max: int
    process_count: int
    publishing_interval_ms: float
    sampling_interval_ms: float
    queue_size: int
    nominal_sample_hz: float | None = None
    source_update_hz_explicit: bool = False
    duration_s: float = 30.0
    read_timeout_s: float = 5.0
    source_update_enabled: bool = True
    source_update_hz: float = 10.0
    startup_stagger_ms: int = 0
    reconnect_stagger_ms: int = 0
    monitored_item_batch_size: int = 100
    monitored_item_batch_gap_ms: int = 0
    fail_confirm_runs: int = 1
    accept_flaky_as_pass: bool = False
    stop_ramp_on_first_fail: bool = True
    progress_enabled: bool = True
    progress_interval_s: float = 5.0
    runner_trace_enabled: bool = False
    runner_trace_top_n: int = 20
    fleet_startup_timeout_s: float = 180.0
    fleet_stop_grace_s: float = 0.2
    min_expected_point_count: int = 300
    max_expected_point_count: int = 500
    missing_timestamp_fail_count: int = 0
    data_period_max_tolerance_ratio: float = 0.2
    publish_gap_p95_limit_ms: float | None = None
    publish_gap_p99_limit_ms: float | None = None
    data_age_p95_limit_ms: float | None = None
    data_age_p99_limit_ms: float | None = None

    def __post_init__(self) -> None:
        """Validate numeric subscription scan settings."""

        if self.server_count_start <= 0 or self.server_count_step <= 0:
            raise ValueError("server_count_start and server_count_step must be greater than 0")
        if self.server_count_max < self.server_count_start:
            raise ValueError("server_count_max must be greater than or equal to server_count_start")
        if self.process_count <= 0:
            raise ValueError("process_count must be greater than 0")
        if self.publishing_interval_ms <= 0 or self.sampling_interval_ms <= 0:
            raise ValueError("publishing_interval_ms and sampling_interval_ms must be greater than 0")
        if self.queue_size <= 0:
            raise ValueError("queue_size must be greater than 0")
        if self.duration_s <= 0 or self.read_timeout_s <= 0:
            raise ValueError("duration_s and read_timeout_s must be greater than 0")
        if self.source_update_enabled and self.source_update_hz <= 0:
            raise ValueError("source_update_hz must be greater than 0 when source updates are enabled")
        if self.startup_stagger_ms < 0 or self.reconnect_stagger_ms < 0:
            raise ValueError("stagger values must be non-negative")
        if self.monitored_item_batch_size <= 0 or self.monitored_item_batch_gap_ms < 0:
            raise ValueError("invalid monitored-item batch settings")
        if self.fail_confirm_runs <= 0:
            raise ValueError("fail_confirm_runs must be greater than 0")
        if self.progress_interval_s <= 0:
            raise ValueError("progress_interval_s must be greater than 0")
        if self.runner_trace_top_n <= 0:
            raise ValueError("runner_trace_top_n must be greater than 0")
        if self.fleet_startup_timeout_s <= 0 or self.fleet_stop_grace_s < 0:
            raise ValueError("invalid fleet timing config")
        if self.min_expected_point_count <= 0 or self.max_expected_point_count < self.min_expected_point_count:
            raise ValueError("invalid expected point count range")
        if self.missing_timestamp_fail_count < 0:
            raise ValueError("missing_timestamp_fail_count must be non-negative")
        if self.data_period_max_tolerance_ratio < 0:
            raise ValueError("data_period_max_tolerance_ratio must be non-negative")


@dataclass(frozen=True, slots=True)
class SubscribeLevelMetrics:
    """Aggregate subscription metrics for one executed level."""

    server_count: int
    process_count: int
    publishing_interval_ms: float
    sampling_interval_ms: float
    effective_source_update_hz: float
    queue_size: int
    expected_monitored_items: int
    monitored_created: int
    monitored_failed: int
    notification_count: int
    value_count: int
    bad_count: int
    missing_ts_count: int
    reserved_sequence_gap_count: int
    reserved_queue_overflow_count: int
    keepalive_count: int
    publish_timeout_count: int
    reconnect_count: int
    notification_rate: float
    value_rate: float
    publish_gap_mean_ms: float
    publish_gap_p95_ms: float
    publish_gap_p99_ms: float
    publish_gap_max_ms: float
    data_age_mean_ms: float
    data_age_p95_ms: float
    data_age_p99_ms: float
    data_age_max_ms: float
    data_period_samples: int
    data_period_mean_ms: float
    data_period_p95_ms: float
    data_period_max_ms: float
    allowed_data_period_max_ms: float
    passed: bool
    failure_reason: str
    keepalive_miss_count: int = 0
    resubscribe_count: int = 0
    resubscribe_success_count: int = 0
    resubscribe_failure_count: int = 0
    unrecovered_endpoint_count: int = 0
    recovery_duration_ms: float = 0.0
    last_reconnect_reason: str = ""
    response_period_samples: int = 0
    response_period_mean_ms: float = 0.0
    response_period_p95_ms: float = 0.0
    response_period_max_ms: float = 0.0
    allowed_response_period_max_ms: float = 0.0
    response_period_observable: bool = True
    response_period_kind: str = "data_notify_proxy"
    points_per_server: int = 0
    point_total: int = 0
    expected_notification_count: int = 0
    expected_value_count: int = 0
    value_delivery_ratio: float = 0.0
    value_missing_count: int = 0
    source_period_p95_ms: float = 0.0
    source_period_max_ms: float = 0.0
    recv_period_p95_ms: float = 0.0
    recv_period_max_ms: float = 0.0
    callback_to_flush_lag_p95_ms: float = 0.0
    callback_to_flush_lag_max_ms: float = 0.0
    dispatch_gap_max_ms: float = 0.0
    run_iterate_duration_max_ms: float = 0.0
    warnings: tuple[str, ...] = ()
    batches: tuple[AccessBatch, ...] = ()
    summaries: tuple[AccessRunSummary, ...] = ()
    top_data_age_traces: tuple[SubscribeRunnerTrace, ...] = ()
    top_period_gap_traces: tuple[SubscribePeriodGapTrace, ...] = ()
    top_data_period_gap_traces: tuple[SubscribePeriodGapTrace, ...] = ()
    top_flush_lag_traces: tuple[SubscribeFlushLagTrace, ...] = ()
    top_dispatch_gap_traces: tuple[SubscribeEndpointDispatchTrace, ...] = ()
    runner_protocol_noise_count: int = 0
    runner_protocol_noise_samples: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SubscribeLevelResult:
    """Final level result after optional subscription fail confirmation."""

    primary: SubscribeLevelMetrics
    attempts: tuple[SubscribeLevelMetrics, ...]
    final_status: CapacityStatus
    final_reason: str

    @property
    def final_metrics(self) -> SubscribeLevelMetrics:
        """Return the metrics object used for final status and table output."""

        return self.attempts[-1] if self.attempts else self.primary


@dataclass(frozen=True, slots=True)
class SubscribeScanResult:
    """Final subscription scan result across all executed levels."""

    config: SubscribeScanConfig
    levels: tuple[SubscribeLevelResult, ...]

    @property
    def has_accepted_level(self) -> bool:
        """Return whether at least one level is accepted by config policy."""

        accepted_statuses = {CapacityStatus.PASS}
        if self.config.accept_flaky_as_pass:
            accepted_statuses.add(CapacityStatus.FLAKY)
        return any(level.final_status in accepted_statuses for level in self.levels)


@dataclass(frozen=True, slots=True)
class SubscribeReportRow:
    """One normalized row written by the subscribe capacity CLI/report path."""

    process_count: int
    server_count: int
    protocol: str
    access_mode: str = AccessMode.SUBSCRIBE.value
    publishing_interval_ms: float = 0.0
    sampling_interval_ms: float = 0.0
    effective_source_update_hz: float = 0.0
    queue_size: int = 0
    point_count: int = 0
    cpu_mean_pct: float = 0.0
    cpu_max_pct: float = 0.0
    rss_mb: float = 0.0
    notification_count: int = 0
    value_count: int = 0
    bad: int = 0
    missing_ts: int = 0
    reserved_sequence_gap_count: int = 0
    reserved_queue_overflow_count: int = 0
    keepalive: int = 0
    reconnect: int = 0
    publish_gap_mean_ms: float = 0.0
    publish_gap_p95_ms: float = 0.0
    publish_gap_p99_ms: float = 0.0
    publish_gap_max_ms: float = 0.0
    data_age_mean_ms: float = 0.0
    data_age_p95_ms: float = 0.0
    data_age_p99_ms: float = 0.0
    data_age_max_ms: float = 0.0
    data_period_p95_ms: float = 0.0
    data_period_max_ms: float = 0.0
    status: str = CapacityStatus.SKIP.value
    reason: str = ""
    warnings: str = ""


@dataclass(slots=True)
class _GroupedBatches:
    """Mutable helper used during subscription metric aggregation."""

    values: list[AccessBatch] = field(default_factory=list)
