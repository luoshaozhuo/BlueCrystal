"""Tests for the field profile production service."""

from __future__ import annotations

import json
from contextlib import nullcontext
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, cast

import pytest

from tools.source_lab.access.capacity import CapacityStatus
from tools.source_lab.access.polling.model import CapacityLevelMetrics, CapacityMode, CapacityScanConfig, CapacityScanResult, ConfirmedLevelResult
from tools.source_lab.access.polling.profile import PollingProfileResult
from tools.source_lab.access.profile import (
    FieldProfileRequest,
    FieldProfileArtifacts,
    FieldProfileServiceResult,
    run_field_profile,
    run_field_profile_from_files,
)
from tools.source_lab.access.providers.base import SourceProvider, SourceRuntimeSpec
from tools.source_lab.access.subscribe.model import SubscribeLevelMetrics, SubscribeLevelResult, SubscribeScanConfig, SubscribeScanResult
from tools.source_lab.access.subscribe.model import SubscribeFlushLagTrace
from tools.source_lab.access.subscribe.profile import SubscribeProfileResult


def _write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


class _Provider(SourceProvider):
    def build_sources(self, config: object, *, server_count: int) -> tuple[SourceRuntimeSpec, ...]:
        return ()

    def started(self, sources: tuple[SourceRuntimeSpec, ...]) -> AbstractContextManager[None]:
        return nullcontext()


def _polling_profile_result(*, warnings: tuple[str, ...] = (), reason: str = "", pyinstrument_text: str | None = None) -> PollingProfileResult:
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
        source_update_enabled=True,
        source_update_hz=5.0,
    )
    level = ConfirmedLevelResult(
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
            worst_gap=None,
            top_gaps=(),
            warnings=warnings,
        ),
        attempts=(),
        final_status=CapacityStatus.PASS if not reason else CapacityStatus.FAIL,
        final_reason=reason,
    )
    return PollingProfileResult(
        result=CapacityScanResult(config=config, levels=(level,)),
        pyinstrument_text=pyinstrument_text,
    )


def _subscribe_profile_result(
    *,
    config: SubscribeScanConfig,
    warnings: tuple[str, ...] = (),
    reason: str = "",
    pyinstrument_text: str | None = None,
) -> SubscribeProfileResult:
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
        notification_count=10,
        value_count=10,
        bad_count=0,
        missing_ts_count=0,
        reserved_sequence_gap_count=0,
        reserved_queue_overflow_count=0,
        keepalive_count=0,
        publish_timeout_count=0,
        reconnect_count=0,
        notification_rate=5.0,
        value_rate=5.0,
        publish_gap_mean_ms=200.0,
        publish_gap_p95_ms=200.0,
        publish_gap_p99_ms=200.0,
        publish_gap_max_ms=200.0,
        data_age_mean_ms=1.0,
        data_age_p95_ms=2.0,
        data_age_p99_ms=2.0,
        data_age_max_ms=2.0,
        data_period_samples=9,
        data_period_mean_ms=200.0,
        data_period_p95_ms=200.0,
        data_period_max_ms=200.0,
        allowed_data_period_max_ms=240.0,
        response_period_samples=9,
        response_period_mean_ms=200.0,
        response_period_p95_ms=200.0,
        response_period_max_ms=200.0,
        allowed_response_period_max_ms=240.0,
        passed=not reason,
        failure_reason=reason,
        recv_period_p95_ms=200.0,
        recv_period_max_ms=220.0,
        callback_to_flush_lag_p95_ms=2.0,
        callback_to_flush_lag_max_ms=4.0,
        warnings=warnings,
        top_period_gap_traces=(),
        top_flush_lag_traces=(
            SubscribeFlushLagTrace(
                worker_index=0,
                local_index=0,
                global_index=0,
                notify_timestamp_ns=1_000_000_000,
                flush_timestamp_ns=1_002_000_000,
                lag_ms=2.0,
            ),
        ),
    )
    level = SubscribeLevelResult(
        primary=level_metrics,
        attempts=(),
        final_status=CapacityStatus.PASS if not reason else CapacityStatus.FAIL,
        final_reason=reason,
    )
    return SubscribeProfileResult(
        result=SubscribeScanResult(config=config, levels=(level,)),
        pyinstrument_text=pyinstrument_text,
    )


def test_run_field_profile_from_files_dispatches_provider_and_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(servers, "endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport\nep-1\tpf-1\topcua\ttcp\t127.0.0.1\t4840")
    _write(items, "profile_id\trelative_path\tdata_type_id\tln_name\tdo_name\npf-1\tIED1.LD0.WPPD1.TotW\tFLOAT64\tWPPD1\tTotW")

    observed: dict[str, Any] = {}

    def _fake_build_runtime_sources(servers_path: Path, profile_items_path: Path, *, protocol: str) -> tuple[object, ...]:
        observed["servers_path"] = servers_path
        observed["profile_items_path"] = profile_items_path
        observed["protocol"] = protocol
        return (object(),)

    def _fake_build_provider(sources: tuple[object, ...], *, protocol: str) -> _Provider:
        observed["sources"] = sources
        observed["provider_protocol"] = protocol
        return _Provider()

    def _fake_run_field_profile(request: FieldProfileRequest, *, provider: object) -> FieldProfileServiceResult:
        observed["request"] = request
        observed["provider"] = provider
        return FieldProfileServiceResult(
            access_mode=request.access_mode,
            protocol=request.protocol,
            status="PASS",
            reason="",
            warnings=(),
            artifacts=FieldProfileArtifacts(report_path=None),
            pyinstrument_text=None,
            raw_result=cast(Any, object()),
        )

    monkeypatch.setattr("tools.source_lab.access.profile.build_field_runtime_sources", _fake_build_runtime_sources)
    monkeypatch.setattr("tools.source_lab.access.profile.build_field_source_provider", _fake_build_provider)
    monkeypatch.setattr("tools.source_lab.access.profile.run_field_profile", _fake_run_field_profile)

    request = FieldProfileRequest(
        access_mode="polling",
        protocol="opcua",
        process_count=1,
        server_count=1,
        output_dir=None,
        run_id="testrun",
        hz=5.0,
    )
    result = run_field_profile_from_files(request, servers_path=servers, profile_items_path=items)

    assert result.status == "PASS"
    assert observed["servers_path"] == servers
    assert observed["profile_items_path"] == items
    assert observed["protocol"] == "opcua"
    assert observed["request"] == request
    assert isinstance(observed["provider"], _Provider)


def test_polling_profile_service_writes_reports_and_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldProfileRequest(
        access_mode="polling",
        protocol="opcua",
        process_count=1,
        server_count=1,
        output_dir=tmp_path,
        run_id="polling_profile",
        duration_s=3.0,
        warmup_s=0.0,
        timeout_s=5.0,
        source_update_enabled=False,
        source_update_hz=None,
        runner_trace_enabled=True,
        runner_trace_top_n=2,
        pyinstrument=True,
        profile_max_lines=20,
        hz=5.0,
    )
    monkeypatch.setattr(
        "tools.source_lab.access.profile.run_polling_profile",
        lambda *args, **kwargs: _polling_profile_result(warnings=("source_update_disabled",), pyinstrument_text="profile summary\nline2"),
    )

    result = run_field_profile(request, provider=_Provider())

    assert result.access_mode == "polling"
    assert result.status == "PASS"
    assert result.reason == ""
    assert "source_update_disabled" in result.warnings
    assert result.artifacts.report_path is not None and result.artifacts.report_path.exists()
    assert result.artifacts.pyinstrument_path is not None and result.artifacts.pyinstrument_path.exists()
    assert result.artifacts.json_path is not None and result.artifacts.json_path.exists()
    assert result.artifacts.report_path.read_text(encoding="utf-8")
    assert result.artifacts.pyinstrument_path.read_text(encoding="utf-8").startswith("profile summary")
    payload = json.loads(result.artifacts.json_path.read_text(encoding="utf-8"))
    assert payload["access_mode"] == "polling"
    assert payload["status"] == "PASS"
    assert payload["warnings"] == ["source_update_disabled"]
    assert payload["report_path"].endswith("field_profile_polling_profile.txt")


def test_polling_profile_service_adds_pyinstrument_warning_when_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldProfileRequest(
        access_mode="polling",
        protocol="opcua",
        process_count=1,
        server_count=1,
        output_dir=tmp_path,
        run_id="polling_profile",
        hz=5.0,
        pyinstrument=True,
    )
    monkeypatch.setattr(
        "tools.source_lab.access.profile.run_polling_profile",
        lambda *args, **kwargs: _polling_profile_result(pyinstrument_text=None),
    )

    result = run_field_profile(request, provider=_Provider())

    assert "pyinstrument_not_installed" in result.warnings


def test_subscribe_profile_service_derives_intervals_and_writes_reports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldProfileRequest(
        access_mode="subscribe",
        protocol="opcua",
        process_count=1,
        server_count=1,
        output_dir=tmp_path,
        run_id="subscribe_profile",
        duration_s=3.0,
        timeout_s=5.0,
        source_update_enabled=True,
        source_update_hz=None,
        runner_trace_enabled=True,
        runner_trace_top_n=2,
        pyinstrument=False,
        profile_max_lines=20,
        sample_hz=5.0,
        sampling_interval_ms=None,
        publishing_interval_ms=None,
        queue_size=1,
        startup_stagger_ms=0,
        monitored_item_batch_size=100,
        monitored_item_batch_gap_ms=0,
    )
    captured: dict[str, SubscribeScanConfig] = {}

    def _fake_run_subscribe_profile(config: SubscribeScanConfig, *, provider: object, runner: object, pyinstrument: bool, show_all: bool = False, max_lines: int = 80) -> SubscribeProfileResult:
        captured["config"] = config
        return _subscribe_profile_result(config=config)

    monkeypatch.setattr("tools.source_lab.access.profile.run_subscribe_profile", _fake_run_subscribe_profile)

    result = run_field_profile(request, provider=_Provider())

    config = captured["config"]
    assert config.sampling_interval_ms == pytest.approx(200.0)
    assert config.publishing_interval_ms == pytest.approx(200.0)
    assert config.source_update_hz == pytest.approx(5.0)
    assert result.status == "PASS"
    assert result.reason == ""
    assert result.artifacts.report_path is not None and result.artifacts.report_path.exists()
    assert result.artifacts.json_path is not None and result.artifacts.json_path.exists()
    payload = json.loads(result.artifacts.json_path.read_text(encoding="utf-8"))
    assert payload["source_update_hz"] == 5.0
    assert payload["metrics"]["p95_ms"] == 200.0
    assert payload["metrics"]["effective_source_update_hz"] == 5.0
    assert payload["metrics"]["recv_period_p95_ms"] == 200.0
    assert payload["metrics"]["callback_to_flush_lag_max_ms"] == 4.0
    assert payload["metrics"]["top_flush_lag_traces"][0]["flush_timestamp_ns"] == 1_002_000_000


def test_subscribe_profile_service_allows_explicit_intervals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldProfileRequest(
        access_mode="subscribe",
        protocol="opcua",
        process_count=1,
        server_count=1,
        output_dir=tmp_path,
        run_id="subscribe_profile_explicit",
        sample_hz=5.0,
        sampling_interval_ms=150.0,
        publishing_interval_ms=250.0,
        queue_size=1,
    )
    captured: dict[str, SubscribeScanConfig] = {}

    def _fake_run_subscribe_profile(config: SubscribeScanConfig, *, provider: object, runner: object, pyinstrument: bool, show_all: bool = False, max_lines: int = 80) -> SubscribeProfileResult:
        captured["config"] = config
        return _subscribe_profile_result(config=config)

    monkeypatch.setattr("tools.source_lab.access.profile.run_subscribe_profile", _fake_run_subscribe_profile)

    run_field_profile(request, provider=_Provider())

    config = captured["config"]
    assert config.sampling_interval_ms == pytest.approx(150.0)
    assert config.publishing_interval_ms == pytest.approx(250.0)
    assert config.source_update_hz == pytest.approx(5.0)


def test_subscribe_profile_service_allows_lower_update_hz_than_sample_hz(tmp_path: Path) -> None:
    request = FieldProfileRequest(
        access_mode="subscribe",
        protocol="opcua",
        process_count=1,
        server_count=1,
        output_dir=tmp_path,
        run_id="subscribe_profile_low",
        sample_hz=10.0,
        queue_size=1,
        source_update_enabled=True,
        source_update_hz=5.0,
    )

    result = run_field_profile(request, provider=_Provider())
    assert result.raw_result.result.config.source_update_hz == pytest.approx(5.0)


def test_subscribe_profile_service_warns_when_updates_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = FieldProfileRequest(
        access_mode="subscribe",
        protocol="opcua",
        process_count=1,
        server_count=1,
        output_dir=tmp_path,
        run_id="subscribe_profile_disabled",
        sample_hz=5.0,
        queue_size=1,
        source_update_enabled=False,
        source_update_hz=1.0,
    )
    monkeypatch.setattr(
        "tools.source_lab.access.profile.run_subscribe_profile",
        lambda *args, **kwargs: _subscribe_profile_result(
            config=_subscribe_scan_config_from_request(request),
            warnings=("source_update_disabled",),
            reason="notification_timeout",
        ),
    )

    result = run_field_profile(request, provider=_Provider())

    assert "source_update_disabled" in result.warnings
    assert result.reason == "notification_timeout"


def _subscribe_scan_config_from_request(request: FieldProfileRequest) -> SubscribeScanConfig:
    sample_hz = request.sample_hz
    assert sample_hz is not None
    source_update_hz = request.source_update_hz if request.source_update_hz is not None else sample_hz
    return SubscribeScanConfig(
        mode=CapacityMode.FIELD,
        protocol=request.protocol,
        server_count_start=request.server_count,
        server_count_step=1,
        server_count_max=request.server_count,
        process_count=request.process_count,
        publishing_interval_ms=request.publishing_interval_ms or 200.0,
        sampling_interval_ms=request.sampling_interval_ms or (1000.0 / sample_hz),
        queue_size=request.queue_size,
        duration_s=request.duration_s,
        read_timeout_s=request.timeout_s,
        source_update_enabled=request.source_update_enabled,
        source_update_hz=source_update_hz,
        startup_stagger_ms=request.startup_stagger_ms,
        monitored_item_batch_size=request.monitored_item_batch_size,
        monitored_item_batch_gap_ms=request.monitored_item_batch_gap_ms,
        runner_trace_enabled=request.runner_trace_enabled,
        runner_trace_top_n=request.runner_trace_top_n,
    )
