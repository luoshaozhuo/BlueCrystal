"""Tests for runtime progress output during capacity scans."""

from __future__ import annotations

from contextlib import nullcontext

import pytest

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec
from tools.source_lab.access.capacity import scan_source_capacity
from tools.source_lab.access.model import CapacityLevelMetrics, CapacityMode, CapacityScanConfig
from tools.source_lab.access.providers.base import SourceRuntimeSpec


class _Provider:
    def build_sources(
        self,
        config: CapacityScanConfig,
        *,
        server_count: int,
    ) -> tuple[SourceRuntimeSpec, ...]:
        endpoint = SourceEndpointSpec(
            name=f"source-{server_count}",
            host="127.0.0.1",
            port=48000 + server_count,
            protocol="opcua",
        )
        points = (SourcePointSpec(address="IED.LD.LN.DO"),)
        return tuple(SourceRuntimeSpec(endpoint=endpoint, points=points) for _ in range(server_count))

    def started(self, sources: tuple[SourceRuntimeSpec, ...]):
        return nullcontext()


class _Runner:
    name = "fake_runner"


def _config(*, progress_enabled: bool = True) -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.SIMULATOR,
        protocol="opcua",
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        hz_start=10.0,
        hz_step=10.0,
        hz_max=10.0,
        process_count=1,
        warmup_s=0.1,
        level_duration_s=0.1,
        progress_enabled=progress_enabled,
        progress_interval_s=0.1,
    )


def _passing_metrics() -> CapacityLevelMetrics:
    return CapacityLevelMetrics(
        server_count=1,
        target_hz=10.0,
        target_period_ms=100.0,
        allowed_period_max_ms=120.0,
        allowed_period_mean_abs_error_ms=5.0,
        read_errors=0,
        batch_mismatches=0,
        missing_response_timestamps=0,
        period_samples=10,
        period_mean_ms=100.5,
        period_max_ms=104.2,
        period_mean_abs_error_ms=1.1,
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
        failure_reason="",
        worst_gap=None,
        top_gaps=(),
    )


def test_scan_progress_output_contains_main_stages(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Capacity scan should emit key progress stages while running."""

    config = _config()
    provider = _Provider()
    runner = _Runner()

    monkeypatch.setattr(
        "tools.source_lab.access.capacity.run_level_once",
        lambda sources, *, target_hz, config, runner: _passing_metrics(),
    )

    result = scan_source_capacity(config, provider=provider, runner=runner)

    output = capsys.readouterr().out
    assert result.levels
    assert "[source-lab] capacity scan started:" in output
    assert "runner=fake_runner" in output
    assert "preflight" not in output
    assert "[source-lab] level start: srv=1 hz=10.0 attempt=1/2 period=100.0ms" in output
    assert "[source-lab] measurement start: srv=1 hz=10.0 warmup=0.1s duration=0.1s" in output
    assert "[source-lab] level done: srv=1 hz=10.0 attempt=1 status=PASS" in output
    assert "[source-lab] capacity scan finished: elapsed=" in output


def test_scan_progress_output_can_be_disabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Disabled progress config should suppress scan progress lines."""

    config = _config(progress_enabled=False)
    provider = _Provider()

    monkeypatch.setattr(
        "tools.source_lab.access.capacity.run_level_once",
        lambda sources, *, target_hz, config, runner: _passing_metrics(),
    )

    scan_source_capacity(config, provider=provider, runner=_Runner())

    assert capsys.readouterr().out == ""
