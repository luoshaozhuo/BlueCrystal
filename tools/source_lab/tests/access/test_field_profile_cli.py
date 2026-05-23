"""Tests for the formal ``field_profile`` CLI wiring."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from tools.source_lab.access.polling.profile import PollingProfileResult
from tools.source_lab.access.profile import FieldProfileArtifacts, FieldProfileRequest, FieldProfileServiceResult
from tools.source_lab.access.subscribe.profile import SubscribeProfileResult
from tools.source_lab.field_profile import main


def _write(path: Path, text: str) -> None:
    """Write one UTF-8 fixture file used by CLI tests.

    Args:
        path: Target file path.
        text: File content without the final newline requirement.
    """

    path.write_text(text.strip() + "\n", encoding="utf-8")


def _write_input_files(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create minimal field input files for CLI tests.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        Tuple of ``servers``, ``items``, and ``output_dir`` paths.
    """

    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    output_dir = tmp_path / "reports"
    _write(
        servers,
        "endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport\nep-1\tpf-1\topcua\ttcp\t127.0.0.1\t4840",
    )
    _write(
        items,
        "profile_id\trelative_path\tdata_type_id\tln_name\tdo_name\npf-1\tIED1.LD0.WPPD1.TotW\tFLOAT64\tWPPD1\tTotW",
    )
    return servers, items, output_dir


def _result(output_dir: Path, run_id: str, *, access_mode: str) -> FieldProfileServiceResult:
    """Build a minimal successful field-profile service result.

    Args:
        output_dir: Directory used to hold artifact paths.
        run_id: Deterministic run identifier.
        access_mode: Profile access mode under test.

    Returns:
        Successful service result with deterministic artifact paths.
    """

    artifacts = FieldProfileArtifacts(
        report_path=output_dir / f"field_profile_{run_id}.txt",
        pyinstrument_path=output_dir / f"field_profile_pyinstrument_{run_id}.txt",
        json_path=output_dir / f"field_profile_{run_id}.json",
    )
    raw_result = cast(Any, object())
    return FieldProfileServiceResult(
        access_mode=access_mode,
        protocol="opcua",
        status="PASS",
        reason="",
        warnings=(),
        artifacts=artifacts,
        pyinstrument_text=None,
        raw_result=raw_result,
    )


def test_field_profile_polling_cli_builds_request_and_prints_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify polling profile CLI prints diagnostics before the summary line."""

    servers, items, output_dir = _write_input_files(tmp_path)
    observed: list[FieldProfileRequest] = []

    def _fake_service(
        request: FieldProfileRequest,
        *,
        servers_path: Path,
        profile_items_path: Path,
    ) -> FieldProfileServiceResult:
        """Capture polling request fields for assertions."""

        del servers_path, profile_items_path
        observed.append(request)
        return _result(output_dir, request.run_id, access_mode=request.access_mode)

    monkeypatch.setattr("tools.source_lab.field_profile.run_field_profile_from_files", _fake_service)
    monkeypatch.setattr("tools.source_lab.field_profile._print_profile_report", lambda result: print("polling-report", result))

    exit_code = main(
        [
            "--access-mode", "polling",
            "--servers", str(servers),
            "--profile-items", str(items),
            "--protocol", "opcua",
            "--process-count", "1",
            "--server-count", "1",
            "--hz", "5",
            "--source-update-hz", "5",
            "--runner-trace", "true",
            "--output-dir", str(output_dir),
            "--run-id", "polling_run",
        ]
    )

    stdout = capsys.readouterr().out
    request = observed[0]
    assert exit_code == 0
    assert request.access_mode == "polling"
    assert request.hz == 5.0
    assert request.source_update_hz == 5.0
    assert request.runner_trace_enabled is True
    assert "polling-report" in stdout
    assert "access_mode=polling" in stdout
    assert "report_path=" in stdout


def test_field_profile_subscribe_cli_builds_request_and_prints_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify subscribe profile CLI forwards subscribe-specific request fields."""

    servers, items, output_dir = _write_input_files(tmp_path)
    observed: list[FieldProfileRequest] = []

    def _fake_service(
        request: FieldProfileRequest,
        *,
        servers_path: Path,
        profile_items_path: Path,
    ) -> FieldProfileServiceResult:
        """Capture subscribe request fields for assertions."""

        del servers_path, profile_items_path
        observed.append(request)
        return _result(output_dir, request.run_id, access_mode=request.access_mode)

    monkeypatch.setattr("tools.source_lab.field_profile.run_field_profile_from_files", _fake_service)
    monkeypatch.setattr("tools.source_lab.field_profile._print_profile_report", lambda result: print("subscribe-report", result))

    exit_code = main(
        [
            "--access-mode", "subscribe",
            "--servers", str(servers),
            "--profile-items", str(items),
            "--protocol", "opcua",
            "--process-count", "1",
            "--server-count", "1",
            "--sample-hz", "5",
            "--sampling-interval-ms", "100",
            "--publishing-interval-ms", "120",
            "--queue-size", "1",
            "--source-update-hz", "5",
            "--warmup", "3",
            "--runner-trace", "true",
            "--output-dir", str(output_dir),
            "--run-id", "subscribe_run",
        ]
    )

    stdout = capsys.readouterr().out
    request = observed[0]
    assert exit_code == 0
    assert request.access_mode == "subscribe"
    assert request.sample_hz == 5.0
    assert request.sampling_interval_ms == 100.0
    assert request.publishing_interval_ms == 120.0
    assert request.source_update_hz == 5.0
    assert request.warmup_s == 3.0
    assert request.runner_trace_enabled is True
    assert "subscribe-report" in stdout
    assert "access_mode=subscribe" in stdout
    assert "report_path=" in stdout


def test_field_profile_cli_with_service_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify --service-type is accepted and forwarded to FieldProfileRequest."""

    servers, items, output_dir = _write_input_files(tmp_path)
    observed: list[FieldProfileRequest] = []

    def _fake_service(
        request: FieldProfileRequest,
        *,
        servers_path: Path,
        profile_items_path: Path,
    ) -> FieldProfileServiceResult:
        del servers_path, profile_items_path
        observed.append(request)
        return _result(output_dir, request.run_id, access_mode=request.access_mode)

    monkeypatch.setattr("tools.source_lab.field_profile.run_field_profile_from_files", _fake_service)
    monkeypatch.setattr("tools.source_lab.field_profile._print_profile_report", lambda result: print("profile-report", result))

    exit_code = main(
        [
            "--access-mode", "polling",
            "--servers", str(servers),
            "--profile-items", str(items),
            "--protocol", "iec61850",
            "--service-type", "MMS_READ",
            "--process-count", "1",
            "--server-count", "1",
            "--hz", "5",
            "--output-dir", str(output_dir),
            "--run-id", "svc_test",
        ]
    )

    request = observed[0]
    assert exit_code == 0
    assert request.service_type == "MMS_READ"


def test_print_profile_report_dispatches_to_polling_reporter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify polling raw results are rendered with the polling reporter."""

    observed: list[tuple[str, object]] = []
    fake_result = object()
    fake = PollingProfileResult(result=cast(Any, fake_result), pyinstrument_text=None)
    monkeypatch.setattr(
        "tools.source_lab.field_profile.print_capacity_report",
        lambda result: observed.append(("polling", result)),
    )

    from tools.source_lab.field_profile import _print_profile_report

    _print_profile_report(fake)

    assert observed == [("polling", fake_result)]


def test_print_profile_report_dispatches_to_subscribe_reporter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify subscribe raw results are rendered with the subscribe reporter."""

    observed: list[tuple[str, object]] = []
    fake_result = object()
    fake = SubscribeProfileResult(result=cast(Any, fake_result), pyinstrument_text=None)
    monkeypatch.setattr(
        "tools.source_lab.field_profile.print_subscribe_report",
        lambda result: observed.append(("subscribe", result)),
    )

    from tools.source_lab.field_profile import _print_profile_report

    _print_profile_report(fake)

    assert observed == [("subscribe", fake_result)]
