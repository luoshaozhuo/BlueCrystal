"""Tests for summary-only capacity table rendering."""

from __future__ import annotations

import pytest

from pathlib import Path

from tools.source_lab.access.capacity import FieldCapacityArtifacts, FieldCapacityRow, FieldCapacityServiceResult, print_capacity_summary, print_capacity_table


def _rows() -> tuple[FieldCapacityRow, ...]:
    return (
        FieldCapacityRow(
            access_mode="polling",
            mode="polling",
            process_count=1,
            server_count=10,
            protocol="opcua",
            hz=5.0,
            period_ms=200.0,
            points_per_server=250,
            point_total=2500,
            expected_values=12500,
            values=12000,
            value_ratio=0.96,
            value_miss=500,
            bad=0,
            miss_ts=0,
            noise=0,
            reads=50,
            batches=50,
            data_period_p95_ms=198.34,
            data_period_max_ms=205.12,
            status="PASS",
            reason="",
        ),
        FieldCapacityRow(
            access_mode="subscribe",
            mode="subscribe",
            process_count=2,
            server_count=20,
            protocol="opcua",
            hz=10.0,
            sample_hz=10.0,
            period_ms=100.0,
            points_per_server=250,
            point_total=5000,
            expected_values=50000,
            values=5200,
            value_ratio=0.104,
            value_miss=44800,
            bad=0,
            miss_ts=0,
            noise=0,
            notify=1040,
            expected_items=5000,
            created_items=5000,
            publishing_interval_ms=100.0,
            sampling_interval_ms=100.0,
            effective_source_update_hz=10.0,
            queue_size=1,
            publish_gap_p95_ms=150.0,
            publish_gap_max_ms=180.0,
            data_age_p95_ms=140.0,
            data_age_max_ms=170.0,
            data_period_p95_ms=101.22,
            data_period_max_ms=119.80,
            source_period_p95_ms=400.0,
            source_period_max_ms=400.0,
            status="FAIL",
            reason="max=119.80>110.00",
        ),
    )


def test_summary_table_is_default_and_short(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SOURCE_LAB_CAPACITY_TABLE_MODE", raising=False)

    print_capacity_table(_rows())
    output = capsys.readouterr().out

    assert "proc" in output
    assert "srv" in output
    assert "hz" in output
    assert "period_ms" in output
    assert "value_ratio" in output
    assert "p95_ms" in output
    assert "max_ms" in output
    assert "data_period_p95_ms" not in output
    assert "data_period_max_ms" not in output
    assert "status" in output
    assert "reason" in output
    assert "expected_values" not in output
    assert "values " not in output
    assert "notify" not in output
    assert "created_items" not in output
    assert "publish_gap" not in output
    assert "data_age" not in output
    assert "source_period" not in output
    assert "p99" not in output
    assert " -" in output
    assert "max=119.80>110.00" in output


def test_detail_mode_is_deprecated_and_summary_only(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_LAB_CAPACITY_TABLE_MODE", "detail")

    print_capacity_table(_rows())
    captured = capsys.readouterr()
    output = captured.out

    assert "p95_ms" in output
    assert "max_ms" in output
    assert "expected_values" not in output
    assert "notify" not in output
    assert "source_period" not in output
    assert "deprecated; use profile for diagnostics" in captured.err


def test_unknown_table_mode_falls_back_to_summary(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_LAB_CAPACITY_TABLE_MODE", "weird")

    print_capacity_table(_rows())
    output = capsys.readouterr().out

    assert "p95_ms" in output
    assert "expected_values" not in output
    assert "notify" not in output


def test_print_capacity_summary_reuses_summary_table(capsys: pytest.CaptureFixture[str]) -> None:
    result = FieldCapacityServiceResult(
        rows=_rows(),
        artifacts=FieldCapacityArtifacts(
            csv_path=Path("/tmp/rows.csv"),
            jsonl_path=Path("/tmp/rows.jsonl"),
        ),
    )

    print_capacity_summary(result)
    output = capsys.readouterr().out

    assert "proc" in output
    assert "max_ms" in output
    assert "max=119.80>110.00" in output
    assert "expected_values" not in output
    assert "\t" not in output


def test_subscribe_summary_uses_subscribe_headers_and_data_period_values(
    capsys: pytest.CaptureFixture[str],
) -> None:
    row = FieldCapacityRow(
        access_mode="subscribe",
        mode="subscribe",
        process_count=1,
        server_count=10,
        protocol="opcua",
        sample_hz=20.0,
        effective_source_update_hz=10.0,
        sub_hz=20.0,
        src_hz=10.0,
        sub_ms=50.0,
        src_ms=100.0,
        value_ratio=1.0,
        data_period_p95_ms=100.0,
        data_period_max_ms=120.0,
        response_period_p95_ms=1.0,
        response_period_max_ms=2.0,
        status="PASS",
        reason="",
    )

    print_capacity_table((row,))
    output = capsys.readouterr().out

    assert "proc" in output and "sub_hz" in output and "src_hz" in output and "sub_ms" in output and "src_ms" in output
    assert "100.00" in output
    assert "120.00" in output
    assert " 1.00 " not in output
    assert " 2.00 " not in output
