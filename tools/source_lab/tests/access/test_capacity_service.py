"""Tests for production field-capacity service functions."""

from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path
from typing import Any, cast

import pytest

from tools.source_lab.access.capacity import FieldCapacityRequest, run_field_capacity
from tools.source_lab.access.polling.model import (
    CapacityLevelMetrics,
    CapacityMode,
    CapacityScanConfig,
    CapacityScanResult,
    CapacityStatus,
    ConfirmedLevelResult,
)
from tools.source_lab.access.subscribe.model import (
    SubscribeLevelMetrics,
    SubscribeLevelResult,
    SubscribeScanConfig,
    SubscribeScanResult,
)


class _Provider:
    def build_sources(self, config: object, *, server_count: int) -> tuple[object, ...]:
        return ()

    def started(self, sources: tuple[object, ...]) -> object:
        return nullcontext()


def _polling_result(*, warnings: tuple[str, ...], reason: str = "") -> CapacityScanResult:
    config = CapacityScanConfig(
        mode=CapacityMode.FIELD,
        protocol="opcua",
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        hz_start=5.0,
        hz_step=5.0,
        hz_max=5.0,
        process_count=1,
        progress_enabled=False,
    )
    return CapacityScanResult(
        config=config,
        levels=(
            ConfirmedLevelResult(
                primary=CapacityLevelMetrics(
                    server_count=1,
                    target_hz=5.0,
                    target_period_ms=200.0,
                    allowed_period_max_ms=240.0,
                    allowed_period_mean_abs_error_ms=10.0,
                    read_errors=0,
                    batch_mismatches=0,
                    missing_response_timestamps=0,
                    period_samples=10,
                    period_mean_ms=200.0,
                    period_p95_ms=200.0,
                    period_max_ms=200.0,
                    period_mean_abs_error_ms=0.0,
                    missed_ticks=0,
                    runner_max_lag_ms=0.0,
                    runner_max_read_ms=0.0,
                    worker_conc_sum=1,
                    worker_conc_max=1,
                    worker_conc_by_worker=(1,),
                    value_count_ok=True,
                    period_max_ok=True,
                    period_mean_ok=True,
                    passed=True,
                    failure_reason=reason,
                    points_per_server=3,
                    point_total=3,
                    expected_value_count=450,
                    value_count=450,
                    value_delivery_ratio=1.0,
                    value_missing_count=0,
                    read_count=150,
                    batch_count=150,
                    worst_gap=None,
                    top_gaps=(),
                    warnings=warnings,
                ),
                attempts=(),
                final_status=CapacityStatus.PASS if not reason else CapacityStatus.FAIL,
                final_reason=reason,
            ),
        ),
    )


def _subscribe_scan_result(
    config: SubscribeScanConfig,
    *,
    passed: bool,
    reason: str,
    warnings: tuple[str, ...] = (),
) -> SubscribeScanResult:
    level_metrics = SubscribeLevelMetrics(
        server_count=config.server_count_start,
        process_count=config.process_count,
        publishing_interval_ms=config.publishing_interval_ms,
        sampling_interval_ms=config.sampling_interval_ms,
        effective_source_update_hz=config.source_update_hz,
        queue_size=config.queue_size,
        expected_monitored_items=1,
        monitored_created=1,
        monitored_failed=0,
        notification_count=1,
        value_count=1,
        bad_count=0,
        missing_ts_count=0,
        reserved_sequence_gap_count=0,
        reserved_queue_overflow_count=0,
        keepalive_count=0,
        publish_timeout_count=0,
        reconnect_count=0,
        notification_rate=1.0,
        value_rate=1.0,
        publish_gap_mean_ms=100.0,
        publish_gap_p95_ms=100.0,
        publish_gap_p99_ms=100.0,
        publish_gap_max_ms=100.0,
        data_age_mean_ms=1.0,
        data_age_p95_ms=1.0,
        data_age_p99_ms=1.0,
        data_age_max_ms=1.0,
        data_period_samples=1,
        data_period_mean_ms=200.0,
        data_period_p95_ms=200.0,
        data_period_max_ms=200.0,
        allowed_data_period_max_ms=240.0,
        passed=passed,
        failure_reason=reason,
        points_per_server=1,
        point_total=1,
        expected_notification_count=50,
        expected_value_count=50,
        value_delivery_ratio=0.02,
        value_missing_count=49,
        warnings=warnings,
    )
    level_result = SubscribeLevelResult(
        primary=level_metrics,
        attempts=(level_metrics,),
        final_status=CapacityStatus.PASS if passed else CapacityStatus.FAIL,
        final_reason="" if passed else reason,
    )
    return SubscribeScanResult(config=config, levels=(level_result,))


def test_polling_pass_keeps_reason_empty_and_cpu_warning_in_warnings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldCapacityRequest(
        access_mode="polling",
        protocol="opcua",
        service_type=None,
        process_counts=(1,),
        server_counts=(1,),
        hz_values=(5.0,),
        output_dir=tmp_path,
        run_id="testrun",
    )
    monkeypatch.setattr(
        "tools.source_lab.access.field_capacity.scan_source_capacity",
        lambda *args, **kwargs: _polling_result(warnings=()),
    )
    monkeypatch.setattr("tools.source_lab.access.field_capacity.CpuSampler.start", lambda self: None)
    monkeypatch.setattr(
        "tools.source_lab.access.field_capacity.CpuSampler.stop",
        lambda self: type(
            "_Cpu",
            (),
            {"cpu_mean_pct": 0.0, "cpu_max_pct": 0.0, "rss_mb": 0.0, "warning": "psutil_not_installed"},
        )(),
    )

    result = run_field_capacity(request, provider=cast(Any, _Provider()), point_count_per_server=3)

    assert result.rows[0].status == CapacityStatus.PASS.value
    assert result.rows[0].reason == ""
    assert "psutil_not_installed" in result.rows[0].warnings
    assert result.rows[0].expected_values == 450
    assert result.rows[0].values == 450
    assert result.rows[0].value_ratio == 1.0


def test_subscribe_pass_keeps_reason_empty_and_cpu_warning_in_warnings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldCapacityRequest(
        access_mode="subscribe",
        protocol="opcua",
        service_type=None,
        process_counts=(1,),
        server_counts=(1,),
        sample_hz_values=(5.0,),
        queue_sizes=(1,),
        output_dir=tmp_path,
        run_id="testrun",
    )

    monkeypatch.setattr(
        "tools.source_lab.access.capacity.scan_source_subscriptions",
        lambda config, **kwargs: _subscribe_scan_result(config, passed=True, reason=""),
    )
    monkeypatch.setattr("tools.source_lab.access.field_capacity.CpuSampler.start", lambda self: None)
    monkeypatch.setattr(
        "tools.source_lab.access.field_capacity.CpuSampler.stop",
        lambda self: type(
            "_Cpu",
            (),
            {"cpu_mean_pct": 0.0, "cpu_max_pct": 0.0, "rss_mb": 0.0, "warning": "psutil_not_installed"},
        )(),
    )

    result = run_field_capacity(request, provider=cast(Any, _Provider()), point_count_per_server=3)

    assert result.rows[0].status == CapacityStatus.PASS.value
    assert result.rows[0].reason == ""
    assert "psutil_not_installed" in result.rows[0].warnings
    assert result.rows[0].expected_values == 50
    assert result.rows[0].values == 1
    assert result.rows[0].expected_items == 1
    assert result.rows[0].created_items == 1


def test_subscribe_fail_keeps_business_reason_when_cpu_warning_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldCapacityRequest(
        access_mode="subscribe",
        protocol="opcua",
        service_type=None,
        process_counts=(1,),
        server_counts=(1,),
        sample_hz_values=(5.0,),
        queue_sizes=(1,),
        output_dir=tmp_path,
        run_id="testrun",
    )

    monkeypatch.setattr(
        "tools.source_lab.access.capacity.scan_source_subscriptions",
        lambda config, **kwargs: _subscribe_scan_result(config, passed=False, reason="notification_timeout"),
    )
    monkeypatch.setattr("tools.source_lab.access.field_capacity.CpuSampler.start", lambda self: None)
    monkeypatch.setattr(
        "tools.source_lab.access.field_capacity.CpuSampler.stop",
        lambda self: type(
            "_Cpu",
            (),
            {"cpu_mean_pct": 0.0, "cpu_max_pct": 0.0, "rss_mb": 0.0, "warning": "psutil_not_installed"},
        )(),
    )

    result = run_field_capacity(request, provider=cast(Any, _Provider()), point_count_per_server=3)

    assert result.rows[0].status == CapacityStatus.FAIL.value
    assert result.rows[0].reason == "notification_timeout"
    assert "psutil_not_installed" in result.rows[0].warnings


def test_subscribe_derives_interval_and_source_update_per_sample_hz(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldCapacityRequest(
        access_mode="subscribe",
        protocol="opcua",
        service_type=None,
        process_counts=(1,),
        server_counts=(1,),
        sample_hz_values=(5.0, 10.0),
        queue_sizes=(1,),
        output_dir=tmp_path,
        run_id="testrun",
        source_update_enabled=True,
        source_update_hz=None,
    )
    captured: list[SubscribeScanConfig] = []

    def _fake_subscribe_scan(config: SubscribeScanConfig, **kwargs: object) -> SubscribeScanResult:
        captured.append(config)
        return _subscribe_scan_result(config, passed=True, reason="")

    monkeypatch.setattr("tools.source_lab.access.capacity.scan_source_subscriptions", _fake_subscribe_scan)
    monkeypatch.setattr("tools.source_lab.access.field_capacity.CpuSampler.start", lambda self: None)
    monkeypatch.setattr(
        "tools.source_lab.access.field_capacity.CpuSampler.stop",
        lambda self: type("_Cpu", (), {"cpu_mean_pct": 0.0, "cpu_max_pct": 0.0, "rss_mb": 0.0, "warning": ""})(),
    )

    run_field_capacity(request, provider=cast(Any, _Provider()), point_count_per_server=3)

    assert [config.publishing_interval_ms for config in captured] == [200.0, 100.0]
    assert [config.sampling_interval_ms for config in captured] == [200.0, 100.0]
    assert [config.source_update_hz for config in captured] == [5.0, 5.0]


def test_subscribe_uses_explicit_publishing_interval_for_all_sample_hz(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldCapacityRequest(
        access_mode="subscribe",
        protocol="opcua",
        service_type=None,
        process_counts=(1,),
        server_counts=(1,),
        sample_hz_values=(5.0, 10.0),
        publishing_interval_ms=250.0,
        queue_sizes=(1,),
        output_dir=tmp_path,
        run_id="testrun",
        source_update_enabled=True,
        source_update_hz=None,
    )
    captured: list[SubscribeScanConfig] = []

    def _fake_subscribe_scan(config: SubscribeScanConfig, **kwargs: object) -> SubscribeScanResult:
        captured.append(config)
        return _subscribe_scan_result(config, passed=True, reason="")

    monkeypatch.setattr("tools.source_lab.access.capacity.scan_source_subscriptions", _fake_subscribe_scan)
    monkeypatch.setattr("tools.source_lab.access.field_capacity.CpuSampler.start", lambda self: None)
    monkeypatch.setattr(
        "tools.source_lab.access.field_capacity.CpuSampler.stop",
        lambda self: type("_Cpu", (), {"cpu_mean_pct": 0.0, "cpu_max_pct": 0.0, "rss_mb": 0.0, "warning": ""})(),
    )

    run_field_capacity(request, provider=cast(Any, _Provider()), point_count_per_server=3)

    assert [config.publishing_interval_ms for config in captured] == [250.0, 250.0]
    assert [config.sampling_interval_ms for config in captured] == [200.0, 100.0]


def test_subscribe_keeps_pass_when_source_update_hz_below_sample_hz(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldCapacityRequest(
        access_mode="subscribe",
        protocol="opcua",
        service_type=None,
        process_counts=(1,),
        server_counts=(1,),
        sample_hz_values=(5.0, 10.0),
        queue_sizes=(1,),
        output_dir=tmp_path,
        run_id="testrun",
        source_update_enabled=True,
        source_update_hz=5.0,
    )

    monkeypatch.setattr(
        "tools.source_lab.access.capacity.scan_source_subscriptions",
        lambda config, **kwargs: _subscribe_scan_result(config, passed=True, reason=""),
    )
    monkeypatch.setattr("tools.source_lab.access.field_capacity.CpuSampler.start", lambda self: None)
    monkeypatch.setattr(
        "tools.source_lab.access.field_capacity.CpuSampler.stop",
        lambda self: type("_Cpu", (), {"cpu_mean_pct": 0.0, "cpu_max_pct": 0.0, "rss_mb": 0.0, "warning": ""})(),
    )

    result = run_field_capacity(request, provider=cast(Any, _Provider()), point_count_per_server=3)

    assert [row.status for row in result.rows] == [CapacityStatus.PASS.value, CapacityStatus.PASS.value]
    assert result.rows[1].reason == ""


def test_source_update_disabled_adds_warning_without_overwriting_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldCapacityRequest(
        access_mode="subscribe",
        protocol="opcua",
        service_type=None,
        process_counts=(1,),
        server_counts=(1,),
        sample_hz_values=(5.0, 10.0),
        queue_sizes=(1,),
        output_dir=tmp_path,
        run_id="testrun",
        source_update_enabled=False,
        source_update_hz=1.0,
    )

    monkeypatch.setattr(
        "tools.source_lab.access.capacity.scan_source_subscriptions",
        lambda config, **kwargs: _subscribe_scan_result(config, passed=False, reason="notification_timeout"),
    )
    monkeypatch.setattr("tools.source_lab.access.field_capacity.CpuSampler.start", lambda self: None)
    monkeypatch.setattr(
        "tools.source_lab.access.field_capacity.CpuSampler.stop",
        lambda self: type("_Cpu", (), {"cpu_mean_pct": 0.0, "cpu_max_pct": 0.0, "rss_mb": 0.0, "warning": ""})(),
    )

    result = run_field_capacity(request, provider=cast(Any, _Provider()), point_count_per_server=3)

    assert result.rows
    for row in result.rows:
        assert row.reason == "notification_timeout"
        assert "source_update_disabled" in row.warnings
