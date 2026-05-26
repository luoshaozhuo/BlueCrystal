"""Native C executable capacity runner — delegates timing loop to the C process.

The C executable handles the full timing loop internally. Python manages process
lifecycle and parses the stdout protocol: READY / SAMPLE / BATCH / SUMMARY / DONE / ERROR.
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from tools.source_lab.access.polling.metrics import WorkerRawStats
from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.runners.base import CapacityRunner
from tools.source_lab.access.runners.native_process import stop_native_process
from tools.source_lab.access.runners.protocol import (
    ProtocolDiagnostics,
    start_stderr_drain_thread,
)


class NativeRunnerUnavailableError(RuntimeError):
    """Native C executable not found or not executable.

    Attributes:
        protocol: Protocol identifier (e.g. "iec61850_mms").
        runner_name: Executable name (e.g. "iec61850_mms_client_runner").
        expected_path: Path where the binary was expected.
        build_hint: Suggested build command.
    """

    def __init__(
        self,
        protocol: str,
        runner_name: str,
        expected_path: str,
        build_hint: str = "",
    ) -> None:
        self.protocol = protocol
        self.runner_name = runner_name
        self.expected_path = expected_path
        self.build_hint = build_hint
        msg = (
            f"Native capacity runner '{runner_name}' for protocol '{protocol}' "
            f"is not available: executable not found at '{expected_path}'. "
            f"{build_hint}"
        )
        super().__init__(msg)


@dataclass
class _NativeSession:
    """Accumulated results from one native runner session."""
    total_reads: int = 0
    ok_reads: int = 0
    read_errors: int = 0
    noise_count: int = 0
    noise_samples: tuple[str, ...] = ()
    response_timestamps: list[float] = field(default_factory=list)
    value_count: int = 0


def _find_executable(name: str) -> Path | None:
    root = Path(__file__).resolve().parents[2] / "native" / "build"
    for candidate in (
        root / name,
        root / "bin" / name,
        root / "Release" / name,
    ):
        if candidate.exists():
            return candidate
    return None


def _read_output_lines(
    proc: subprocess.Popen[str],
    session: _NativeSession,
    diagnostics: ProtocolDiagnostics,
) -> None:
    """Read and parse stdout lines from a native C runner process."""
    if proc.stdout is None:
        return
    for raw_line in proc.stdout:
        stripped = raw_line.rstrip("\n\r")
        if not stripped:
            continue
        if stripped == "READY":
            continue
        if stripped.startswith("SAMPLE"):
            session.total_reads += 1
            session.ok_reads += 1
            session.response_timestamps.append(time.time())
            continue
        if stripped.startswith("BATCH"):
            continue
        if stripped.startswith("SUMMARY"):
            parts = stripped.split("\t")
            if len(parts) >= 4:
                try:
                    session.value_count = int(parts[3])
                except (ValueError, IndexError):
                    pass
            continue
        if stripped == "DONE":
            break
        if stripped.startswith("ERROR"):
            session.read_errors += 1
            diagnostics.record_stderr(stripped)
            continue
        # Non-protocol noise
        session.noise_count += 1
        if session.noise_count <= 5:
            session.noise_samples = session.noise_samples + (stripped,)


class NativeCmdCapacityRunner(CapacityRunner):
    """Capacity runner that delegates the full polling loop to a native C executable.

    Subclasses must set ``executable_name`` and implement ``build_command``.
    """

    name: str = "native_cmd_runner"
    executable_name: str = ""

    def check_available(self) -> None:
        """Check native executable is available (exists and executable).

        Raises ``NativeRunnerUnavailableError`` with clear context if unavailable.
        """
        exe = _find_executable(self.executable_name)
        if exe is not None and exe.exists():
            if os.access(exe, os.X_OK):
                return
            path_str = str(exe)
        else:
            root = Path(__file__).resolve().parents[2] / "native" / "build"
            path_str = str(root / self.executable_name)

        protocol = (
            self.executable_name.replace("_polling_runner", "")
            .replace("_client_runner", "")
            .replace("_event_runner", "")
            .replace("_subscriber_runner", "")
        )
        raise NativeRunnerUnavailableError(
            protocol=protocol,
            runner_name=self.executable_name,
            expected_path=path_str,
            build_hint=(
                "Run 'cmake --build tools/source_lab/native/build' "
                "to compile native runners."
            ),
        )

    def _resolve_exe(self) -> Path:
        exe = _find_executable(self.executable_name)
        if exe is not None and exe.exists():
            return exe
        raise RuntimeError(
            f"native executable '{self.executable_name}' not found — "
            "dependency missing or not compiled"
        )

    def build_command(
        self,
        worker_index: int,
        specs: tuple,  # tuple[RunnerEndpointPlan, ...]
        target_hz: float,
        config: CapacityScanConfig,
    ) -> list[str]:
        """Build CLI command list. Override in subclasses."""
        raise NotImplementedError

    def run_worker(
        self,
        worker_index: int,
        specs: tuple,  # tuple[RunnerEndpointPlan, ...]
        target_hz: float,
        config: CapacityScanConfig,
    ) -> WorkerRawStats:
        exe_path = self._resolve_exe()
        cmd = self.build_command(worker_index, specs, target_hz, config)
        diagnostics = ProtocolDiagnostics()

        try:
            proc = subprocess.Popen(
                [str(a) for a in cmd],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
        except Exception as exc:
            raise RuntimeError(f"failed to start {self.executable_name}: {exc}") from exc

        stderr_thread = start_stderr_drain_thread(proc.stderr, diagnostics)
        session = _NativeSession()
        started_at = time.monotonic()

        try:
            _read_output_lines(proc, session, diagnostics)
        finally:
            stop_native_process(proc)
            elapsed = time.monotonic() - started_at

        return WorkerRawStats(
            worker_index=worker_index,
            reader_count=len(specs),
            batch_mismatches=0,
            read_errors=session.read_errors,
            missing_response_timestamps=0,
            response_timestamps_by_reader=(
                tuple(session.response_timestamps) if session.response_timestamps else (),
            ),
            max_observed_concurrent_reads=1,
            total_reads=session.total_reads,
            ok_reads=session.ok_reads,
            value_count=session.value_count if session.value_count > 0 else session.ok_reads,
            runner_protocol_noise_count=session.noise_count,
            runner_protocol_noise_samples=session.noise_samples,
        )
