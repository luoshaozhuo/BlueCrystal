from __future__ import annotations

import asyncio
import os
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from whale.shared.source.models import SourceConnectionProfile
from whale.shared.source.opcua.backends.base import (
    Open62541PreparedReadPlan,
    PreparedReadPlan,
    RawDataValue,
    RawOpcUaReadResult,
)

_CONNECT_TIMEOUT_FACTOR: Final[float] = 2.0
_PROCESS_STOP_TIMEOUT_S: Final[float] = 2.0
_READY_RESPONSE_PREFIX: Final[str] = "READY"
_RESULT_RESPONSE_PREFIX: Final[str] = "RESULT"
_RUNNER_SUMMARY_PREFIX: Final[str] = "RUNNER_SUMMARY"
_POLL_DONE_RESPONSE_PREFIX: Final[str] = "POLL_DONE"


@dataclass(frozen=True, slots=True)
class Open62541ReadDebugTiming:
    """Cross-process timing for one open62541 runner read command."""

    runner_scheduled_ts_ns: int | None = None
    runner_read_start_ts_ns: int | None = None
    runner_read_end_ts_ns: int | None = None


@dataclass(frozen=True, slots=True)
class _CachedPlanRuntime:
    """Runtime metadata stored alongside one prepared open62541 read plan."""

    node_ids_path: Path


def resolve_client_runner_path() -> Path:
    """Resolve the open62541 client runner executable path."""

    env_path = os.environ.get("WHALE_OPEN62541_CLIENT_RUNNER_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()

    source_lab_root = Path(__file__).resolve().parents[6] / "tools" / "source_lab"
    suffix = ".exe" if os.name == "nt" else ""
    return source_lab_root / "native" / "build" / f"open62541_client_runner{suffix}"


def _normalize_open62541_node_id(address: str) -> str:
    """Normalize one address to the string node id expected by the client runner."""

    if address.startswith("ns=") and ";s=" in address:
        return address.split(";s=", 1)[1]
    if address.startswith("nsu=") and ";s=" in address:
        return address.split(";s=", 1)[1]
    if address.startswith("s="):
        return address[2:]
    return address


def _datetime_from_runner_timestamp(value: str) -> datetime | None:
    try:
        unix_seconds = float(value)
    except ValueError:
        return None
    if unix_seconds <= 0:
        return None
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc)


class Open62541OpcUaClientBackend:
    """open62541-based OPC UA client backend backed by serial polling protocol."""

    def __init__(self, connection: SourceConnectionProfile) -> None:
        self._connection = connection
        self._connected = False
        self._nsidx: int | None = None
        self._runner: asyncio.subprocess.Process | None = None
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None
        self._read_plan_cache: dict[tuple[str, ...], Open62541PreparedReadPlan] = {}
        self._read_plan_runtime: dict[tuple[str, ...], _CachedPlanRuntime] = {}
        self._io_lock = asyncio.Lock()
        self._last_read_debug_timing: Open62541ReadDebugTiming | None = None

    async def connect(self) -> None:
        if self._connected:
            return

        runner_path = resolve_client_runner_path()
        if not runner_path.exists():
            raise RuntimeError(
                "open62541 client runner executable does not exist: "
                f"{runner_path}. Build `open62541_client_runner` first with CMake."
            )

        self._temp_dir = tempfile.TemporaryDirectory(prefix="open62541_client_runner_")
        self._runner = await asyncio.create_subprocess_exec(
            str(runner_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )

        try:
            ready_line = await self._read_protocol_line(
                expected_prefixes=(_READY_RESPONSE_PREFIX,),
                timeout_seconds=max(self._connection.timeout_seconds * _CONNECT_TIMEOUT_FACTOR, 1.0),
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
                    runner.stdin.write(b"STOP_POLL\nQUIT\n")
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

        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None

        self._connected = False
        self._nsidx = None
        self._read_plan_cache.clear()
        self._read_plan_runtime.clear()
        self._last_read_debug_timing = None

    @property
    def namespace_index(self) -> int | None:
        return self._nsidx

    def prepare_read(self, addresses: Sequence[str]) -> Open62541PreparedReadPlan:
        self._ensure_connected()
        if self._temp_dir is None:
            raise RuntimeError("open62541 client runner temp directory is not initialized")

        normalized_node_ids = tuple(_normalize_open62541_node_id(address) for address in addresses)
        cached = self._read_plan_cache.get(normalized_node_ids)
        if cached is not None:
            return cached

        plan = Open62541PreparedReadPlan(
            node_paths=normalized_node_ids,
            node_ids=normalized_node_ids,
            namespace_uri=self._connection.namespace_uri,
            namespace_index=self._nsidx,
        )
        node_ids_path = Path(self._temp_dir.name) / f"plan_{len(self._read_plan_cache)}.tsv"
        node_ids_path.write_text("\n".join(plan.node_ids) + "\n", encoding="utf-8")
        self._read_plan_cache[normalized_node_ids] = plan
        self._read_plan_runtime[normalized_node_ids] = _CachedPlanRuntime(node_ids_path=node_ids_path)
        return plan

    async def read_prepared_raw(self, plan: PreparedReadPlan) -> RawOpcUaReadResult:
        open62541_plan = self._require_plan_type(plan)
        runtime = self._runtime_for_plan(open62541_plan)

        async with self._io_lock:
            self._ensure_connected()
            runner = self._runner
            assert runner is not None
            if runner.stdin is None or runner.stdout is None:
                raise RuntimeError("open62541 client runner pipes are unavailable")

            timeout_s = max(self._connection.timeout_seconds, 1.0)
            period_ns = 1_000_000_000
            namespace_uri = self._connection.namespace_uri or "-"
            endpoint = self._connection.endpoint
            runner.stdin.write(
                (
                    "START_SERIAL_POLL\t0\t1.000000000\t1000000000\t0.000000000\t1.500000000\t"
                    f"{timeout_s:.9f}\t1\n"
                    f"ENDPOINT\t0\t{endpoint}\t{namespace_uri}\t-\t-\t{runtime.node_ids_path}\t0\n"
                    "END_SERIAL_POLL\n"
                ).encode("utf-8")
            )
            await runner.stdin.drain()

            first_result: tuple[int, datetime | None, str | None] | None = None
            summary_seen = False
            while True:
                line = await self._read_protocol_line(
                    expected_prefixes=(
                        _RESULT_RESPONSE_PREFIX,
                        _RUNNER_SUMMARY_PREFIX,
                        _POLL_DONE_RESPONSE_PREFIX,
                        "ERROR",
                    ),
                    timeout_seconds=max(timeout_s * 2.0, 2.0),
                )
                if line.startswith("ERROR"):
                    return RawOpcUaReadResult(
                        ok=False,
                        data_values=(),
                        response_timestamp=None,
                        error_reason="read_failed",
                        exception=line,
                    )
                if line.startswith(_RESULT_RESPONSE_PREFIX):
                    first_result = self._parse_result_line(line)
                    continue
                if line.startswith(_RUNNER_SUMMARY_PREFIX):
                    summary_seen = True
                    continue
                if line.startswith(_POLL_DONE_RESPONSE_PREFIX):
                    break

        if first_result is None:
            return RawOpcUaReadResult(
                ok=False,
                data_values=(),
                response_timestamp=None,
                error_reason="read_failed",
                exception="no_result",
            )

        value_count, response_timestamp, error_reason = first_result
        data_values = tuple(RawDataValue(value=True) for _ in range(value_count))
        return RawOpcUaReadResult(
            ok=error_reason is None,
            data_values=data_values if error_reason is None else (),
            response_timestamp=response_timestamp,
            error_reason=error_reason,
            exception=None if summary_seen else "missing_summary",
        )

    def _ensure_connected(self) -> None:
        if not self._connected or self._runner is None:
            raise RuntimeError("open62541 OPC UA client backend is not connected")

    def _require_plan_type(self, plan: PreparedReadPlan) -> Open62541PreparedReadPlan:
        if not isinstance(plan, Open62541PreparedReadPlan):
            raise TypeError("Open62541OpcUaClientBackend requires Open62541PreparedReadPlan")
        return plan

    def _runtime_for_plan(self, plan: Open62541PreparedReadPlan) -> _CachedPlanRuntime:
        runtime = self._read_plan_runtime.get(plan.node_paths)
        if runtime is None:
            raise RuntimeError("Prepared open62541 plan runtime metadata is missing")
        return runtime

    async def _read_protocol_line(
        self,
        *,
        expected_prefixes: tuple[str, ...],
        timeout_seconds: float,
    ) -> str:
        runner = self._runner
        assert runner is not None
        if runner.stdout is None:
            raise RuntimeError("open62541 client runner stdout is unavailable")

        while True:
            raw_line = await asyncio.wait_for(runner.stdout.readline(), timeout=timeout_seconds)
            if raw_line == b"":
                raise RuntimeError("open62541 client runner exited unexpectedly")
            line = raw_line.decode("utf-8", errors="replace").strip()
            if any(line.startswith(prefix) for prefix in expected_prefixes):
                return line

    def _parse_result_line(self, line: str) -> tuple[int, datetime | None, str | None]:
        fields = line.split("\t")
        if len(fields) != 13 or fields[0] != _RESULT_RESPONSE_PREFIX:
            raise RuntimeError(f"Unexpected runner RESULT response: {line!r}")

        value_count = int(fields[11])
        error_code = None if fields[8] == "OK" else fields[8]
        response_timestamp = _datetime_from_runner_timestamp(fields[12])
        self._last_read_debug_timing = Open62541ReadDebugTiming(
            runner_scheduled_ts_ns=int(fields[5]),
            runner_read_start_ts_ns=int(fields[6]),
            runner_read_end_ts_ns=int(fields[7]),
        )
        return value_count, response_timestamp, error_code
