"""Tests for unified access facades that dispatch by access_mode."""

from __future__ import annotations

from contextlib import nullcontext
from typing import cast

import pytest

from tools.source_lab.access.capacity import SubscribeCapacityResult, scan_capacity
from tools.source_lab.access.polling.model import (
    CapacityLevelMetrics,
    CapacityMode,
    CapacityScanConfig,
    CapacityScanResult,
    CapacityStatus,
    ConfirmedLevelResult,
)
from tools.source_lab.access.profile import run_profile
from tools.source_lab.access.providers.base import SourceProvider, SourceRuntimeSpec
from tools.source_lab.access.runners.base import CapacityRunner, SubscriptionRunner
from tools.source_lab.access.subscribe.capacity_plan import SubscribeCapacityMatrixPlan
from tools.source_lab.access.subscribe.model import (
    SubscribeLevelMetrics,
    SubscribeLevelResult,
    SubscribeScanConfig,
    SubscribeScanResult,
)


class _Provider:
    def build_sources(self, config: object, *, server_count: int) -> tuple[SourceRuntimeSpec, ...]:
        return ()

    def started(self, sources: tuple[SourceRuntimeSpec, ...]) -> object:
        return nullcontext()


class _CapacityRunner:
    name = "fake_capacity"

    def run_worker(self, worker_index: int, specs: tuple, target_hz: float, config: CapacityScanConfig) -> object:
        raise AssertionError("run_worker() should not be reached in facade dispatch tests")


class _SubscriptionRunner:
    name = "fake_subscribe"

    def run_worker(self, worker_index: int, specs: tuple, config: SubscribeScanConfig) -> object:
        raise AssertionError("run_worker() should not be reached in facade dispatch tests")


def _polling_config() -> CapacityScanConfig:
    return CapacityScanConfig(
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


def _subscribe_config() -> SubscribeScanConfig:
    return SubscribeScanConfig(
        mode=CapacityMode.FIELD,
        protocol="opcua",
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        process_count=1,
        publishing_interval_ms=200.0,
        sampling_interval_ms=200.0,
        queue_size=1,
        duration_s=1.0,
        progress_enabled=False,
        source_update_enabled=True,
        source_update_hz=5.0,
    )


def _subscribe_level_result(config: SubscribeScanConfig, *, status: CapacityStatus) -> SubscribeLevelResult:
    metrics = SubscribeLevelMetrics(
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
        publish_gap_mean_ms=1.0,
        publish_gap_p95_ms=1.0,
        publish_gap_p99_ms=1.0,
        publish_gap_max_ms=1.0,
        data_age_mean_ms=1.0,
        data_age_p95_ms=1.0,
        data_age_p99_ms=1.0,
        data_age_max_ms=1.0,
        data_period_samples=1,
        data_period_mean_ms=1.0,
        data_period_p95_ms=1.0,
        data_period_max_ms=1.0,
        allowed_data_period_max_ms=2.0,
        passed=status is CapacityStatus.PASS,
        failure_reason="" if status is CapacityStatus.PASS else "failed",
    )
    return SubscribeLevelResult(
        primary=metrics,
        attempts=(metrics,),
        final_status=status,
        final_reason="" if status is CapacityStatus.PASS else metrics.failure_reason,
    )


def _polling_level_result(*, server_count: int, hz: float, status: CapacityStatus) -> ConfirmedLevelResult:
    metrics = CapacityLevelMetrics(
        server_count=server_count,
        target_hz=hz,
        target_period_ms=1000.0 / hz,
        allowed_period_max_ms=(1000.0 / hz) * 1.2,
        allowed_period_mean_abs_error_ms=(1000.0 / hz) * 0.05,
        read_errors=0,
        batch_mismatches=0,
        missing_response_timestamps=0,
        period_samples=10,
        period_mean_ms=1000.0 / hz,
        period_p95_ms=1000.0 / hz,
        period_max_ms=1000.0 / hz,
        period_mean_abs_error_ms=0.0,
        missed_ticks=0,
        runner_max_lag_ms=0.0,
        runner_max_read_ms=0.0,
        worker_conc_sum=1,
        worker_conc_max=1,
        worker_conc_by_worker=(1,),
        value_count_ok=True,
        period_max_ok=status is CapacityStatus.PASS,
        period_mean_ok=True,
        passed=status is CapacityStatus.PASS,
        failure_reason="" if status is CapacityStatus.PASS else "data_period_max_ms=1.00>1.00",
    )
    return ConfirmedLevelResult(
        primary=metrics,
        attempts=(metrics,),
        final_status=status,
        final_reason="" if status is CapacityStatus.PASS else metrics.failure_reason,
    )


def test_capacity_facade_dispatches_polling(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = CapacityScanResult(config=_polling_config(), levels=())
    monkeypatch.setattr(
        "tools.source_lab.access.capacity.scan_source_capacity",
        lambda *args, **kwargs: expected,
    )

    result = scan_capacity(
        "polling",
        config=_polling_config(),
        provider=cast(SourceProvider, _Provider()),
        runner=cast(CapacityRunner, _CapacityRunner()),
    )

    assert result is expected


def test_capacity_facade_dispatches_subscribe(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = SubscribeScanResult(config=_subscribe_config(), levels=())
    monkeypatch.setattr(
        "tools.source_lab.access.capacity.scan_source_subscriptions",
        lambda *args, **kwargs: expected,
    )

    result = scan_capacity(
        "subscribe",
        config=_subscribe_config(),
        provider=cast(SourceProvider, _Provider()),
        runner=cast(SubscriptionRunner, _SubscriptionRunner()),
    )

    assert result is expected


def test_capacity_facade_subscribe_uses_source_update_hz_dimension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[float, float, float]] = []

    def _fake_scan_source_subscriptions(config: SubscribeScanConfig, **_: object) -> SubscribeScanResult:
        captured.append((config.nominal_sample_hz or 0.0, config.sampling_interval_ms, config.source_update_hz))
        return SubscribeScanResult(
            config=config,
            levels=(_subscribe_level_result(config, status=CapacityStatus.PASS),),
        )

    monkeypatch.setattr(
        "tools.source_lab.access.capacity.scan_source_subscriptions",
        _fake_scan_source_subscriptions,
    )

    result = scan_capacity(
        "subscribe",
        config=_subscribe_config(),
        provider=cast(SourceProvider, _Provider()),
        runner=cast(SubscriptionRunner, _SubscriptionRunner()),
        process_counts=(1,),
        sample_hz_values=(5.0, 10.0),
        queue_sizes=(1,),
        source_update_hz_values=(10.0,),
        stop_on_first_fail_per_server=False,
    )

    assert isinstance(result, SubscribeCapacityResult)
    assert len(result.combos) == 2
    assert captured == [(5.0, 200.0, 10.0), (10.0, 100.0, 10.0)]
    assert [combo.status for combo in result.combos] == [CapacityStatus.PASS, CapacityStatus.PASS]
    assert all(combo.result is not None for combo in result.combos)
    assert all(combo.executed is True for combo in result.combos)
    assert all(combo.failure_stage is None for combo in result.combos)


def test_capacity_facade_subscribe_executes_when_sample_hz_below_explicit_source_rate() -> None:
    def _fake_scan_source_subscriptions(config: SubscribeScanConfig, **_: object) -> SubscribeScanResult:
        return SubscribeScanResult(
            config=config,
            levels=(_subscribe_level_result(config, status=CapacityStatus.PASS),),
        )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "tools.source_lab.access.capacity.scan_source_subscriptions",
        _fake_scan_source_subscriptions,
    )
    try:
        result = scan_capacity(
            "subscribe",
            config=_subscribe_config(),
            provider=cast(SourceProvider, _Provider()),
            runner=cast(SubscriptionRunner, _SubscriptionRunner()),
            process_counts=(1,),
            sample_hz_values=(5.0, 10.0),
            queue_sizes=(1,),
            explicit_source_update_hz=10.0,
            stop_on_first_fail_per_server=False,
        )

        assert isinstance(result, SubscribeCapacityResult)
        assert [combo.status for combo in result.combos] == [CapacityStatus.PASS, CapacityStatus.PASS]
        assert result.combos[0].reason == ""
        assert result.combos[0].effective_source_update_hz == 10.0
        assert result.combos[0].executed is True
    finally:
        monkeypatch.undo()


def test_capacity_facade_subscribe_explicit_source_update_keeps_all_lower_hz_runnable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "tools.source_lab.access.capacity.scan_source_subscriptions",
        lambda config, **_: SubscribeScanResult(
            config=config,
            levels=(_subscribe_level_result(config, status=CapacityStatus.PASS),),
        ),
    )

    result = scan_capacity(
        "subscribe",
        config=_subscribe_config(),
        provider=cast(SourceProvider, _Provider()),
        runner=cast(SubscriptionRunner, _SubscriptionRunner()),
        process_counts=(1,),
        sample_hz_values=(5.0, 10.0, 15.0),
        queue_sizes=(1,),
        explicit_source_update_hz=15.0,
        stop_on_first_fail_per_server=False,
    )

    assert isinstance(result, SubscribeCapacityResult)
    assert [combo.status for combo in result.combos] == [
        CapacityStatus.PASS,
        CapacityStatus.PASS,
        CapacityStatus.PASS,
    ]
    assert [combo.sample_hz for combo in result.combos] == [5.0, 10.0, 15.0]
    assert all(combo.result is not None for combo in result.combos)


def test_subscribe_capacity_matrix_plan_validates_and_counts() -> None:
    plan = SubscribeCapacityMatrixPlan(
        process_counts=(1, 2),
        server_counts=(10,),
        source_update_hz_values=(10.0, 20.0),
        sample_hz_values=(10.0, 20.0, 30.0),
        queue_sizes=(1, 8),
    )

    plan.validate()

    assert plan.combo_count() == 24


def test_subscribe_capacity_matrix_plan_rejects_empty_dimensions() -> None:
    with pytest.raises(ValueError, match="process_counts must not be empty"):
        SubscribeCapacityMatrixPlan(
            process_counts=(),
            server_counts=(1,),
            source_update_hz_values=(1.0,),
            sample_hz_values=(1.0,),
            queue_sizes=(1,),
        ).validate()


def test_capacity_facade_subscribe_matrix_keeps_all_runtime_combos_after_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_sample_hz: list[float] = []

    def _fake_scan_source_subscriptions(config: SubscribeScanConfig, **_: object) -> SubscribeScanResult:
        sample_hz = config.nominal_sample_hz or 0.0
        seen_sample_hz.append(sample_hz)
        status = CapacityStatus.FAIL if sample_hz == 15.0 else CapacityStatus.PASS
        return SubscribeScanResult(
            config=config,
            levels=(_subscribe_level_result(config, status=status),),
        )

    monkeypatch.setattr(
        "tools.source_lab.access.capacity.scan_source_subscriptions",
        _fake_scan_source_subscriptions,
    )

    result = scan_capacity(
        "subscribe",
        config=_subscribe_config(),
        provider=cast(SourceProvider, _Provider()),
        runner=cast(SubscriptionRunner, _SubscriptionRunner()),
        process_counts=(1,),
        sample_hz_values=(10.0, 15.0, 20.0),
        queue_sizes=(1,),
        source_update_hz_values=(10.0,),
    )

    assert isinstance(result, SubscribeCapacityResult)
    assert len(result.combos) == 3
    assert seen_sample_hz == [10.0, 15.0, 20.0]
    assert [combo.status for combo in result.combos] == [
        CapacityStatus.PASS,
        CapacityStatus.FAIL,
        CapacityStatus.PASS,
    ]


def test_capacity_facade_polling_process_ramp_builds_independent_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[int, int, float]] = []

    def _fake_scan_source_capacity(config: CapacityScanConfig, **_: object) -> CapacityScanResult:
        calls.append((config.process_count, config.server_count_start, config.hz_start))
        return CapacityScanResult(
            config=config,
            levels=(
                _polling_level_result(
                    server_count=config.server_count_start,
                    hz=config.hz_start,
                    status=CapacityStatus.PASS,
                ),
            ),
        )

    monkeypatch.setattr("tools.source_lab.access.capacity.scan_source_capacity", _fake_scan_source_capacity)

    result = scan_capacity(
        "polling",
        config=CapacityScanConfig(
            mode=CapacityMode.FIELD,
            protocol="opcua",
            endpoints=(),
            points=(),
            server_count_start=10,
            server_count_step=10,
            server_count_max=20,
            hz_start=5.0,
            hz_step=5.0,
            hz_max=10.0,
            process_count=1,
            progress_enabled=False,
        ),
        provider=cast(SourceProvider, _Provider()),
        runner=cast(CapacityRunner, _CapacityRunner()),
        process_counts=(1, 3),
    )

    assert isinstance(result, tuple)
    assert tuple(item.config.process_count for item in result) == (1, 3)
    assert tuple(len(item.levels) for item in result) == (4, 4)
    assert calls == [
        (1, 10, 5.0),
        (1, 10, 10.0),
        (1, 20, 5.0),
        (1, 20, 10.0),
        (3, 10, 5.0),
        (3, 10, 10.0),
        (3, 20, 5.0),
        (3, 20, 10.0),
    ]


def test_capacity_facade_polling_stop_hz_ramp_only_for_current_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[int, float]] = []

    def _fake_scan_source_capacity(config: CapacityScanConfig, **_: object) -> CapacityScanResult:
        calls.append((config.server_count_start, config.hz_start))
        status = CapacityStatus.FAIL if (config.server_count_start, config.hz_start) == (10, 5.0) else CapacityStatus.PASS
        return CapacityScanResult(
            config=config,
            levels=(
                _polling_level_result(
                    server_count=config.server_count_start,
                    hz=config.hz_start,
                    status=status,
                ),
            ),
        )

    monkeypatch.setattr("tools.source_lab.access.capacity.scan_source_capacity", _fake_scan_source_capacity)

    result = scan_capacity(
        "polling",
        config=CapacityScanConfig(
            mode=CapacityMode.FIELD,
            protocol="opcua",
            endpoints=(),
            points=(),
            server_count_start=10,
            server_count_step=10,
            server_count_max=20,
            hz_start=5.0,
            hz_step=5.0,
            hz_max=10.0,
            process_count=1,
            stop_hz_ramp_on_first_fail=True,
            progress_enabled=False,
        ),
        provider=cast(SourceProvider, _Provider()),
        runner=cast(CapacityRunner, _CapacityRunner()),
        process_counts=(1,),
    )

    assert isinstance(result, tuple)
    assert len(result) == 1
    assert len(result[0].levels) == 3
    assert calls == [
        (10, 5.0),
        (20, 5.0),
        (20, 10.0),
    ]


def test_capacity_facade_rejects_invalid_access_mode() -> None:
    with pytest.raises(ValueError, match="unsupported access_mode"):
        scan_capacity(
            "invalid",
            config=_polling_config(),
            provider=cast(SourceProvider, _Provider()),
            runner=cast(CapacityRunner, _CapacityRunner()),
        )


def test_profile_facade_dispatches_polling(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = object()
    monkeypatch.setattr(
        "tools.source_lab.access.profile.run_polling_profile",
        lambda *args, **kwargs: expected,
    )

    result = run_profile(
        "polling",
        config=_polling_config(),
        provider=cast(SourceProvider, _Provider()),
        runner=cast(CapacityRunner, _CapacityRunner()),
    )

    assert result is expected


def test_profile_facade_dispatches_subscribe(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = object()
    monkeypatch.setattr(
        "tools.source_lab.access.profile.run_subscribe_profile",
        lambda *args, **kwargs: expected,
    )

    result = run_profile(
        "subscribe",
        config=_subscribe_config(),
        provider=cast(SourceProvider, _Provider()),
        runner=cast(SubscriptionRunner, _SubscriptionRunner()),
    )

    assert result is expected


def test_profile_facade_rejects_invalid_access_mode() -> None:
    with pytest.raises(ValueError, match="unsupported access_mode"):
        run_profile(
            "invalid",
            config=_polling_config(),
            provider=cast(SourceProvider, _Provider()),
            runner=cast(CapacityRunner, _CapacityRunner()),
        )
