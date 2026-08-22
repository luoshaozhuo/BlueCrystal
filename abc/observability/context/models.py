"""Observation context domain models."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    runtime_id: str | None = None
    node_id: str | None = None


@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str | None = None
    actor: str | None = None


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    task_id: int | None = None
    connection_id: str | None = None


@dataclass(frozen=True, slots=True)
class TraceContext:
    force_sample: bool = False
    trace_tags: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ObservationContext:
    runtime: RuntimeContext = field(default_factory=RuntimeContext)
    request: RequestContext = field(default_factory=RequestContext)
    execution: ExecutionContext = field(default_factory=ExecutionContext)
    trace: TraceContext = field(default_factory=TraceContext)
