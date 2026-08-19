from __future__ import annotations
from contextlib import contextmanager
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from ..shared import bind_observation_context
from .dedup import ErrorTraceDeduplicator
from .fingerprint import make_error_fingerprint
from .policy import TracePolicy
class TraceManager:
    def __init__(self,policy:TracePolicy):
        self.policy=policy; self._tracer=trace.get_tracer(__name__); self._errors=ErrorTraceDeduplicator(ttl_seconds=policy.error_dedup_ttl_seconds,max_entries=policy.error_dedup_max_entries)
    @contextmanager
    def span(self,name:str,*,attributes:dict[str,object]|None=None):
        with self._tracer.start_as_current_span(name,attributes=attributes) as span: yield span
    def record_exception(self,span,exc:BaseException):
        if span.is_recording(): span.record_exception(exc); span.set_status(Status(StatusCode.ERROR,str(exc)))
    def representative_error(self,exc:BaseException,*,operation:str)->bool:
        fp=make_error_fingerprint(exc,operation=operation)
        if not self._errors.should_trace(fp): return False
        with bind_observation_context(force_trace=True):
            with self._tracer.start_as_current_span("diagnostic.error",attributes={"bluecrystal.operation":operation,"bluecrystal.error.fingerprint":fp}) as span:
                span.record_exception(exc); span.set_status(Status(StatusCode.ERROR,str(exc)))
        return True
