"""IEC 61850 Report production capacity / profile gate test.

验证 IEC 61850 Report 的 subscription 路径可执行的硬性门禁。

门禁要求：
1. native report runner 二进制存在或可构建。
2. simulator 可启动且 stdout 无噪声。
3. report runner --version 输出正确。
4. report runner 可连接 simulator 并收到 READY。
5. 可收到真实 REPORT event。
6. registry 标记与真实能力一致。
7. stdout noise = 0（只输出协议行）。
8. 短周期内至少收到 5 个 report（稳定性 smoke）。
9. 不允许 skipped。
"""
from __future__ import annotations

import asyncio
import subprocess
import time
from contextlib import closing
from pathlib import Path

import pytest

from tools.source_lab.access.runners.registry import (
    PROTOCOL_CAPABILITIES,
)

# ── Binary resolution ────────────────────────────────────────────────────


def _resolve_simulator() -> Path | None:
    build = Path(__file__).resolve().parents[2] / "native" / "build"
    for name in ("iec61850_simulator_server", "iec61850_simulator_server.exe"):
        p = build / name
        if p.exists():
            return p.resolve()
    return None


def _resolve_report_runner() -> Path | None:
    build = Path(__file__).resolve().parents[2] / "native" / "build"
    for name in ("iec61850_report_runner", "iec61850_report_runner.exe"):
        p = build / name
        if p.exists():
            return p.resolve()
    return None


SIMULATOR_PATH = _resolve_simulator()
REPORT_RUNNER_PATH = _resolve_report_runner()


def _find_free_port() -> int:
    with closing(__import__("socket").socket(__import__("socket").AF_INET, __import__("socket").SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


# ── Binary existence gate ────────────────────────────────────────────────


def test_simulator_binary_exists() -> None:
    """模拟器二进制必须存在。"""
    assert SIMULATOR_PATH is not None, (
        "iec61850_simulator_server not found; build with CMake first"
    )
    assert SIMULATOR_PATH.exists()


def test_report_runner_binary_exists() -> None:
    """报告运行器二进制必须存在。"""
    assert REPORT_RUNNER_PATH is not None, (
        "iec61850_report_runner not found; build with CMake first"
    )
    assert REPORT_RUNNER_PATH.exists()


# ── Version gate ─────────────────────────────────────────────────────────


def test_report_runner_version_output() -> None:
    """--version 输出验证。"""
    assert REPORT_RUNNER_PATH is not None
    result = subprocess.run(
        [str(REPORT_RUNNER_PATH), "--version"],
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 0
    assert result.stdout.startswith("iec61850_report_runner")
    assert "REPORT" in result.stdout
    assert result.stderr == "", f"stderr must be empty: {result.stderr}"


# ── Simulator + Runner smoke ─────────────────────────────────────────────


@pytest.fixture(scope="module")
def simulator_port() -> int:
    """Start the IEC 61850 simulator and yield its port."""
    assert SIMULATOR_PATH is not None
    port = _find_free_port()
    proc = subprocess.Popen(
        [str(SIMULATOR_PATH), str(port)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None
    ready_line = proc.stdout.readline().strip()
    assert ready_line == "READY", (
        f"simulator stdout noise: expected READY, got {ready_line!r}"
    )
    yield port
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def test_report_runner_connects_and_reads_ready(simulator_port: int) -> None:
    """report runner 连接 simulator 并收到 READY。"""
    assert REPORT_RUNNER_PATH is not None
    proc = subprocess.Popen(
        [str(REPORT_RUNNER_PATH), "127.0.0.1", str(simulator_port), "Simulator", "EventsRCB01"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None
    ready_line = proc.stdout.readline().strip()
    assert ready_line == "READY", (
        f"expected READY from report runner, got {ready_line!r}"
    )

    # Verify stdout noise = 0 immediately after READY
    import select
    import sys
    if hasattr(select, "select"):
        r, _, _ = select.select([proc.stdout], [], [], 0.1)
        if r:
            extra = proc.stdout.readline().strip()
            assert extra == "", (
                f"stdout noise after READY: {extra!r}"
            )

    # Send QUIT
    assert proc.stdin is not None
    proc.stdin.write("QUIT\n")
    proc.stdin.flush()

    stopped_line = proc.stdout.readline().strip()
    assert stopped_line == "STOPPED", (
        f"expected STOPPED, got {stopped_line!r}"
    )
    proc.wait(timeout=5)


def test_report_runner_receives_events(simulator_port: int) -> None:
    """短周期内至少收到 5 个 REPORT event（稳定性 smoke）。"""
    assert REPORT_RUNNER_PATH is not None
    proc = subprocess.Popen(
        [str(REPORT_RUNNER_PATH), "127.0.0.1", str(simulator_port), "Simulator", "EventsRCB01"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None

    # Wait for READY
    ready_line = proc.stdout.readline().strip()
    assert ready_line == "READY"

    # Collect events for 6 seconds (simulator triggers every 1s + intgPd=10s,
    # but data change triggers via daemon toggle every 1s)
    events: list[str] = []
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline:
        try:
            line = proc.stdout.readline()
            if not line:
                break
            events.append(line.strip())
        except OSError:
            break

    # Send QUIT
    assert proc.stdin is not None
    proc.stdin.write("QUIT\n")
    proc.stdin.flush()
    proc.wait(timeout=5)

    # Verify REPORT events
    report_events = [e for e in events if e.startswith("REPORT")]
    assert len(report_events) >= 5, (
        f"expected >=5 REPORT events in 8s, got {len(report_events)}"
    )

    # Verify stdout noise = 0 (only READY, REPORT, STOPPED)
    all_lines = [ready_line] + events
    for line in all_lines:
        if line.startswith("REPORT"):
            continue
        assert line in ("READY", "STOPPED", ""), (
            f"stdout noise: unexpected line {line!r}"
        )


def test_report_runner_multiple_events_with_sequence_numbers(simulator_port: int) -> None:
    """多个 REPORT event 的 seq_num 单调递增。"""
    assert REPORT_RUNNER_PATH is not None
    proc = subprocess.Popen(
        [str(REPORT_RUNNER_PATH), "127.0.0.1", str(simulator_port), "Simulator", "EventsRCB01"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None

    ready_line = proc.stdout.readline().strip()
    assert ready_line == "READY"

    collected: list[str] = []
    deadline = time.monotonic() + 6.0
    while time.monotonic() < deadline:
        try:
            line = proc.stdout.readline()
            if not line:
                break
            collected.append(line.strip())
        except OSError:
            break

    assert proc.stdin is not None
    proc.stdin.write("QUIT\n")
    proc.stdin.flush()
    proc.wait(timeout=5)

    report_lines = [e for e in collected if e.startswith("REPORT")]
    assert len(report_lines) >= 3

    seq_nums: list[int] = []
    for line in report_lines:
        parts = line.split("\t")
        assert len(parts) >= 4
        seq_nums.append(int(parts[3]))

    # Verify monotonic: each seq_num should be > previous
    for i in range(1, len(seq_nums)):
        assert seq_nums[i] > seq_nums[i - 1], (
            f"seq_num not monotonic: {seq_nums}"
        )


# ── Registry gate ────────────────────────────────────────────────────────


class TestIec61850ReportRegistry:
    """Registry 标记验证。"""

    def test_report_in_protocol_capabilities(self) -> None:
        assert "iec61850_report" in PROTOCOL_CAPABILITIES

    def test_production_client_subscribe_is_true(self) -> None:
        cap = PROTOCOL_CAPABILITIES["iec61850_report"]
        assert cap.get("production_client_subscribe") is True

    def test_production_client_read_is_false(self) -> None:
        cap = PROTOCOL_CAPABILITIES["iec61850_report"]
        assert cap.get("production_client_read") is False

    def test_production_client_write_is_false(self) -> None:
        cap = PROTOCOL_CAPABILITIES["iec61850_report"]
        assert cap.get("production_client_write") is False

    def test_no_goose_or_sv_falsely_marked(self) -> None:
        cap = PROTOCOL_CAPABILITIES["iec61850_report"]
        unsupported = cap.get("unsupported_subscription_operations", ())
        assert "goose" in unsupported, "goose must be in unsupported_subscription_operations"
        assert "sv" in unsupported, "sv must be in unsupported_subscription_operations"

    def test_supported_subscription_operations(self) -> None:
        cap = PROTOCOL_CAPABILITIES["iec61850_report"]
        supported = cap.get("supported_subscription_operations", ())
        assert "report_subscription" in supported
        assert "brcb" not in supported, "BRCB not yet supported"

    def test_service_capability_real_native_runner(self) -> None:
        cap = PROTOCOL_CAPABILITIES["iec61850_report"]
        assert cap.get("current_implementation_level") == "real_native_runner"
