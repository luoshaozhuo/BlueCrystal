"""IEC 104 client backend backed by native C runner subprocess."""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from whale.shared.source.iec104.backends.base import (
    RawIec104ReadResult,
    RawWriteItemResult,
)

_READY_RESPONSE_PREFIX: str = "READY"
_DONE_RESPONSE_PREFIX: str = "DONE"
_BATCH_RESPONSE_PREFIX: str = "BATCH"
_SAMPLE_RESPONSE_PREFIX: str = "SAMPLE"
_WRITE_RESULT_RESPONSE_PREFIX: str = "WRITE_RESULT"
_PROCESS_STOP_TIMEOUT_S: float = 2.0


def resolve_client_runner_path() -> Path:
    """Resolve the IEC 104 client runner executable path."""
    env_path = os.environ.get("WHALE_IEC104_CLIENT_RUNNER_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()

    source_lab_root = Path(__file__).resolve().parents[6] / "tools" / "source_lab"
    suffix = ".exe" if os.name == "nt" else ""
    return source_lab_root / "native" / "build" / f"iec104_client_runner{suffix}"


class Iec104Lib60870Backend:
    """IEC 104 client backend backed by native C runner subprocess."""

    def __init__(self, host: str, port: int, common_addr: int = 1) -> None:
        self._host = host
        self._port = port
        self._common_addr = common_addr
        self._connected = False
        self._runner: asyncio.subprocess.Process | None = None

    async def connect(self) -> None:
        if self._connected:
            return

        runner_path = resolve_client_runner_path()
        if not runner_path.exists():
            raise RuntimeError(
                "IEC 104 client runner executable does not exist: "
                f"{runner_path}. Build `iec104_client_runner` first with CMake."
            )

        self._runner = await asyncio.create_subprocess_exec(
            str(runner_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )

        try:
            ready_line = await self._read_protocol_line(
                expected_prefixes=(_READY_RESPONSE_PREFIX,),
                timeout_seconds=5.0,
            )
            if ready_line != _READY_RESPONSE_PREFIX:
                raise RuntimeError(f"Unexpected runner ready response: {ready_line!r}")
            self._connected = True
        except Exception:
            await self.disconnect()
            raise

    async def disconnect(self) -> None:
        runner = self._runner
        self._runner = None

        if runner is not None:
            try:
                if runner.returncode is None and runner.stdin is not None:
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

        self._connected = False

    async def __aenter__(self) -> Iec104Lib60870Backend:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.disconnect()

    async def read(self, ioa_list: tuple[int, ...]) -> RawIec104ReadResult:
        """Execute one IEC 104 interrogation read via CLI polling mode.

        Spawns a fresh runner process for each read.
        """
        runner_path = resolve_client_runner_path()

        proc = await asyncio.create_subprocess_exec(
            str(runner_path),
            self._host, str(self._port),
            str(self._common_addr),
            "0",  # interval_ms
            "1",  # count (single read)
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        assert proc.stdout is not None

        try:
            sample_values: dict[int, tuple[str, str]] = {}
            done = False

            while not done:
                try:
                    raw_line = await asyncio.wait_for(
                        proc.stdout.readline(), timeout=15.0
                    )
                except asyncio.TimeoutError:
                    break

                if raw_line == b"":
                    break

                line = raw_line.decode("utf-8", errors="replace").strip()
                if line.startswith(_SAMPLE_RESPONSE_PREFIX):
                    parsed = self._parse_sample_line(line)
                    if parsed is not None:
                        ioa, type_tag, value_str = parsed
                        sample_values[ioa] = (type_tag, value_str)
                elif line.startswith(_DONE_RESPONSE_PREFIX):
                    done = True
                elif line.startswith(_BATCH_RESPONSE_PREFIX):
                    continue
                elif line == _READY_RESPONSE_PREFIX:
                    continue

            if not sample_values:
                return RawIec104ReadResult(
                    ok=False, values={},
                    error_reason="read_failed",
                    exception="no_samples_received",
                )

            return RawIec104ReadResult(
                ok=True,
                values=sample_values,
                response_timestamp=datetime.now(tz=timezone.utc),
            )
        except asyncio.TimeoutError:
            return RawIec104ReadResult(
                ok=False, values={},
                error_reason="timeout",
                exception="read_timed_out",
            )
        finally:
            if proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()

    async def write(
        self,
        ioa: int,
        command_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        """Write one IEC 104 command via the native runner subprocess."""
        if not self._connected or self._runner is None:
            await self.connect()

        assert self._runner is not None
        assert self._runner.stdin is not None
        assert self._runner.stdout is not None

        safe_request_id = request_id or "cli"
        cmd = (
            f"WRITE\t{safe_request_id}\t{self._host}\t{self._port}\t"
            f"{self._common_addr}\t{ioa}\t{command_type}\t{value}\n"
        )
        self._runner.stdin.write(cmd.encode("utf-8"))
        await self._runner.stdin.drain()

        line = await self._read_protocol_line(
            expected_prefixes=(_WRITE_RESULT_RESPONSE_PREFIX, "ERROR"),
            timeout_seconds=10.0,
        )

        if line.startswith("ERROR"):
            return RawWriteItemResult(
                ioa=ioa,
                ok=False,
                status_code="runner_error",
                error_message=line,
                command_type=command_type,
            )

        return self._parse_write_result_line(line, ioa, command_type)

    @staticmethod
    def _parse_sample_line(line: str) -> tuple[int, str, str] | None:
        """Parse a SAMPLE line from the runner.

        Format: SAMPLE\\t<count>\\t<ioa>\\t<type>\\t<value>
        """
        fields = line.split("\t")
        if len(fields) < 5:
            return None
        try:
            ioa = int(fields[2])
            type_tag = fields[3]
            value_str = fields[4]
            return (ioa, type_tag, value_str)
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _parse_write_result_line(
        line: str,
        expected_ioa: int,
        expected_command_type: str,
    ) -> RawWriteItemResult:
        """Parse a WRITE_RESULT line from the runner.

        Expected format::
            WRITE_RESULT\\t<request_id>\\tok=<0|1>\\t<status>
        """
        fields = line.split("\t")
        if len(fields) < 4 or fields[0] != _WRITE_RESULT_RESPONSE_PREFIX:
            return RawWriteItemResult(
                ioa=expected_ioa,
                ok=False,
                status_code="protocol_error",
                error_message=f"Unexpected WRITE_RESULT format: {line!r}",
                command_type=expected_command_type,
            )

        ok_field = fields[2] if len(fields) > 2 else "ok=0"
        ok = ok_field == "ok=1"
        status = fields[3] if len(fields) > 3 else None

        return RawWriteItemResult(
            ioa=expected_ioa,
            ok=ok,
            status_code="OK" if ok else (status or "write_failed"),
            error_message=None if ok else (status or "write_failed"),
            command_type=expected_command_type,
        )

    async def _read_protocol_line(
        self,
        *,
        expected_prefixes: tuple[str, ...],
        timeout_seconds: float,
    ) -> str:
        assert self._runner is not None
        assert self._runner.stdout is not None

        while True:
            raw_line = await asyncio.wait_for(
                self._runner.stdout.readline(), timeout=timeout_seconds
            )
            if raw_line == b"":
                raise RuntimeError("IEC 104 client runner exited unexpectedly")
            line = raw_line.decode("utf-8", errors="replace").strip()
            if any(line.startswith(prefix) for prefix in expected_prefixes):
                return line
