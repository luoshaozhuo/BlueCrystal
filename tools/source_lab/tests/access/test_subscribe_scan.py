"""Tests for subscribe scan attempt selection and result presentation."""

from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext

import pytest

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec

from tools.source_lab.access.polling.model import CapacityMode, CapacityStatus
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.common.access_model import AccessMode, AccessRunSummary
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.subscribe.model import (
    SubscribeLevelMetrics,
    SubscribeScanConfig,
    SubscribeWorkerRawStats,
)
from tools.source_lab.access.subscribe.scan import scan_source_subscriptions
from tools.source_lab.access.polling.model import CapacityScanConfig


class _Provider:
    """Minimal provider used to isolate subscribe scan result selection."""

    def build_sources(
        self,
        config: CapacityScanConfig | SubscribeScanConfig,
        *,
        server_count: int,
    ) -> tuple[SourceRuntimeSpec, ...]:
        """Build one static source per requested server."""

        endpoint = SourceEndpointSpec(
            name="source-1",
            host="127.0.0.1",
            port=48001,
            protocol="opcua",
        )
        point = SourcePointSpec(address="IED.LD.LN.DO")
        return tuple(SourceRuntimeSpec(endpoint=endpoint, points=(point,)) for _ in range(server_count))

    def started(
        self,
        sources: tuple[SourceRuntimeSpec, ...],
    ) -> AbstractContextManager[None]:
        """Provide a no-op lifecycle context."""

        return nullcontext()


class _Runner:
    """Minimal runner stub for scan entrypoint wiring."""

    name = "fake_subscribe_runner"

    def run_worker(
        self,
        worker_index: int,
        specs: tuple[RunnerEndpointPlan, ...],
        config: SubscribeScanConfig,
    ) -> SubscribeWorkerRawStats:
        """返回最小订阅 worker 统计，满足 SubscriptionRunner 协议。"""

        _ = config
        return SubscribeWorkerRawStats(
            worker_index=worker_index,
            endpoint_count=len(specs),
            expected_monitored_items=1,
            monitored_created=1,
            monitored_failed=0,
            batches=(),
            notification_count=1,
            value_count=1,
            bad_count=0,
            missing_ts_count=0,
            reserved_sequence_gap_count=0,
            reserved_queue_overflow_count=0,
            keepalive_count=0,
            publish_timeout_count=0,
            reconnect_count=0,
            summary=AccessRunSummary(
                access_mode=AccessMode.SUBSCRIBE,
                worker_index=worker_index,
                endpoint_count=len(specs),
                expected_point_count=1,
                batch_count=1,
                value_count=1,
                bad_count=0,
                missing_timestamp_count=0,
                error_count=0,
            ),
        )


def _config() -> SubscribeScanConfig:
    """Build a two-attempt subscribe config for scan tests."""

    return SubscribeScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        process_count=1,
        publishing_interval_ms=100.0,
        sampling_interval_ms=100.0,
        queue_size=1,
        duration_s=1.0,
        fail_confirm_runs=2,
        progress_enabled=False,
    )


def _metrics(*, passed: bool, failure_reason: str) -> SubscribeLevelMetrics:
    """Build one minimal level metrics object for attempt selection tests."""

    return SubscribeLevelMetrics(
        server_count=1,
        process_count=1,
        publishing_interval_ms=100.0,
        sampling_interval_ms=100.0,
        effective_source_update_hz=10.0,
        queue_size=1,
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
        data_period_mean_ms=100.0,
        data_period_p95_ms=100.0,
        data_period_max_ms=100.0,
        allowed_data_period_max_ms=120.0,
        passed=passed,
        failure_reason=failure_reason,
    )


def test_scan_uses_passing_attempt_as_primary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Subscribe scan should present the passing confirmation attempt as primary."""

    first = _metrics(passed=False, failure_reason="notification_timeout")
    second = _metrics(passed=True, failure_reason="")
    attempts = iter((first, second))

    monkeypatch.setattr(
        "tools.source_lab.access.subscribe.scan.run_subscribe_level_once",
        lambda *args, **kwargs: next(attempts),
    )

    result = scan_source_subscriptions(_config(), provider=_Provider(), runner=_Runner())

    assert len(result.levels) == 1
    level = result.levels[0]
    assert level.final_status == CapacityStatus.PASS
    assert level.primary is second
    assert level.final_metrics is second
    assert level.attempts == (first, second)
