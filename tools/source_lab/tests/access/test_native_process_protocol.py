"""Native process protocol helper tests."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest

from tools.source_lab.access.runners.native_process import ensure_executable, read_ready_line
from tools.source_lab.access.runners.protocol import ProtocolDiagnostics


def test_ensure_executable_raises_for_missing_binary(tmp_path: Path) -> None:
    """Missing native executable should raise a stable error."""

    missing_path = tmp_path / "missing_runner"
    with pytest.raises(RuntimeError, match="does not exist"):
        ensure_executable(missing_path, label="test-runner")


def test_read_ready_line_skips_noise_and_returns_ready() -> None:
    """READY parser should tolerate non-protocol noise lines."""

    diagnostics = ProtocolDiagnostics()
    stream = StringIO("noise line\nREADY endpoint=tcp://127.0.0.1:9000\n")
    line = read_ready_line(
        stream,
        diagnostics=diagnostics,
        label="test-runner",
        ready_prefix="READY",
        error_prefix="ERROR",
    )
    assert line.startswith("READY")
    assert diagnostics.stdout_noise_count == 1
