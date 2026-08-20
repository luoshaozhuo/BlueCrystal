"""BlueCrystal OpenTelemetry 自定义采样器。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.sdk.trace.sampling import (
    Decision,
    Sampler,
    SamplingResult,
    TraceIdRatioBased,
)
from opentelemetry.trace import Link, SpanKind, TraceState

from ..shared import get_observation_context
from .policy import TracePolicy


class BlueCrystalSampler(Sampler):
    """定向对象和 `force_trace` 强制采样，其余按概率采样。"""

    def __init__(self, policy: TracePolicy) -> None:
        self._policy = policy
        self._ratio = TraceIdRatioBased(policy.normal_sample_rate)

    def should_sample(
        self,
        parent_context: Context | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Mapping[str, object] | None = None,
        links: Sequence[Link] | None = None,
        trace_state: TraceState | None = None,
    ) -> SamplingResult:
        """按关联上下文和父 Span 状态确定采样决策。"""
        if not self._policy.enabled:
            return SamplingResult(Decision.DROP)

        context = get_observation_context()
        should_force_trace = (
            context.force_trace
            or context.task_id in self._policy.traced_task_ids
            or (
                context.connection_id is not None
                and context.connection_id
                in self._policy.traced_connection_ids
            )
        )
        if should_force_trace:
            return SamplingResult(
                Decision.RECORD_AND_SAMPLE,
                trace_state=trace_state,
            )

        if parent_context is not None:
            parent = trace.get_current_span(parent_context).get_span_context()
            if parent.is_valid and parent.trace_flags.sampled:
                return SamplingResult(
                    Decision.RECORD_AND_SAMPLE,
                    trace_state=parent.trace_state,
                )

        return self._ratio.should_sample(
            parent_context,
            trace_id,
            name,
            kind,
            attributes,
            links,
            trace_state,
        )

    def get_description(self) -> str:
        """返回采样器描述。"""
        return f"BlueCrystalSampler(rate={self._policy.normal_sample_rate})"
