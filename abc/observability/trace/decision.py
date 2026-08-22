"""Trace sampling decision context."""

from dataclasses import dataclass, field
from contextvars import ContextVar


@dataclass(frozen=True, slots=True)
class TraceDecisionContext:
    force_sample: bool = False
    trace_tags: dict[str, str] = field(default_factory=dict)


_trace_decision_var = ContextVar(
    "trace_decision_context",
    default=TraceDecisionContext(),
)


def get_trace_decision_context() -> TraceDecisionContext:
    return _trace_decision_var.get()
