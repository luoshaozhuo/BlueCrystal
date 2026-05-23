# mypy: disable-error-code=import-untyped
"""Data models for protocol-agnostic capacity scans and standalone field probes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec  # type: ignore[import-untyped]


class CapacityMode(str, Enum):
    """Capacity scanning mode."""

    SIMULATOR = "simulator"
    FIELD = "field"


class CapacityStatus(str, Enum):
    """Result status for one capacity or probe row."""

    PASS = "PASS"
    FLAKY = "FLAKY"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass(frozen=True, slots=True)
class PeriodGap:
    """One adjacent response-timestamp period gap."""

    reader_index: int
    gap_index: int
    previous_timestamp_s: float
    current_timestamp_s: float
    period_ms: float


@dataclass(frozen=True, slots=True)
class ResponsePeriodStats:
    """Aggregate response-period metrics from all readers."""

    samples: int
    mean_ms: float
    p95_ms: float
    max_ms: float
    mean_abs_error_ms: float
    worst_gap: PeriodGap | None = None
    top_gaps: tuple[PeriodGap, ...] = ()


@dataclass(frozen=True, slots=True)
class TickResult:
    """Normalized one-shot read result used by metrics and field probes."""

    ok: bool
    value_count: int
    elapsed_ms: float
    response_timestamp_s: float | None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class CapacityLevelMetrics:
    """Measured metrics for one ``(server_count, hz)`` level."""

    server_count: int
    target_hz: float
    target_period_ms: float
    allowed_period_max_ms: float
    allowed_period_mean_abs_error_ms: float
    read_errors: int
    batch_mismatches: int
    missing_response_timestamps: int
    period_samples: int
    period_mean_ms: float
    period_p95_ms: float
    period_max_ms: float
    period_mean_abs_error_ms: float
    missed_ticks: int
    runner_max_lag_ms: float
    runner_max_read_ms: float
    worker_conc_sum: int
    worker_conc_max: int
    worker_conc_by_worker: tuple[int, ...]
    value_count_ok: bool
    period_max_ok: bool
    period_mean_ok: bool
    passed: bool
    failure_reason: str
    points_per_server: int = 0
    point_total: int = 0
    expected_value_count: int = 0
    value_count: int = 0
    value_delivery_ratio: float = 0.0
    value_missing_count: int = 0
    read_count: int = 0
    batch_count: int = 0
    worst_gap: PeriodGap | None = None
    top_gaps: tuple[PeriodGap, ...] = ()
    warnings: tuple[str, ...] = ()
    runner_protocol_noise_count: int = 0
    runner_protocol_noise_samples: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConfirmedLevelResult:
    """Final level result after optional fail confirmation retries."""

    primary: CapacityLevelMetrics
    attempts: tuple[CapacityLevelMetrics, ...]
    final_status: CapacityStatus
    final_reason: str

    @property
    def final_metrics(self) -> CapacityLevelMetrics:
        """Return the metrics object used for final status and table output."""

        return self.attempts[-1] if self.attempts else self.primary


@dataclass(frozen=True, slots=True)
class CapacityScanConfig:
    """Protocol-agnostic capacity scan configuration."""

    mode: CapacityMode
    protocol: str
    endpoints: tuple[SourceEndpointSpec, ...]
    points: tuple[SourcePointSpec, ...]
    server_count_start: int
    server_count_step: int
    server_count_max: int
    hz_start: float
    hz_step: float
    hz_max: float
    process_count: int
    level_duration_s: float = 30.0
    warmup_s: float = 10.0
    read_timeout_s: float = 5.0
    source_update_enabled: bool = True
    source_update_hz: float = 10.0
    period_max_tolerance_ratio: float = 0.2
    period_mean_error_ratio: float = 0.05
    fail_confirm_runs: int = 2
    accept_flaky_as_pass: bool = False
    stop_hz_ramp_on_first_fail: bool = True
    top_gap_count: int = 10
    fleet_startup_timeout_s: float = 180.0
    fleet_stop_grace_s: float = 0.2
    progress_enabled: bool = True
    progress_interval_s: float = 5.0
    runner_trace_enabled: bool = False
    runner_trace_top_n: int = 20
    port_start: int = 45000
    port_end: int = 65000
    min_expected_point_count: int = 300
    max_expected_point_count: int = 500
    verbose_errors: bool = False

    def __post_init__(self) -> None:
        """Validate numeric scan settings."""

        if self.server_count_start <= 0 or self.server_count_step <= 0:
            raise ValueError("server_count_start and server_count_step must be greater than 0")
        if self.server_count_max < self.server_count_start:
            raise ValueError("server_count_max must be greater than or equal to server_count_start")
        if self.hz_start <= 0 or self.hz_step <= 0:
            raise ValueError("hz_start and hz_step must be greater than 0")
        if self.hz_max < self.hz_start:
            raise ValueError("hz_max must be greater than or equal to hz_start")
        if self.process_count <= 0:
            raise ValueError("process_count must be greater than 0")
        if self.level_duration_s <= 0 or self.warmup_s < 0 or self.read_timeout_s <= 0:
            raise ValueError("invalid timing config")
        if self.period_max_tolerance_ratio < 0:
            raise ValueError("period_max_tolerance_ratio must be non-negative")
        if self.period_mean_error_ratio < 0:
            raise ValueError("period_mean_error_ratio must be non-negative")
        if self.progress_interval_s <= 0:
            raise ValueError("progress_interval_s must be greater than 0")
        if self.runner_trace_top_n <= 0:
            raise ValueError("runner_trace_top_n must be greater than 0")

    @classmethod
    def from_env_for_simulator(cls) -> CapacityScanConfig:
        """Build simulator-mode config from environment variables."""

        from ..config import from_env_for_simulator

        return from_env_for_simulator()


@dataclass(frozen=True, slots=True)
class CapacityScanResult:
    """Final capacity scan result across all tested levels."""

    config: CapacityScanConfig
    levels: tuple[ConfirmedLevelResult, ...]

    @property
    def has_accepted_level(self) -> bool:
        """Return whether at least one level is accepted by config policy."""

        accepted_statuses = {CapacityStatus.PASS}
        if self.config.accept_flaky_as_pass:
            accepted_statuses.add(CapacityStatus.FLAKY)
        return any(level.final_status in accepted_statuses for level in self.levels)


@dataclass(frozen=True, slots=True)
class ProbeConfig:
    """Configuration for standalone field endpoint probing."""

    protocol: str
    service_type: str | None = None
    timeout_s: float = 5.0
    samples: int = 1
    concurrency: int = 16
    tcp_timeout_s: float = 3.0

    def __post_init__(self) -> None:
        """Validate probe settings."""

        if self.timeout_s <= 0:
            raise ValueError("timeout_s must be greater than 0")
        if self.samples <= 0:
            raise ValueError("samples must be greater than 0")
        if self.concurrency <= 0:
            raise ValueError("concurrency must be greater than 0")
        if self.tcp_timeout_s <= 0:
            raise ValueError("tcp_timeout_s must be greater than 0")


@dataclass(frozen=True, slots=True)
class ProbeLatencyStats:
    """Latency aggregates in milliseconds for one probe target."""

    min_ms: float
    mean_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float


@dataclass(frozen=True, slots=True)
class ServerProbeResult:
    """Probe result for one field server endpoint."""

    endpoint_id: str
    profile_id: str
    protocol: str
    host: str
    port: int
    point_count: int
    tcp_status: str
    protocol_status: str
    readable_count: int
    expected_count: int
    latency: ProbeLatencyStats | None
    missing_ts: bool
    status: CapacityStatus
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ProbeResult:
    """Aggregate standalone probe result."""

    config: ProbeConfig
    rows: tuple[ServerProbeResult, ...]
