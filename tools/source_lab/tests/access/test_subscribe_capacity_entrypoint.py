"""Tests for subscribe-specific capacity service entrypoint."""

from __future__ import annotations

from contextlib import nullcontext
from typing import cast

from tools.source_lab.access.polling.model import CapacityMode
from tools.source_lab.access.providers.base import SourceProvider, SourceRuntimeSpec
from tools.source_lab.access.runners.base import SubscriptionRunner
from tools.source_lab.access.subscribe.capacity import (
    SubscribeCapacityResult,
    scan_subscribe_capacity_service,
)
from tools.source_lab.access.subscribe.capacity_model import SubscribeCapacityLimitSummary
from tools.source_lab.access.subscribe.capacity_plan import SubscribeCapacityMatrixPlan
from tools.source_lab.access.subscribe.model import SubscribeScanConfig
import pytest


class _Provider:
    def build_sources(self, config: object, *, server_count: int) -> tuple[SourceRuntimeSpec, ...]:
        return ()

    def started(self, sources: tuple[SourceRuntimeSpec, ...]) -> object:
        return nullcontext()


class _Runner:
    name = "fake_subscribe_runner"

    def run_worker(self, worker_index: int, specs: tuple, config: SubscribeScanConfig) -> object:
        raise AssertionError("run_worker should not be called in facade delegation tests")


def _config() -> SubscribeScanConfig:
    return SubscribeScanConfig(
        mode=CapacityMode.FIELD,
        protocol="opcua",
        server_count_start=10,
        server_count_step=10,
        server_count_max=20,
        process_count=1,
        publishing_interval_ms=100.0,
        sampling_interval_ms=100.0,
        queue_size=1,
        source_update_enabled=True,
        source_update_hz=10.0,
        progress_enabled=False,
    )


def test_subscribe_capacity_service_builds_matrix_plan_and_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}
    expected = SubscribeCapacityResult(combos=(), limit_summaries=())

    def _fake_scan_subscribe_capacity(*args, **kwargs):
        observed["args"] = args
        observed["kwargs"] = kwargs
        return expected

    monkeypatch.setattr(
        "tools.source_lab.access.subscribe.capacity.scan_subscribe_capacity",
        _fake_scan_subscribe_capacity,
    )

    result = scan_subscribe_capacity_service(
        _config(),
        provider=cast(SourceProvider, _Provider()),
        runner=cast(SubscriptionRunner, _Runner()),
        process_counts=(1, 2),
        sample_hz_values=(5.0, 10.0),
        queue_sizes=(1, 2),
        source_update_hz_values=(10.0, 20.0),
        explicit_publishing_interval_ms=80.0,
        stop_on_first_fail_per_server=False,
    )

    assert result is expected
    assert observed["args"] == (_config(),)
    kwargs = cast(dict[str, object], observed["kwargs"])
    plan = cast(SubscribeCapacityMatrixPlan, kwargs["plan"])
    assert plan.process_counts == (1, 2)
    assert plan.server_counts == (10, 20)
    assert plan.source_update_hz_values == (10.0, 20.0)
    assert plan.sample_hz_values == (5.0, 10.0)
    assert plan.queue_sizes == (1, 2)
    assert kwargs["explicit_publishing_interval_ms"] == 80.0
    assert kwargs["stop_on_runtime_fail"] is False
    assert kwargs["stop_on_recovery_fail"] is False


def test_subscribe_capacity_service_uses_config_source_update_hz_when_not_overridden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_plan: SubscribeCapacityMatrixPlan | None = None

    def _fake_scan_subscribe_capacity(*args, **kwargs):
        nonlocal captured_plan
        captured_plan = cast(SubscribeCapacityMatrixPlan, kwargs["plan"])
        return SubscribeCapacityResult(
            combos=(),
            limit_summaries=(
                SubscribeCapacityLimitSummary(
                    process_count=1,
                    server_count=10,
                    queue_size=1,
                    effective_source_update_hz=10.0,
                    max_pass_sample_hz=10.0,
                    first_fail_sample_hz=None,
                    reason="",
                ),
            ),
        )

    monkeypatch.setattr(
        "tools.source_lab.access.subscribe.capacity.scan_subscribe_capacity",
        _fake_scan_subscribe_capacity,
    )

    scan_subscribe_capacity_service(
        _config(),
        provider=cast(SourceProvider, _Provider()),
        runner=cast(SubscriptionRunner, _Runner()),
        process_counts=(1,),
        sample_hz_values=(10.0,),
        queue_sizes=(1,),
        source_update_hz_values=None,
    )

    assert captured_plan is not None
    assert captured_plan.source_update_hz_values == (10.0,)