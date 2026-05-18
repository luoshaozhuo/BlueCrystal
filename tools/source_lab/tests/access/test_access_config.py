"""Tests for capacity and probe config env parsing."""

from __future__ import annotations

import pytest

from tools.source_lab.access.config import from_env_for_probe, from_env_for_simulator


def test_from_env_supports_start_step_max(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parse server and hz ramps from start/step/max variables."""

    monkeypatch.setenv("SOURCE_SIM_LOAD_SERVER_COUNT_START", "2")
    monkeypatch.setenv("SOURCE_SIM_LOAD_SERVER_COUNT_STEP", "3")
    monkeypatch.setenv("SOURCE_SIM_LOAD_SERVER_COUNT_MAX", "8")
    monkeypatch.setenv("SOURCE_SIM_LOAD_HZ_START", "15")
    monkeypatch.setenv("SOURCE_SIM_LOAD_HZ_STEP", "5")
    monkeypatch.setenv("SOURCE_SIM_LOAD_HZ_MAX", "40")

    config = from_env_for_simulator()

    assert config.server_count_start == 2
    assert config.server_count_step == 3
    assert config.server_count_max == 8
    assert config.hz_start == 15.0
    assert config.hz_step == 5.0
    assert config.hz_max == 40.0


def test_from_env_supports_alias_server_count_and_target_hz(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prefer compatibility aliases for server_count and target_hz."""

    monkeypatch.setenv("SOURCE_SIM_LOAD_SERVER_COUNT", "7")
    monkeypatch.setenv("SOURCE_SIM_LOAD_TARGET_HZ", "22")

    config = from_env_for_simulator()

    assert config.server_count_start == 7
    assert config.server_count_max == 7
    assert config.hz_start == 22.0
    assert config.hz_max == 22.0


def test_from_env_fixed_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep fixed defaults expected by the capacity scanner."""

    monkeypatch.delenv("SOURCE_SIM_LOAD_LEVEL_DURATION_S", raising=False)
    monkeypatch.delenv("SOURCE_SIM_LOAD_WARMUP_S", raising=False)
    monkeypatch.delenv("SOURCE_SIM_LOAD_SOURCE_UPDATE_ENABLED", raising=False)
    monkeypatch.delenv("SOURCE_SIM_LOAD_PERIOD_MAX_TOLERANCE_RATIO", raising=False)
    monkeypatch.delenv("SOURCE_SIM_LOAD_PERIOD_TOLERANCE_RATIO", raising=False)
    monkeypatch.delenv("SOURCE_SIM_LOAD_PERIOD_MEAN_ERROR_RATIO", raising=False)
    monkeypatch.delenv("SOURCE_SIM_LOAD_FAIL_CONFIRM_RUNS", raising=False)
    monkeypatch.delenv("SOURCE_SIM_LOAD_ACCEPT_FLAKY_AS_PASS", raising=False)
    monkeypatch.delenv("SOURCE_SIM_LOAD_STOP_HZ_RAMP_ON_FIRST_FAIL", raising=False)
    monkeypatch.delenv("SOURCE_SIM_LOAD_TOP_GAP_COUNT", raising=False)
    monkeypatch.delenv("SOURCE_SIM_LOAD_PROGRESS_ENABLED", raising=False)
    monkeypatch.delenv("SOURCE_SIM_LOAD_PROGRESS_INTERVAL_S", raising=False)
    monkeypatch.delenv("SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S", raising=False)

    config = from_env_for_simulator()

    assert config.level_duration_s == 30.0
    assert config.warmup_s == 10.0
    assert config.source_update_enabled is False
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

    monkeypatch.setenv("SOURCE_SIM_LOAD_PREFLIGHT_ENABLED", "false")
    monkeypatch.setenv("SOURCE_SIM_LOAD_PREFLIGHT_TCP_TIMEOUT_S", "2.5")
    monkeypatch.setenv("SOURCE_SIM_LOAD_PREFLIGHT_CONCURRENCY", "7")

    config = from_env_for_simulator()

    assert not hasattr(config, "preflight_enabled")
    assert not hasattr(config, "preflight_tcp_timeout_s")
    assert not hasattr(config, "preflight_concurrency")


def test_from_env_supports_progress_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parse progress output config from environment."""

    monkeypatch.setenv("SOURCE_SIM_LOAD_PROGRESS_ENABLED", "false")
    monkeypatch.setenv("SOURCE_SIM_LOAD_PROGRESS_INTERVAL_S", "2.0")

    config = from_env_for_simulator()

    assert config.progress_enabled is False
    assert config.progress_interval_s == 2.0


def test_from_env_ignores_removed_legacy_coroutine_env(monkeypatch: pytest.MonkeyPatch) -> None:
    legacy_name = "SOURCE_SIM_LOAD_" + "COROUTINES_PER_PROCESS"
    monkeypatch.setenv(legacy_name, "99")

    config = from_env_for_simulator()

    assert not hasattr(config, "coroutines_" + "per_process")


def test_from_env_does_not_expose_backend_fields() -> None:
    config = from_env_for_simulator()

    assert not hasattr(config, "opcua_" + "client" + "_" + "backend")
    assert not hasattr(config, "opcua_" + "simulator" + "_" + "backend")


def test_from_env_supports_runner_trace_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_SIM_LOAD_RUNNER_TRACE_ENABLED", "true")
    monkeypatch.setenv("SOURCE_SIM_LOAD_RUNNER_TRACE_TOP_N", "9")

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
