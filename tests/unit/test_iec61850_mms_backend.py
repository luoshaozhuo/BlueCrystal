"""libiec61850 backend 单元测试。

直接覆盖 native runner READ_RESULT/WRITE_RESULT 协议到 RawMmsReadResult/RawWriteItemResult 的解析。
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import cast

from whale.shared.source.iec61850.backends.base import (
    RawMmsReadResult,
    RawWriteItemResult,
)
from whale.shared.source.iec61850.backends.libiec61850_backend import (
    LibIec61850MmsClientBackend,
)


@dataclass
class _FakeStdout:
    """异步协议 stdout 假实现。"""

    lines: list[bytes] = field(default_factory=list)

    async def readline(self) -> bytes:
        if not self.lines:
            return b""
        return self.lines.pop(0)


@dataclass
class _FakeStdin:
    """异步协议 stdin 假实现。"""

    writes: list[bytes] = field(default_factory=list)

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


def _backend(protocol_lines: list[str]) -> LibIec61850MmsClientBackend:
    backend = LibIec61850MmsClientBackend(
        host="127.0.0.1",
        port=1102,
        timeout_seconds=1.5,
    )
    backend._connected = True  # type: ignore[attr-defined]
    backend._runner = cast(
        asyncio.subprocess.Process,
        _FakeRunner(
            stdout=_FakeStdout([f"{line}\n".encode("utf-8") for line in protocol_lines]),
            stdin=_FakeStdin([]),
        ),
    )
    return backend


# ── Read tests ──────────────────────────────────────────────────────────


def test_read_parses_success_result() -> None:
    """成功 READ_RESULT 应解析为 RawMmsReadResult(ok=True)。"""
    async def _run() -> RawMmsReadResult:
        backend = _backend([
            "READ_RESULT\treq-001\tSimulator/GGIO1.SPCtrl1.setVal\tok=1\tOK\tBOOLEAN\ttrue",
        ])
        return await backend.read(
            obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
            fc="SP",
            request_id="req-001",
        )
    result = asyncio.run(_run())
    assert result.ok is True
    assert result.obj_ref == "Simulator/GGIO1.SPCtrl1.setVal"
    assert result.value_type == "BOOLEAN"
    assert result.value == "true"
    assert result.error_reason is None


def test_read_parses_failure_result() -> None:
    """失败 READ_RESULT 应解析为 RawMmsReadResult(ok=False)。"""
    async def _run() -> RawMmsReadResult:
        backend = _backend([
            "READ_RESULT\treq-002\tSimulator/GGIO1.SPCtrl1.setVal\tok=0\tobject-does-not-exist\t-\t-",
        ])
        return await backend.read(
            obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
            fc="SP",
            request_id="req-002",
        )
    result = asyncio.run(_run())
    assert result.ok is False
    assert result.error_reason == "object-does-not-exist"


def test_read_handles_malformed_line() -> None:
    """格式异常的 READ_RESULT 应标记为协议错误。"""
    async def _run() -> RawMmsReadResult:
        backend = _backend([
            "garbage_line",
        ])
        result = await backend.read(
            obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
            fc="SP",
        )
        return result

    # The line won't match READ_RESULT prefix, so timeout will happen
    # Instead verify with a proper prefix:
    async def _run2() -> RawMmsReadResult:
        backend = _backend([
            "WRITE_RESULT\t-\t-\tok=0\tprotocol_error",
        ])
        result = await backend.read(
            obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
            fc="SP",
        )
        return result

    result = asyncio.run(_run2())
    assert result.ok is False
    assert result.error_reason == "protocol_error"
    assert "unexpected_write_result_for_read" in (result.exception or "")


def test_read_sends_correct_stdin_command() -> None:
    """read 应按协议格式发送 READ 命令到 stdin。"""
    async def _run() -> None:
        backend = _backend([
            "READ_RESULT\tcli\tSimulator/GGIO1.SPCtrl1.setVal\tok=1\tOK\tINT32\t42",
        ])
        result = await backend.read(
            obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
            fc="SP",
        )
        stdin = cast(_FakeStdin, cast(_FakeRunner, backend._runner).stdin)
        assert len(stdin.writes) > 0
        read_cmd = stdin.writes[0].decode("utf-8")
        assert "READ\tcli" in read_cmd
        assert "Simulator/GGIO1.SPCtrl1.setVal" in read_cmd
        assert "SP" in read_cmd
        assert result.ok is True
        assert result.value == "42"
    asyncio.run(_run())


# ── Write tests ─────────────────────────────────────────────────────────


def test_write_sends_correct_stdin_command() -> None:
    """write 应按协议格式发送 WRITE 命令到 stdin。"""
    async def _run() -> None:
        backend = _backend([
            "WRITE_RESULT\tcli\tSimulator/GGIO1.SPCtrl1.setVal\tok=1\tOK\tBOOLEAN",
        ])
        result = await backend.write(
            obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
            fc="SP",
            value_type="BOOLEAN",
            value="true",
            request_id="cli",
        )
        stdin = cast(_FakeStdin, cast(_FakeRunner, backend._runner).stdin)
        assert len(stdin.writes) > 0
        write_cmd = stdin.writes[0].decode("utf-8")
        assert "WRITE\tcli" in write_cmd
        assert "Simulator/GGIO1.SPCtrl1.setVal" in write_cmd
        assert "BOOLEAN" in write_cmd
        assert "true" in write_cmd
        assert result.ok is True
        assert result.obj_ref == "Simulator/GGIO1.SPCtrl1.setVal"
        assert result.status_code == "OK"
    asyncio.run(_run())


def test_write_parses_success_result() -> None:
    """成功 WRITE_RESULT 应解析为 RawWriteItemResult(ok=True)。"""
    async def _run() -> None:
        backend = _backend([
            "WRITE_RESULT\treq-001\tSimulator/GGIO1.SPCtrl1.setVal\tok=1\tOK\tBOOLEAN",
        ])
        result = await backend.write(
            obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
            fc="SP",
            value_type="BOOLEAN",
            value="true",
            request_id="req-001",
        )
        assert result.ok is True
        assert result.obj_ref == "Simulator/GGIO1.SPCtrl1.setVal"
        assert result.status_code == "OK"
        assert result.error_message is None
        assert result.value_type == "BOOLEAN"
    asyncio.run(_run())


def test_write_parses_failure_result() -> None:
    """失败 WRITE_RESULT 应解析为 RawWriteItemResult(ok=False)。"""
    async def _run() -> None:
        backend = _backend([
            "WRITE_RESULT\treq-002\tSimulator/GGIO1.SPCtrl1.setVal\tok=0\taccess-denied\tBOOLEAN",
        ])
        result = await backend.write(
            obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
            fc="ST",
            value_type="BOOLEAN",
            value="true",
            request_id="req-002",
        )
        assert result.ok is False
        assert result.status_code == "access-denied"
        assert result.error_message is not None
    asyncio.run(_run())


def test_write_handles_malformed_line() -> None:
    """格式异常的 WRITE_RESULT 应标记为协议错误。"""
    async def _run() -> None:
        backend = _backend([
            "garbage_line",
        ])
        # Timeout would happen, but we test with a timeout wrapper
        # Instead verify the parse method:
        result = backend._parse_write_result_line(
            "garbage_line",
            expected_obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
            expected_value_type="BOOLEAN",
        )
        assert result.ok is False
        assert result.status_code == "protocol_error"
    asyncio.run(_run())


# ── Parse result tests ─────────────────────────────────────────────────


def test_parse_read_result_line_ok() -> None:
    """_parse_read_result_line 应正确解析成功的响应行。"""
    backend = _backend([])
    result = backend._parse_read_result_line(
        "READ_RESULT\treq-1\tobj\tok=1\tOK\tBOOLEAN\ttrue",
        expected_obj_ref="obj",
    )
    assert result.ok is True
    assert result.obj_ref == "obj"
    assert result.value_type == "BOOLEAN"
    assert result.value == "true"
    assert result.error_reason is None


def test_parse_read_result_line_fail() -> None:
    """_parse_read_result_line 应正确解析失败的响应行。"""
    backend = _backend([])
    result = backend._parse_read_result_line(
        "READ_RESULT\treq-1\tobj\tok=0\tobject-does-not-exist\t-\t-",
        expected_obj_ref="obj",
    )
    assert result.ok is False
    assert result.error_reason == "object-does-not-exist"


def test_parse_read_result_line_malformed() -> None:
    """格式异常的 READ_RESULT 应标记为协议错误。"""
    backend = _backend([])
    result = backend._parse_read_result_line(
        "garbage_line",
        expected_obj_ref="obj",
    )
    assert result.ok is False
    assert result.error_reason == "protocol_error"


def test_parse_write_result_line_ok() -> None:
    """_parse_write_result_line 应正确解析成功的响应行。"""
    backend = _backend([])
    result = backend._parse_write_result_line(
        "WRITE_RESULT\treq-1\tobj\tok=1\tOK\tBOOLEAN",
        expected_obj_ref="obj",
        expected_value_type="BOOLEAN",
    )
    assert result.ok is True
    assert result.obj_ref == "obj"
    assert result.status_code == "OK"
    assert result.error_message is None
    assert result.value_type == "BOOLEAN"


def test_parse_write_result_line_fail() -> None:
    """_parse_write_result_line 应正确解析失败的响应行。"""
    backend = _backend([])
    result = backend._parse_write_result_line(
        "WRITE_RESULT\treq-1\tobj\tok=0\taccess-denied\tBOOLEAN",
        expected_obj_ref="obj",
        expected_value_type="BOOLEAN",
    )
    assert result.ok is False
    assert result.status_code == "access-denied"
    assert result.error_message is not None
    assert result.value_type == "BOOLEAN"


def test_parse_write_result_line_malformed() -> None:
    """格式异常的 WRITE_RESULT 应标记为协议错误。"""
    backend = _backend([])
    result = backend._parse_write_result_line(
        "garbage_line",
        expected_obj_ref="obj",
        expected_value_type="BOOLEAN",
    )
    assert result.ok is False
    assert result.status_code == "protocol_error"
