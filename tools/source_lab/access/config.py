"""容量扫描与场端探测的环境变量配置加载。

负责：从环境变量读取 SOURCE_SIM_*/SOURCE_LAB_* 系列配置，构造 CapacityScanConfig/SubscribeScanConfig/ProbeConfig 等配置对象。
不负责：配置的持久化、运行时修改。
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import sys

from .common.scheduling import parse_float_list_or_ramp, parse_int_list_or_ramp
from .polling.model import CapacityMode, CapacityScanConfig, ProbeConfig
from .subscribe.model import SubscribeScanConfig


def _env_flag(name: str, default: bool) -> bool:
    """Return boolean env var value with common false spellings."""

    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _env_int(name: str, default: int) -> int:
    """Return integer env var value with fallback."""

    value = os.environ.get(name)
    return default if value is None or value.strip() == "" else int(value)


def _env_float(name: str, default: float) -> float:
    """Return float env var value with fallback."""

    value = os.environ.get(name)
    return default if value is None or value.strip() == "" else float(value)


def _env_first_int(names: tuple[str, ...], default: int) -> int:
    """Return first available integer env var from aliases."""

    for name in names:
        value = os.environ.get(name)
        if value is not None and value.strip() != "":
            return int(value)
    return default


def _env_first_float(names: tuple[str, ...], default: float) -> float:
    """Return first available float env var from aliases."""

    for name in names:
        value = os.environ.get(name)
        if value is not None and value.strip() != "":
            return float(value)
    return default


def _env_first_flag(names: tuple[str, ...], default: bool) -> bool:
    """Return first available boolean env var from aliases."""

    for name in names:
        value = os.environ.get(name)
        if value is not None and value.strip() != "":
            return value.strip().lower() not in {"0", "false", "no", "off"}
    return default


def _env_first_int_or_none(names: tuple[str, ...]) -> int | None:
    """Return first available integer env var from aliases, or None if none exist."""

    for name in names:
        value = os.environ.get(name)
        if value is not None and value.strip() != "":
            try:
                return int(value.strip())
            except ValueError:
                continue
    return None


def _env_first_float_or_none(names: tuple[str, ...]) -> float | None:
    """Return first available float env var from aliases, or None if none exist."""

    for name in names:
        value = os.environ.get(name)
        if value is not None and value.strip() != "":
            try:
                return float(value.strip())
            except ValueError:
                continue
    return None


def _check_deprecated_load_env() -> None:
    """Fail if SOURCE_SIM_LOAD_* capacity env vars are used (deprecated)."""
    deprecated_vars = {
        "SOURCE_SIM_LOAD_PROCESS_COUNT",
        "SOURCE_SIM_LOAD_PROCESS_COUNT_START",
        "SOURCE_SIM_LOAD_PROCESS_COUNT_STEP",
        "SOURCE_SIM_LOAD_PROCESS_COUNT_MAX",
        "SOURCE_SIM_LOAD_SERVER_COUNT_START",
        "SOURCE_SIM_LOAD_SERVER_COUNT_STEP",
        "SOURCE_SIM_LOAD_SERVER_COUNT_MAX",
        "SOURCE_SIM_LOAD_HZ_START",
        "SOURCE_SIM_LOAD_HZ_STEP",
        "SOURCE_SIM_LOAD_HZ_MAX",
        "SOURCE_SIM_LOAD_TARGET_HZ",
        "SOURCE_SIM_LOAD_TARGET_HZ_START",
        "SOURCE_SIM_LOAD_TARGET_HZ_STEP",
        "SOURCE_SIM_LOAD_TARGET_HZ_MAX",
        "SOURCE_SIM_LOAD_LEVEL_DURATION_S",
        "SOURCE_SIM_LOAD_SOURCE_UPDATE_ENABLED",
        "SOURCE_SIM_LOAD_SOURCE_UPDATE_HZ",
    }
    found = [var for var in deprecated_vars if os.environ.get(var) is not None]
    if found:
        raise ValueError(
            f"SOURCE_SIM_LOAD_* variables are deprecated and no longer supported. "
            f"Found: {', '.join(sorted(found))}. "
            f"Use SOURCE_SIM_POLL_* for polling or SOURCE_SIM_SUB_* for subscribe instead."
        )


def from_env_for_simulator() -> CapacityScanConfig:
    """Build simulator-mode capacity config from environment variables."""

    _check_deprecated_load_env()

    server_count_start = _env_first_int(
        (
            "SOURCE_SIM_POLL_SERVER_COUNT",
            "SOURCE_SIM_POLL_SERVER_COUNT_START",
        ),
        9,
    )
    server_count_max = _env_first_int(
        (
            "SOURCE_SIM_POLL_SERVER_COUNT",
            "SOURCE_SIM_POLL_SERVER_COUNT_MAX",
        ),
        server_count_start,
    )

    hz_start = _env_first_float(
        (
            "SOURCE_SIM_POLL_HZ",
            "SOURCE_SIM_POLL_HZ_START",
        ),
        9.0,
    )
    hz_max = _env_first_float(
        (
            "SOURCE_SIM_POLL_HZ",
            "SOURCE_SIM_POLL_HZ_MAX",
        ),
        hz_start,
    )

    return CapacityScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        endpoints=(),
        points=(),
        server_count_start=server_count_start,
        server_count_step=_env_int("SOURCE_SIM_POLL_SERVER_COUNT_STEP", 1),
        server_count_max=server_count_max,
        hz_start=hz_start,
        hz_step=_env_float("SOURCE_SIM_POLL_HZ_STEP", 1.0),
        hz_max=hz_max,
        process_count=_env_int("SOURCE_SIM_POLL_PROCESS_COUNT", 1),
        level_duration_s=_env_float("SOURCE_SIM_POLL_DURATION_S", 30.0),
        warmup_s=_env_float("SOURCE_SIM_POLL_WARMUP_S", 10.0),
        read_timeout_s=_env_float("SOURCE_SIM_POLL_READ_TIMEOUT_S", 5.0),
        source_update_enabled=_env_flag("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", True),
        source_update_hz=_env_float("SOURCE_SIM_POLL_SOURCE_UPDATE_HZ", 10.0),
        period_max_tolerance_ratio=_env_float("SOURCE_SIM_POLL_PERIOD_MAX_TOLERANCE_RATIO", 0.2),
        period_mean_error_ratio=_env_float("SOURCE_SIM_POLL_PERIOD_MEAN_ERROR_RATIO", 0.05),
        fail_confirm_runs=_env_int("SOURCE_SIM_POLL_FAIL_CONFIRM_RUNS", 2),
        accept_flaky_as_pass=_env_flag("SOURCE_SIM_POLL_ACCEPT_FLAKY_AS_PASS", False),
        stop_hz_ramp_on_first_fail=_env_flag("SOURCE_SIM_POLL_STOP_HZ_RAMP_ON_FIRST_FAIL", True),
        top_gap_count=_env_int("SOURCE_SIM_POLL_TOP_GAP_COUNT", 10),
        fleet_startup_timeout_s=_env_float("SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S", 180.0),
        fleet_stop_grace_s=_env_float("SOURCE_SIM_FLEET_STOP_GRACE_S", 0.2),
        progress_enabled=_env_flag("SOURCE_SIM_POLL_PROGRESS_ENABLED", sys.stderr.isatty()),
        progress_interval_s=_env_float("SOURCE_SIM_POLL_PROGRESS_INTERVAL_S", 5.0),
        runner_trace_enabled=_env_flag("SOURCE_SIM_POLL_RUNNER_TRACE_ENABLED", False),
        runner_trace_top_n=_env_int("SOURCE_SIM_POLL_RUNNER_TRACE_TOP_N", 20),
        port_start=_env_int("SOURCE_SIM_PORT_START", 45000),
        port_end=_env_int("SOURCE_SIM_PORT_END", 65000),
        min_expected_point_count=_env_int("SOURCE_SIM_POLL_MIN_POINTS", 300),
        max_expected_point_count=_env_int("SOURCE_SIM_POLL_MAX_POINTS", 500),
        verbose_errors=_env_flag("SOURCE_SIM_POLL_VERBOSE_ERRORS", False),
    )


def from_env_for_simulator_polling_capacity_args() -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Build polling capacity process and hz matrix arguments from environment variables.
    
    Only SOURCE_SIM_POLL_* variables are supported. SOURCE_SIM_LOAD_* is deprecated.
    """
    _check_deprecated_load_env()

    # Parse process_count ramp from env using only SOURCE_SIM_POLL_*
    process_counts = parse_int_list_or_ramp(
        os.environ.get("SOURCE_SIM_POLL_PROCESS_COUNTS"),
        start=_env_first_int_or_none(("SOURCE_SIM_POLL_PROCESS_COUNT_START",)),
        step=_env_first_int_or_none(("SOURCE_SIM_POLL_PROCESS_COUNT_STEP",)),
        maximum=_env_first_int_or_none(("SOURCE_SIM_POLL_PROCESS_COUNT_MAX",)),
        default=(_env_int("SOURCE_SIM_POLL_PROCESS_COUNT", 1),),
        value_name="process_count",
    )

    # Parse hz ramp from env using only SOURCE_SIM_POLL_*
    hz_values = parse_float_list_or_ramp(
        os.environ.get("SOURCE_SIM_POLL_HZ_VALUES"),
        start=_env_first_float_or_none(("SOURCE_SIM_POLL_HZ_START",)),
        step=_env_first_float_or_none(("SOURCE_SIM_POLL_HZ_STEP",)),
        maximum=_env_first_float_or_none(("SOURCE_SIM_POLL_HZ_MAX",)),
        default=(_env_float("SOURCE_SIM_POLL_HZ", 10.0),),
        value_name="hz",
    )

    return process_counts, hz_values



def from_env_for_field_capacity() -> CapacityScanConfig:
    """Build field-mode capacity config from a small env subset."""

    server_count_start = _env_first_int(
        ("SOURCE_LAB_FIELD_SERVER_COUNT",),
        1,
    )
    server_count_max = _env_first_int(
        ("SOURCE_LAB_FIELD_SERVER_COUNT_MAX",),
        server_count_start,
    )
    hz_start = _env_first_float(("SOURCE_LAB_FIELD_HZ",), 10.0)
    hz_max = _env_first_float(("SOURCE_LAB_FIELD_HZ_MAX",), hz_start)

    return CapacityScanConfig(
        mode=CapacityMode.FIELD,
        protocol=os.environ.get("SOURCE_LAB_FIELD_PROTOCOL", "opcua"),
        endpoints=(),
        points=(),
        server_count_start=server_count_start,
        server_count_step=_env_int("SOURCE_LAB_FIELD_SERVER_COUNT_STEP", 1),
        server_count_max=server_count_max,
        hz_start=hz_start,
        hz_step=_env_float("SOURCE_LAB_FIELD_HZ_STEP", 1.0),
        hz_max=hz_max,
        process_count=_env_int("SOURCE_LAB_FIELD_PROCESS_COUNT", 1),
        level_duration_s=_env_float("SOURCE_LAB_FIELD_LEVEL_DURATION_S", 30.0),
        warmup_s=_env_float("SOURCE_LAB_FIELD_WARMUP_S", 10.0),
        read_timeout_s=_env_float("SOURCE_LAB_FIELD_READ_TIMEOUT_S", 5.0),
        source_update_enabled=_env_flag("SOURCE_LAB_FIELD_SOURCE_UPDATE_ENABLED", True),
        source_update_hz=_env_float("SOURCE_LAB_FIELD_SOURCE_UPDATE_HZ", hz_start),
        progress_enabled=_env_flag("SOURCE_LAB_FIELD_PROGRESS_ENABLED", sys.stderr.isatty()),
        runner_trace_enabled=_env_flag("SOURCE_LAB_FIELD_RUNNER_TRACE_ENABLED", False),
    )


def from_env_for_probe() -> ProbeConfig:
    """Build standalone probe config from a small env subset."""

    return ProbeConfig(
        protocol=os.environ.get("SOURCE_LAB_PROBE_PROTOCOL", "opcua"),
        timeout_s=_env_float("SOURCE_LAB_PROBE_TIMEOUT_S", 5.0),
        samples=_env_int("SOURCE_LAB_PROBE_SAMPLES", 10),
        concurrency=_env_int("SOURCE_LAB_PROBE_CONCURRENCY", 16),
        tcp_timeout_s=_env_float("SOURCE_LAB_PROBE_TCP_TIMEOUT_S", 3.0),
    )


def from_env_for_simulator_subscribe() -> SubscribeScanConfig:
    """Build simulator-mode subscribe config from environment variables."""

    server_count_start = _env_first_int(
        ("SOURCE_SIM_SUB_SERVER_COUNT", "SOURCE_SIM_SUB_SERVER_COUNT_START"),
        2,
    )
    server_count_max = _env_first_int(
        ("SOURCE_SIM_SUB_SERVER_COUNT", "SOURCE_SIM_SUB_SERVER_COUNT_MAX"),
        server_count_start,
    )
    sample_hz = _env_first_float(
        (
            "SOURCE_SIM_SUB_SAMPLE_HZ",
            "SOURCE_SIM_SUB_SAMPLE_HZ_START",
        ),
        10.0,
    )
    default_interval_ms = 1000.0 / sample_hz
    sampling_interval_ms = (
        _env_float("SOURCE_SIM_SUB_SAMPLING_INTERVAL_MS", default_interval_ms)
        if os.environ.get("SOURCE_SIM_SUB_SAMPLING_INTERVAL_MS", "").strip() != ""
        else default_interval_ms
    )
    publishing_interval_ms = (
        _env_float("SOURCE_SIM_SUB_PUBLISHING_INTERVAL_MS", sampling_interval_ms)
        if os.environ.get("SOURCE_SIM_SUB_PUBLISHING_INTERVAL_MS", "").strip() != ""
        else sampling_interval_ms
    )
    explicit_source_update_hz = os.environ.get("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ", "").strip() != ""
    source_update_enabled = _env_flag("SOURCE_SIM_SUB_SOURCE_UPDATE_ENABLED", True)
    if source_update_enabled and not explicit_source_update_hz:
        raise ValueError("source_update_enabled=true but SOURCE_SIM_SUB_SOURCE_UPDATE_HZ not explicitly set; fail-fast to avoid auto-match.")
    source_update_hz = (
        _env_float("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ", sample_hz)
        if explicit_source_update_hz
        else sample_hz
    )
    return SubscribeScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        server_count_start=server_count_start,
        server_count_step=_env_int("SOURCE_SIM_SUB_SERVER_COUNT_STEP", 1),
        server_count_max=server_count_max,
        process_count=_env_int("SOURCE_SIM_SUB_PROCESS_COUNT", 1),
        publishing_interval_ms=publishing_interval_ms,
        sampling_interval_ms=sampling_interval_ms,
        queue_size=_env_int("SOURCE_SIM_SUB_QUEUE_SIZE", 1),
        nominal_sample_hz=sample_hz,
        source_update_hz_explicit=explicit_source_update_hz,
        duration_s=_env_float("SOURCE_SIM_SUB_DURATION_S", 5.0),
        read_timeout_s=_env_float("SOURCE_SIM_SUB_READ_TIMEOUT_S", 5.0),
        source_update_enabled=source_update_enabled,
        source_update_hz=source_update_hz,
        startup_stagger_ms=_env_int("SOURCE_SIM_SUB_STARTUP_STAGGER_MS", 0),
        reconnect_stagger_ms=_env_int("SOURCE_SIM_SUB_RECONNECT_STAGGER_MS", 0),
        monitored_item_batch_size=_env_int("SOURCE_SIM_SUB_MONITORED_ITEM_BATCH_SIZE", 100),
        monitored_item_batch_gap_ms=_env_int("SOURCE_SIM_SUB_MONITORED_ITEM_BATCH_GAP_MS", 0),
        fail_confirm_runs=_env_int("SOURCE_SIM_SUB_FAIL_CONFIRM_RUNS", 1),
        accept_flaky_as_pass=_env_flag("SOURCE_SIM_SUB_ACCEPT_FLAKY_AS_PASS", False),
        stop_ramp_on_first_fail=_env_flag("SOURCE_SIM_SUB_STOP_RAMP_ON_FIRST_FAIL", True),
        progress_enabled=_env_flag("SOURCE_SIM_SUB_PROGRESS_ENABLED", sys.stderr.isatty()),
        progress_interval_s=_env_float("SOURCE_SIM_SUB_PROGRESS_INTERVAL_S", 5.0),
        runner_trace_enabled=_env_flag("SOURCE_SIM_SUB_RUNNER_TRACE_ENABLED", False),
        runner_trace_top_n=_env_int("SOURCE_SIM_SUB_RUNNER_TRACE_TOP_N", 20),
        fleet_startup_timeout_s=_env_float("SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S", 180.0),
        fleet_stop_grace_s=_env_float("SOURCE_SIM_FLEET_STOP_GRACE_S", 0.2),
        min_expected_point_count=_env_int("SOURCE_SIM_SUB_MIN_POINTS", 20),
        max_expected_point_count=_env_int("SOURCE_SIM_SUB_MAX_POINTS", 30),
        missing_timestamp_fail_count=_env_int("SOURCE_SIM_SUB_MISSING_TS_FAIL_COUNT", 0),
        data_period_max_tolerance_ratio=_env_float("SOURCE_SIM_SUB_DATA_PERIOD_MAX_TOLERANCE_RATIO", 0.2),
        publish_gap_p95_limit_ms=(
            _env_float("SOURCE_SIM_SUB_PUBLISH_GAP_P95_LIMIT_MS", 0.0)
            if os.environ.get("SOURCE_SIM_SUB_PUBLISH_GAP_P95_LIMIT_MS")
            else None
        ),
        publish_gap_p99_limit_ms=(
            _env_float("SOURCE_SIM_SUB_PUBLISH_GAP_P99_LIMIT_MS", 0.0)
            if os.environ.get("SOURCE_SIM_SUB_PUBLISH_GAP_P99_LIMIT_MS")
            else None
        ),
        data_age_p95_limit_ms=(
            _env_float("SOURCE_SIM_SUB_DATA_AGE_P95_LIMIT_MS", 0.0)
            if os.environ.get("SOURCE_SIM_SUB_DATA_AGE_P95_LIMIT_MS")
            else None
        ),
        data_age_p99_limit_ms=(
            _env_float("SOURCE_SIM_SUB_DATA_AGE_P99_LIMIT_MS", 0.0)
            if os.environ.get("SOURCE_SIM_SUB_DATA_AGE_P99_LIMIT_MS")
            else None
        ),
    )



@dataclass(frozen=True, slots=True)
class SimulatorSubscribeCapacityArgs:
    """Env-derived subscribe capacity matrix arguments."""

    process_counts: tuple[int, ...]
    sample_hz_values: tuple[float, ...]
    queue_sizes: tuple[int, ...]
    source_update_hz_values: tuple[float, ...]
    server_counts: tuple[int, ...] = ()

def from_env_for_simulator_subscribe_capacity_args() -> SimulatorSubscribeCapacityArgs:
    """Build subscribe capacity matrix arguments from environment variables, including source_update_hz ramp."""

    process_start_raw = os.environ.get("SOURCE_SIM_SUB_PROCESS_COUNT_START", "").strip()
    process_step_raw = os.environ.get("SOURCE_SIM_SUB_PROCESS_COUNT_STEP", "").strip()
    process_max_raw = os.environ.get("SOURCE_SIM_SUB_PROCESS_COUNT_MAX", "").strip()
    process_counts = parse_int_list_or_ramp(
        os.environ.get("SOURCE_SIM_SUB_PROCESS_COUNTS"),
        start=_env_int("SOURCE_SIM_SUB_PROCESS_COUNT_START", 1) if process_start_raw != "" else None,
        step=(
            _env_int("SOURCE_SIM_SUB_PROCESS_COUNT_STEP", 1)
            if process_step_raw != ""
            else (1 if process_start_raw != "" or process_max_raw != "" else None)
        ),
        maximum=_env_int("SOURCE_SIM_SUB_PROCESS_COUNT_MAX", 1) if process_max_raw != "" else None,
        default=(
            _env_int("SOURCE_SIM_SUB_PROCESS_COUNT", 1),
        ),
        value_name="process_count",
    )

    sample_start_raw = os.environ.get("SOURCE_SIM_SUB_SAMPLE_HZ_START", "").strip()
    sample_step_raw = os.environ.get("SOURCE_SIM_SUB_SAMPLE_HZ_STEP", "").strip()
    sample_max_raw = os.environ.get("SOURCE_SIM_SUB_SAMPLE_HZ_MAX", "").strip()
    sample_hz_values = parse_float_list_or_ramp(
        os.environ.get("SOURCE_SIM_SUB_SAMPLE_HZ_VALUES"),
        start=_env_float("SOURCE_SIM_SUB_SAMPLE_HZ_START", 10.0) if sample_start_raw != "" else None,
        step=(
            _env_float("SOURCE_SIM_SUB_SAMPLE_HZ_STEP", 1.0)
            if sample_step_raw != ""
            else (1.0 if sample_start_raw != "" or sample_max_raw != "" else None)
        ),
        maximum=_env_float("SOURCE_SIM_SUB_SAMPLE_HZ_MAX", 10.0) if sample_max_raw != "" else None,
        default=(
            _env_first_float(
                (
                    "SOURCE_SIM_SUB_SAMPLE_HZ",
                    "SOURCE_SIM_SUB_SAMPLE_HZ_START",
                ),
                10.0,
            ),
        ),
        value_name="sample_hz",
    )

    queue_sizes = parse_int_list_or_ramp(
        os.environ.get("SOURCE_SIM_SUB_QUEUE_SIZES"),
        start=None,
        step=None,
        maximum=None,
        default=(_env_int("SOURCE_SIM_SUB_QUEUE_SIZE", 1),),
        value_name="queue_size",
    )

    # 新增 source_update_hz ramp
    src_update_start_raw = os.environ.get("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_START", "").strip()
    src_update_step_raw = os.environ.get("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_STEP", "").strip()
    src_update_max_raw = os.environ.get("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_MAX", "").strip()
    source_update_hz_values = parse_float_list_or_ramp(
        os.environ.get("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_VALUES"),
        start=_env_float("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_START", 10.0) if src_update_start_raw != "" else None,
        step=(
            _env_float("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_STEP", 10.0)
            if src_update_step_raw != ""
            else (1.0 if src_update_start_raw != "" or src_update_max_raw != "" else None)
        ),
        maximum=_env_float("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_MAX", 10.0) if src_update_max_raw != "" else None,
        default=(
            _env_first_float(
                (
                    "SOURCE_SIM_SUB_SOURCE_UPDATE_HZ",
                    "SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_START",
                ),
                10.0,
            ),
        ),
        value_name="source_update_hz",
    )

    server_counts = parse_int_list_or_ramp(
        os.environ.get("SOURCE_SIM_SUB_SERVER_COUNTS"),
        start=_env_first_int_or_none(("SOURCE_SIM_SUB_SERVER_COUNT_START",)),
        step=_env_first_int_or_none(("SOURCE_SIM_SUB_SERVER_COUNT_STEP",)),
        maximum=_env_first_int_or_none(("SOURCE_SIM_SUB_SERVER_COUNT_MAX",)),
        default=(
            _env_first_int(
                ("SOURCE_SIM_SUB_SERVER_COUNT", "SOURCE_SIM_SUB_SERVER_COUNT_START"),
                2,
            ),
        ),
        value_name="server_count",
    )

    return SimulatorSubscribeCapacityArgs(
        process_counts=process_counts,
        server_counts=server_counts,
        sample_hz_values=sample_hz_values,
        queue_sizes=queue_sizes,
        source_update_hz_values=source_update_hz_values,
    )
