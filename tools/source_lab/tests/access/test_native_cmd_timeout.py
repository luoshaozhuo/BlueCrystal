"""QA-7: NativeCmdCapacityRunner stdout 超时测试。

验证 _read_output_lines 在子进程 hang 住不输出时，在超时后抛出 TimeoutError。
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

from tools.source_lab.access.runners.native_cmd import (
    NativeCmdCapacityRunner,
    _NativeSession,
    _read_output_lines,
)
from tools.source_lab.access.runners.protocol import ProtocolDiagnostics


def test_read_output_lines_times_out_on_hang(tmp_path: Path) -> None:
    """子进程 hang 住不输出时，_read_output_lines 应在超时后抛出 TimeoutError。"""
    # 启动一个 sleep 很长时间的进程来模拟 hang
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(300)"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )

    session = _NativeSession()
    diagnostics = ProtocolDiagnostics()

    start = time.monotonic()
    with pytest.raises(TimeoutError, match="timed out"):
        # 设置极短超时 (1s)
        _read_output_lines(proc, session, diagnostics, timeout_seconds=1)
    elapsed = time.monotonic() - start
    # 确保实际超时时间在合理范围内
    assert elapsed < 5, f"Timeout took too long: {elapsed:.1f}s"

    # 清理
    proc.terminate()
    proc.wait(timeout=3)


def test_read_output_lines_completes_normally(tmp_path: Path) -> None:
    """正常输出 DONE 的进程应在超时前完成。"""
    proc = subprocess.Popen(
        [sys.executable, "-c", "print('SAMPLE x'); print('DONE')"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )

    session = _NativeSession()
    diagnostics = ProtocolDiagnostics()

    # 足够长的超时，进程应当正常完成不触发超时
    _read_output_lines(proc, session, diagnostics, timeout_seconds=10)
    assert session.total_reads == 1
    assert session.ok_reads == 1

    proc.wait(timeout=3)


def test_native_cmd_runner_timeout_configurable() -> None:
    """NativeCmdCapacityRunner 的 stdout_timeout_seconds 应可配置。"""
    runner = NativeCmdCapacityRunner()
    assert runner.stdout_timeout_seconds == 60
    runner.stdout_timeout_seconds = 30
    assert runner.stdout_timeout_seconds == 30
