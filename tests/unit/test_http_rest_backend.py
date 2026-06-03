"""HTTP REST client backend 单元测试。

被验证对象：``whale.shared.source.http_rest.client.HttpRestClientBackend``。
证据等级：L1 unit/mock — 使用 asyncio mock stream 模拟 HTTP 服务器通信。
不能证明：真实 HTTP 服务器连接、TLS/HTTPS 握手、大规模并发。
"""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from whale.shared.source.http_rest.client import HttpRestClientBackend, HttpResponseData, HttpReadResult


def _http_response(status: int, body: str, content_type: str = "application/json") -> bytes:
    lines = [
        f"HTTP/1.1 {status} OK",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body.encode('utf-8'))}",
        "Connection: close",
        "",
        body,
    ]
    return "\r\n".join(lines).encode("utf-8")


class _ByteBufferReader:
    """模拟 asyncio.StreamReader，从字节缓冲区按需读取。"""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._offset = 0

    async def readexactly(self, n: int) -> bytes:
        remaining = len(self._data) - self._offset
        if remaining < n:
            import asyncio as _asyncio
            raise _asyncio.IncompleteReadError(
                partial=self._data[self._offset:], expected=n
            )
        chunk = self._data[self._offset:self._offset + n]
        self._offset += n
        return chunk

    async def read(self, n: int = -1) -> bytes:
        if n < 0 or self._offset + n > len(self._data):
            chunk = self._data[self._offset:]
            self._offset = len(self._data)
        else:
            chunk = self._data[self._offset:self._offset + n]
            self._offset += n
        return chunk

    async def readline(self) -> bytes:
        remaining = self._data[self._offset:]
        for i, b in enumerate(remaining):
            if b == 0x0A:
                line = self._data[self._offset:self._offset + i + 1]
                self._offset += i + 1
                return line
        line = remaining
        self._offset = len(self._data)
        return line


class _FakeStreamWriter:
    """模拟 asyncio.StreamWriter。"""

    def __init__(self) -> None:
        self.written: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.written.append(data)

    async def drain(self) -> None:
        pass

    def close(self) -> None:
        pass

    async def wait_closed(self) -> None:
        pass


def _fake_open_connection_factory(reader_data: bytes):  # type: ignore[no-untyped-def]
    async def _factory(host, port):
        reader = _ByteBufferReader(reader_data)
        writer = _FakeStreamWriter()
        return reader, writer
    return _factory


@pytest.mark.asyncio
async def test_http_get_returns_ok_for_200() -> None:
    """HTTP GET 返回 200 时应标记 ok=True。"""
    body = json.dumps({"temperature": 25.5})
    data = _http_response(200, body)
    fake_open = _fake_open_connection_factory(data)

    with patch("asyncio.open_connection", fake_open):
        client = HttpRestClientBackend(base_url="http://localhost:8080")
        resp = await client.get(path="/api/temp")

        assert resp.ok
        assert resp.status_code == 200
        assert resp.json_body == {"temperature": 25.5}
        assert resp.error_reason is None


@pytest.mark.asyncio
async def test_http_get_returns_not_ok_for_500() -> None:
    """HTTP GET 返回 500 时应标记 ok=False。"""
    body = "Internal Server Error"
    data = _http_response(500, body, content_type="text/plain")
    fake_open = _fake_open_connection_factory(data)

    with patch("asyncio.open_connection", fake_open):
        client = HttpRestClientBackend(base_url="http://localhost:8080")
        resp = await client.get(path="/api/error")

        assert not resp.ok
        assert resp.status_code == 500
        assert "500" in (resp.error_reason or "")


@pytest.mark.asyncio
async def test_http_read_wraps_result() -> None:
    """read() 应将响应包装为 HttpReadResult。"""
    body = json.dumps({"value": 42})
    data = _http_response(200, body)
    fake_open = _fake_open_connection_factory(data)

    with patch("asyncio.open_connection", fake_open):
        client = HttpRestClientBackend(base_url="http://localhost:8080")
        result = await client.read(path="/api/value")

        assert result.ok
        assert result.response is not None
        assert result.response.json_body == {"value": 42}


@pytest.mark.asyncio
async def test_http_read_with_query_params() -> None:
    """HTTP GET 应正确拼接查询参数。"""
    body = json.dumps({"result": "ok"})
    data = _http_response(200, body)
    fake_open = _fake_open_connection_factory(data)

    with patch("asyncio.open_connection", fake_open):
        client = HttpRestClientBackend(base_url="http://localhost:8080/api")
        resp = await client.get(path="/data", query_params={"id": "123"})

        assert resp.ok


def test_http_response_data_dataclass() -> None:
    """HttpResponseData 字段应正确设置。"""
    resp = HttpResponseData(ok=True, status_code=200, body="test")
    assert resp.ok
    assert resp.status_code == 200
    assert resp.body == "test"


def test_http_read_result_dataclass() -> None:
    """HttpReadResult 字段应正确设置。"""
    result = HttpReadResult(ok=False, error_reason="timeout")
    assert not result.ok
    assert result.error_reason == "timeout"
    assert result.response is None


@pytest.mark.asyncio
async def test_http_connect_failure_returns_not_ok() -> None:
    """HTTP 连接失败时应返回 not ok 结果，不抛异常。"""
    async def _fake_open(host, port):
        raise ConnectionRefusedError("simulated connection failure")

    with patch("asyncio.open_connection", _fake_open):
        client = HttpRestClientBackend(base_url="http://localhost:9999")
        resp = await client.get(path="/api/status")

        assert not resp.ok
        assert resp.status_code == 0
        assert resp.error_reason is not None
        assert "connect" in resp.error_reason.lower()
