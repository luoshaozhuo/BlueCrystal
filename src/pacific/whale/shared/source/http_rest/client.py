"""HTTP REST 生产级 shared source backend。

提供基于 asyncio 标准库的 HTTP/HTTPS 客户端实现。
支持 GET 请求、响应解析、JSON 路径提取和超时控制。

职责边界：
- 实现 HTTP 客户端请求和响应解析；
- 不负责业务数据映射或采集策略编排——这些由 ingest adapter 处理；
- 不负责缓存、重试、授权——由上层 decorator 链处理；
- 当前为 python_lightweight_runner 级别实现。

资源生命周期：
- 每次 read 操作创建临时 HTTP 连接（不保持长连接）；
- 超时通过 asyncio.wait_for 保证；
- 连接在请求完成后释放。

Write 状态：
- HTTP POST/PUT/PATCH/DELETE（写入）当前为 NOT_IMPLEMENTED；
- 仅支持 GET 读取。
"""
from __future__ import annotations

import asyncio
import json as _json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode, urlparse


@dataclass(frozen=True, slots=True)
class HttpResponseData:
    """HTTP 响应数据。

    Attributes:
        ok: 响应是否成功（状态码 2xx）。
        status_code: HTTP 状态码。
        body: 响应体（字符串格式）。
        json_body: 若响应为 JSON，则包含解析后的 dict/list；否则为 None。
        headers: 响应头（dict 格式）。
        error_reason: 失败原因（仅 ok=False 时有效）。
        response_at: 响应接收时间戳（UTC）。
    """

    ok: bool
    status_code: int
    body: str = ""
    json_body: dict[str, Any] | list[Any] | None = None
    headers: dict[str, str] = field(default_factory=dict)
    error_reason: str | None = None
    response_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass(frozen=True, slots=True)
class HttpReadResult:
    """HTTP 读取结果。

    Attributes:
        ok: 读取是否成功。
        response: 成功时的 HttpResponseData。
        error_reason: 失败原因（仅 ok=False 时有效）。
    """

    ok: bool
    response: HttpResponseData | None = None
    error_reason: str | None = None


class HttpRestClientBackend:
    """基于 asyncio stream 的轻量级 HTTP 客户端。

    支持 GET 请求、响应体解析和 JSON 处理。
    当前为 python_lightweight_runner 级别实现，不使用外部 HTTP 库。

    Args:
        base_url: 基础 URL（如 "http://localhost:8080/api"）。
        timeout_seconds: 请求超时时间（秒），默认 15。
        default_headers: 默认请求头（dict）。
    """

    def __init__(
        self,
        base_url: str = "",
        timeout_seconds: float = 15.0,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        parsed = urlparse(base_url)
        self._host = parsed.hostname or "localhost"
        self._port = parsed.port or (443 if parsed.scheme == "https" else 80)
        self._base_path = parsed.path or "/"
        self._timeout_seconds = timeout_seconds
        self._default_headers = default_headers or {}

    async def get(
        self,
        path: str = "/",
        query_params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> HttpResponseData:
        """发送 HTTP GET 请求并返回解析后的响应。

        Args:
            path: 请求路径（相对于 base_url 的路径部分）。
            query_params: 可选的查询参数。
            headers: 可选的请求头，与 default_headers 合并。
            timeout_seconds: 本次请求超时，若为 None 则使用实例默认值。

        Returns:
            HttpResponseData 包含状态码、响应体和可能的 JSON 数据。

        Raises:
            ConnectionError: TCP 连接或 HTTP 通信失败。
            asyncio.TimeoutError: 请求超时。
        """
        timeout = timeout_seconds or self._timeout_seconds
        full_path = self._build_path(path, query_params)
        merged_headers = {**self._default_headers, **(headers or {})}

        request_line = f"GET {full_path} HTTP/1.1\r\n"
        header_lines = f"Host: {self._host}\r\n"
        for key, value in merged_headers.items():
            header_lines += f"{key}: {value}\r\n"
        header_lines += "Connection: close\r\n\r\n"

        raw_request = (request_line + header_lines).encode("utf-8")

        reader: asyncio.StreamReader
        writer: asyncio.StreamWriter
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=timeout,
            )
        except Exception as exc:
            return HttpResponseData(
                ok=False,
                status_code=0,
                error_reason=f"HTTP connect failed: {exc}",
            )

        try:
            writer.write(raw_request)
            await writer.drain()

            # Read status line
            status_line = await asyncio.wait_for(
                reader.readline(), timeout=timeout
            )
            status_parts = status_line.decode("utf-8", errors="replace").strip().split(" ", 2)
            status_code = int(status_parts[1]) if len(status_parts) >= 2 else 0

            # Read headers
            response_headers: dict[str, str] = {}
            while True:
                line = await asyncio.wait_for(
                    reader.readline(), timeout=timeout
                )
                decoded = line.decode("utf-8", errors="replace").strip()
                if not decoded:
                    break
                if ":" in decoded:
                    key, _, value = decoded.partition(":")
                    response_headers[key.strip().lower()] = value.strip()

            # Read body
            content_length = int(response_headers.get("content-length", 0))
            body_chunks: list[bytes] = []
            if content_length > 0:
                remaining = content_length
                while remaining > 0:
                    chunk = await asyncio.wait_for(
                        reader.read(min(remaining, 65536)),
                        timeout=timeout,
                    )
                    if not chunk:
                        break
                    body_chunks.append(chunk)
                    remaining -= len(chunk)
            else:
                # Read until EOF
                try:
                    while True:
                        chunk = await asyncio.wait_for(
                            reader.read(65536), timeout=timeout
                        )
                        if not chunk:
                            break
                        body_chunks.append(chunk)
                except asyncio.TimeoutError:
                    pass

            body = b"".join(body_chunks).decode("utf-8", errors="replace")
            json_body = None
            if "application/json" in response_headers.get("content-type", ""):
                try:
                    json_body = _json.loads(body)
                except (_json.JSONDecodeError, ValueError):
                    pass

            ok = 200 <= status_code < 300
            return HttpResponseData(
                ok=ok,
                status_code=status_code,
                body=body,
                json_body=json_body,
                headers=response_headers,
                error_reason=None if ok else f"HTTP {status_code}",
            )
        except asyncio.TimeoutError:
            return HttpResponseData(
                ok=False,
                status_code=0,
                error_reason="HTTP request timed out",
            )
        except Exception as exc:
            return HttpResponseData(
                ok=False,
                status_code=0,
                error_reason=f"HTTP error: {exc}",
            )
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    def _build_path(
        self, path: str, query_params: dict[str, str] | None
    ) -> str:
        """构建包含基础路径和查询参数的完整请求路径。

        Args:
            path: 请求路径。
            query_params: 查询参数字典。

        Returns:
            完整的请求路径（含 query string）。
        """
        if not path.startswith("/"):
            path = "/" + path
        if self._base_path.endswith("/") and path.startswith("/"):
            full = self._base_path + path[1:]
        else:
            full = self._base_path + path
        if query_params:
            qs = urlencode(query_params)
            full += "?" + qs
        return full

    async def read(
        self,
        path: str = "/",
        query_params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> HttpReadResult:
        """执行 HTTP GET 读取并返回结构化结果。

        Args:
            path: 请求路径。
            query_params: 查询参数。
            headers: 请求头。
            timeout_seconds: 超时。

        Returns:
            HttpReadResult 包装响应数据或错误原因。
        """
        response = await self.get(
            path=path,
            query_params=query_params,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )
        if response.ok:
            return HttpReadResult(ok=True, response=response)
        return HttpReadResult(
            ok=False,
            response=response,
            error_reason=response.error_reason,
        )

    async def __aenter__(self) -> HttpRestClientBackend:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        pass
