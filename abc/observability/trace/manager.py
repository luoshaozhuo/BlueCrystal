"""Trace 创建、异常记录与代表性错误 Trace 管理。"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode

from ..shared import bind_observation_context
from .dedup import ErrorTraceDeduplicator
from .fingerprint import make_error_fingerprint
from .policy import TracePolicy


class TraceManager:
    """封装业务侧常用 Trace 操作和错误去重策略。"""

    def __init__(self, policy: TracePolicy) -> None:
        self.policy = policy
        self._tracer = trace.get_tracer(__name__)
        self._errors = ErrorTraceDeduplicator(
            ttl_seconds=policy.error_dedup_ttl_seconds,
            max_entries=policy.error_dedup_max_entries,
        )

    @contextmanager
    def span(
        self,
        name: str,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> Iterator[Span]:
        """创建并进入一个 Span 上下文。"""
        with self._tracer.start_as_current_span(
            name,
            attributes=attributes,
        ) as span:
            yield span

    def record_exception(self, span: Span, exc: BaseException) -> None:
        """在记录中的 Span 上登记异常并标记错误状态。"""
        if span.is_recording():
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))

    def representative_error(
        self,
        exc: BaseException,
        *,
        operation: str,
    ) -> bool:
        """为未被采样的错误按指纹生成代表性 Trace。

        Returns:
            本次是否实际生成代表性错误 Trace。
        """
        fingerprint = make_error_fingerprint(exc, operation=operation)
        if not self._errors.should_trace(fingerprint):
            return False

        with bind_observation_context(force_trace=True):
            with self._tracer.start_as_current_span(
                "diagnostic.error",
                attributes={
                    "bluecrystal.operation": operation,
                    "bluecrystal.error.fingerprint": fingerprint,
                },
            ) as span:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
        return True
