"""libiec61850-based IEC 61850 Report backend (subprocess runner).

Connects to an IEC 61850 server, subscribes to a Report Control Block,
and delivers REPORT events via async callback.

Architecture:
- Runs ``iec61850_report_runner`` as a subprocess.
- Uses stdin/stdout protocol: send QUIT to stop, parse REPORT lines from stdout.
- stderr is captured for diagnostics.
- No ingest imports. No source_lab imports.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TypedDict

from whale.shared.source.runner_resolution import (
    ResolvedRunnerPath,
    build_runner_unavailable_message,
    is_source_lab_dev_runner_path,
    resolve_native_runner_path,
)
from whale.shared.source.iec61850.backends.report_base import (
    RawReportEvent,
    RawReportEventHandler,
    ReportErrorHandler,
)

_PROCESS_STOP_TIMEOUT_S: float = 3.0
_READY_TIMEOUT_FACTOR: float = 2.0

_READY_PREFIX: str = "READY"
_REPORT_PREFIX: str = "REPORT"
_ERROR_PREFIX: str = "ERROR"
_STOPPED_PREFIX: str = "STOPPED"

_RECONNECT_BASE_DELAY_S: float = 1.0
_RECONNECT_MAX_DELAY_S: float = 5.0


class _SubscribeArgs(TypedDict):
    """重连时复用的订阅参数快照。"""

    host: str
    port: int
    ied_name: str
    rcb_ref: str
    timeout_seconds: float


def resolve_report_runner_path() -> Path:
    """Resolve the IEC 61850 report runner executable path."""
    return resolve_native_runner_path(
        executable_stem="iec61850_report_runner",
        specific_env_var="WHALE_IEC61850_REPORT_RUNNER_PATH",
    ).path


class LibIec61850ReportBackend:
    """libiec61850-based Report backend using subprocess runner."""

    def __init__(self) -> None:
        self._runner: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._event_callback: RawReportEventHandler | None = None
        self._error_callback: ReportErrorHandler | None = None
        self._closed = False

        # Reconnect state
        self._max_reconnect_attempts: int = 0
        self._reconnect_attempts: int = 0
        self._subscribe_args: _SubscribeArgs = {
            "host": "",
            "port": 0,
            "ied_name": "",
            "rcb_ref": "",
            "timeout_seconds": 10.0,
        }

    @property
    def is_active(self) -> bool:
        """Whether the backend currently has an active subscription."""
        return self._runner is not None and self._reader_task is not None and not self._closed

    async def subscribe(
        self,
        host: str,
        port: int,
        ied_name: str,
        rcb_ref: str,
        *,
        timeout_seconds: float = 10.0,
        event_callback: RawReportEventHandler,
        error_callback: ReportErrorHandler | None = None,
        max_reconnect_attempts: int = 0,
    ) -> None:
        """Start report subscription via subprocess runner.

        Args:
            host: Server hostname or IP.
            port: Server port.
            ied_name: IED name.
            rcb_ref: RCB reference (short name or full ref).
            timeout_seconds: Timeout for initial READY from runner.
            event_callback: Async callback invoked for each REPORT line.
            error_callback: Optional async callback for errors.
            max_reconnect_attempts: Max reconnect attempts on unexpected exit.
                Default 0 = disabled.
        """
        if self.is_active:
            raise RuntimeError("Report subscription already active")

        self._event_callback = event_callback
        self._error_callback = error_callback
        self._max_reconnect_attempts = max_reconnect_attempts
        self._reconnect_attempts = 0
        self._subscribe_args = {
            "host": host,
            "port": port,
            "ied_name": ied_name,
            "rcb_ref": rcb_ref,
            "timeout_seconds": timeout_seconds,
        }

        await self._start_subprocess()

        # Wait for READY
        await self._wait_for_ready(timeout_seconds)

        # Start background reader task
        self._reader_task = asyncio.create_task(self._reader_loop())

    async def _start_subprocess(self) -> None:
        """Create the report runner subprocess."""
        runner_path = resolve_report_runner_path()
        if not runner_path.exists():
            resolution = resolve_native_runner_path(
                executable_stem="iec61850_report_runner",
                specific_env_var="WHALE_IEC61850_REPORT_RUNNER_PATH",
            )
            if runner_path != resolution.path:
                resolution = ResolvedRunnerPath(
                    executable_name=runner_path.name,
                    path=runner_path,
                    source="custom_override",
                    evidence_level="unknown",
                    used_dev_fallback=is_source_lab_dev_runner_path(runner_path),
                )
            raise RuntimeError(
                build_runner_unavailable_message(
                    runner_label="IEC 61850 report runner",
                    specific_env_var="WHALE_IEC61850_REPORT_RUNNER_PATH",
                    resolution=resolution,
                )
            )

        args = self._subscribe_args
        self._runner = await asyncio.create_subprocess_exec(
            str(runner_path),
            str(args["host"]),
            str(args["port"]),
            str(args["ied_name"]),
            str(args["rcb_ref"]),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def _wait_for_ready(self, timeout_seconds: float) -> None:
        """Wait for READY line from the runner."""
        try:
            ready_line = await self._read_protocol_line(
                timeout_seconds=max(timeout_seconds * _READY_TIMEOUT_FACTOR, 5.0),
            )
            if ready_line is None:
                raise RuntimeError("Report runner exited before READY")
            if not ready_line.startswith(_READY_PREFIX):
                raise RuntimeError(
                    f"Unexpected report runner response: {ready_line!r}"
                )
        except Exception:
            await self._close_runner()
            raise

    async def close(self) -> None:
        """Stop the subscription and release resources."""
        if self._closed:
            return
        self._closed = True

        # Cancel reader task
        if self._reader_task is not None:
            self._reader_task.cancel()
            try:
                await asyncio.wait_for(self._reader_task, timeout=_PROCESS_STOP_TIMEOUT_S)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            self._reader_task = None

        await self._close_runner()
        self._event_callback = None
        self._error_callback = None

    async def _reader_loop(self) -> None:
        """Background task: read stdout lines and dispatch events."""
        runner = self._runner
        if runner is None or runner.stdout is None:
            return

        try:
            while True:
                raw_line = await runner.stdout.readline()
                if raw_line == b"":
                    # Process exited unexpectedly
                    await self._on_unexpected_exit("process_exited_unexpectedly")
                    return

                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                if line.startswith(_REPORT_PREFIX):
                    event = self._parse_report_line(line)
                    if self._event_callback is not None:
                        await self._event_callback(event)
                elif line.startswith(_ERROR_PREFIX):
                    error_msg = line[len(_ERROR_PREFIX):].strip() or "unknown_error"
                    await self._on_runner_error(error_msg)
                elif line.startswith(_STOPPED_PREFIX):
                    # Unexpected STOPPED (not from close())
                    if not self._closed:
                        await self._on_unexpected_exit("stopped_unexpectedly")
                    return
                elif line.startswith(_READY_PREFIX):
                    pass  # Already handled in subscribe()
                else:
                    pass  # Unknown/noise — ignore
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            if not self._closed:
                await self._on_unexpected_exit(f"reader_error:{exc}")

    async def _on_runner_error(self, error_msg: str) -> None:
        """Handle an ERROR line from the runner. Runner continues running."""
        if self._error_callback is not None:
            try:
                await self._error_callback(error_msg)
            except Exception:
                pass

    async def _on_unexpected_exit(self, reason: str) -> None:
        """Handle unexpected exit: propagate error, possibly reconnect."""
        if self._closed:
            return

        # Try reconnect if enabled and attempts remain
        if (
            self._max_reconnect_attempts > 0
            and self._reconnect_attempts < self._max_reconnect_attempts
        ):
            self._reconnect_attempts += 1
            delay = min(
                _RECONNECT_BASE_DELAY_S * (2 ** (self._reconnect_attempts - 1)),
                _RECONNECT_MAX_DELAY_S,
            )
            await asyncio.sleep(delay)
            try:
                await self._reconnect()
                # Notify adapter that reconnect succeeded
                if self._error_callback is not None:
                    try:
                        await self._error_callback("reconnected")
                    except Exception:
                        pass
                return
            except Exception as exc:
                # Reconnect failed — notify with permanent failure
                if self._error_callback is not None:
                    try:
                        await self._error_callback(f"subscription_terminated:reconnect_failed:{exc}")
                    except Exception:
                        pass

        # Permanent failure — no reconnect or exhausted
        if self._error_callback is not None:
            try:
                await self._error_callback(f"subscription_terminated:{reason}")
            except Exception:
                pass

        self._closed = True
        await self._close_runner()
        self._event_callback = None

    async def _reconnect(self) -> None:
        """Reconnect: create new subprocess and resubscribe."""
        # Clean up old runner
        await self._close_runner()

        # Create new subprocess
        await self._start_subprocess()

        # Wait for READY
        args = self._subscribe_args
        timeout_seconds = args["timeout_seconds"]
        await self._wait_for_ready(timeout_seconds)

        # Restart reader loop (old loop already returned)
        self._reader_task = asyncio.create_task(self._reader_loop())

    async def _read_protocol_line(
        self,
        *,
        timeout_seconds: float,
    ) -> str | None:
        """Read the first protocol line from stdout.

        Returns the line or None if the process exited.
        """
        runner = self._runner
        if runner is None or runner.stdout is None:
            return None

        try:
            raw_line = await asyncio.wait_for(
                runner.stdout.readline(), timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            raise RuntimeError("Report runner READY timeout") from None

        if raw_line == b"":
            return None

        return raw_line.decode("utf-8", errors="replace").strip()

    async def _close_runner(self) -> None:
        """Stop the subprocess and wait for exit."""
        runner = self._runner
        self._runner = None

        if runner is None:
            return

        # Send QUIT via stdin
        if runner.returncode is None and runner.stdin is not None:
            try:
                runner.stdin.write(b"QUIT\n")
                await runner.stdin.drain()
            except (BrokenPipeError, ConnectionResetError, RuntimeError):
                pass

        try:
            await asyncio.wait_for(runner.wait(), timeout=_PROCESS_STOP_TIMEOUT_S)
        except asyncio.TimeoutError:
            runner.terminate()
            try:
                await asyncio.wait_for(runner.wait(), timeout=_PROCESS_STOP_TIMEOUT_S)
            except asyncio.TimeoutError:
                runner.kill()
                await runner.wait()

    @staticmethod
    def _parse_report_line(line: str) -> RawReportEvent:
        """Parse a REPORT protocol line.

        Expected format:
            REPORT\t<rcb_ref>\t<timestamp_ms>\t<seq_num>\t<array_size>\t<val1>\t<val2>...
        """
        fields = line.split("\t")
        if len(fields) < 5 or fields[0] != _REPORT_PREFIX:
            return RawReportEvent(
                ok=False,
                rcb_ref="-",
                timestamp_ms=0,
                seq_num=0,
                values=(),
                error_reason=f"Unexpected REPORT format: {line!r}",
            )

        rcb_ref = fields[1]
        try:
            timestamp_ms = int(fields[2])
        except (ValueError, IndexError):
            timestamp_ms = 0
        try:
            seq_num = int(fields[3])
        except (ValueError, IndexError):
            seq_num = 0
        try:
            array_size = int(fields[4])
        except (ValueError, IndexError):
            array_size = 0

        values = tuple(fields[5:5 + array_size]) if len(fields) > 5 else ()

        return RawReportEvent(
            ok=True,
            rcb_ref=rcb_ref,
            timestamp_ms=timestamp_ms,
            seq_num=seq_num,
            values=values,
        )
