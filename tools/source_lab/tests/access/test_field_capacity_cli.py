"""Tests for the formal ``field_capacity`` CLI wiring."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from tools.source_lab.access.capacity import (
    FieldCapacityArtifacts,
    FieldCapacityRequest,
    FieldCapacityRow,
    FieldCapacityServiceResult,
)
from tools.source_lab.field_capacity import main


def _write(path: Path, text: str) -> None:
    """Write one UTF-8 fixture file used by CLI tests.

    Args:
        path: Target file path.
        text: File content without the final newline requirement.
    """

    path.write_text(text.strip() + "\n", encoding="utf-8")


def _result(tmp_path: Path) -> FieldCapacityServiceResult:
    """Build a minimal successful field-capacity service result.

    Args:
        tmp_path: Temporary directory used to hold artifact paths.

    Returns:
        Service result with one polling row and deterministic artifacts.
    """

    return FieldCapacityServiceResult(
        rows=(
            FieldCapacityRow(
                access_mode="polling",
                process_count=1,
                server_count=1,
                protocol="opcua",
                hz=5.0,
                point_count=1,
                status="PASS",
            ),
        ),
        artifacts=FieldCapacityArtifacts(
            csv_path=tmp_path / "field_capacity_testrun.csv",
            jsonl_path=tmp_path / "field_capacity_testrun.jsonl",
        ),
    )


def _capture_request(
    observed: list[FieldCapacityRequest],
    output_dir: Path,
) -> Callable[..., FieldCapacityServiceResult]:
    """Build a fake service function that captures one request.

    Args:
        observed: Mutable list receiving captured requests.
        output_dir: Output directory used to construct fake artifacts.

    Returns:
        Fake service callable compatible with ``run_field_capacity_from_files``.
    """

    def _run(
        request: FieldCapacityRequest,
        *,
        servers_path: Path,
        profile_items_path: Path,
    ) -> FieldCapacityServiceResult:
        """Capture one request and return a stable fake result.

        Args:
            request: Request built by the CLI.
            servers_path: Servers file path passed through by the CLI.
            profile_items_path: Profile-items file path passed through by the CLI.

        Returns:
            Stable fake service result for assertions.
        """

        del servers_path, profile_items_path
        observed.append(request)
        return _result(output_dir)

    return _run


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


def test_field_capacity_polling_list_calls_service_with_list_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify polling list arguments are forwarded to the capacity request."""

    servers, items, output_dir = _write_input_files(tmp_path)
    observed: list[tuple[FieldCapacityRequest, Path, Path]] = []

    def _fake_run(
        request: FieldCapacityRequest,
        *,
        servers_path: Path,
        profile_items_path: Path,
    ) -> FieldCapacityServiceResult:
        """Capture request plus input paths for polling assertions."""

        observed.append((request, servers_path, profile_items_path))
        return _result(output_dir)

    monkeypatch.setattr("tools.source_lab.field_capacity.run_field_capacity_from_files", _fake_run)

    exit_code = main(
        [
            "--access-mode", "polling",
            "--servers", str(servers),
            "--profile-items", str(items),
            "--protocol", "opcua",
            "--process-counts", "1,2",
            "--server-counts", "1,3",
            "--hz", "5,10",
            "--output-dir", str(output_dir),
            "--run-id", "testrun",
        ]
    )

    request, servers_path, profile_items_path = observed[0]
    assert exit_code == 0
    assert request.process_counts == (1, 2)
    assert request.server_counts == (1, 3)
    assert request.hz_values == (5.0, 10.0)
    assert servers_path == servers
    assert profile_items_path == items


def test_field_capacity_polling_ramp_calls_service_with_ramp_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify polling ramp arguments are expanded before service dispatch."""

    servers, items, output_dir = _write_input_files(tmp_path)
    observed: list[FieldCapacityRequest] = []
    monkeypatch.setattr(
        "tools.source_lab.field_capacity.run_field_capacity_from_files",
        _capture_request(observed, output_dir),
    )

    exit_code = main(
        [
            "--access-mode", "polling",
            "--servers", str(servers),
            "--profile-items", str(items),
            "--protocol", "opcua",
            "--process-count-start", "1",
            "--process-count-step", "1",
            "--process-count-max", "2",
            "--server-count-start", "1",
            "--server-count-step", "2",
            "--server-count-max", "3",
            "--hz-start", "5",
            "--hz-step", "5",
            "--hz-max", "10",
            "--output-dir", str(output_dir),
            "--run-id", "testrun",
        ]
    )

    request = observed[0]
    assert exit_code == 0
    assert request.process_counts == (1, 2)
    assert request.server_counts == (1, 3)
    assert request.hz_values == (5.0, 10.0)


def test_field_capacity_subscribe_ramp_calls_service_with_ramp_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify subscribe ramp arguments populate warmup and source-rate matrix fields."""

    servers, items, output_dir = _write_input_files(tmp_path)
    observed: list[FieldCapacityRequest] = []
    monkeypatch.setattr(
        "tools.source_lab.field_capacity.run_field_capacity_from_files",
        _capture_request(observed, output_dir),
    )

    exit_code = main(
        [
            "--access-mode", "subscribe",
            "--servers", str(servers),
            "--profile-items", str(items),
            "--protocol", "opcua",
            "--process-count-start", "1",
            "--process-count-step", "1",
            "--process-count-max", "1",
            "--server-count-start", "1",
            "--server-count-step", "1",
            "--server-count-max", "2",
            "--sample-hz-start", "5",
            "--sample-hz-step", "5",
            "--sample-hz-max", "10",
            "--source-update-hz-start", "10",
            "--source-update-hz-step", "20",
            "--source-update-hz-max", "50",
            "--queue-size", "1,3",
            "--warmup", "3.0",
            "--output-dir", str(output_dir),
            "--run-id", "testrun",
        ]
    )

    request = observed[0]
    assert exit_code == 0
    assert request.process_counts == (1,)
    assert request.server_counts == (1, 2)
    assert request.sample_hz_values == (5.0, 10.0)
    assert request.source_update_hz_values == (10.0, 30.0, 50.0)
    assert request.queue_sizes == (1, 3)
    assert request.warmup_s == 3.0


def test_field_capacity_subscribe_single_source_update_hz_stays_scalar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify fixed subscribe source-update-hz keeps the scalar request field."""

    servers, items, output_dir = _write_input_files(tmp_path)
    observed: list[FieldCapacityRequest] = []
    monkeypatch.setattr(
        "tools.source_lab.field_capacity.run_field_capacity_from_files",
        _capture_request(observed, output_dir),
    )

    exit_code = main(
        [
            "--access-mode", "subscribe",
            "--servers", str(servers),
            "--profile-items", str(items),
            "--protocol", "opcua",
            "--process-counts", "1",
            "--server-counts", "1",
            "--sample-hz", "5",
            "--source-update-hz", "7",
            "--queue-size", "1",
            "--warmup", "3.0",
            "--output-dir", str(output_dir),
            "--run-id", "testrun",
        ]
    )

    request = observed[0]
    assert exit_code == 0
    assert request.source_update_hz == 7.0
    assert request.source_update_hz_values == ()
    assert request.warmup_s == 3.0


def test_field_capacity_list_takes_priority_over_ramp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify explicit list arguments override matching ramp inputs."""

    servers, items, output_dir = _write_input_files(tmp_path)
    observed: list[FieldCapacityRequest] = []
    monkeypatch.setattr(
        "tools.source_lab.field_capacity.run_field_capacity_from_files",
        _capture_request(observed, output_dir),
    )

    exit_code = main(
        [
            "--access-mode", "polling",
            "--servers", str(servers),
            "--profile-items", str(items),
            "--protocol", "opcua",
            "--process-counts", "3",
            "--process-count-start", "1",
            "--process-count-step", "1",
            "--process-count-max", "2",
            "--server-counts", "4",
            "--server-count-start", "1",
            "--server-count-step", "1",
            "--server-count-max", "2",
            "--hz", "8",
            "--hz-start", "5",
            "--hz-step", "5",
            "--hz-max", "10",
            "--output-dir", str(output_dir),
            "--run-id", "testrun",
        ]
    )

    request = observed[0]
    assert exit_code == 0
    assert request.process_counts == (3,)
    assert request.server_counts == (4,)
    assert request.hz_values == (8.0,)


def test_field_capacity_rejects_invalid_ramp(tmp_path: Path) -> None:
    """Verify invalid ramp parameters still raise a validation error."""

    servers, items, output_dir = _write_input_files(tmp_path)

    with pytest.raises(ValueError, match="server_count step must be greater than 0"):
        main(
            [
                "--access-mode", "polling",
                "--servers", str(servers),
                "--profile-items", str(items),
                "--protocol", "opcua",
                "--server-count-start", "1",
                "--server-count-step", "0",
                "--server-count-max", "1",
                "--output-dir", str(output_dir),
                "--run-id", "testrun",
            ]
        )


def test_field_capacity_rejects_conflicting_source_update_hz_inputs(tmp_path: Path) -> None:
    """Verify subscribe scalar and ramp source-rate flags cannot be mixed."""

    servers, items, output_dir = _write_input_files(tmp_path)

    with pytest.raises(
        ValueError,
        match="use either --source-update-hz or --source-update-hz-start/--source-update-hz-step/--source-update-hz-max",
    ):
        main(
            [
                "--access-mode", "subscribe",
                "--servers", str(servers),
                "--profile-items", str(items),
                "--protocol", "opcua",
                "--process-counts", "1",
                "--server-counts", "1",
                "--sample-hz", "5",
                "--source-update-hz", "10",
                "--source-update-hz-start", "10",
                "--source-update-hz-step", "20",
                "--source-update-hz-max", "50",
                "--queue-size", "1",
                "--output-dir", str(output_dir),
                "--run-id", "testrun",
            ]
        )


def test_field_capacity_subscribe_rejects_sampling_interval_arg(tmp_path: Path) -> None:
    """Verify subscribe capacity rejects direct sampling-interval overrides."""

    servers, items, output_dir = _write_input_files(tmp_path)

    with pytest.raises(
        ValueError,
        match="derives sampling_interval_ms from sample_hz; use --sample-hz instead",
    ):
        main(
            [
                "--access-mode", "subscribe",
                "--servers", str(servers),
                "--profile-items", str(items),
                "--protocol", "opcua",
                "--process-counts", "1",
                "--server-counts", "1",
                "--sample-hz", "5",
                "--sampling-interval-ms", "100",
                "--queue-size", "1",
                "--output-dir", str(output_dir),
                "--run-id", "testrun",
            ]
        )
