"""Public exports for the worker-local source polling kernel.

This package contains protocol-agnostic scheduling primitives used by
SourceRuntime/worker layers to run high-frequency source polling inside one
worker process and one asyncio event loop. It is not a general-purpose
scheduler and it is not a replacement for APScheduler.

Typical layering:
- APScheduler or another low-frequency orchestrator manages runtime lifecycle;
- runtime/supervisor layers shard sources across workers or processes;
- each worker uses this package for local staggering, concurrency limiting,
  and fixed-rate polling execution.
"""

from pacific.whale.shared.source.scheduling.concurrency import ConcurrencySnapshot, ReadConcurrencyLimiter
from pacific.whale.shared.source.scheduling.polling import (
    PollingErrorEvent,
    PollingJobSpec,
    PollingJobStats,
    PollingResultEvent,
    PollingTickDiagnostics,
    SourcePollingScheduler,
)
from pacific.whale.shared.source.scheduling.stagger import (
    StaggerAssignment,
    assign_even_stagger,
    build_even_stagger_offsets,
    build_stagger_assignments,
)

__all__ = [
    "ConcurrencySnapshot",
    "ReadConcurrencyLimiter",
    "PollingErrorEvent",
    "PollingJobSpec",
    "PollingJobStats",
    "PollingResultEvent",
    "PollingTickDiagnostics",
    "SourcePollingScheduler",
    "StaggerAssignment",
    "assign_even_stagger",
    "build_even_stagger_offsets",
    "build_stagger_assignments",
]
