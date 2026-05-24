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


# ── WRITE 指令解析测试 ──────────────────────────────────────────────────


def test_write_sends_correct_stdin_command() -> None:
    """write 应按协议格式发送 WRITE 命令到 stdin。"""
    async def _run() -> None:
        backend, temp_dir = _backend(
            [
                "WRITE_RESULT\tcli\ts=test.value\tok=1\tOK\tvalue_type=double",
            ]
        )
        try:
            result = await backend.write(
                node_id="s=test.value",
                value_type="double",
                value="42.0",
                request_id="cli",
            )
            stdin = cast(_FakeStdin, cast(_FakeRunner, backend._runner).stdin)
            assert len(stdin.writes) > 0
            write_cmd = stdin.writes[0].decode("utf-8")
            assert "WRITE\tcli" in write_cmd
            assert "s=test.value" in write_cmd
            assert "double" in write_cmd
            assert "42.0" in write_cmd
            assert result.ok is True
            assert result.node_id == "s=test.value"
            assert result.status_code == "OK"
        finally:
            temp_dir.cleanup()
    asyncio.run(_run())


def test_write_parses_success_result() -> None:
    """成功 WRITE_RESULT 应解析为 RawWriteItemResult(ok=True)。"""
    async def _run() -> None:
        backend, temp_dir = _backend(
            [
                "WRITE_RESULT\treq-001\ts=test.bool\tok=1\tOK\tvalue_type=bool",
            ]
        )
        try:
            result = await backend.write(
                node_id="s=test.bool",
                value_type="bool",
                value="true",
                request_id="req-001",
            )
            assert result.ok is True
            assert result.node_id == "s=test.bool"
            assert result.status_code == "OK"
            assert result.error_message is None
            assert result.value_type == "bool"
        finally:
            temp_dir.cleanup()
    asyncio.run(_run())


def test_write_parses_failure_result() -> None:
    """失败 WRITE_RESULT 应解析为 RawWriteItemResult(ok=False)。"""
    async def _run() -> None:
        backend, temp_dir = _backend(
            [
                "WRITE_RESULT\treq-002\ts=test.fail\tok=0\tBadInvalidArgument\tvalue_type=double",
            ]
        )
        try:
            result = await backend.write(
                node_id="s=test.fail",
                value_type="double",
                value="bad",
                request_id="req-002",
            )
            assert result.ok is False
            assert result.status_code == "BadInvalidArgument"
            assert result.error_message is not None
        finally:
            temp_dir.cleanup()
    asyncio.run(_run())


def test_write_handles_error_line() -> None:
    """runner 返回 ERROR 行应转化为失败结果。"""
    async def _run() -> None:
        backend, temp_dir = _backend(
            [
                "ERROR\twrite\tconnection_failed",
            ]
        )
        try:
            result = await backend.write(
                node_id="s=test.error",
                value_type="int32",
                value="1",
            )
            assert result.ok is False
            assert result.status_code == "runner_error"
            assert "connection_failed" in (result.error_message or "")
        finally:
            temp_dir.cleanup()
    asyncio.run(_run())


def test_write_batch_sequential() -> None:
    """write_batch 应依次写入每个 item。"""
    async def _run() -> None:
        backend, temp_dir = _backend(
            [
                "WRITE_RESULT\tbatch_0\ts=item1\tok=1\tOK\tvalue_type=double",
                "WRITE_RESULT\tbatch_1\ts=item2\tok=1\tOK\tvalue_type=bool",
                "WRITE_RESULT\tbatch_2\ts=item3\tok=0\tBadNodeId\tvalue_type=int32",
            ]
        )
        try:
            items = [
                ("s=item1", "double", "1.0"),
                ("s=item2", "bool", "false"),
                ("s=item3", "int32", "not_a_number"),
            ]
            results = await backend.write_batch(items, request_id="batch")
            assert len(results) == 3
            assert results[0].ok is True
            assert results[1].ok is True
            assert results[2].ok is False
            assert results[2].status_code == "BadNodeId"
        finally:
            temp_dir.cleanup()
    asyncio.run(_run())


def test_parse_write_result_line_ok() -> None:
    """_parse_write_result_line 应正确解析成功的响应行。"""
    backend, temp_dir = _backend([])
    try:
        result = backend._parse_write_result_line(
            "WRITE_RESULT\treq-1\ts=test.value\tok=1\tOK\tvalue_type=double",
            expected_node_id="s=test.value",
            expected_value_type="double",
        )
        assert result.ok is True
        assert result.node_id == "s=test.value"
        assert result.status_code == "OK"
        assert result.error_message is None
        assert result.value_type == "double"
    finally:
        temp_dir.cleanup()


def test_parse_write_result_line_fail() -> None:
    """_parse_write_result_line 应正确解析失败的响应行。"""
    backend, temp_dir = _backend([])
    try:
        result = backend._parse_write_result_line(
            "WRITE_RESULT\treq-1\ts=test.value\tok=0\tBadTypeMismatch\tvalue_type=bool",
            expected_node_id="s=test.value",
            expected_value_type="bool",
        )
        assert result.ok is False
        assert result.node_id == "s=test.value"
        assert result.status_code == "BadTypeMismatch"
        assert result.error_message is not None
        assert result.value_type == "bool"
    finally:
        temp_dir.cleanup()


def test_parse_write_result_line_malformed() -> None:
    """格式异常的 WRITE_RESULT 应标记为协议错误。"""
    backend, temp_dir = _backend([])
    try:
        result = backend._parse_write_result_line(
            "garbage_line",
            expected_node_id="s=test.value",
            expected_value_type="double",
        )
        assert result.ok is False
        assert result.status_code == "protocol_error"
    finally:
        temp_dir.cleanup()
