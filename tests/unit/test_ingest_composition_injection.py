"""QA-1: composition.py 注入完整性测试。

验证 build_source_write_composition 正确将 audit_sink、metrics_sink、write_lease_port
注入到 SourceCommandUseCase。现有测试绕过 composition 直接构造 use case，
无法发现注入缺失问题。
"""

from __future__ import annotations

import logging

from whale.ingest.composition import build_source_write_composition
from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase
from whale.shared.crosscutting.compliance import AuditEvent, AuditEventSinkPort
from whale.shared.crosscutting.observability import MetricsSinkPort


class _TrackingAuditSink(AuditEventSinkPort):
    """记录 emit 次数的测试用 audit sink。"""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def emit(self, event: AuditEvent) -> None:
        self.events.append(event)


class _TrackingMetricsSink(MetricsSinkPort):
    """记录 increment/observe_duration 次数的测试用 metrics sink。"""

    def __init__(self) -> None:
        self.metric_names: list[str] = []

    def increment(self, metric_name: str, value: int = 1, **labels: str) -> None:
        self.metric_names.append(metric_name)

    def observe_duration(
        self,
        metric_name: str,
        duration_seconds: float,
        **labels: str,
    ) -> None:
        self.metric_names.append(metric_name)


def test_composition_provides_audit_sink_when_injected() -> None:
    """注入 audit_sink 后，SourceCommandUseCase 的 _audit_port 不为 None。"""
    audit_sink = _TrackingAuditSink()
    composition = build_source_write_composition(
        audit_sink=audit_sink,
        logger=logging.getLogger(__name__),
    )
    use_case = composition.command_use_case
    # 通过检查内部属性确认注入成功
    assert use_case._audit_port is audit_sink


def test_composition_provides_metrics_sink_when_injected() -> None:
    """注入 metrics_sink 后，SourceCommandUseCase 的 _metrics_port 不为 None。"""
    metrics_sink = _TrackingMetricsSink()
    composition = build_source_write_composition(
        metrics_sink=metrics_sink,
        logger=logging.getLogger(__name__),
    )
    use_case = composition.command_use_case
    assert use_case._metrics_port is metrics_sink


def test_composition_provides_write_lease_port_when_injected() -> None:
    """注入 write_lease_port 后，SourceCommandUseCase 的 _write_lease_port 不为 None。"""
    from whale.ingest.ports.runtime.write_lease_port import WriteLeasePort

    class _FakeWriteLeasePort(WriteLeasePort):
        def acquire(self, **kwargs):
            from whale.ingest.ports.runtime.write_lease_port import WriteLeaseDecisionData
            return WriteLeaseDecisionData(
                allowed=True, result="ALLOW", reason_code=None, fencing_token=1,
            )
        def renew(self, **kwargs):
            from whale.ingest.ports.runtime.write_lease_port import WriteLeaseDecisionData
            return WriteLeaseDecisionData(
                allowed=True, result="ALLOW", reason_code=None, fencing_token=1,
            )
        def validate(self, **kwargs):
            from whale.ingest.ports.runtime.write_lease_port import WriteLeaseDecisionData
            return WriteLeaseDecisionData(
                allowed=True, result="ALLOW", reason_code=None, fencing_token=1,
            )
        def release(self, **kwargs):
            pass

    lease_port = _FakeWriteLeasePort()
    composition = build_source_write_composition(
        write_lease_port=lease_port,
        logger=logging.getLogger(__name__),
    )
    use_case = composition.command_use_case
    assert use_case._write_lease_port is lease_port


def test_composition_defaults_to_no_ports() -> None:
    """不注入时 audit/metrics/write_lease_port 均为 None，向后兼容。"""
    composition = build_source_write_composition()
    use_case = composition.command_use_case
    assert isinstance(use_case, SourceCommandUseCase)
    # 默认不注入时，三个 port 都是 None
    assert use_case._audit_port is None
    assert use_case._metrics_port is None
    assert use_case._write_lease_port is None
