"""open62541 backend 单元测试。

这些测试直接覆盖 native runner VALUE 协议到 RawOpcUaReadResult 的解析。
"""

from __future__ import annotations

import asyncio
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from whale.shared.source.models import SourceConnectionProfile
from whale.shared.source.opcua.backends import RawDataValue, RawOpcUaReadResult
from whale.shared.source.opcua.backends.open62541_backend import (
    Open62541OpcUaClientBackend,
)


@dataclass
class _FakeStdout:
    """异步协议 stdout 假实现。"""

    lines: list[bytes]

    async def readline(self) -> bytes:
        if not self.lines:
            return b""
        return self.lines.pop(0)


@dataclass
class _FakeStdin:
    """异步协议 stdin 假实现。"""

    writes: list[bytes]

    def write(self, data: bytes) -> None:
        self.writes.append(data)

    async def drain(self) -> None:
        return None


@dataclass
class _FakeRunner:
    """满足 backend 读取所需字段的假 runner。"""

    stdout: _FakeStdout
    stdin: _FakeStdin
    returncode: int | None = None


def _backend(protocol_lines: list[str]) -> tuple[Open62541OpcUaClientBackend, tempfile.TemporaryDirectory[str]]:
    backend = Open62541OpcUaClientBackend(
        SourceConnectionProfile(
            endpoint="opc.tcp://127.0.0.1:4840",
            namespace_uri="urn:test",
            timeout_seconds=1.5,
        )
    )
    temp_dir = tempfile.TemporaryDirectory()
    backend._connected = True  # type: ignore[attr-defined]
    backend._temp_dir = temp_dir  # type: ignore[attr-defined]
    backend._runner = cast(
        asyncio.subprocess.Process,
        _FakeRunner(
            stdout=_FakeStdout([f"{line}\n".encode("utf-8") for line in protocol_lines]),
            stdin=_FakeStdin([]),
        ),
    )
    return backend, temp_dir


def test_read_prepared_raw_parses_real_values_from_value_lines() -> None:
    async def _run() -> RawOpcUaReadResult:
        backend, temp_dir = _backend(
            [
                "RESULT\t0\t0\t0\t0\t100\t101\t102\tOK\t1.25\t2.50\t2\t1712345678.250000",
                "VALUE\t0\t0\t0\t0\tGOOD\t123.4\t1712345678.000000\t1712345678.250000",
                "VALUE\t0\t0\t0\t1\tGOOD\ttrue\t-1.000000\t1712345678.250000",
                "RUNNER_SUMMARY\t0\t1\t1\t1\t0\t0\t0\t0\t1.250\t2.500\t0\t0\t0.000\t0.000",
                "POLL_DONE\t0",
            ]
        )
        try:
            plan = backend.prepare_read(["s=Node1", "s=Node2"])
            return await backend.read_prepared_raw(plan)
        finally:
            temp_dir.cleanup()

    raw = asyncio.run(_run())
    values = cast(tuple[RawDataValue, ...], tuple(raw.data_values))

    assert raw.ok is True
    assert len(values) == 2
    assert values[0].value == "123.4"
    assert values[0].status_code == "GOOD"
    assert values[0].source_timestamp == datetime.fromtimestamp(1712345678.0, tz=UTC)
    assert values[1].value == "true"
    assert values[1].server_timestamp == datetime.fromtimestamp(1712345678.25, tz=UTC)


def test_read_prepared_raw_reorders_value_lines_by_value_index() -> None:
    async def _run() -> RawOpcUaReadResult:
        backend, temp_dir = _backend(
            [
                "RESULT\t0\t0\t0\t0\t100\t101\t102\tOK\t1.25\t2.50\t2\t1712345678.250000",
                "VALUE\t0\t0\t0\t1\tGOOD\tsecond\t-1.000000\t1712345678.250000",
                "VALUE\t0\t0\t0\t0\tGOOD\tfirst\t1712345678.000000\t1712345678.250000",
                "RUNNER_SUMMARY\t0\t1\t1\t1\t0\t0\t0\t0\t1.250\t2.500\t0\t0\t0.000\t0.000",
                "POLL_DONE\t0",
            ]
        )
        try:
            plan = backend.prepare_read(["s=Node1", "s=Node2"])
            return await backend.read_prepared_raw(plan)
        finally:
            temp_dir.cleanup()

    raw = asyncio.run(_run())
    values = cast(tuple[RawDataValue, ...], tuple(raw.data_values))

    assert raw.ok is True
    assert [value.value for value in values] == ["first", "second"]


def test_read_prepared_raw_fails_when_result_value_count_does_not_match_plan() -> None:
    async def _run() -> RawOpcUaReadResult:
        backend, temp_dir = _backend(
            [
                "RESULT\t0\t0\t0\t0\t100\t101\t102\tOK\t1.25\t2.50\t1\t1712345678.250000",
                "VALUE\t0\t0\t0\t0\tGOOD\t123.4\t1712345678.000000\t1712345678.250000",
                "RUNNER_SUMMARY\t0\t1\t1\t1\t0\t0\t0\t0\t1.250\t2.500\t0\t0\t0.000\t0.000",
                "POLL_DONE\t0",
            ]
        )
        try:
            plan = backend.prepare_read(["s=Node1", "s=Node2"])
            return await backend.read_prepared_raw(plan)
        finally:
            temp_dir.cleanup()

    raw = asyncio.run(_run())

    assert raw.ok is False
    assert raw.error_reason == "batch_mismatch"


def test_read_prepared_raw_fails_when_value_lines_are_missing() -> None:
    async def _run() -> RawOpcUaReadResult:
        backend, temp_dir = _backend(
            [
                "RESULT\t0\t0\t0\t0\t100\t101\t102\tOK\t1.25\t2.50\t2\t1712345678.250000",
                "VALUE\t0\t0\t0\t0\tGOOD\t123.4\t1712345678.000000\t1712345678.250000",
                "RUNNER_SUMMARY\t0\t1\t1\t1\t0\t0\t0\t0\t1.250\t2.500\t0\t0\t0.000\t0.000",
                "POLL_DONE\t0",
            ]
        )
        try:
            plan = backend.prepare_read(["s=Node1", "s=Node2"])
            return await backend.read_prepared_raw(plan)
        finally:
            temp_dir.cleanup()

    raw = asyncio.run(_run())

    assert raw.ok is False
    assert raw.error_reason == "protocol_error"


def test_read_prepared_raw_fails_when_value_index_is_duplicated() -> None:
    async def _run() -> RawOpcUaReadResult:
        backend, temp_dir = _backend(
            [
                "RESULT\t0\t0\t0\t0\t100\t101\t102\tOK\t1.25\t2.50\t2\t1712345678.250000",
                "VALUE\t0\t0\t0\t0\tGOOD\tfirst\t1712345678.000000\t1712345678.250000",
                "VALUE\t0\t0\t0\t0\tGOOD\tsecond\t1712345678.000000\t1712345678.250000",
                "RUNNER_SUMMARY\t0\t1\t1\t1\t0\t0\t0\t0\t1.250\t2.500\t0\t0\t0.000\t0.000",
                "POLL_DONE\t0",
            ]
        )
        try:
            plan = backend.prepare_read(["s=Node1", "s=Node2"])
            return await backend.read_prepared_raw(plan)
        finally:
            temp_dir.cleanup()

    raw = asyncio.run(_run())

    assert raw.ok is False
    assert raw.error_reason == "protocol_error"
    assert raw.exception == "duplicate_value_index:0"


def test_read_prepared_raw_fails_when_value_index_is_out_of_range() -> None:
    async def _run() -> RawOpcUaReadResult:
        backend, temp_dir = _backend(
            [
                "RESULT\t0\t0\t0\t0\t100\t101\t102\tOK\t1.25\t2.50\t2\t1712345678.250000",
                "VALUE\t0\t0\t0\t2\tGOOD\tthird\t1712345678.000000\t1712345678.250000",
                "RUNNER_SUMMARY\t0\t1\t1\t1\t0\t0\t0\t0\t1.250\t2.500\t0\t0\t0.000\t0.000",
                "POLL_DONE\t0",
            ]
        )
        try:
            plan = backend.prepare_read(["s=Node1", "s=Node2"])
            return await backend.read_prepared_raw(plan)
        finally:
            temp_dir.cleanup()

    raw = asyncio.run(_run())

    assert raw.ok is False
    assert raw.error_reason == "protocol_error"
    assert raw.exception == "value_index_out_of_range:2"
