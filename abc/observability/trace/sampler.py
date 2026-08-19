from __future__ import annotations
from opentelemetry import trace
from opentelemetry.sdk.trace.sampling import Decision, Sampler, SamplingResult, TraceIdRatioBased
from ..shared import get_observation_context
from .policy import TracePolicy
class BlueCrystalSampler(Sampler):
    """指定 task/connection 或 force_trace 强制采样，其余按概率。"""
    def __init__(self,policy:TracePolicy): self._policy=policy; self._ratio=TraceIdRatioBased(policy.normal_sample_rate)
    def should_sample(self,parent_context,trace_id:int,name:str,kind=None,attributes=None,links=None,trace_state=None):
        if not self._policy.enabled: return SamplingResult(Decision.DROP)
        ctx=get_observation_context()
        if ctx.force_trace or ctx.task_id in self._policy.traced_task_ids or (ctx.connection_id is not None and ctx.connection_id in self._policy.traced_connection_ids):
            return SamplingResult(Decision.RECORD_AND_SAMPLE,trace_state=trace_state)
        if parent_context is not None:
            parent=trace.get_current_span(parent_context).get_span_context()
            if parent.is_valid and parent.trace_flags.sampled:
                return SamplingResult(Decision.RECORD_AND_SAMPLE,trace_state=parent.trace_state)
        return self._ratio.should_sample(parent_context,trace_id,name,kind,attributes,links,trace_state)
    def get_description(self)->str: return f"BlueCrystalSampler(rate={self._policy.normal_sample_rate})"
