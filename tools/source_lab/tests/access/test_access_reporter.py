"""Tests for capacity reporter summary semantics."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tools.source_lab.access.metrics import RunnerSummary, RunnerTrace, WorkerRawStats
from tools.source_lab.access.model import (
    CapacityMode,
    CapacityScanConfig,
    CapacityLevelMetrics,
    CapacityScanResult,
    CapacityStatus,
    ConfirmedLevelResult,
)
from tools.source_lab.access.reporter import (
    print_capacity_report,
    print_level_done,
    print_measurement_progress,
    print_scan_started,
    print_worker_diagnostics,
    summarize_server_count_levels,
)


def _config(*, progress_enabled: bool = True) -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=2,
        hz_start=10.0,
        hz_step=10.0,
        hz_max=20.0,
        process_count=1,
        progress_enabled=progress_enabled,
        progress_interval_s=2.0,
    )


def _level(server_count: int, hz: float, status: CapacityStatus) -> ConfirmedLevelResult:
    metrics = CapacityLevelMetrics(
        server_count=server_count,
        target_hz=hz,
        target_period_ms=1000.0 / hz,
        allowed_period_max_ms=1000.0 / hz,
        allowed_period_mean_abs_error_ms=1.0,
        read_errors=0,
        batch_mismatches=0,
        missing_response_timestamps=0,
        period_samples=10,
        period_mean_ms=1000.0 / hz,
        period_max_ms=1000.0 / hz,
        period_mean_abs_error_ms=0.1,
        missed_ticks=0,
        runner_max_lag_ms=0.0,
        runner_max_read_ms=0.0,
        worker_conc_sum=2,
        worker_conc_max=2,
        worker_conc_by_worker=(2,),
        value_count_ok=True,
        period_max_ok=True,
        period_mean_ok=True,
        passed=status in {CapacityStatus.PASS, CapacityStatus.FLAKY},
        failure_reason="",
        worst_gap=None,
        top_gaps=(),
    )
    return ConfirmedLevelResult(
        primary=metrics,
        attempts=(metrics,),
        final_status=status,
        final_reason="",
    )


def test_summary_distinguishes_stable_flaky_fail() -> None:
    levels = (
        _level(1, 10.0, CapacityStatus.PASS),
        _level(1, 20.0, CapacityStatus.PASS),
        _level(1, 30.0, CapacityStatus.FLAKY),
        _level(1, 40.0, CapacityStatus.FAIL),
    )

    summaries = summarize_server_count_levels(levels, accept_flaky_as_pass=False)

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.stable_pass_hz == 20.0
    assert summary.first_flaky_hz == 30.0
    assert summary.first_fail_hz == 40.0
    assert summary.best_accepted_hz == 20.0


def test_summary_can_accept_flaky_when_enabled() -> None:
    levels = (
        _level(2, 10.0, CapacityStatus.PASS),
        _level(2, 20.0, CapacityStatus.FLAKY),
    )

    summaries = summarize_server_count_levels(levels, accept_flaky_as_pass=True)

    assert len(summaries) == 1
    assert summaries[0].best_accepted_hz == 20.0


def test_progress_output_contains_key_fields(capsys: pytest.CaptureFixture[str]) -> None:
    """Progress helpers should emit stable key fields."""

    config = _config()
    metrics = _level(1, 10.0, CapacityStatus.PASS).primary

    print_scan_started(config, runner_name="fake_runner")
    print_measurement_progress(
        config,
        server_count=1,
        target_hz=10.0,
        elapsed_s=2.0,
        ticks=20,
        bad=0,
    )
    print_level_done(
        config,
        metrics=metrics,
        attempt_index=1,
        status=CapacityStatus.PASS,
        reason="",
    )

    output = capsys.readouterr().out
    assert "[source-lab] capacity scan started:" in output
    assert "runner=fake_runner" in output
    assert "preflight" not in output
    assert "[source-lab] measurement progress: srv=1 hz=10.0" in output
    assert "elapsed=2.0/30.0s ticks=20 bad=0" in output
    assert "[source-lab] level done: srv=1 hz=10.0 attempt=1 status=PASS" in output


def test_progress_output_can_be_disabled(capsys: pytest.CaptureFixture[str]) -> None:
    """Disabled progress config should suppress progress helpers."""

    config = _config(progress_enabled=False)
    metrics = _level(1, 10.0, CapacityStatus.PASS).primary

    print_scan_started(config, runner_name="fake_runner")
    print_level_done(
        config,
        metrics=metrics,
        attempt_index=1,
        status=CapacityStatus.PASS,
        reason="",
    )

    assert capsys.readouterr().out == ""


def test_worker_diagnostics_prints_summaries_and_top_traces(
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = replace(_config(), runner_trace_enabled=True, runner_trace_top_n=2)
    worker_stats = (
        WorkerRawStats(
            worker_index=0,
            reader_count=1,
            batch_mismatches=0,
            read_errors=0,
            missing_response_timestamps=0,
            response_timestamps_by_reader=((1.0,),),
            max_observed_concurrent_reads=1,
            runner_summary=RunnerSummary(
                worker_index=0,
                endpoint_count=1,
                total_reads=10,
                ok_reads=10,
                bad_reads=0,
                read_errors=0,
                missing_response_timestamps=0,
                missed_ticks=2,
                max_lag_ms=3.5,
                max_read_ms=4.5,
                warmup_reads=2,
                warmup_errors=0,
                warmup_max_lag_ms=0.5,
                warmup_max_read_ms=0.7,
            ),
            top_lag_traces=(
                RunnerTrace(0, 1, 11, 7, 3.5, 2.0),
                RunnerTrace(0, 0, 10, 6, 2.5, 1.0),
            ),
            top_read_traces=(
                RunnerTrace(0, 1, 11, 7, 3.5, 4.5),
                RunnerTrace(0, 0, 10, 6, 2.5, 3.0),
            ),
        ),
    )

    print_worker_diagnostics(config, worker_stats)

    output = capsys.readouterr().out
    assert "runner summaries:" in output
    assert "worker=0 endpoints=1 total=10" in output
    assert "missed=2 max_lag=3.500ms max_read=4.500ms" in output
    assert "top runner lag:" in output
    assert "top runner read:" in output
    assert "worker=0 local=1 global=11 tick=7 lag_ms=3.500 read_ms=2.000" in output
    assert "worker=0 local=1 global=11 tick=7 lag_ms=3.500 read_ms=4.500" in output


def test_worker_diagnostics_skips_top_trace_when_disabled(
    capsys: pytest.CaptureFixture[str],
) -> None:
    worker_stats = (
        WorkerRawStats(
            worker_index=0,
            reader_count=0,
            batch_mismatches=0,
            read_errors=0,
            missing_response_timestamps=0,
            response_timestamps_by_reader=(),
            max_observed_concurrent_reads=0,
        ),
    )

    print_worker_diagnostics(_config(progress_enabled=True), worker_stats)

    assert capsys.readouterr().out == ""


def test_capacity_report_omits_preflight_and_keeps_core_columns(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = CapacityScanResult(config=_config(), levels=(_level(1, 10.0, CapacityStatus.PASS),))

    print_capacity_report(result)

    output = capsys.readouterr().out
    assert "preflight" not in output
    assert "open62541_serial_runner" not in output
    assert "srv" in output
    assert "hz" in output
    assert "period" in output
    assert "bad" in output
    assert "p_n" in output
    assert "p_mean" in output
    assert "p_max" in output
    assert "mean_err" in output
    assert "status" in output
    assert "reason" in output
