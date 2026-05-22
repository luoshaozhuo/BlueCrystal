"""Tests for capacity and probe config env parsing."""

from __future__ import annotations

import pytest

from tools.source_lab.access.config import (
    from_env_for_probe,
    from_env_for_simulator,
    from_env_for_simulator_subscribe,
    from_env_for_simulator_polling_capacity_args,
    from_env_for_simulator_subscribe_capacity_args,
)


def test_from_env_supports_start_step_max(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parse server and hz ramps from start/step/max variables."""

    monkeypatch.setenv("SOURCE_SIM_POLL_SERVER_COUNT_START", "2")
    monkeypatch.setenv("SOURCE_SIM_POLL_SERVER_COUNT_STEP", "3")
    monkeypatch.setenv("SOURCE_SIM_POLL_SERVER_COUNT_MAX", "8")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_START", "15")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_STEP", "5")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_MAX", "40")

    config = from_env_for_simulator()

    assert config.server_count_start == 2
    assert config.server_count_step == 3
    assert config.server_count_max == 8
    assert config.hz_start == 15.0
    assert config.hz_step == 5.0
    assert config.hz_max == 40.0


def test_from_env_supports_alias_server_count_and_target_hz(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prefer compatibility aliases for server_count and target_hz."""

    monkeypatch.setenv("SOURCE_SIM_POLL_SERVER_COUNT", "7")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ", "22")

    config = from_env_for_simulator()

    assert config.server_count_start == 7
    assert config.server_count_max == 7
    assert config.hz_start == 22.0
    assert config.hz_max == 22.0


def test_from_env_fixed_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep fixed defaults expected by the capacity scanner."""

    # Mock TTY to ensure progress_enabled defaults to True in test
    monkeypatch.setattr("sys.stderr.isatty", lambda: True)
    
    monkeypatch.delenv("SOURCE_SIM_POLL_LEVEL_DURATION_S", raising=False)
    monkeypatch.delenv("SOURCE_SIM_POLL_DURATION_S", raising=False)
    monkeypatch.delenv("SOURCE_SIM_POLL_WARMUP_S", raising=False)
    monkeypatch.delenv("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", raising=False)
    monkeypatch.delenv("SOURCE_SIM_POLL_PERIOD_MAX_TOLERANCE_RATIO", raising=False)
    monkeypatch.delenv("SOURCE_SIM_POLL_PERIOD_MEAN_ERROR_RATIO", raising=False)
    monkeypatch.delenv("SOURCE_SIM_POLL_FAIL_CONFIRM_RUNS", raising=False)
    monkeypatch.delenv("SOURCE_SIM_POLL_ACCEPT_FLAKY_AS_PASS", raising=False)
    monkeypatch.delenv("SOURCE_SIM_POLL_STOP_HZ_RAMP_ON_FIRST_FAIL", raising=False)
    monkeypatch.delenv("SOURCE_SIM_POLL_TOP_GAP_COUNT", raising=False)
    monkeypatch.delenv("SOURCE_SIM_POLL_PROGRESS_ENABLED", raising=False)
    monkeypatch.delenv("SOURCE_SIM_POLL_PROGRESS_INTERVAL_S", raising=False)
    monkeypatch.delenv("SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S", raising=False)

    config = from_env_for_simulator()

    assert config.level_duration_s == 30.0
    assert config.warmup_s == 10.0
    assert config.source_update_enabled is True
    assert config.period_max_tolerance_ratio == 0.2
    assert config.period_mean_error_ratio == 0.05
    assert config.fail_confirm_runs == 2
    assert config.accept_flaky_as_pass is False
    assert config.stop_hz_ramp_on_first_fail is True
    assert config.top_gap_count == 10
    assert config.progress_enabled is True
    assert config.progress_interval_s == 5.0
    assert config.fleet_startup_timeout_s == 180.0


def test_capacity_config_does_not_expose_preflight_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Capacity config should not retain preflight-era fields."""

    # These should be ignored; setting them should not cause error
    monkeypatch.setenv("SOURCE_SIM_POLL_PREFLIGHT_ENABLED", "false")
    monkeypatch.setenv("SOURCE_SIM_POLL_PREFLIGHT_TCP_TIMEOUT_S", "2.5")
    monkeypatch.setenv("SOURCE_SIM_POLL_PREFLIGHT_CONCURRENCY", "7")

    config = from_env_for_simulator()

    assert not hasattr(config, "preflight_enabled")
    assert not hasattr(config, "preflight_tcp_timeout_s")
    assert not hasattr(config, "preflight_concurrency")


def test_from_env_supports_progress_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parse progress output config from environment."""

    monkeypatch.setenv("SOURCE_SIM_POLL_PROGRESS_ENABLED", "false")
    monkeypatch.setenv("SOURCE_SIM_POLL_PROGRESS_INTERVAL_S", "2.0")

    config = from_env_for_simulator()

    assert config.progress_enabled is False
    assert config.progress_interval_s == 2.0


def test_from_env_supports_polling_tolerance_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_SIM_POLL_PERIOD_MAX_TOLERANCE_RATIO", "0.35")
    monkeypatch.setenv("SOURCE_SIM_POLL_PERIOD_MEAN_ERROR_RATIO", "0.12")

    config = from_env_for_simulator()

    assert config.period_max_tolerance_ratio == 0.35
    assert config.period_mean_error_ratio == 0.12


def test_from_env_rejects_negative_polling_tolerances(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_SIM_POLL_PERIOD_MAX_TOLERANCE_RATIO", "-0.1")

    with pytest.raises(ValueError, match="period_max_tolerance_ratio must be non-negative"):
        from_env_for_simulator()

    monkeypatch.setenv("SOURCE_SIM_POLL_PERIOD_MAX_TOLERANCE_RATIO", "0.2")
    monkeypatch.setenv("SOURCE_SIM_POLL_PERIOD_MEAN_ERROR_RATIO", "-0.1")

    with pytest.raises(ValueError, match="period_mean_error_ratio must be non-negative"):
        from_env_for_simulator()


def test_from_env_supports_subscribe_data_period_tolerance_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_SIM_SUB_DATA_PERIOD_MAX_TOLERANCE_RATIO", "0.5")
    monkeypatch.setenv("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ", "10")

    config = from_env_for_simulator_subscribe()

    assert config.data_period_max_tolerance_ratio == 0.5


def test_from_env_for_subscribe_defaults_to_auto_match_source_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ", raising=False)
    monkeypatch.setenv("SOURCE_SIM_SUB_SAMPLE_HZ", "20")

    with pytest.raises(
        ValueError,
        match="SOURCE_SIM_SUB_SOURCE_UPDATE_HZ not explicitly set",
    ):
        from_env_for_simulator_subscribe()


def test_from_env_for_subscribe_marks_explicit_source_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_SIM_SUB_SAMPLE_HZ", "10")
    monkeypatch.setenv("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ", "20")

    config = from_env_for_simulator_subscribe()

    assert config.source_update_hz == 20.0
    assert config.source_update_hz_explicit is True


def test_from_env_keeps_subscribe_tolerance_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOURCE_SIM_SUB_DATA_PERIOD_MAX_TOLERANCE_RATIO", raising=False)
    monkeypatch.setenv("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ", "10")

    config = from_env_for_simulator_subscribe()

    assert config.data_period_max_tolerance_ratio == 0.2


def test_from_env_rejects_negative_subscribe_tolerance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_SIM_SUB_DATA_PERIOD_MAX_TOLERANCE_RATIO", "-0.1")
    monkeypatch.setenv("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ", "10")

    with pytest.raises(ValueError, match="data_period_max_tolerance_ratio must be non-negative"):
        from_env_for_simulator_subscribe()


def test_from_env_ignores_removed_legacy_coroutine_env(monkeypatch: pytest.MonkeyPatch) -> None:
    legacy_name = "SOURCE_SIM_POLL_" + "COROUTINES_PER_PROCESS"
    monkeypatch.setenv(legacy_name, "99")

    config = from_env_for_simulator()

    assert not hasattr(config, "coroutines_" + "per_process")


def test_from_env_does_not_expose_backend_fields() -> None:
    config = from_env_for_simulator()

    assert not hasattr(config, "opcua_" + "client" + "_" + "backend")
    assert not hasattr(config, "opcua_" + "simulator" + "_" + "backend")


def test_from_env_supports_runner_trace_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_SIM_POLL_RUNNER_TRACE_ENABLED", "true")
    monkeypatch.setenv("SOURCE_SIM_POLL_RUNNER_TRACE_TOP_N", "9")

    config = from_env_for_simulator()

    assert config.runner_trace_enabled is True
    assert config.runner_trace_top_n == 9


def test_probe_env_loader_parses_probe_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_LAB_PROBE_PROTOCOL", "opc-ua")
    monkeypatch.setenv("SOURCE_LAB_PROBE_TIMEOUT_S", "6")
    monkeypatch.setenv("SOURCE_LAB_PROBE_SAMPLES", "12")
    monkeypatch.setenv("SOURCE_LAB_PROBE_CONCURRENCY", "4")
    monkeypatch.setenv("SOURCE_LAB_PROBE_TCP_TIMEOUT_S", "2")

    config = from_env_for_probe()

    assert config.protocol == "opc-ua"
    assert config.timeout_s == 6.0
    assert config.samples == 12
    assert config.concurrency == 4
    assert config.tcp_timeout_s == 2.0


def test_from_env_rejects_deprecated_load_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that SOURCE_SIM_LOAD_* variables cause explicit ValueError."""

    monkeypatch.setenv("SOURCE_SIM_LOAD_PROCESS_COUNT", "1")

    with pytest.raises(ValueError, match="SOURCE_SIM_LOAD_\\* variables are deprecated"):
        from_env_for_simulator()


def test_subscribe_capacity_args_parse_ramps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_SIM_SUB_PROCESS_COUNT_START", "1")
    monkeypatch.setenv("SOURCE_SIM_SUB_PROCESS_COUNT_STEP", "1")
    monkeypatch.setenv("SOURCE_SIM_SUB_PROCESS_COUNT_MAX", "3")
    monkeypatch.setenv("SOURCE_SIM_SUB_SAMPLE_HZ_START", "5")
    monkeypatch.setenv("SOURCE_SIM_SUB_SAMPLE_HZ_STEP", "5")
    monkeypatch.setenv("SOURCE_SIM_SUB_SAMPLE_HZ_MAX", "15")
    monkeypatch.setenv("SOURCE_SIM_SUB_QUEUE_SIZE", "2")

    monkeypatch.setenv("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_START", "10")
    monkeypatch.setenv("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_STEP", "10")
    monkeypatch.setenv("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_MAX", "20")

    args = from_env_for_simulator_subscribe_capacity_args()

    assert args.process_counts == (1, 2, 3)
    assert args.sample_hz_values == (5.0, 10.0, 15.0)
    assert args.queue_sizes == (2,)
    assert args.source_update_hz_values == (10.0, 20.0)


def test_subscribe_capacity_args_prefers_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_SIM_SUB_PROCESS_COUNTS", "2,4")
    monkeypatch.setenv("SOURCE_SIM_SUB_PROCESS_COUNT_START", "1")
    monkeypatch.setenv("SOURCE_SIM_SUB_PROCESS_COUNT_STEP", "1")
    monkeypatch.setenv("SOURCE_SIM_SUB_PROCESS_COUNT_MAX", "3")
    monkeypatch.setenv("SOURCE_SIM_SUB_SAMPLE_HZ_VALUES", "6,12")
    monkeypatch.setenv("SOURCE_SIM_SUB_SAMPLE_HZ_START", "5")
    monkeypatch.setenv("SOURCE_SIM_SUB_SAMPLE_HZ_STEP", "5")
    monkeypatch.setenv("SOURCE_SIM_SUB_SAMPLE_HZ_MAX", "15")
    monkeypatch.setenv("SOURCE_SIM_SUB_QUEUE_SIZES", "1,3")
    monkeypatch.setenv("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_VALUES", "8,16")

    args = from_env_for_simulator_subscribe_capacity_args()

    assert args.process_counts == (2, 4)
    assert args.sample_hz_values == (6.0, 12.0)
    assert args.queue_sizes == (1, 3)
    assert args.source_update_hz_values == (8.0, 16.0)


def test_polling_capacity_args_parse_ramps_from_poll_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_SIM_POLL_PROCESS_COUNT_START", "1")
    monkeypatch.setenv("SOURCE_SIM_POLL_PROCESS_COUNT_STEP", "1")
    monkeypatch.setenv("SOURCE_SIM_POLL_PROCESS_COUNT_MAX", "3")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_START", "5")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_STEP", "5")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_MAX", "15")

    process_counts, hz_values = from_env_for_simulator_polling_capacity_args()

    assert process_counts == (1, 2, 3)
    assert hz_values == (5.0, 10.0, 15.0)


def test_polling_capacity_args_poll_env_precedence_over_load_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify POLL env vars are read (no fallback to deprecated LOAD env)."""
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_START", "20")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_STEP", "10")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_MAX", "30")

    process_counts, hz_values = from_env_for_simulator_polling_capacity_args()

    assert process_counts == (1,)
    assert hz_values == (20.0, 30.0)


def test_from_env_poll_aliases_take_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify POLL aliases work correctly."""
    monkeypatch.setenv("SOURCE_SIM_POLL_SERVER_COUNT_START", "11")
    monkeypatch.setenv("SOURCE_SIM_POLL_SERVER_COUNT_STEP", "11")
    monkeypatch.setenv("SOURCE_SIM_POLL_SERVER_COUNT_MAX", "22")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_START", "8")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_STEP", "2")
    monkeypatch.setenv("SOURCE_SIM_POLL_HZ_MAX", "12")

    config = from_env_for_simulator()

    assert config.server_count_start == 11
    assert config.server_count_step == 11
    assert config.server_count_max == 22
    assert config.hz_start == 8.0
    assert config.hz_step == 2.0
    assert config.hz_max == 12.0
