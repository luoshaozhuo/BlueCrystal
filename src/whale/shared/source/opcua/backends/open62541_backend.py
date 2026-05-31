"""open62541 OPC UA 客户端后端实现。

通过 open62541 C native binary 子进程提供 OPC UA 读写能力。
使用 stdin/stdout 协议与 native runner 通信。
"""
from __future__ import annotations

import asyncio
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from whale.shared.source.runner_resolution import (
    ResolvedRunnerPath,
    build_runner_unavailable_message,
    is_source_lab_dev_runner_path,
    resolve_native_runner_path,
)
from whale.shared.source.models import SourceConnectionProfile
from whale.shared.source.opcua.backends.base import (
    Open62541PreparedReadPlan,
    PreparedReadPlan,
    RawDataValue,
    RawOpcUaReadResult,
    RawWriteItemResult,
)

_CONNECT_TIMEOUT_FACTOR: Final[float] = 2.0
_PROCESS_STOP_TIMEOUT_S: Final[float] = 2.0
_READY_RESPONSE_PREFIX: Final[str] = "READY"
_RESULT_RESPONSE_PREFIX: Final[str] = "RESULT"
_VALUE_RESPONSE_PREFIX: Final[str] = "VALUE"
_RUNNER_SUMMARY_PREFIX: Final[str] = "RUNNER_SUMMARY"
_POLL_DONE_RESPONSE_PREFIX: Final[str] = "POLL_DONE"
_WRITE_RESULT_RESPONSE_PREFIX: Final[str] = "WRITE_RESULT"


@dataclass(frozen=True, slots=True)
class _ParsedReadResult:
    """一次 RESULT 行解析结果。"""

    value_count: int
    response_timestamp: datetime | None
    error_reason: str | None


@dataclass(frozen=True, slots=True)
class _ParsedValueLine:
    """一次 VALUE 行解析结果。"""

    value_index: int
    status_code: str | None
    value_text: str
    source_timestamp: datetime | None
    server_timestamp: datetime | None


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
    return resolve_native_runner_path(
        executable_stem="open62541_client_runner",
        specific_env_var="WHALE_OPEN62541_CLIENT_RUNNER_PATH",
    ).path


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
            resolution = resolve_native_runner_path(
                executable_stem="open62541_client_runner",
                specific_env_var="WHALE_OPEN62541_CLIENT_RUNNER_PATH",
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
                    runner_label="open62541 client runner",
                    specific_env_var="WHALE_OPEN62541_CLIENT_RUNNER_PATH",
                    resolution=resolution,
                )
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

            latest_result: _ParsedReadResult | None = None
            latest_values: list[RawDataValue | None] = []
            summary_seen = False
            while True:
                line = await self._read_protocol_line(
                    expected_prefixes=(
                        _RESULT_RESPONSE_PREFIX,
                        _VALUE_RESPONSE_PREFIX,
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
                    latest_result = self._parse_result_line(line)
                    latest_values = [None] * latest_result.value_count
                    continue
                if line.startswith(_VALUE_RESPONSE_PREFIX):
                    if latest_result is None:
                        return RawOpcUaReadResult(
                            ok=False,
                            data_values=(),
                            response_timestamp=None,
                            error_reason="protocol_error",
                            exception="value_before_result",
                        )
                    parsed_value = self._parse_value_line(line)
                    if parsed_value.value_index < 0 or parsed_value.value_index >= latest_result.value_count:
                        return RawOpcUaReadResult(
                            ok=False,
                            data_values=(),
                            response_timestamp=latest_result.response_timestamp,
                            error_reason="protocol_error",
                            exception=f"value_index_out_of_range:{parsed_value.value_index}",
                        )
                    if latest_values[parsed_value.value_index] is not None:
                        return RawOpcUaReadResult(
                            ok=False,
                            data_values=(),
                            response_timestamp=latest_result.response_timestamp,
                            error_reason="protocol_error",
                            exception=f"duplicate_value_index:{parsed_value.value_index}",
                        )
                    latest_values[parsed_value.value_index] = RawDataValue(
                        value=parsed_value.value_text,
                        source_timestamp=parsed_value.source_timestamp,
                        server_timestamp=parsed_value.server_timestamp,
                        status_code=parsed_value.status_code,
                    )
                    continue
                if line.startswith(_RUNNER_SUMMARY_PREFIX):
                    summary_seen = True
                    continue
                if line.startswith(_POLL_DONE_RESPONSE_PREFIX):
                    break

        if latest_result is None:
            return RawOpcUaReadResult(
                ok=False,
                data_values=(),
                response_timestamp=None,
                error_reason="read_failed",
                exception="no_result",
            )

        if latest_result.value_count != len(open62541_plan.node_paths):
            return RawOpcUaReadResult(
                ok=False,
                data_values=(),
                response_timestamp=latest_result.response_timestamp,
                error_reason="batch_mismatch",
                exception=(
                    f"result value_count {latest_result.value_count} does not match "
                    f"plan node count {len(open62541_plan.node_paths)}"
                ),
            )
        if latest_result.error_reason is None and any(value is None for value in latest_values):
            return RawOpcUaReadResult(
                ok=False,
                data_values=(),
                response_timestamp=latest_result.response_timestamp,
                error_reason="protocol_error",
                exception=(
                    f"expected {latest_result.value_count} VALUE lines, "
                    f"got {sum(1 for value in latest_values if value is not None)}"
                ),
            )

        return RawOpcUaReadResult(
            ok=latest_result.error_reason is None,
            data_values=(
                tuple(value for value in latest_values if value is not None)
                if latest_result.error_reason is None
                else ()
            ),
            response_timestamp=latest_result.response_timestamp,
            error_reason=latest_result.error_reason,
            exception=None if summary_seen else "missing_summary",
        )

    async def write(
        self,
        node_id: str,
        value_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        """Write one value to an OPC UA node via the runner subprocess.

        The runner connects to the endpoint configured in the connection profile,
        writes the value, and disconnects.  A fresh runner process is started if
        the backend is not currently connected.
        """
        if not self._connected or self._runner is None:
            await self.connect()

        async with self._io_lock:
            self._ensure_connected()
            runner = self._runner
            assert runner is not None
            if runner.stdin is None or runner.stdout is None:
                raise RuntimeError("open62541 client runner pipes are unavailable")

            endpoint = self._connection.endpoint
            namespace_uri = self._connection.namespace_uri or "-"
            safe_request_id = request_id or "cli"
            runner.stdin.write(
                (
                    f"WRITE\t{safe_request_id}\t{endpoint}\t{namespace_uri}\t"
                    f"{node_id}\t{value_type}\t{value}\n"
                ).encode("utf-8")
            )
            await runner.stdin.drain()

            timeout_s = max(self._connection.timeout_seconds * 2.0, 5.0)
            line = await self._read_protocol_line(
                expected_prefixes=(_WRITE_RESULT_RESPONSE_PREFIX, "ERROR"),
                timeout_seconds=timeout_s,
            )

            if line.startswith("ERROR"):
                return RawWriteItemResult(
                    node_id=node_id,
                    ok=False,
                    status_code="runner_error",
                    error_message=line,
                    value_type=value_type,
                )

            return self._parse_write_result_line(line, node_id, value_type)

    async def write_batch(
        self,
        items: Sequence[tuple[str, str, str]],
        *,
        request_id: str = "",
    ) -> list[RawWriteItemResult]:
        """Write multiple values sequentially, returning per-item results."""
        results: list[RawWriteItemResult] = []
        for idx, (node_id, value_type, value) in enumerate(items):
            item_rid = f"{request_id}_{idx}" if request_id else f"batch_{idx}"
            result = await self.write(node_id, value_type, value, request_id=item_rid)
            results.append(result)
        return results

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

    def _parse_result_line(self, line: str) -> _ParsedReadResult:
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
        return _ParsedReadResult(
            value_count=value_count,
            response_timestamp=response_timestamp,
            error_reason=error_code,
        )

    def _parse_value_line(self, line: str) -> _ParsedValueLine:
        fields = line.split("\t")
        if len(fields) != 9 or fields[0] != _VALUE_RESPONSE_PREFIX:
            raise RuntimeError(f"Unexpected runner VALUE response: {line!r}")

        return _ParsedValueLine(
            value_index=int(fields[4]),
            status_code=None if fields[5] in {"", "-"} else fields[5],
            value_text="" if fields[6] == "-" else fields[6],
            source_timestamp=_datetime_from_runner_timestamp(fields[7]),
            server_timestamp=_datetime_from_runner_timestamp(fields[8]),
        )

    def _parse_write_result_line(
        self,
        line: str,
        expected_node_id: str,
        expected_value_type: str,
    ) -> RawWriteItemResult:
        """Parse a WRITE_RESULT line from the runner.

        Expected format::
            WRITE_RESULT\\t<request_id>\\t<node_id>\\tok=<0|1>\\t<status>\\t<value_type=<type>>
        """
        fields = line.split("\t")
        if len(fields) < 4 or fields[0] != _WRITE_RESULT_RESPONSE_PREFIX:
            return RawWriteItemResult(
                node_id=expected_node_id,
                ok=False,
                status_code="protocol_error",
                error_message=f"Unexpected WRITE_RESULT format: {line!r}",
                value_type=expected_value_type,
            )

        node_id = fields[2] if len(fields) > 2 else expected_node_id
        ok_field = fields[3] if len(fields) > 3 else "ok=0"
        ok = ok_field == "ok=1"
        status = fields[4] if len(fields) > 4 else None
        value_type = expected_value_type
        if len(fields) > 5 and fields[5].startswith("value_type="):
            value_type = fields[5].split("=", 1)[1]

        return RawWriteItemResult(
            node_id=node_id,
            ok=ok,
            status_code="OK" if ok else status,
            error_message=None if ok else (status or "write_failed"),
            value_type=value_type,
        )
