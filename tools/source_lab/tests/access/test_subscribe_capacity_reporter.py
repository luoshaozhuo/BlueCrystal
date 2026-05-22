"""Tests for subscribe capacity/profile reporting helpers."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from tools.source_lab.access.capacity import (
    SubscribeCapacityComboResult,
    SubscribeCapacityLimitSummary,
    SubscribeCapacityResult,
    build_subscribe_capacity_rows,
    print_capacity_table,
)
from tools.source_lab.access.polling.model import CapacityMode, CapacityStatus
from tools.source_lab.access.subscribe.model import (
    SubscribeLevelMetrics,
    SubscribeLevelResult,
    SubscribeScanConfig,
    SubscribeScanResult,
)
from tools.source_lab.access.subscribe.reporter import (
    SubscribeProgressReporter,
    print_subscribe_capacity_table,
    print_subscribe_report,
)


def _config(*, progress_enabled: bool = True, sampling_interval_ms: float = 200.0) -> SubscribeScanConfig:
    return SubscribeScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        server_count_start=10,
        server_count_step=10,
        server_count_max=20,
        process_count=1,
        publishing_interval_ms=200.0,
        sampling_interval_ms=sampling_interval_ms,
        queue_size=1,
        duration_s=5.0,
        read_timeout_s=5.0,
        source_update_enabled=True,
        source_update_hz=5.0,
        progress_enabled=progress_enabled,
        progress_interval_s=5.0,
        fleet_startup_timeout_s=180.0,
        fleet_stop_grace_s=0.2,
        min_expected_point_count=1,
        max_expected_point_count=10,
    )


def _metrics(
    *,
    server_count: int,
    passed: bool = True,
    reason: str = "",
    response_period_p95_ms: float = 201.125,
    response_period_max_ms: float = 219.875,
    data_period_p95_ms: float = 201.125,
    data_period_max_ms: float = 219.875,
) -> SubscribeLevelMetrics:
    return SubscribeLevelMetrics(
        server_count=server_count,
        process_count=1,
        publishing_interval_ms=200.0,
        sampling_interval_ms=200.0,
        effective_source_update_hz=5.0,
        queue_size=1,
        expected_monitored_items=20,
        monitored_created=20,
        monitored_failed=0,
        notification_count=1002,
        value_count=2507,
        bad_count=0,
        missing_ts_count=0,
        reserved_sequence_gap_count=0,
        reserved_queue_overflow_count=0,
        keepalive_count=0,
        publish_timeout_count=0,
        reconnect_count=0,
        notification_rate=5.0,
        value_rate=5.0,
        publish_gap_mean_ms=300.0,
        publish_gap_p95_ms=339.671,
        publish_gap_p99_ms=360.1,
        publish_gap_max_ms=380.5,
        data_age_mean_ms=250.0,
        data_age_p95_ms=290.605,
        data_age_p99_ms=310.902,
        data_age_max_ms=330.0,
        data_period_samples=1000,
        data_period_mean_ms=200.0,
        data_period_p95_ms=data_period_p95_ms,
        data_period_max_ms=data_period_max_ms,
        allowed_data_period_max_ms=240.0,
        response_period_samples=1000,
        response_period_mean_ms=200.0,
        response_period_p95_ms=response_period_p95_ms,
        response_period_max_ms=response_period_max_ms,
        allowed_response_period_max_ms=240.0,
        passed=passed,
        failure_reason=reason,
        source_period_p95_ms=400.0,
        source_period_max_ms=400.0,
        recv_period_p95_ms=205.0,
        recv_period_max_ms=240.0,
        callback_to_flush_lag_p95_ms=3.5,
        callback_to_flush_lag_max_ms=8.0,
        warnings=(),
        batches=(),
        summaries=(),
        top_data_age_traces=(),
        top_period_gap_traces=(),
        top_flush_lag_traces=(),
        runner_protocol_noise_count=0,
        runner_protocol_noise_samples=(),
    )


def _capacity_result() -> SubscribeCapacityResult:
    pass_metrics = _metrics(server_count=10)
    fail_metrics = _metrics(server_count=20, passed=False, reason="queue_overflow")
    pass_level = SubscribeLevelResult(
        primary=pass_metrics,
        attempts=(pass_metrics,),
        final_status=CapacityStatus.PASS,
        final_reason="",
    )
    fail_level = SubscribeLevelResult(
        primary=fail_metrics,
        attempts=(fail_metrics,),
        final_status=CapacityStatus.FAIL,
        final_reason="queue_overflow",
    )
    return SubscribeCapacityResult(
        combos=(
            SubscribeCapacityComboResult(
                process_count=1,
                server_count=10,
                sample_hz=5.0,
                effective_source_update_hz=5.0,
                result=pass_level,
                status=CapacityStatus.PASS,
                reason="",
            ),
            SubscribeCapacityComboResult(
                process_count=1,
                server_count=20,
                sample_hz=5.0,
                effective_source_update_hz=5.0,
                result=fail_level,
                status=CapacityStatus.FAIL,
                reason="queue_overflow",
            ),
        ),
        limit_summaries=(
            SubscribeCapacityLimitSummary(
                process_count=1,
                server_count=20,
                queue_size=1,
                effective_source_update_hz=5.0,
                max_pass_sample_hz=5.0,
                first_fail_sample_hz=10.0,
                reason="queue_overflow",
            ),
        ),
    )


def test_print_subscribe_capacity_table_outputs_summary_only(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_LAB_CAPACITY_PRINT_LIMITS", "true")

    print_subscribe_capacity_table(_capacity_result())
    output = capsys.readouterr().out

    assert "proc" in output and "srv" in output and "status" in output and "reason" in output
    assert "sub_hz" in output and "src_hz" in output and "sub_ms" in output and "src_ms" in output
    assert "value_ratio" in output
    assert "p95_ms" in output
    assert "max_ms" in output
    assert "data_period_p95_ms" not in output
    assert "data_period_max_ms" not in output
    assert "expected_values" not in output
    assert "notify" not in output
    assert "queue " not in output
    assert "max_pass" not in output
    assert "queue_overflow" in output


def test_subscribe_progress_reporter_defaults_to_quiet_on_non_tty(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys.stderr, "isatty", lambda: False)
    reporter = SubscribeProgressReporter.from_config(_config(progress_enabled=True), runner_name="runner")

    assert reporter.mode == "quiet"
    reporter.scan_started()
    reporter.level_started(server_count=10, attempt_index=1, attempt_total=1)
    reporter.level_done(metrics=_metrics(server_count=10), attempt_index=1, status=CapacityStatus.PASS, reason="")
    reporter.scan_finished()

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_subscribe_progress_reporter_uses_inline_tty_update(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    reporter = SubscribeProgressReporter.from_config(_config(progress_enabled=True), runner_name="runner")

    assert reporter.mode == "inline"
    reporter.scan_started()
    reporter.level_started(server_count=10, attempt_index=1, attempt_total=1)
    reporter.level_done(metrics=_metrics(server_count=10), attempt_index=1, status=CapacityStatus.PASS, reason="")
    reporter.scan_finished()

    err = capsys.readouterr().err
    assert "\r" in err
    assert "[source-lab] subscribe capacity" in err


def test_subscribe_report_remains_profile_friendly(capsys: pytest.CaptureFixture[str]) -> None:
    config = _config(progress_enabled=False)
    metrics = _metrics(server_count=10)
    result = SubscribeScanResult(
        config=config,
        levels=(
            SubscribeLevelResult(
                primary=metrics,
                attempts=(metrics,),
                final_status=CapacityStatus.PASS,
                final_reason="",
            ),
        ),
    )

    print_subscribe_report(result)
    output = capsys.readouterr().out

    assert "source_lab subscribe scan" in output
    assert "srv" in output and "notify" in output and "status" in output
    assert "source_update_hz=5.0" in output
    assert "src_p95" in output
    assert "src_max" in output
    assert "recv_p95" in output
    assert "lag_p95" in output
    assert "resub_ok" in output
    assert "resub_fail" in output
    assert "recovery_ms" in output


def test_subscribe_report_summary_uses_data_period_not_response_period(capsys: pytest.CaptureFixture[str]) -> None:
    config = _config(progress_enabled=False)
    metrics = _metrics(
        server_count=10,
        response_period_p95_ms=50.0,
        response_period_max_ms=50.0,
        data_period_p95_ms=100.0,
        data_period_max_ms=100.0,
    )
    result = SubscribeScanResult(
        config=config,
        levels=(
            SubscribeLevelResult(
                primary=metrics,
                attempts=(metrics,),
                final_status=CapacityStatus.PASS,
                final_reason="",
            ),
        ),
    )

    print_subscribe_report(result)
    output = capsys.readouterr().out

    assert "100.000" in output
    assert "50.000" not in output


def test_subscribe_capacity_wrapper_calls_formal_cli(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify the subscribe smoke wrapper now executes the formal CLI."""

    from tools.source_lab.tests import test_source_simulation_multi_server_subscribe_capacity as wrapper

    output_dir = tmp_path / "subscribe_capacity"

    monkeypatch.setattr(wrapper, "_fixture_path", lambda name: tmp_path / name)
    monkeypatch.setattr(wrapper, "_output_dir", lambda: output_dir)
    monkeypatch.setattr(wrapper, "_print_completed_process", lambda completed: None)

    def _fake_run_cli(command: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        """Capture CLI args and emulate generated subscribe capacity artifacts."""

        assert "--access-mode" in command
        assert "subscribe" in command
        assert "--source-update-hz-start" in command
        assert "--source-update-hz-step" in command
        assert "--source-update-hz-max" in command
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "field_capacity_demo.csv").write_text("header\n", encoding="utf-8")
        (output_dir / "field_capacity_demo.jsonl").write_text("{}\n", encoding="utf-8")
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="proc srv sub_hz src_hz sub_ms src_ms value_ratio p95_ms max_ms status reason\n",
            stderr="",
        )

    monkeypatch.setattr(wrapper, "_run_cli", _fake_run_cli)

    wrapper.test_source_simulation_multi_server_subscribe_capacity()
