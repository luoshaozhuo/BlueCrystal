"""IEC 61850 L2 native runner 故障模式测试。

验证 L2 native runner（GOOSE/SV）的各种故障模式和行为。
证据等级：L2（contract）。
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def _binary(name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "native" / "build" / name


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _run_in_unshare(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["unshare", "-Urn", "bash", "-lc", command],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_goose_invalid_interface_returns_error_not_segfault() -> None:
    result = _run(str(_binary("iec61850_goose_subscriber_runner")), "not-an-iface", "1000", "1")
    assert result.returncode == 2
    assert "ERROR\tinvalid interface" in result.stderr


def test_goose_invalid_app_id_returns_error_not_segfault() -> None:
    result = _run(str(_binary("iec61850_goose_subscriber_runner")), "lo", "bad", "1")
    assert result.returncode == 2
    assert "ERROR\tinvalid app_id" in result.stderr


def test_goose_timeout_without_events_prints_summary_and_done() -> None:
    command = """
set -euo pipefail
source <(bash scripts/source_lab_l2_test_env.sh setup)
trap 'bash scripts/source_lab_l2_test_env.sh teardown >/dev/null 2>&1 || true' EXIT
tools/source_lab/native/build/iec61850_goose_subscriber_runner "${SOURCE_LAB_L2_SUBSCRIBER_INTERFACE}" 1000 1
"""
    result = _run_in_unshare(command)
    assert result.returncode == 0, result.stderr
    assert "READY" in result.stdout
    assert "STREAM_SUMMARY\t0\t0" in result.stdout
    assert "DONE" in result.stdout


def test_sv_invalid_interface_returns_error_not_segfault() -> None:
    result = _run(str(_binary("iec61850_sv_subscriber_runner")), "not-an-iface", "4000", "1")
    assert result.returncode == 2
    assert "ERROR\tinvalid interface" in result.stderr


def test_sv_timeout_without_events_prints_summary_and_done() -> None:
    command = """
set -euo pipefail
source <(bash scripts/source_lab_l2_test_env.sh setup)
trap 'bash scripts/source_lab_l2_test_env.sh teardown >/dev/null 2>&1 || true' EXIT
tools/source_lab/native/build/iec61850_sv_subscriber_runner "${SOURCE_LAB_L2_SUBSCRIBER_INTERFACE}" 4000 1
"""
    result = _run_in_unshare(command)
    assert result.returncode == 0, result.stderr
    assert "READY" in result.stdout
    assert "STREAM_SUMMARY\t0\t0" in result.stdout
    assert "DONE" in result.stdout
