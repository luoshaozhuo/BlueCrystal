"""IEC 104 client runner WRITE 协议测试。

验证 C runner 的 WRITE 指令格式、WRITE_RESULT 输出以及 stdout/stderr 协议治理。
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _resolve_runner() -> Path | None:
    build_dir = Path(__file__).resolve().parents[2] / "native" / "build"
    for candidate in (
        build_dir / "iec104_client_runner",
        build_dir / "iec104_client_runner.exe",
    ):
        if candidate.exists():
            return candidate.resolve()
    return None


RUNNER_PATH = _resolve_runner()


@pytest.mark.skipif(RUNNER_PATH is None, reason="iec104_client_runner not compiled")
class TestIec104ClientRunnerWriteProtocol:
    """直接测试 C runner 的 WRITE 指令行为。"""

    def test_version_flag(self) -> None:
        """--version 应返回版本信息且不报错。"""
        assert RUNNER_PATH is not None
        result = subprocess.run(
            [str(RUNNER_PATH), "--version"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "iec104_client_runner" in result.stdout
        assert "C_SC_NA_1" in result.stdout

    def test_short_version_flag(self) -> None:
        """-v 应等同于 --version。"""
        assert RUNNER_PATH is not None
        result = subprocess.run(
            [str(RUNNER_PATH), "-v"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "iec104_client_runner" in result.stdout

    def test_interactive_ready_on_stdout(self) -> None:
        """交互模式应在 stdout 输出 READY。"""
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

        proc.stdin.write("QUIT\n")
        proc.stdin.flush()
        proc.wait(timeout=5)

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

        ready = proc.stdout.readline().strip()
        assert ready == "READY"

        # WRITE to non-existent server (expect execution_failed)
        proc.stdin.write("WRITE\ttest-001\t127.0.0.1\t2404\t1\t101\tC_SC_NA_1\t1\n")
        proc.stdin.flush()

        write_result = proc.stdout.readline().strip()
        assert write_result.startswith("WRITE_RESULT")

        fields = write_result.split("\t")
        assert len(fields) >= 4
        assert fields[0] == "WRITE_RESULT"
        assert fields[1] == "test-001"

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

        # Incomplete WRITE command (missing fields)
        proc.stdin.write("WRITE\tonly_two_fields\n")
        proc.stdin.flush()

        write_result = proc.stdout.readline().strip()
        assert write_result.startswith("WRITE_RESULT")
        assert "ok=0" in write_result
        assert "protocol_error" in write_result or "invalid_format" in write_result

        proc.stdin.write("QUIT\n")
        proc.stdin.flush()
        proc.wait(timeout=5)

    def test_stdin_unknown_command_returns_error(self) -> None:
        """未知命令应返回协议错误。"""
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

        proc.stdin.write("UNKNOWN_COMMAND\n")
        proc.stdin.flush()

        write_result = proc.stdout.readline().strip()
        assert write_result.startswith("WRITE_RESULT")
        assert "ok=0" in write_result

        proc.stdin.write("QUIT\n")
        proc.stdin.flush()
        proc.wait(timeout=5)

    def test_stdin_no_stdout_noise(self) -> None:
        """stdout 不应包含非协议行（日志只应在 stderr）。"""
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

        proc.stdin.write("WRITE\ttest-002\t127.0.0.1\t2404\t1\t101\tC_SC_NA_1\t0\n")
        proc.stdin.flush()

        write_result = proc.stdout.readline().strip()
        assert write_result.startswith("WRITE_RESULT")

        proc.stdin.write("QUIT\n")
        proc.stdin.flush()
        proc.wait(timeout=5)

        # Check stderr is only diagnostic (no test assertion on content)
        if proc.stderr:
            _ = proc.stderr.read()
