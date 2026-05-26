"""IEC 61850 Report runner protocol tests.

Tests the stdin/stdout protocol of the iec61850_report_runner C executable.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_NATIVE_BUILD_DIR = _REPO_ROOT / "tools" / "source_lab" / "native" / "build"
_RUNNER_EXE = _NATIVE_BUILD_DIR / "iec61850_report_runner"


def _runner_path() -> Path:
    if not _RUNNER_EXE.exists():
        pytest.skip(f"Report runner not built: {_RUNNER_EXE}")
    return _RUNNER_EXE


class TestIec61850ReportRunnerVersion:
    """--version 输出验证。"""

    def test_version_flag(self) -> None:
        exe = _runner_path()
        result = subprocess.run(
            [str(exe), "--version"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0
        assert result.stdout.startswith("iec61850_report_runner")
        assert "REPORT" in result.stdout

    def test_version_short_flag(self) -> None:
        exe = _runner_path()
        result = subprocess.run(
            [str(exe), "-v"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0

    def test_version_stdout_only(self) -> None:
        """--version 的 stderr 必须为空。"""
        exe = _runner_path()
        result = subprocess.run(
            [str(exe), "--version"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.stderr == ""


class TestIec61850ReportRunnerInvalidArgs:
    """参数校验测试。"""

    def test_no_args_prints_usage(self) -> None:
        exe = _runner_path()
        result = subprocess.run(
            [str(exe)],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 2
        assert "Usage:" in result.stderr

    def test_invalid_host_empty_args_fails(self) -> None:
        exe = _runner_path()
        result = subprocess.run(
            [str(exe), "", "0", "", ""],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode != 0

    def test_stdout_noise_zero_for_invalid_args(self) -> None:
        """无效参数时 stdout 必须为空（所有信息输出到 stderr）。"""
        exe = _runner_path()
        result = subprocess.run(
            [str(exe)],
            capture_output=True, text=True, timeout=5,
        )
        assert result.stdout == ""
