"""Environment config loading for capacity scans and standalone field probes."""

from __future__ import annotations

import os

from .model import CapacityMode, CapacityScanConfig, ProbeConfig


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


def from_env_for_simulator() -> CapacityScanConfig:
    """Build simulator-mode capacity config from environment variables."""

    server_count_start = _env_first_int(
        ("SOURCE_SIM_LOAD_SERVER_COUNT", "SOURCE_SIM_LOAD_SERVER_COUNT_START"), 9
    )
    server_count_max = _env_first_int(
        ("SOURCE_SIM_LOAD_SERVER_COUNT", "SOURCE_SIM_LOAD_SERVER_COUNT_MAX"),
        server_count_start,
    )

    hz_start = _env_first_float(("SOURCE_SIM_LOAD_TARGET_HZ", "SOURCE_SIM_LOAD_HZ_START"), 9.0)
    hz_max = _env_first_float(("SOURCE_SIM_LOAD_TARGET_HZ", "SOURCE_SIM_LOAD_HZ_MAX"), hz_start)

    return CapacityScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        endpoints=(),
        points=(),
        server_count_start=server_count_start,
        server_count_step=_env_int("SOURCE_SIM_LOAD_SERVER_COUNT_STEP", 1),
        server_count_max=server_count_max,
        hz_start=hz_start,
        hz_step=_env_float("SOURCE_SIM_LOAD_HZ_STEP", 1.0),
        hz_max=hz_max,
        process_count=_env_int("SOURCE_SIM_LOAD_PROCESS_COUNT", 1),
        level_duration_s=_env_float("SOURCE_SIM_LOAD_LEVEL_DURATION_S", 30.0),
        warmup_s=_env_float("SOURCE_SIM_LOAD_WARMUP_S", 10.0),
        read_timeout_s=_env_float("SOURCE_SIM_LOAD_READ_TIMEOUT_S", 5.0),
        source_update_enabled=_env_flag("SOURCE_SIM_LOAD_SOURCE_UPDATE_ENABLED", False),
        source_update_hz=_env_float("SOURCE_SIM_LOAD_SOURCE_UPDATE_HZ", 10.0),
        period_max_tolerance_ratio=_env_first_float(
            (
                "SOURCE_SIM_LOAD_PERIOD_MAX_TOLERANCE_RATIO",
                "SOURCE_SIM_LOAD_PERIOD_TOLERANCE_RATIO",
            ),
            0.2,
        ),
        period_mean_error_ratio=_env_float("SOURCE_SIM_LOAD_PERIOD_MEAN_ERROR_RATIO", 0.05),
        fail_confirm_runs=_env_int("SOURCE_SIM_LOAD_FAIL_CONFIRM_RUNS", 2),
        accept_flaky_as_pass=_env_flag("SOURCE_SIM_LOAD_ACCEPT_FLAKY_AS_PASS", False),
        stop_hz_ramp_on_first_fail=_env_flag("SOURCE_SIM_LOAD_STOP_HZ_RAMP_ON_FIRST_FAIL", True),
        top_gap_count=_env_int("SOURCE_SIM_LOAD_TOP_GAP_COUNT", 10),
        fleet_startup_timeout_s=_env_float("SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S", 180.0),
        fleet_stop_grace_s=_env_float("SOURCE_SIM_FLEET_STOP_GRACE_S", 0.2),
        progress_enabled=_env_flag("SOURCE_SIM_LOAD_PROGRESS_ENABLED", True),
        progress_interval_s=_env_float("SOURCE_SIM_LOAD_PROGRESS_INTERVAL_S", 5.0),
        runner_trace_enabled=_env_flag("SOURCE_SIM_LOAD_RUNNER_TRACE_ENABLED", False),
        runner_trace_top_n=_env_int("SOURCE_SIM_LOAD_RUNNER_TRACE_TOP_N", 20),
        port_start=_env_int("SOURCE_SIM_PORT_START", 45000),
        port_end=_env_int("SOURCE_SIM_PORT_END", 65000),
        min_expected_point_count=_env_int("SOURCE_SIM_LOAD_MIN_POINTS", 300),
        max_expected_point_count=_env_int("SOURCE_SIM_LOAD_MAX_POINTS", 500),
        verbose_errors=_env_flag("SOURCE_SIM_LOAD_VERBOSE_ERRORS", False),
    )


def from_env_for_field_capacity() -> CapacityScanConfig:
    """Build field-mode capacity config from a small env subset."""

    server_count_start = _env_first_int(
        ("SOURCE_LAB_FIELD_SERVER_COUNT", "SOURCE_SIM_LOAD_SERVER_COUNT"),
        1,
    )
    server_count_max = _env_first_int(
        ("SOURCE_LAB_FIELD_SERVER_COUNT_MAX", "SOURCE_SIM_LOAD_SERVER_COUNT_MAX"),
        server_count_start,
    )
    hz_start = _env_first_float(("SOURCE_LAB_FIELD_HZ", "SOURCE_SIM_LOAD_TARGET_HZ"), 10.0)
    hz_max = _env_first_float(("SOURCE_LAB_FIELD_HZ_MAX", "SOURCE_SIM_LOAD_HZ_MAX"), hz_start)

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
        progress_enabled=_env_flag("SOURCE_LAB_FIELD_PROGRESS_ENABLED", True),
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
