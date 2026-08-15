"""Modbus TCP client backend backed by native C runner subprocess."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from pacific.whale.shared.source.runner_resolution import (
    ResolvedRunnerPath,
    build_runner_unavailable_message,
    is_source_lab_dev_runner_path,
    resolve_native_runner_path,
)
from pacific.whale.shared.source.modbus.backends.base import (
    ModbusPreparedReadPlan,
    RawModbusReadResult,
    RawWriteItemResult,
)

_READY_RESPONSE_PREFIX: str = "READY"
_WRITE_RESULT_RESPONSE_PREFIX: str = "WRITE_RESULT"
_PROCESS_STOP_TIMEOUT_S: float = 2.0


def resolve_client_runner_path() -> Path:
    """Resolve the modbus TCP client runner executable path."""
    return resolve_native_runner_path(
        executable_stem="modbus_tcp_polling_runner",
        specific_env_var="WHALE_MODBUS_CLIENT_RUNNER_PATH",
    ).path


class ModbusTcpClientBackend:
    """Modbus TCP client backend backed by native C runner subprocess."""

    def __init__(self, host: str, port: int, unit_id: int = 1) -> None:
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._connected = False
        self._runner: asyncio.subprocess.Process | None = None

    async def connect(self) -> None:
        if self._connected:
            return

        runner_path = resolve_client_runner_path()
        if not runner_path.exists():
            resolution = resolve_native_runner_path(
                executable_stem="modbus_tcp_polling_runner",
                specific_env_var="WHALE_MODBUS_CLIENT_RUNNER_PATH",
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
                    runner_label="Modbus client runner",
                    specific_env_var="WHALE_MODBUS_CLIENT_RUNNER_PATH",
                    resolution=resolution,
                )
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

    async def __aenter__(self) -> ModbusTcpClientBackend:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.disconnect()

    def prepare_read(self, reg_addrs: tuple[int, ...]) -> ModbusPreparedReadPlan:
        return ModbusPreparedReadPlan(
            reg_addrs=reg_addrs,
            unit_id=self._unit_id,
        )

    async def read_prepared(self, plan: ModbusPreparedReadPlan) -> RawModbusReadResult:
        """Read holding registers. Uses the C runner in polling mode via CLI."""
        runner_path = resolve_client_runner_path()

        start_addr = plan.reg_addrs[0] if plan.reg_addrs else 0
        reg_count = max(1, len(plan.reg_addrs))

        proc = await asyncio.create_subprocess_exec(
            str(runner_path),
            self._host, str(self._port),
            str(plan.unit_id),
            str(start_addr), str(reg_count),
            "0",  # interval_ms (0 = no repeat)
            "1",  # count (single read)
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        assert proc.stdout is not None

        try:
            # Read READY line
            ready_line = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
            ready = ready_line.decode("utf-8", errors="replace").strip()
            if ready != _READY_RESPONSE_PREFIX:
                return RawModbusReadResult(
                    ok=False, values=(),
                    error_reason="protocol_error",
                    exception=f"unexpected_ready:{ready}",
                )

            # Read SAMPLE line
            sample_line = await asyncio.wait_for(proc.stdout.readline(), timeout=10.0)
            sample = sample_line.decode("utf-8", errors="replace").strip()
            if not sample.startswith("SAMPLE"):
                return RawModbusReadResult(
                    ok=False, values=(),
                    error_reason="read_failed",
                    exception=f"no_sample:{sample}",
                )

            fields = sample.split("\t")
            values = tuple(int(v) for v in fields[1:] if v.strip())

            # Drain remaining output
            remaining = await asyncio.wait_for(proc.stdout.read(), timeout=5.0)
            _ = remaining  # BATCH/SUMMARY/DONE

            return RawModbusReadResult(
                ok=True,
                values=values,
                response_timestamp=datetime.now(tz=timezone.utc),
            )
        except asyncio.TimeoutError:
            return RawModbusReadResult(
                ok=False, values=(),
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
        reg_addr: int,
        value_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        """Write one holding register via the native runner subprocess.

        The runner is started fresh (or reused if already connected).
        """
        if not self._connected or self._runner is None:
            await self.connect()

        assert self._runner is not None
        assert self._runner.stdin is not None
        assert self._runner.stdout is not None

        safe_request_id = request_id or "cli"
        cmd = (
            f"WRITE\t{safe_request_id}\t{self._host}\t{self._port}\t"
            f"{self._unit_id}\t{reg_addr}\t{value_type}\t{value}\n"
        )
        self._runner.stdin.write(cmd.encode("utf-8"))
        await self._runner.stdin.drain()

        line = await self._read_protocol_line(
            expected_prefixes=(_WRITE_RESULT_RESPONSE_PREFIX, "ERROR"),
            timeout_seconds=10.0,
        )

        if line.startswith("ERROR"):
            return RawWriteItemResult(
                reg_addr=reg_addr,
                ok=False,
                status_code="runner_error",
                error_message=line,
            )

        return self._parse_write_result_line(line, reg_addr)

    async def _read_protocol_line(
        self,
        *,
        expected_prefixes: tuple[str, ...],
        timeout_seconds: float,
    ) -> str:
        assert self._runner is not None
        assert self._runner.stdout is not None

        while True:
            raw_line = await asyncio.wait_for(self._runner.stdout.readline(), timeout=timeout_seconds)
            if raw_line == b"":
                raise RuntimeError("Modbus client runner exited unexpectedly")
            line = raw_line.decode("utf-8", errors="replace").strip()
            if any(line.startswith(prefix) for prefix in expected_prefixes):
                return line

    @staticmethod
    def _parse_write_result_line(line: str, expected_reg_addr: int) -> RawWriteItemResult:
        """Parse a WRITE_RESULT line from the runner.

        Expected format::
            WRITE_RESULT\\t<request_id>\\tok=<0|1>\\t<status>\\t<extra_fields>
        """
        fields = line.split("\t")
        if len(fields) < 4 or fields[0] != _WRITE_RESULT_RESPONSE_PREFIX:
            return RawWriteItemResult(
                reg_addr=expected_reg_addr,
                ok=False,
                status_code="protocol_error",
                error_message=f"Unexpected WRITE_RESULT format: {line!r}",
            )

        ok_field = fields[2] if len(fields) > 2 else "ok=0"
        ok = ok_field == "ok=1"
        status = fields[3] if len(fields) > 3 else None

        # Extract reg_addr from extra fields if present
        reg_addr = expected_reg_addr
        for extra in fields[4:]:
            if extra.startswith("reg_addr="):
                try:
                    reg_addr = int(extra.split("=", 1)[1])
                except (ValueError, IndexError):
                    pass

        return RawWriteItemResult(
            reg_addr=reg_addr,
            ok=ok,
            status_code="OK" if ok else status,
            error_message=None if ok else (status or "write_failed"),
        )
