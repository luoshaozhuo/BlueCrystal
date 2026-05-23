"""原生可执行 runner 的统一进程管理基类。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from threading import Thread
from typing import Final, IO

from tools.source_lab.access.runners.protocol import ProtocolDiagnostics, read_protocol_line, start_stderr_drain_thread

_STOP_TIMEOUT_SECONDS: Final[float] = 3.0


@dataclass(frozen=True, slots=True)
class NativeProcessResult:
    """一次 native 进程协议会话的公共结果。"""

    return_code: int | None
    diagnostics: ProtocolDiagnostics


def stop_native_process(process: subprocess.Popen[str]) -> None:
    """停止 native 进程，优先 terminate，再必要时 kill。

    Args:
        process: 已启动的 native runner 进程。
    """

    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=_STOP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=_STOP_TIMEOUT_SECONDS)


def ensure_executable(path: Path, *, label: str) -> None:
    """校验 native runner 可执行文件存在。

    Args:
        path: 可执行文件路径。
        label: 报错用 runner 标签。

    Raises:
        RuntimeError: 文件不存在时抛出。
    """

    if not path.exists():
        raise RuntimeError(f"{label} executable does not exist: {path}")


def read_ready_line(
    stream: IO[str] | None,
    *,
    diagnostics: ProtocolDiagnostics,
    label: str,
    ready_prefix: str,
    error_prefix: str,
) -> str:
    """读取 READY 协议行并处理噪声与 ERROR。"""

    if stream is None:
        raise RuntimeError(f"{label} stdout is unavailable")
    return read_protocol_line(
        stream,
        allowed_prefixes=(ready_prefix,),
        error_prefix=error_prefix,
        diagnostics=diagnostics,
        label=label,
    )


def start_native_process(
    command: tuple[str, ...],
    *,
    diagnostics: ProtocolDiagnostics,
) -> tuple[subprocess.Popen[str], Thread]:
    """启动 native 进程并附加 stderr drain 线程。"""

    process = subprocess.Popen(
        list(command),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    stderr_thread = start_stderr_drain_thread(process.stderr, diagnostics)
    return process, stderr_thread
