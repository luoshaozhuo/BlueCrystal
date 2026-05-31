"""libiec61850-based IEC 61850 MMS client backend (subprocess runner)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from whale.shared.source.runner_resolution import (
    ResolvedRunnerPath,
    build_runner_unavailable_message,
    is_source_lab_dev_runner_path,
    resolve_native_runner_path,
)
from whale.shared.source.iec61850.backends.base import (
    RawMmsReadResult,
    RawWriteItemResult,
)

_CONNECT_TIMEOUT_FACTOR: float = 2.0
_PROCESS_STOP_TIMEOUT_S: float = 2.0
_READY_RESPONSE_PREFIX: str = "READY"
_READ_RESULT_RESPONSE_PREFIX: str = "READ_RESULT"
_WRITE_RESULT_RESPONSE_PREFIX: str = "WRITE_RESULT"


def resolve_client_runner_path() -> Path:
    """Resolve the IEC 61850 MMS client runner executable path."""
    return resolve_native_runner_path(
        executable_stem="iec61850_mms_client_runner",
        specific_env_var="WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH",
    ).path


@dataclass(frozen=True, slots=True)
class _MmsConnectionParams:
    """Connection parameters for MMS READ/WRITE commands."""

    host: str
    port: int


class LibIec61850MmsClientBackend:
    """libiec61850-based MMS client backend using subprocess runner."""

    def __init__(self, host: str, port: int, *, timeout_seconds: float = 5.0) -> None:
        self._host = host
        self._port = port
        self._timeout_seconds = timeout_seconds
        self._connected = False
        self._runner: asyncio.subprocess.Process | None = None

    @property
    def _connection_params(self) -> _MmsConnectionParams:
        return _MmsConnectionParams(host=self._host, port=self._port)

    async def connect(self) -> None:
        if self._connected:
            return

        runner_path = resolve_client_runner_path()
        if not runner_path.exists():
            resolution = resolve_native_runner_path(
                executable_stem="iec61850_mms_client_runner",
                specific_env_var="WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH",
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
                    runner_label="IEC 61850 MMS client runner",
                    specific_env_var="WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH",
                    resolution=resolution,
                )
            )

        self._runner = await asyncio.create_subprocess_exec(
            str(runner_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            ready_line = await self._read_protocol_line(
                expected_prefixes=(_READY_RESPONSE_PREFIX,),
                timeout_seconds=max(self._timeout_seconds * _CONNECT_TIMEOUT_FACTOR, 1.0),
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
        self._connected = False

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

    def _ensure_connected(self) -> None:
        if not self._connected or self._runner is None:
            raise RuntimeError("IEC 61850 MMS client backend is not connected")

    async def _read_protocol_line(
        self,
        *,
        expected_prefixes: tuple[str, ...],
        timeout_seconds: float,
    ) -> str:
        runner = self._runner
        assert runner is not None
        if runner.stdout is None:
            raise RuntimeError("IEC 61850 MMS client runner stdout is unavailable")

        while True:
            raw_line = await asyncio.wait_for(runner.stdout.readline(), timeout=timeout_seconds)
            if raw_line == b"":
                raise RuntimeError("IEC 61850 MMS client runner exited unexpectedly")
            line = raw_line.decode("utf-8", errors="replace").strip()
            if any(line.startswith(prefix) for prefix in expected_prefixes):
                return line

    async def read(
        self,
        obj_ref: str,
        fc: str,
        *,
        request_id: str = "",
    ) -> RawMmsReadResult:
        """Read one MMS variable via the runner subprocess."""
        if not self._connected or self._runner is None:
            await self.connect()

        self._ensure_connected()
        runner = self._runner
        assert runner is not None
        if runner.stdin is None or runner.stdout is None:
            raise RuntimeError("IEC 61850 MMS client runner pipes are unavailable")

        safe_rid = request_id or "cli"
        fc_arg = fc if fc else "NONE"
        cmd = f"READ\t{safe_rid}\t{self._host}\t{self._port}\t{obj_ref}\t{fc_arg}\n"
        runner.stdin.write(cmd.encode("utf-8"))
        await runner.stdin.drain()

        timeout_s = max(self._timeout_seconds * 2.0, 5.0)
        line = await self._read_protocol_line(
            expected_prefixes=(_READ_RESULT_RESPONSE_PREFIX, "WRITE_RESULT"),
            timeout_seconds=timeout_s,
        )

        if line.startswith("WRITE_RESULT"):
            return RawMmsReadResult(
                ok=False,
                obj_ref=obj_ref,
                value_type=None,
                value=None,
                error_reason="protocol_error",
                exception="unexpected_write_result_for_read",
            )

        return self._parse_read_result_line(line, obj_ref)

    async def write(
        self,
        obj_ref: str,
        fc: str,
        value_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        """Write one MMS variable via the runner subprocess."""
        if not self._connected or self._runner is None:
            await self.connect()

        self._ensure_connected()
        runner = self._runner
        assert runner is not None
        if runner.stdin is None or runner.stdout is None:
            raise RuntimeError("IEC 61850 MMS client runner pipes are unavailable")

        safe_rid = request_id or "cli"
        fc_arg = fc if fc else "NONE"
        cmd = f"WRITE\t{safe_rid}\t{self._host}\t{self._port}\t{obj_ref}\t{fc_arg}\t{value_type}\t{value}\n"
        runner.stdin.write(cmd.encode("utf-8"))
        await runner.stdin.drain()

        timeout_s = max(self._timeout_seconds * 2.0, 5.0)
        line = await self._read_protocol_line(
            expected_prefixes=(_WRITE_RESULT_RESPONSE_PREFIX,),
            timeout_seconds=timeout_s,
        )

        return self._parse_write_result_line(line, obj_ref, value_type)

    @staticmethod
    def _parse_read_result_line(line: str, expected_obj_ref: str) -> RawMmsReadResult:
        """Parse a READ_RESULT line.

        Expected format:
            READ_RESULT\t<request_id>\t<obj_ref>\tok=<0|1>\t<status>\t<value_type>\t<value>
        """
        fields = line.split("\t")
        if len(fields) < 5 or fields[0] != _READ_RESULT_RESPONSE_PREFIX:
            return RawMmsReadResult(
                ok=False,
                obj_ref=expected_obj_ref,
                value_type=None,
                value=None,
                error_reason="protocol_error",
                exception=f"Unexpected READ_RESULT format: {line!r}",
            )

        obj_ref = fields[2] if len(fields) > 2 else expected_obj_ref
        ok_field = fields[3] if len(fields) > 3 else "ok=0"
        ok = ok_field == "ok=1"
        status = fields[4] if len(fields) > 4 else None
        value_type = fields[5] if len(fields) > 5 else None
        value = fields[6] if len(fields) > 6 else None

        if ok:
            return RawMmsReadResult(
                ok=True,
                obj_ref=obj_ref,
                value_type=value_type,
                value=value,
                error_reason=None,
                exception=None,
            )

        return RawMmsReadResult(
            ok=False,
            obj_ref=obj_ref,
            value_type=value_type,
            value=None,
            error_reason=status,
            exception=None,
        )

    @staticmethod
    def _parse_write_result_line(
        line: str,
        expected_obj_ref: str,
        expected_value_type: str,
    ) -> RawWriteItemResult:
        """Parse a WRITE_RESULT line.

        Expected format:
            WRITE_RESULT\t<request_id>\t<obj_ref>\tok=<0|1>\t<status>\t<value_type>
        """
        fields = line.split("\t")
        if len(fields) < 4 or fields[0] != _WRITE_RESULT_RESPONSE_PREFIX:
            return RawWriteItemResult(
                obj_ref=expected_obj_ref,
                ok=False,
                status_code="protocol_error",
                error_message=f"Unexpected WRITE_RESULT format: {line!r}",
                value_type=expected_value_type,
            )

        obj_ref = fields[2] if len(fields) > 2 else expected_obj_ref
        ok_field = fields[3] if len(fields) > 3 else "ok=0"
        ok = ok_field == "ok=1"
        status = fields[4] if len(fields) > 4 else None
        value_type = expected_value_type
        if len(fields) > 5 and fields[5]:
            value_type = fields[5]

        return RawWriteItemResult(
            obj_ref=obj_ref,
            ok=ok,
            status_code="OK" if ok else status,
            error_message=None if ok else (status or "write_failed"),
            value_type=value_type,
        )
