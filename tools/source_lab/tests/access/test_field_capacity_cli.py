"""Tests for field capacity CLI skip reporting and report file naming."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.source_lab.access.model import (
    CapacityLevelMetrics,
    CapacityMode,
    CapacityScanConfig,
    CapacityScanResult,
    CapacityStatus,
    ConfirmedLevelResult,
)
from tools.source_lab.field_capacity import main


def _write(path: Path, text: str) -> None:
    """Write fixture text to disk.

    Args:
        path: Target file path.
        text: Fixture body.
    """

    path.write_text(text.strip() + "\n", encoding="utf-8")


def _result(server_count: int, hz: float) -> CapacityScanResult:
    """Build a minimal successful capacity result for CLI tests.

    Args:
        server_count: Executed server count.
        hz: Executed polling rate.

    Returns:
        Capacity result with one passing level.
    """

    config = CapacityScanConfig(
        mode=CapacityMode.FIELD,
        protocol="opcua",
        endpoints=(),
        points=(),
        server_count_start=server_count,
        server_count_step=1,
        server_count_max=server_count,
        hz_start=hz,
        hz_step=hz,
        hz_max=hz,
        process_count=1,
        progress_enabled=False,
    )
    metrics = ConfirmedLevelResult(
        primary=CapacityLevelMetrics(
            server_count=server_count,
            target_hz=hz,
            target_period_ms=100.0,
            allowed_period_max_ms=120.0,
            allowed_period_mean_abs_error_ms=5.0,
            read_errors=0,
            batch_mismatches=0,
            missing_response_timestamps=0,
            period_samples=10,
            period_mean_ms=100.0,
            period_max_ms=100.0,
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
            failure_reason="",
            worst_gap=None,
            top_gaps=(),
        ),
        attempts=(),
        final_status=CapacityStatus.PASS,
        final_reason="",
    )
    return CapacityScanResult(config=config, levels=(metrics,))


def test_field_capacity_reports_existing_unsupported_protocol_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    output_dir = tmp_path / "reports"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport
        ep-1\tpf-1\tmodbus-tcp\ttcp\t127.0.0.1\t502
        ep-2\tpf-2\topcua\ttcp\t127.0.0.1\t4840
        """,
    )
    _write(
        items,
        """
        profile_id\taddress\tdata_type\tprotocol
        pf-1\t40001\tINT32\tmodbus_tcp
        pf-2\ts=Node1\tFLOAT64\topcua
        """,
    )

    monkeypatch.setattr("tools.source_lab.field_capacity.scan_source_capacity", lambda *args, **kwargs: _result(1, 10.0))
    monkeypatch.setattr("tools.source_lab.field_capacity.CpuSampler.start", lambda self: None)
    monkeypatch.setattr(
        "tools.source_lab.field_capacity.CpuSampler.stop",
        lambda self: type("_Cpu", (), {"cpu_mean_pct": 0.0, "cpu_max_pct": 0.0, "rss_mb": 0.0, "warning": ""})(),
    )

    exit_code = main(
        [
            "--servers",
            str(servers),
            "--profile-items",
            str(items),
            "--protocol",
            "opcua",
            "--process-counts",
            "1",
            "--hz",
            "10",
            "--output-dir",
            str(output_dir),
            "--run-id",
            "testrun",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "modbustcp" in output
    assert "unsupported_protocol" in output
    assert (output_dir / "field_capacity_testrun.csv").exists()
    assert (output_dir / "field_capacity_testrun.jsonl").exists()


def test_field_capacity_uses_timestamped_filenames_without_run_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    output_dir = tmp_path / "reports"
    _write(
        servers,
        """
        endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport
        ep-1\tpf-1\topcua\ttcp\t127.0.0.1\t4840
        """,
    )
    _write(
        items,
        """
        profile_id\taddress\tdata_type\tprotocol
        pf-1\ts=Node1\tFLOAT64\topcua
        """,
    )

    monkeypatch.setattr("tools.source_lab.field_capacity.scan_source_capacity", lambda *args, **kwargs: _result(1, 10.0))
    monkeypatch.setattr("tools.source_lab.field_capacity.CpuSampler.start", lambda self: None)
    monkeypatch.setattr(
        "tools.source_lab.field_capacity.CpuSampler.stop",
        lambda self: type("_Cpu", (), {"cpu_mean_pct": 0.0, "cpu_max_pct": 0.0, "rss_mb": 0.0, "warning": ""})(),
    )

    exit_code = main(
        [
            "--servers",
            str(servers),
            "--profile-items",
            str(items),
            "--protocol",
            "opcua",
            "--process-counts",
            "1",
            "--hz",
            "10",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert len(list(output_dir.glob("field_capacity_*.csv"))) == 1
    assert len(list(output_dir.glob("field_capacity_*.jsonl"))) == 1
