"""Tests for LibIec61850ReportBackend — report event parsing & subprocess protocol."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from whale.shared.source.iec61850.backends.libiec61850_report_backend import (
    LibIec61850ReportBackend,
)
from whale.shared.source.iec61850.backends.report_base import RawReportEvent


class TestReportLineParsing:
    """Static REPORT line parsing. No subprocess needed."""

    def test_parse_report_line_full(self) -> None:
        line = "REPORT\tSimulator/LLN0.RP.EventsRCB01\t1000000\t42\t3\ttrue\tfalse\t12345"
        event = LibIec61850ReportBackend._parse_report_line(line)
        assert event.ok is True
        assert event.rcb_ref == "Simulator/LLN0.RP.EventsRCB01"
        assert event.timestamp_ms == 1000000
        assert event.seq_num == 42
        assert event.values == ("true", "false", "12345")

    def test_parse_report_line_minimal(self) -> None:
        line = "REPORT\t-\t0\t1\t0"
        event = LibIec61850ReportBackend._parse_report_line(line)
        assert event.ok is True
        assert event.rcb_ref == "-"
        assert event.timestamp_ms == 0
        assert event.seq_num == 1
        assert event.values == ()

    def test_parse_report_line_no_values(self) -> None:
        line = "REPORT\tSimulator/LLN0.RP.EventsRCB01\t5000\t3\t0"
        event = LibIec61850ReportBackend._parse_report_line(line)
        assert event.ok is True
        assert event.values == ()

    def test_parse_report_line_malformed(self) -> None:
        line = "NOT_A_REPORT_LINE"
        event = LibIec61850ReportBackend._parse_report_line(line)
        assert event.ok is False
        assert event.error_reason is not None

    def test_parse_report_line_empty(self) -> None:
        event = LibIec61850ReportBackend._parse_report_line("")
        assert event.ok is False
        assert event.error_reason is not None

    def test_parse_report_line_with_special_chars(self) -> None:
        """值中包含特殊字符不应破坏解析。"""
        line = "REPORT\tSimulator/LLN0.RP.EventsRCB01\t100\t5\t5\ttrue\t12.5\t-\t0xFF\ttext value"
        event = LibIec61850ReportBackend._parse_report_line(line)
        assert event.ok is True
        assert event.values == ("true", "12.5", "-", "0xFF", "text value")

    def test_parse_report_line_extra_fields(self) -> None:
        """额外字段被忽略，只取 array_size 指定数量的值。"""
        line = "REPORT\t-\t0\t1\t2\ta\tb\tc\td"
        event = LibIec61850ReportBackend._parse_report_line(line)
        assert event.values == ("a", "b")


class TestReportBackendErrors:
    """Error scenarios for the report backend."""

    @pytest.mark.asyncio
    async def test_report_runner_not_found(self) -> None:
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
            return_value=mock_path,
        ):
            backend = LibIec61850ReportBackend()
            with pytest.raises(RuntimeError, match="executable does not exist"):
                await backend.subscribe("localhost", 9999, "IED", "RCB", event_callback=AsyncMock())

    @pytest.mark.asyncio
    async def test_close_without_subscribe(self) -> None:
        backend = LibIec61850ReportBackend()
        await backend.close()  # should not raise

    @pytest.mark.asyncio
    async def test_close_idempotent(self) -> None:
        backend = LibIec61850ReportBackend()
        await backend.close()
        await backend.close()  # second close should be no-op

    @pytest.mark.asyncio
    async def test_is_active_false_by_default(self) -> None:
        backend = LibIec61850ReportBackend()
        assert backend.is_active is False

    @pytest.mark.asyncio
    async def test_double_subscribe_fails(self) -> None:
        backend = LibIec61850ReportBackend()
        with pytest.raises(RuntimeError, match="already active"):
            backend._runner = MagicMock()
            backend._reader_task = asyncio.create_task(asyncio.sleep(99999))
            backend._closed = False
            await backend.subscribe("localhost", 102, "IED", "RCB", event_callback=AsyncMock())

    @pytest.mark.asyncio
    async def test_subscribe_ready_timeout(self) -> None:
        """当 C runner 不输出 READY 时超时失败。"""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=asyncio.TimeoutError("timeout")
        )
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.returncode = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.drain = AsyncMock()

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                backend = LibIec61850ReportBackend()
                with pytest.raises(RuntimeError, match="READY timeout"):
                    await backend.subscribe("localhost", 102, "IED", "RCB", event_callback=AsyncMock())


class TestReportLineIntegration:
    """Integration-style tests for the report backend with simulated subprocess."""

    @pytest.mark.asyncio
    async def test_report_event_callback(self) -> None:
        """REPORT 行触发 event_callback。"""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=[
                b"READY\n",
                b"REPORT\tSimulator/LLN0.RP.EventsRCB01\t1000\t1\t2\ttrue\t42\n",
                b"",
            ]
        )
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.returncode = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.drain = AsyncMock()

        events: list[RawReportEvent] = []

        async def on_event(event: RawReportEvent) -> None:
            events.append(event)

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                backend = LibIec61850ReportBackend()
                await backend.subscribe(
                    "localhost", 102, "Simulator", "EventsRCB01",
                    event_callback=on_event,
                )
                # Wait for reader task to process
                await asyncio.sleep(0.05)
                await backend.close()

        assert len(events) == 1
        assert events[0].rcb_ref == "Simulator/LLN0.RP.EventsRCB01"
        assert events[0].values == ("true", "42")

    @pytest.mark.asyncio
    async def test_multiple_report_events(self) -> None:
        """多个 REPORT 事件都触发回调。"""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=[
                b"READY\n",
                b"REPORT\t-\t0\t1\t1\tv1\n",
                b"REPORT\t-\t0\t2\t1\tv2\n",
                b"REPORT\t-\t0\t3\t1\tv3\n",
                b"",
            ]
        )
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.returncode = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.drain = AsyncMock()

        events: list[RawReportEvent] = []

        async def on_event(event: RawReportEvent) -> None:
            events.append(event)

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                backend = LibIec61850ReportBackend()
                await backend.subscribe(
                    "localhost", 102, "Simulator", "EventsRCB01",
                    event_callback=on_event,
                )
                await asyncio.sleep(0.05)
                await backend.close()

        assert len(events) == 3

    @pytest.mark.asyncio
    async def test_stopped_ends_reader_loop(self) -> None:
        """STOPPED 行正常结束 reader loop。"""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=[
                b"READY\n",
                b"REPORT\t-\t0\t1\t1\tx\n",
                b"STOPPED\n",
            ]
        )
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.returncode = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.drain = AsyncMock()

        async def on_event(event: RawReportEvent) -> None:
            pass

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                backend = LibIec61850ReportBackend()
                await backend.subscribe(
                    "localhost", 102, "Simulator", "EventsRCB01",
                    event_callback=on_event,
                )
                await asyncio.sleep(0.05)
                await backend.close()
        # Success if no timeout/crash

    @pytest.mark.asyncio
    async def test_close_sends_quit(self) -> None:
        """close() 发送 QUIT 到 stdin。"""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=[b"READY\n", b""]
        )
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.returncode = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.drain = AsyncMock()

        async def on_event(event: RawReportEvent) -> None:
            pass

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                backend = LibIec61850ReportBackend()
                await backend.subscribe(
                    "localhost", 102, "Simulator", "EventsRCB01",
                    event_callback=on_event,
                )
                await asyncio.sleep(0.01)
                await backend.close()

        # Verify QUIT was written to stdin
        mock_process.stdin.write.assert_called()
        written = b"".join(
            call[0][0] for call in mock_process.stdin.write.call_args_list
        )
        assert b"QUIT" in written


class TestReportBackendErrorCallback:
    """Error callback propagation tests."""

    @pytest.mark.asyncio
    async def test_error_line_calls_error_callback(self) -> None:
        """ERROR 协议行触发 error_callback。"""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=[
                b"READY\n",
                b"ERROR\tconnect_lost\n",
                b"",
            ]
        )
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.returncode = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.drain = AsyncMock()

        errors: list[str] = []

        async def on_error(msg: str) -> None:
            errors.append(msg)

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                backend = LibIec61850ReportBackend()
                await backend.subscribe(
                    "localhost", 102, "Simulator", "EventsRCB01",
                    event_callback=AsyncMock(),
                    error_callback=on_error,
                )
                await asyncio.sleep(0.05)
                await backend.close()

        assert len(errors) >= 1
        assert "connect_lost" in errors[0]

    @pytest.mark.asyncio
    async def test_unexpected_exit_calls_error_callback(self) -> None:
        """进程意外退出触发 error_callback。"""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=[
                b"READY\n",
                b"",  # EOF → unexpected exit
            ]
        )
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.returncode = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.drain = AsyncMock()

        errors: list[str] = []

        async def on_error(msg: str) -> None:
            errors.append(msg)

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                backend = LibIec61850ReportBackend()
                await backend.subscribe(
                    "localhost", 102, "Simulator", "EventsRCB01",
                    event_callback=AsyncMock(),
                    error_callback=on_error,
                    max_reconnect_attempts=0,
                )
                await asyncio.sleep(0.05)
                await backend.close()

        assert len(errors) >= 1
        assert "subscription_terminated" in errors[0]

    @pytest.mark.asyncio
    async def test_error_callback_not_set_does_not_crash(self) -> None:
        """error_callback=None 不导致崩溃。"""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=[
                b"READY\n",
                b"ERROR\tsome_error\n",
                b"",
            ]
        )
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.returncode = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.drain = AsyncMock()

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                backend = LibIec61850ReportBackend()
                await backend.subscribe(
                    "localhost", 102, "Simulator", "EventsRCB01",
                    event_callback=AsyncMock(),
                )
                await asyncio.sleep(0.05)
                await backend.close()
        # Success if no exception


class TestReportBackendReconnect:
    """Reconnect behavior tests."""

    @pytest.mark.asyncio
    async def test_reconnect_disabled_subscription_terminated(self) -> None:
        """max_reconnect_attempts=0 时退出即终止。"""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=[
                b"READY\n",
                b"",  # EOF → unexpected exit
            ]
        )
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.returncode = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.drain = AsyncMock()

        errors: list[str] = []

        async def on_error(msg: str) -> None:
            errors.append(msg)

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                backend = LibIec61850ReportBackend()
                await backend.subscribe(
                    "localhost", 102, "Simulator", "EventsRCB01",
                    event_callback=AsyncMock(),
                    error_callback=on_error,
                    max_reconnect_attempts=0,
                )
                await asyncio.sleep(0.1)
                await backend.close()

        assert len(errors) >= 1
        assert "subscription_terminated" in errors[0]
        assert not backend.is_active

    @pytest.mark.asyncio
    async def test_reconnect_enabled_reattempts_subscribe(self) -> None:
        """max_reconnect_attempts>0 时尝试重新 subscribe。"""
        first_process = AsyncMock()
        first_process.stdout.readline = AsyncMock(
            side_effect=[
                b"READY\n",
                b"",  # EOF → trigger reconnect
            ]
        )
        first_process.wait = AsyncMock(return_value=0)
        first_process.returncode = None
        first_process.stdin = MagicMock()
        first_process.stdin.drain = AsyncMock()

        second_process = AsyncMock()
        second_process.stdout.readline = AsyncMock(
            side_effect=[
                b"READY\n",
            ]
        )
        second_process.wait = AsyncMock(return_value=0)
        second_process.returncode = None
        second_process.stdin = MagicMock()
        second_process.stdin.drain = AsyncMock()

        errors: list[str] = []

        async def on_error(msg: str) -> None:
            errors.append(msg)

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                side_effect=[first_process, second_process],
            ):
                backend = LibIec61850ReportBackend()
                await backend.subscribe(
                    "localhost", 102, "Simulator", "EventsRCB01",
                    event_callback=AsyncMock(),
                    error_callback=on_error,
                    max_reconnect_attempts=1,
                )
                # Wait for reconnect to happen (1s backoff)
                await asyncio.sleep(1.5)
                await backend.close()

        # Should have received reconnected notification
        assert any("reconnected" in e for e in errors), (
            f"expected 'reconnected' in errors, got {errors}"
        )

    @pytest.mark.asyncio
    async def test_reconnect_enabled_attempt_fails(self) -> None:
        """重连尝试后新进程也不 READY 时 subscription_terminated。"""
        first_process = AsyncMock()
        first_process.stdout.readline = AsyncMock(
            side_effect=[
                b"READY\n",
                b"",  # EOF → trigger reconnect
            ]
        )
        first_process.wait = AsyncMock(return_value=0)
        first_process.returncode = None
        first_process.stdin = MagicMock()
        first_process.stdin.drain = AsyncMock()

        second_process = AsyncMock()
        second_process.stdout.readline = AsyncMock(
            side_effect=asyncio.TimeoutError("timeout"),
        )
        second_process.wait = AsyncMock(return_value=0)
        second_process.returncode = None
        second_process.stdin = MagicMock()
        second_process.stdin.drain = AsyncMock()

        errors: list[str] = []

        async def on_error(msg: str) -> None:
            errors.append(msg)

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                side_effect=[first_process, second_process],
            ):
                backend = LibIec61850ReportBackend()
                await backend.subscribe(
                    "localhost", 102, "Simulator", "EventsRCB01",
                    event_callback=AsyncMock(),
                    error_callback=on_error,
                    max_reconnect_attempts=1,
                )
                # Wait for reconnect to happen (1s backoff + READY timeout)
                await asyncio.sleep(2.0)
                await backend.close()

        # Should have received reconnect_failed notification
        assert any("reconnect_failed" in e for e in errors), (
            f"expected 'reconnect_failed' in errors, got {errors}"
        )
        assert not backend.is_active

    @pytest.mark.asyncio
    async def test_unexpected_stopped_calls_error_callback(self) -> None:
        """意外 STOPPED 行（非 close 触发）触发 error_callback。"""
        mock_process = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            side_effect=[
                b"READY\n",
                b"STOPPED\n",
            ]
        )
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.returncode = None
        mock_process.stdin = MagicMock()
        mock_process.stdin.drain = AsyncMock()

        errors: list[str] = []

        async def on_error(msg: str) -> None:
            errors.append(msg)

        with patch(
            "whale.shared.source.iec61850.backends.libiec61850_report_backend.resolve_report_runner_path",
        ) as mock_resolve:
            mock_resolve.return_value.exists.return_value = True
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_process,
            ):
                backend = LibIec61850ReportBackend()
                await backend.subscribe(
                    "localhost", 102, "Simulator", "EventsRCB01",
                    event_callback=AsyncMock(),
                    error_callback=on_error,
                )
                await asyncio.sleep(0.05)
                await backend.close()

        assert any("stopped_unexpectedly" in e for e in errors), (
            f"expected 'stopped_unexpectedly' in errors, got {errors}"
        )
