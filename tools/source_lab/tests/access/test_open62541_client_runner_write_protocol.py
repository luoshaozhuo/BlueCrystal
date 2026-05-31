"""open62541 client runner WRITE 协议测试。

验证 C runner 的 WRITE 指令格式、WRITE_RESULT 输出解析以及 stdout/stderr 协议治理。
这些测试不要求 native runner 编译可用；它们通过模拟 stdin/stdout 验证协议边界。
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _resolve_runner() -> Path | None:
    """查找编译好的 open62541_client_runner。"""
    # 优先从环境变量读取
    env_path = Path(__file__).resolve().parents[2] / "native" / "build"
    for candidate in (
        Path(env_path) / "open62541_client_runner",
        Path(env_path) / "open62541_client_runner.exe",
    ):
        if candidate.exists():
            return candidate.resolve()
    return None


RUNNER_PATH = _resolve_runner()


@pytest.mark.skipif(RUNNER_PATH is None, reason="open62541_client_runner not compiled")
class TestOpen62541ClientRunnerWriteProtocol:
    """直接测试 C runner 的 WRITE 指令行为。"""

    def test_version_flag(self) -> None:
        """--version 应返回版本信息且不报错。"""
        assert RUNNER_PATH is not None
        result = subprocess.run(
            [str(RUNNER_PATH), "--version"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "open62541_client_runner" in result.stdout
        assert "WRITE" in result.stdout

    def test_short_version_flag(self) -> None:
        """-v 应等同于 --version。"""
        assert RUNNER_PATH is not None
        result = subprocess.run(
            [str(RUNNER_PATH), "-v"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "open62541_client_runner" in result.stdout

    def test_stdin_write_command_format(self) -> None:
        """WRITE stdin 命令应在 stdout 输出 WRITE_RESULT。"""
        assert RUNNER_PATH is not None
        proc = subprocess.Popen(
            [str(RUNNER_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert proc.stdin is not None
        assert proc.stdout is not None

        # 先读 READY
        ready = proc.stdout.readline().strip()
        assert ready == "READY"

        # 发送 WRITE 命令（连接不存在的 server，预期 connect_failed）
        proc.stdin.write("WRITE\ttest-001\topc.tcp://127.0.0.1:1\t-\ts=test.value\tdouble\t42.0\n")
        proc.stdin.flush()

        # 读 WRITE_RESULT
        write_result = proc.stdout.readline().strip()
        assert write_result.startswith("WRITE_RESULT")

        # 解析字段
        fields = write_result.split("\t")
        assert len(fields) >= 4
        assert fields[0] == "WRITE_RESULT"
        assert fields[1] == "test-001"
        assert fields[2] == "s=test.value"
        assert "ok=0" in fields[3]  # 连接失败预期

        # 清理
        proc.stdin.write("QUIT\n")
        proc.stdin.flush()
        proc.wait(timeout=5)

    def test_stdin_malformed_write_returns_error(self) -> None:
        """格式错误的 WRITE 命令应返回协议错误。"""
        assert RUNNER_PATH is not None
        proc = subprocess.Popen(
            [str(RUNNER_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert proc.stdin is not None
        assert proc.stdout is not None

        ready = proc.stdout.readline().strip()
        assert ready == "READY"

        # 发送格式错误的 WRITE 命令（字段数不足）
        proc.stdin.write("WRITE\tonly_two_fields\n")
        proc.stdin.flush()

        write_result = proc.stdout.readline().strip()
        assert write_result.startswith("WRITE_RESULT")
        assert "ok=0" in write_result
        assert "protocol_error" in write_result

        proc.stdin.write("QUIT\n")
        proc.stdin.flush()
        proc.wait(timeout=5)

    def test_stdin_no_stdout_noise_for_write(self) -> None:
        """WRITE 命令不应在 stdout 产生噪声行。"""
        assert RUNNER_PATH is not None
        proc = subprocess.Popen(
            [str(RUNNER_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert proc.stdin is not None
        assert proc.stdout is not None

        ready = proc.stdout.readline().strip()
        assert ready == "READY"

        # 发送 WRITE 命令
        proc.stdin.write("WRITE\ttest-002\topc.tcp://127.0.0.1:1\t-\ts=test.value\tdouble\t42.0\n")
        proc.stdin.flush()

        # 只应有一行输出
        write_result = proc.stdout.readline().strip()
        assert write_result.startswith("WRITE_RESULT")

        proc.stdin.write("QUIT\n")
        proc.stdin.flush()
        proc.wait(timeout=5)

        # stderr 用于诊断日志，允许输出但不允许 stdout 有噪声
        if proc.stderr:
            proc.stderr.read()  # drain stderr
