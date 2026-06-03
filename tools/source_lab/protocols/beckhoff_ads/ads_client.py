"""Beckhoff ADS 客户端封装，支持 read/write/readwrite/readback 操作。

本文件负责：
1. 提供统一的 AdsClientRunner 抽象——通过子进程调用 AdsLib native runner
   或 Python lightweight client 实现 ADS 协议读写；
2. 支持 read、write、readwrite、readback 四种操作模式；
3. Python 层只负责进程编排、超时、JSON 解析和错误映射；
4. AdsLib native runner preflight：若二进制缺失返回 unavailable，
   error 包含 protocol、runner、path、build hint；
5. 不得让缺失二进制导致假通过。

不负责：真实 ADS Router 连接维护、reconnect 策略、生产级 ADS 连接池。
本文件属于 tools/source_lab 工具层，不进入 `src/whale/ingest` 生产路径。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── 常量 ──────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parents[4]
_NATIVE_BUILD_DIR = _REPO_ROOT / "tools" / "source_lab" / "native" / "build"
_ADSLIB_RUNNER_NAME = "beckhoff_ads_polling_runner"

_CLIENT_TIMEOUT_S = 15.0
_CLIENT_START_TIMEOUT_S = 5.0


# ── 异常 ──────────────────────────────────────────────────────────────────


class AdsClientError(RuntimeError):
    """ADS 客户端操作错误基类。"""


class AdsClientUnavailableError(AdsClientError):
    """ADS 客户端不可用（native binary 缺失或环境不满足）。

    Attributes:
        protocol: 协议标识。
        runner: runner 名称。
        path: 期望的 binary 路径。
        build_hint: 构建提示。
    """

    def __init__(
        self,
        protocol: str,
        runner: str,
        path: str,
        build_hint: str = "",
    ) -> None:
        self.protocol = protocol
        self.runner = runner
        self.path = path
        self.build_hint = build_hint
        msg = (
            f"ADS client runner '{runner}' for protocol '{protocol}' "
            f"is not available: executable not found at '{path}'. "
            f"{build_hint}"
        )
        super().__init__(msg)


class AdsClientTimeoutError(AdsClientError):
    """ADS 客户端操作超时。"""


class AdsClientProtocolError(AdsClientError):
    """ADS 客户端与 runner 之间的协议错误（JSON 解析失败、非法返回等）。"""


# ── 数据模型 ──────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class AdsReadResult:
    """ADS 单次读取结果。

    Attributes:
        ok: 是否成功。
        values: 点位键 -> 值的映射。
        errors: 错误列表，每个元素为 "{point_key}: {error_message}"。
        response_timestamp_s: 响应时间戳（epoch 秒）。
        raw_output: runner 原始 stdout 输出，用于诊断。
    """

    ok: bool
    values: dict[str, str | int | float | bool | None] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    response_timestamp_s: float | None = None
    raw_output: str = ""


@dataclass(frozen=True, slots=True)
class AdsWriteResult:
    """ADS 单次写入结果。

    Attributes:
        ok: 是否成功。
        written_count: 成功写入的点位数。
        errors: 错误列表。
        readback: 写入后的 readback 值（如果支持）。
        response_timestamp_s: 响应时间戳。
        raw_output: runner 原始输出。
    """

    ok: bool
    written_count: int = 0
    errors: list[str] = field(default_factory=list)
    readback: dict[str, str | int | float | bool | None] = field(default_factory=dict)
    response_timestamp_s: float | None = None
    raw_output: str = ""


@dataclass(frozen=True, slots=True)
class AdsReadWriteResult:
    """ADS 读写组合结果。

    Attributes:
        ok: 读写均成功。
        read_result: 写前读取快照。
        write_result: 写入结果。
        readback_result: 写后读取（readback）结果。
    """

    ok: bool
    read_result: AdsReadResult | None = None
    write_result: AdsWriteResult | None = None
    readback_result: AdsReadResult | None = None


# ── Native runner 路径解析 ────────────────────────────────────────────────


def _find_ads_native_runner() -> Path | None:
    """查找 AdsLib native runner 二进制。

    查找路径：
    1. 当前 PATH 中的 ``beckhoff_ads_polling_runner``
    2. ``tools/source_lab/native/build/beckhoff_ads_polling_runner``
    3. ``tools/source_lab/native/build/bin/beckhoff_ads_polling_runner``
    4. ``tools/source_lab/native/build/Release/beckhoff_ads_polling_runner``

    Returns:
        binary 路径，或 None。
    """
    # 先检查 PATH
    which_result = shutil.which(_ADSLIB_RUNNER_NAME)
    if which_result is not None:
        return Path(which_result)

    # 检查构建目录
    for candidate in (
        _NATIVE_BUILD_DIR / _ADSLIB_RUNNER_NAME,
        _NATIVE_BUILD_DIR / "bin" / _ADSLIB_RUNNER_NAME,
        _NATIVE_BUILD_DIR / "Release" / _ADSLIB_RUNNER_NAME,
    ):
        if candidate.exists():
            return candidate

    return None


def ads_native_preflight() -> dict[str, Any]:
    """执行 AdsLib native runner 预检，返回结构化诊断信息。

    Returns:
        字典包含 availability、path、error、build_hint 等字段。
        若 native runner 不可用，error 字段包含完整错误信息，
        protocol、runner、path、build_hint 均在其中。
    """
    runner_path = _find_ads_native_runner()
    if runner_path is not None:
        import os

        executable = os.access(runner_path, os.X_OK)
        return {
            "available": executable,
            "path": str(runner_path),
            "executable": executable,
            "error": None,
            "build_hint": None,
            "protocol": "beckhoff_ads",
            "runner": _ADSLIB_RUNNER_NAME,
        }

    build_hint = (
        "Run 'cmake --build tools/source_lab/native/build' "
        "to compile AdsLib native runner. "
        "Requires Beckhoff AdsLib C++ library."
    )
    return {
        "available": False,
        "path": str(_NATIVE_BUILD_DIR / _ADSLIB_RUNNER_NAME),
        "executable": False,
        "error": (
            f"AdsLib native runner '{_ADSLIB_RUNNER_NAME}' "
            f"for protocol 'beckhoff_ads' is not available: "
            f"executable not found at '{_NATIVE_BUILD_DIR / _ADSLIB_RUNNER_NAME}'. "
            f"{build_hint}"
        ),
        "build_hint": build_hint,
        "protocol": "beckhoff_ads",
        "runner": _ADSLIB_RUNNER_NAME,
    }


# ── Python lightweight ADS client（子进程编排） ────────────────────────────


class PyAdsClient:
    """Python 编排的 ADS 客户端，通过子进程调用 AdsLib native runner。

    若 native runner 不可用，所有操作返回不可用错误，不抛出假通过。

    Python 层职责：
    - 进程启动/停止/超时管理；
    - 通过 stdin/stdout JSON 协议与 runner 通信；
    - 返回结构化结果，错误映射为 AdsClientError 子类。

    Args:
        host: ADS server 主机地址。
        ads_port: ADS server 端口。
        ams_net_id: AMS Net ID。
        timeout_s: 操作超时秒数。
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        ads_port: int = 851,
        ams_net_id: str = "5.32.160.1.1.1",
        timeout_s: float = _CLIENT_TIMEOUT_S,
    ) -> None:
        self._host = host
        self._ads_port = ads_port
        self._ams_net_id = ams_net_id
        self._timeout_s = timeout_s
        self._runner_path = _find_ads_native_runner()
        self._protocol_evidence = self._runner_path is not None

    @property
    def protocol_evidence(self) -> bool:
        """是否具有真实的 native protocol 证据。"""
        return self._protocol_evidence

    def _check_available(self) -> None:
        """检查 native runner 是否可用，不可用时抛出 AdsClientUnavailableError。"""
        if self._runner_path is None:
            preflight = ads_native_preflight()
            raise AdsClientUnavailableError(
                protocol=preflight["protocol"],
                runner=preflight["runner"],
                path=preflight["path"],
                build_hint=preflight["build_hint"] or "",
            )

    def _build_command(
        self,
        operation: str,
        point_keys: list[str],
        values: dict[str, str | int | float | bool | None] | None = None,
    ) -> list[str]:
        """构建 ADS runner 命令行。

        Args:
            operation: "read" 或 "write"。
            point_keys: 要操作的点位键列表。
            values: 写入值（仅 write 操作需要）。

        Returns:
            命令行参数列表。
        """
        assert self._runner_path is not None
        cmd: list[str] = [
            str(self._runner_path),
            "--host", self._host,
            "--port", str(self._ads_port),
            "--ams-net-id", self._ams_net_id,
            "--operation", operation,
        ]
        if point_keys:
            cmd.extend(["--point-keys", *point_keys])
        if values:
            values_json = json.dumps(
                {k: v for k, v in values.items() if v is not None},
                ensure_ascii=False,
            )
            cmd.extend(["--values", values_json])
        return cmd

    def read(
        self,
        point_keys: list[str],
    ) -> AdsReadResult:
        """通过 native runner 读取指定点位。

        Args:
            point_keys: 要读取的点位键列表。

        Returns:
            AdsReadResult。

        Raises:
            AdsClientUnavailableError: native runner 不可用。
            AdsClientTimeoutError: 操作超时。
            AdsClientProtocolError: runner 返回了非法 JSON 或协议错误。
        """
        self._check_available()
        cmd = self._build_command("read", point_keys)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AdsClientTimeoutError(
                f"ADS read timed out after {self._timeout_s}s: {exc}"
            ) from exc

        return _parse_read_output(proc.stdout, proc.stderr, proc.returncode)

    def write(
        self,
        values: dict[str, str | int | float | bool | None],
    ) -> AdsWriteResult:
        """通过 native runner 写入点位值。

        Args:
            values: 点位键 -> 值的映射。

        Returns:
            AdsWriteResult。

        Raises:
            AdsClientUnavailableError: native runner 不可用。
            AdsClientTimeoutError: 操作超时。
            AdsClientProtocolError: protocol error。
        """
        self._check_available()
        point_keys = list(values.keys())
        cmd = self._build_command("write", point_keys, values=values)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AdsClientTimeoutError(
                f"ADS write timed out after {self._timeout_s}s: {exc}"
            ) from exc

        return _parse_write_output(proc.stdout, proc.stderr, proc.returncode)

    def readwrite(
        self,
        values: dict[str, str | int | float | bool | None],
        point_keys: list[str] | None = None,
    ) -> AdsReadWriteResult:
        """先读取当前值，再写入，最后 readback 验证。

        操作顺序：
        1. read: 获取写入前的快照；
        2. write: 写入新值；
        3. read: readback 确认新值已生效。

        Args:
            values: 要写入的点位键 -> 值映射。
            point_keys: 读取的点位键列表（默认使用 values 的键）。

        Returns:
            AdsReadWriteResult 包含三次操作的结果。
        """
        keys = point_keys or list(values.keys())

        # 1. Read before write
        try:
            before = self.read(keys)
        except AdsClientError as exc:
            return AdsReadWriteResult(
                ok=False,
                read_result=AdsReadResult(ok=False, errors=[str(exc)]),
            )

        # 2. Write
        try:
            write_result = self.write(values)
        except AdsClientError as exc:
            return AdsReadWriteResult(
                ok=False,
                read_result=before,
                write_result=AdsWriteResult(ok=False, errors=[str(exc)]),
            )

        # 3. Readback
        try:
            after = self.read(keys)
        except AdsClientError as exc:
            after = AdsReadResult(ok=False, errors=[str(exc)])

        ok = write_result.ok and after.ok
        return AdsReadWriteResult(
            ok=ok,
            read_result=before,
            write_result=write_result,
            readback_result=after,
        )

    def readback(
        self,
        point_keys: list[str],
    ) -> AdsReadResult:
        """直接读取指定点位的最新值（等价于 read）。

        Args:
            point_keys: 要读取的点位键列表。

        Returns:
            AdsReadResult。
        """
        return self.read(point_keys)


# ── 输出解析 ──────────────────────────────────────────────────────────────


def _parse_read_output(
    stdout: str,
    stderr: str,
    returncode: int,
) -> AdsReadResult:
    """解析 native runner read 操作的输出。

    期望输出格式（JSON 行）：
    {"values": {"key1": 123, "key2": true}, "errors": []}

    Args:
        stdout: runner stdout。
        stderr: runner stderr。
        returncode: 进程返回码。

    Returns:
        AdsReadResult。

    Raises:
        AdsClientProtocolError: 输出无法解析或 runner 返回错误。
    """
    _check_returncode(returncode, stderr, "read")
    values: dict[str, str | int | float | bool | None] = {}
    errors: list[str] = []
    raw_output = stdout.strip()

    if not raw_output:
        return AdsReadResult(
            ok=False,
            values=values,
            errors=["empty runner output"],
            response_timestamp_s=time.time(),
            raw_output=raw_output,
        )

    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        return AdsReadResult(
            ok=False,
            values=values,
            errors=[f"JSON parse error: {exc}"],
            response_timestamp_s=time.time(),
            raw_output=raw_output,
        )

    if not isinstance(payload, dict):
        raise AdsClientProtocolError(
            f"ADS read returned non-dict output: {raw_output[:200]}"
        )

    values = _normalize_values(payload.get("values", {}))
    errors = _extract_errors(payload.get("errors", []))
    ok = len(errors) == 0

    return AdsReadResult(
        ok=ok,
        values=values,
        errors=errors,
        response_timestamp_s=time.time(),
        raw_output=raw_output,
    )


def _parse_write_output(
    stdout: str,
    stderr: str,
    returncode: int,
) -> AdsWriteResult:
    """解析 native runner write 操作的输出。

    Args:
        stdout: runner stdout。
        stderr: runner stderr。
        returncode: 进程返回码。

    Returns:
        AdsWriteResult。

    Raises:
        AdsClientProtocolError: 输出非法。
    """
    _check_returncode(returncode, stderr, "write")
    errors: list[str] = []
    readback: dict[str, str | int | float | bool | None] = {}
    written_count = 0
    raw_output = stdout.strip()

    if not raw_output:
        return AdsWriteResult(
            ok=False,
            written_count=0,
            errors=["empty runner output"],
            response_timestamp_s=time.time(),
            raw_output=raw_output,
        )

    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        return AdsWriteResult(
            ok=False,
            written_count=0,
            errors=[f"JSON parse error: {exc}"],
            response_timestamp_s=time.time(),
            raw_output=raw_output,
        )

    if not isinstance(payload, dict):
        raise AdsClientProtocolError(
            f"ADS write returned non-dict output: {raw_output[:200]}"
        )

    written_count = int(payload.get("written_count", 0))
    errors = _extract_errors(payload.get("errors", []))
    readback = _normalize_values(payload.get("readback", {}))

    return AdsWriteResult(
        ok=len(errors) == 0,
        written_count=written_count,
        errors=errors,
        readback=readback,
        response_timestamp_s=time.time(),
        raw_output=raw_output,
    )


def _check_returncode(returncode: int, stderr: str, operation: str) -> None:
    """检查 runner 返回码，非零时抛出协议错误。

    Args:
        returncode: 进程返回码。
        stderr: stderr 输出。
        operation: 操作名（如 "read"）。

    Raises:
        AdsClientProtocolError: 返回码非零。
    """
    if returncode != 0:
        detail = stderr.strip()[:500] if stderr else "no stderr output"
        raise AdsClientProtocolError(
            f"ADS {operation} runner exited with code {returncode}: {detail}"
        )


def _normalize_values(
    raw: dict[str, Any],
) -> dict[str, str | int | float | bool | None]:
    """规范化值字典，将非法类型转换为字符串。

    Args:
        raw: 原始值字典。

    Returns:
        规范化后的值字典。
    """
    result: dict[str, str | int | float | bool | None] = {}
    for key, val in raw.items():
        if isinstance(val, (str, int, float, bool)) or val is None:
            result[key] = val
        else:
            result[key] = str(val)
    return result


def _extract_errors(raw_errors: Any) -> list[str]:
    """从 runner 输出中提取错误列表。

    Args:
        raw_errors: 可能是 list[dict] 或 list[str]。

    Returns:
        规范化的错误字符串列表。
    """
    if not isinstance(raw_errors, list):
        return [f"unexpected errors format: {type(raw_errors).__name__}"]
    result: list[str] = []
    for item in raw_errors:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            result.append(item.get("message", json.dumps(item)))
        else:
            result.append(str(item))
    return result


__all__ = [
    "AdsClientError",
    "AdsClientProtocolError",
    "AdsClientTimeoutError",
    "AdsClientUnavailableError",
    "AdsReadResult",
    "AdsReadWriteResult",
    "AdsWriteResult",
    "PyAdsClient",
    "ads_native_preflight",
]
