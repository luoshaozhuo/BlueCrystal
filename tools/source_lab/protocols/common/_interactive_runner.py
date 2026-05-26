"""Native interactive runner — subprocess stdin/stdout protocol helper.

Launches a compiled C runner in interactive mode (no CLI args) and
communicates via tab-separated commands on stdin, tab-separated result
lines on stdout.

Usage::

    runner = NativeInteractiveRunner("iec61850_mms_client_runner")
    runner.start(timeout=10.0)
    response = runner.command("READ\\t...")
    runner.stop()
"""

from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import IO

from tools.source_lab.access.runners.protocol import (
    ProtocolDiagnostics,
    read_protocol_line,
    start_stderr_drain_thread,
)

_NATIVE_BUILD_DIR = Path(__file__).resolve().parents[2] / "native" / "build"


class NativeInteractiveRunner:
    """Manages a native C runner subprocess with stdin/stdout protocol.

    The runner must support interactive mode: print ``READY`` on stdout
    when ready, then accept commands on stdin and print responses on stdout.
    """

    def __init__(self, executable_name: str) -> None:
        self._executable_name = executable_name
        self._process: subprocess.Popen[str] | None = None
        self._stderr_thread: threading.Thread | None = None
        self._diagnostics = ProtocolDiagnostics()

    # ── Public API ─────────────────────────────────────────────────────

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self, timeout: float = 10.0) -> None:
        """Launch the native runner and wait for READY."""
        if self._process is not None:
            return  # already started

        runner_path = _resolve_executable(self._executable_name)
        if not runner_path.exists():
            raise RuntimeError(
                f"native runner {self._executable_name} not compiled: "
                f"{runner_path} does not exist"
            )

        self._process = subprocess.Popen(
            [str(runner_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        assert self._process.stdout is not None
        assert self._process.stdin is not None

        self._stderr_thread = start_stderr_drain_thread(
            self._process.stderr, self._diagnostics
        )

        ready_line = read_protocol_line(
            self._process.stdout,
            allowed_prefixes=("READY",),
            error_prefix="ERROR",
            diagnostics=self._diagnostics,
            label=self._executable_name,
        )
        if ready_line != "READY":
            raise RuntimeError(
                f"{self._executable_name}: expected READY, got {ready_line!r}"
                f"{self._diagnostics.render_context()}"
            )

    def command(self, cmd_line: str, *, timeout: float = 30.0) -> str:
        """Send one command line and return the response line.

        Args:
            cmd_line: Full command string (e.g. ``READ\\t...``).  The
                trailing newline is added automatically.
            timeout: Max seconds to wait for a response.

        Returns:
            The response line from stdout (stripped).

        Raises:
            RuntimeError: Process died or no response within timeout.
        """
        if self._process is None or self._process.stdin is None:
            raise RuntimeError(f"{self._executable_name}: not started")
        if self._process.poll() is not None:
            raise RuntimeError(
                f"{self._executable_name}: process died (rc={self._process.returncode})"
            )

        # Write command
        self._process.stdin.write(cmd_line + "\n")
        self._process.stdin.flush()

        # Read response
        deadline = time.monotonic() + timeout
        buf = ""
        assert self._process.stdout is not None
        while time.monotonic() < deadline:
            line = self._process.stdout.readline()
            if line == "":
                raise RuntimeError(
                    f"{self._executable_name}: stdout closed while waiting for response"
                )
            text = line.strip()
            if not text:
                continue
            if text.startswith("ERROR"):
                raise RuntimeError(
                    f"{self._executable_name}: command error: {text}"
                )
            return text

        raise RuntimeError(f"{self._executable_name}: timeout waiting for response")

    def stop(self, timeout: float = 5.0) -> None:
        """Send QUIT and terminate the runner process."""
        if self._process is None:
            return

        try:
            if self._process.stdin is not None and self._process.poll() is None:
                self._process.stdin.write("QUIT\n")
                self._process.stdin.flush()
        except OSError:
            pass

        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.communicate(timeout=timeout)

        if self._stderr_thread is not None:
            self._stderr_thread.join(timeout=1.0)

        self._process = None
        self._stderr_thread = None


def _resolve_executable(name: str) -> Path:
    """Resolve a native runner executable path.

    Respects ``WHALE_NATIVE_RUNNER_DIR`` env var override, otherwise
    looks in the CMake build directory.
    """
    env_dir = os.environ.get("WHALE_NATIVE_RUNNER_DIR")
    if env_dir:
        base = Path(env_dir).expanduser().resolve()
    else:
        base = _NATIVE_BUILD_DIR
    return base / name
