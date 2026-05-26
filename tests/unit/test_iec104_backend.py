"""Unit tests for IEC 104 backend (stdout protocol parsing)."""
from __future__ import annotations

from datetime import datetime, timezone

from whale.shared.source.iec104.backends.base import (
    Iec104PreparedReadPlan,
    RawIec104ReadResult,
    RawWriteItemResult,
)
from whale.shared.source.iec104.backends.lib60870_backend import Iec104Lib60870Backend


class TestIec104ParseSampleLine:
    """Parse SAMPLE protocol lines from native runner."""

    def test_parse_sp_sample(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("SAMPLE\t1\t101\tSP\t1")
        assert result == (101, "SP", "1")

    def test_parse_short_sample(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("SAMPLE\t1\t5\tSHORT\t550.000000")
        assert result == (5, "SHORT", "550.000000")

    def test_parse_sp_zero(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("SAMPLE\t1\t102\tSP\t0")
        assert result == (102, "SP", "0")

    def test_parse_malformed_line(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("SAMPLE")
        assert result is None

    def test_parse_empty_line(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("")
        assert result is None

    def test_parse_non_sample(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("READY")
        assert result is None


class TestIec104ParseWriteResult:
    """Parse WRITE_RESULT protocol lines."""

    def test_parse_ok(self) -> None:
        result = Iec104Lib60870Backend._parse_write_result_line(
            "WRITE_RESULT\treq-001\tok=1\tOK",
            expected_ioa=101,
            expected_command_type="C_SC_NA_1",
        )
        assert result.ioa == 101
        assert result.ok is True
        assert result.status_code == "OK"
        assert result.error_message is None

    def test_parse_failed(self) -> None:
        result = Iec104Lib60870Backend._parse_write_result_line(
            "WRITE_RESULT\treq-001\tok=0\texecution_failed",
            expected_ioa=101,
            expected_command_type="C_SC_NA_1",
        )
        assert result.ioa == 101
        assert result.ok is False
        assert result.status_code == "execution_failed"
        assert result.error_message is not None

    def test_parse_malformed(self) -> None:
        result = Iec104Lib60870Backend._parse_write_result_line(
            "NOISE",
            expected_ioa=101,
            expected_command_type="C_SC_NA_1",
        )
        assert result.ok is False
        assert result.status_code == "protocol_error"

    def test_parse_protocol_error_format(self) -> None:
        result = Iec104Lib60870Backend._parse_write_result_line(
            "WRITE_RESULT\treq-001",
            expected_ioa=102,
            expected_command_type="C_SC_NA_1",
        )
        assert result.ok is False
        assert result.status_code == "protocol_error"
        assert result.command_type == "C_SC_NA_1"


class TestIec104RawReadResult:
    """RawIec104ReadResult DTO behavior."""

    def test_ok_result(self) -> None:
        ts = datetime.now(tz=timezone.utc)
        result = RawIec104ReadResult(
            ok=True,
            values={101: ("SP", "1"), 102: ("SP", "0")},
            response_timestamp=ts,
        )
        assert result.ok is True
        assert result.values[101] == ("SP", "1")

    def test_failed_result(self) -> None:
        result = RawIec104ReadResult(
            ok=False,
            values={},
            error_reason="timeout",
        )
        assert result.ok is False
        assert result.error_reason == "timeout"


class TestIec104PreparedReadPlan:
    """Prepared read plan DTO."""

    def test_create_plan(self) -> None:
        plan = Iec104PreparedReadPlan(ioa_list=(101, 102, 103), common_addr=1)
        assert plan.ioa_list == (101, 102, 103)
        assert plan.common_addr == 1


class TestIec104RawWriteItemResult:
    """RawWriteItemResult DTO behavior."""

    def test_ok_result(self) -> None:
        result = RawWriteItemResult(
            ioa=101,
            ok=True,
            status_code="OK",
            error_message=None,
            command_type="C_SC_NA_1",
        )
        assert result.ok is True
        assert result.ioa == 101

    def test_failed_result(self) -> None:
        result = RawWriteItemResult(
            ioa=101,
            ok=False,
            status_code="timeout",
            error_message="connection failed",
            command_type="C_SC_NA_1",
        )
        assert result.ok is False
        assert result.error_message == "connection failed"
