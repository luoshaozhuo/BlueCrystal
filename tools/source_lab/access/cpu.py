"""CPU and RSS sampling utilities used only for field capacity reporting."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import threading
import time


@dataclass(frozen=True, slots=True)
class CpuSampleSummary:
    """Aggregate CPU and memory usage statistics for one scan window."""

    cpu_mean_pct: float
    cpu_max_pct: float
    cpu_p95_pct: float
    rss_mb: float
    warning: str = ""


def _percentile(values: list[float], percentile: float) -> float:
    """Return a simple percentile from a non-empty list."""

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = round((len(ordered) - 1) * percentile)
    return ordered[index]


def _safe_mean(values: Iterable[float]) -> float:
    """Return the arithmetic mean or ``0.0`` for an empty iterable."""

    seq = list(values)
    return sum(seq) / len(seq) if seq else 0.0


class CpuSampler:
    """Background CPU sampler for the current Python process tree."""

    def __init__(self, *, interval_s: float = 1.0) -> None:
        """Initialize the sampler.

        Args:
            interval_s: Sampling interval in seconds.
        """

        self._interval_s = interval_s
        self._cpu_samples: list[float] = []
        self._rss_samples_mb: list[float] = []
        self._warning = ""
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start background sampling."""

        try:
            import psutil  # type: ignore[import-not-found, import-untyped]
        except ImportError:
            self._warning = "psutil_not_installed"
            return

        process = psutil.Process()
        process.cpu_percent(interval=None)
        for child in process.children(recursive=True):
            child.cpu_percent(interval=None)

        def _sample_loop() -> None:
            while not self._stop_event.wait(self._interval_s):
                try:
                    processes = [process, *process.children(recursive=True)]
                    cpu_pct = sum(item.cpu_percent(interval=None) for item in processes if item.is_running())
                    rss_mb = sum(item.memory_info().rss for item in processes if item.is_running()) / (1024**2)
                    self._cpu_samples.append(cpu_pct)
                    self._rss_samples_mb.append(rss_mb)
                except Exception as exc:  # pragma: no cover - defensive reporting path
                    self._warning = f"cpu_sampling_failed:{type(exc).__name__}"
                    return

        self._thread = threading.Thread(target=_sample_loop, name="source-lab-cpu-sampler", daemon=True)
        self._thread.start()

    def stop(self) -> CpuSampleSummary:
        """Stop sampling and return aggregate statistics."""

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._interval_s + 1.0)
        return CpuSampleSummary(
            cpu_mean_pct=_safe_mean(self._cpu_samples),
            cpu_max_pct=max(self._cpu_samples, default=0.0),
            cpu_p95_pct=_percentile(self._cpu_samples, 0.95) if self._cpu_samples else 0.0,
            rss_mb=max(self._rss_samples_mb, default=0.0),
            warning=self._warning,
        )
