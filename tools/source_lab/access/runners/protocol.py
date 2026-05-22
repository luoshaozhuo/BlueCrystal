"""Shared stdout/stderr protocol diagnostics for native access runners."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import threading
from typing import IO

RUNNER_PROTOCOL_NOISE_KEEP = 5
RUNNER_PROTOCOL_NOISE_LIMIT = 10
RUNNER_STDERR_KEEP = 10


@dataclass(slots=True)
class ProtocolDiagnostics:
    """Collect stdout noise and stderr summaries for runner failures."""

    stdout_noise_count: int = 0
    stdout_noise_samples: deque[str] = field(
        default_factory=lambda: deque(maxlen=RUNNER_PROTOCOL_NOISE_KEEP),
        repr=False,
    )
    stderr_samples: deque[str] = field(
        default_factory=lambda: deque(maxlen=RUNNER_STDERR_KEEP),
        repr=False,
    )

    def record_stdout_noise(self, line: str) -> None:
        """Record one unexpected stdout line from the runner."""

        self.stdout_noise_count += 1
        if len(self.stdout_noise_samples) < RUNNER_PROTOCOL_NOISE_KEEP:
            self.stdout_noise_samples.append(line)

    def record_stderr(self, line: str) -> None:
        """Record one stderr line from the runner."""

        text = line.strip()
        if text:
            self.stderr_samples.append(text)

    def render_context(self) -> str:
        """Render a compact human-readable diagnostics suffix."""

        details: list[str] = []
        if self.stdout_noise_count > 0:
            details.append(
                "stdout_noise="
                f"{self.stdout_noise_count} samples={list(self.stdout_noise_samples)!r}"
            )
        if self.stderr_samples:
            details.append(f"stderr_tail={list(self.stderr_samples)!r}")
        return "" if not details else f" ({'; '.join(details)})"


def read_protocol_line(
    stream: IO[str],
    *,
    allowed_prefixes: tuple[str, ...],
    error_prefix: str,
    diagnostics: ProtocolDiagnostics,
    label: str,
) -> str:
    """Read one protocol line and reject unexpected stdout noise."""

    while True:
        line = stream.readline()
        if line == "":
            raise RuntimeError(
                f"{label} exited while waiting for {allowed_prefixes!r}"
                f"{diagnostics.render_context()}"
            )
        text = line.strip()
        if text.startswith(error_prefix):
            raise RuntimeError(
                f"{label} protocol error: {text}{diagnostics.render_context()}"
            )
        if any(text.startswith(prefix) for prefix in allowed_prefixes):
            return text
        if not text:
            continue
        diagnostics.record_stdout_noise(text)
        if diagnostics.stdout_noise_count > RUNNER_PROTOCOL_NOISE_LIMIT:
            raise RuntimeError(
                f"{label} emitted too much non-protocol stdout noise"
                f"{diagnostics.render_context()}"
            )


def drain_stderr(stream: IO[str] | None, diagnostics: ProtocolDiagnostics) -> None:
    """Drain stderr into diagnostics without affecting stdout protocol parsing."""

    if stream is None:
        return
    for line in stream:
        diagnostics.record_stderr(line)


def start_stderr_drain_thread(
    stream: IO[str] | None,
    diagnostics: ProtocolDiagnostics,
) -> threading.Thread:
    """Start a daemon thread that drains stderr into diagnostics."""

    thread = threading.Thread(
        target=drain_stderr,
        args=(stream, diagnostics),
        daemon=True,
    )
    thread.start()
    return thread
