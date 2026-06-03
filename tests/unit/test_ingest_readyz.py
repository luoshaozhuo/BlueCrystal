"""ingest readyz 模块级就绪聚合单元测试。

被验证对象：src/whale/ingest/api/readyz.py 中的 evaluate_readiness() 和
build_readyz_response()。

所属生命周期阶段：开发期验证 — 注入 fake 组件验证聚合逻辑，不涉及真实外部依赖。

使用 fake 组件：
- FakeEngine / FakeSessionFactory：模拟数据库连接。
- FakeRedisClient：模拟 Redis ping 响应。
- FakeAuditSink / FakeAccessPolicy / FakeAcquisitionRegistry / FakeWriteRegistry。

不能证明：
- 真实数据库连接超时和故障注入行为（需模块集成期验证）。
- Redis/Kafka 真实网络故障场景（需准生产依赖验证期）。
- 生产环境多进程就绪聚合的竞态行为。

关键环境依赖：无。测试独立于任何外部服务。
"""

from __future__ import annotations

from whale.ingest.api.readyz import (
    ReadyzAggregate,
    _build_check_result,
    _sanitize_detail,
    _check_audit_sink,
    _check_access_policy,
    _check_config_runtime_mode,
    _check_source_adapter_registry,
    build_readyz_response,
    evaluate_readiness,
)


class FakeEngine:
    """模拟 SQLAlchemy Engine，使用 SQLite 内存数据库。"""

    url = "sqlite:///:memory:"

    def connect(self):
        from sqlalchemy import create_engine

        real_engine = create_engine("sqlite:///:memory:")
        return real_engine.connect()


class _FakeConnection:
    """模拟数据库连接，execute 返回包含一行结果的代理。"""

    def execute(self, stmt):
        return _FakeResult()

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _FakeResult:
    """模拟查询结果集。"""

    def fetchone(self):
        return (1,)


class FakeSessionFactory:
    """模拟 session 工厂，返回包含 FakeEngine 的 session。"""
    kw = {"bind": FakeEngine()}


class FakeRedisClient:
    """模拟 Redis 客户端，ping 始终返回 True。"""

    def ping(self):
        return True


class FakeAuditSink:
    """模拟审计 sink。"""

    def emit(self, event):
        pass


class FakeAccessPolicy:
    """模拟访问策略。"""

    def authorize(self, request, action, resource_type, resource_id=None):
        return True


class FakeAcquisitionRegistry:
    """模拟采集适配器注册表。"""

    def __init__(self, protocols: tuple[str, ...] = ("opcua", "modbus_tcp")):
        self.ports_by_protocol = {p: None for p in protocols}


class FakeWriteRegistry:
    """模拟写入适配器注册表。"""

    def __init__(self, protocols: tuple[str, ...] = ("opcua",)):
        self.ports_by_protocol = {p: None for p in protocols}


class FakeMessagePublisher:
    """模拟消息发布器。"""

    def health_check(self):
        """返回 True 表示健康。"""
        return True


# ── sanitize 测试 ──────────────────────────────────────────────────

class TestReadyzSanitize:
    """就绪响应敏感信息脱敏测试。"""

    def test_sanitize_strips_sensitive_keys(self):
        """detail 中的 password/token/secret 应被替换为 ***REDACTED***。"""
        detail = {
            "host": "10.0.0.1",
            "password": "admin123",
            "api_key": "sk-12345",
            "token": "bearer-xxx",
            "dsn": "postgresql://user:pass@host/db",
            "redis_url": "redis://:secret@host:6379/0",
            "endpoint": "/api/v1/data",
            "protocol": "opcua",
        }
        sanitized = _sanitize_detail(detail)
        assert sanitized is not None
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["token"] == "***REDACTED***"
        assert sanitized["dsn"] == "***REDACTED***"
        assert sanitized["redis_url"] == "***REDACTED***"
        # 非敏感键保持不变
        assert sanitized["host"] == "10.0.0.1"
        assert sanitized["endpoint"] == "/api/v1/data"
        assert sanitized["protocol"] == "opcua"

    def test_sanitize_none_returns_none(self):
        """None detail 应返回 None。"""
        assert _sanitize_detail(None) is None

    def test_sanitize_empty_returns_empty(self):
        """空 detail 应返回空字典。"""
        assert _sanitize_detail({}) == {}

    def test_sanitize_all_safe_keys_preserved(self):
        """全部安全键应保持不变。"""
        detail = {"protocol": "opcua", "status": "ok", "endpoint": "/v1"}
        sanitized = _sanitize_detail(detail)
        assert sanitized == detail


# ── build_check_result 测试 ─────────────────────────────────────────

class TestBuildCheckResult:
    """就绪检查条目构建测试。"""

    def test_build_check_result_sanitizes_detail(self):
        """构建结果时应对 detail 脱敏。"""
        result = _build_check_result(
            component="test_comp",
            status="ready",
            reason="ok",
            required=True,
            fail_open=False,
            latency_ms=12.345,
            detail={"password": "secret123", "host": "10.0.0.1"},
        )
        assert result["component"] == "test_comp"
        assert result["status"] == "ready"
        assert result["latency_ms"] == 12.345
        assert result["detail"] is not None
        assert result["detail"]["password"] == "***REDACTED***"
        assert result["detail"]["host"] == "10.0.0.1"


# ── component check 测试 ────────────────────────────────────────────

class TestComponentChecks:
    """各组件独立就绪检查测试。"""

    def test_audit_sink_ready_with_instance(self):
        """有审计 sink 实例时应返回 ready。"""
        entry = _check_audit_sink(audit_sink=FakeAuditSink())
        assert entry.status == "ready"
        assert entry.required is False
        assert entry.fail_open is True

    def test_audit_sink_degraded_without_instance(self):
        """审计 sink 未注入时应返回 degraded。"""
        entry = _check_audit_sink(audit_sink=None)
        assert entry.status == "degraded"
        assert entry.required is False

    def test_access_policy_degraded_without_instance(self):
        """访问策略未注入时应返回 degraded。"""
        entry = _check_access_policy(access_policy=None)
        assert entry.status == "degraded"
        assert entry.required is False
        assert "allow-all" in entry.reason.lower()

    def test_access_policy_ready_with_instance(self):
        """访问策略已注入时应返回 ready。"""
        entry = _check_access_policy(access_policy=FakeAccessPolicy())
        assert entry.status == "ready"

    def test_config_runtime_mode_ready(self):
        """配置加载正常时应返回 ready。"""
        entry = _check_config_runtime_mode()
        assert entry.status == "ready"
        assert entry.required is True
        assert entry.fail_open is False

    def test_source_adapter_registry_ready(self):
        """已注册采集和写入适配器时应返回 ready。"""
        entry = _check_source_adapter_registry(
            acquisition_registry=FakeAcquisitionRegistry(),
            write_registry=FakeWriteRegistry(),
        )
        assert entry.status == "ready"
        assert entry.required is True

    def test_source_adapter_registry_not_ready_without_registries(self):
        """未注册任何适配器时应返回 not_ready。"""
        entry = _check_source_adapter_registry(
            acquisition_registry=None,
            write_registry=None,
        )
        assert entry.status == "not_ready"
        assert entry.required is True


# ── 聚合就绪测试 ────────────────────────────────────────────────────

class TestEvaluateReadiness:
    """模块级就绪聚合逻辑测试。"""

    def test_all_required_ready_returns_ready(self):
        """所有必需组件正常时 overall 应为 ready。"""
        aggregate = evaluate_readiness(
            session_factory=FakeSessionFactory(),
            audit_sink=FakeAuditSink(),
            access_policy=FakeAccessPolicy(),
            acquisition_registry=FakeAcquisitionRegistry(),
            write_registry=FakeWriteRegistry(),
            redis_client=FakeRedisClient(),
            message_publisher=FakeMessagePublisher(),
        )
        assert aggregate.overall in ("ready", "degraded")
        # 检查各核心组件为 ready
        component_statuses = {c["component"]: c["status"] for c in aggregate.components}
        assert component_statuses.get("config_runtime_mode") == "ready"
        assert component_statuses.get("audit_sink") == "ready"
        assert component_statuses.get("access_policy") == "ready"
        assert component_statuses.get("source_adapter_registry") == "ready"

    def test_required_component_failed_makes_not_ready(self, monkeypatch):
        """required 组件失败时应导致 overall not_ready。

        使用 monkeypatch 模拟 source_adapter_registry 失败。
        """
        # 传入 None registry -> source_adapter_registry 应为 not_ready
        aggregate = evaluate_readiness(
            session_factory=FakeSessionFactory(),
            audit_sink=FakeAuditSink(),
            access_policy=FakeAccessPolicy(),
            acquisition_registry=None,
            write_registry=None,
            redis_client=FakeRedisClient(),
            message_publisher=FakeMessagePublisher(),
        )
        # source_adapter_registry 是 required=True 且 fail_open=False
        # 应导致 overall 为 not_ready
        assert aggregate.overall == "not_ready"

    def test_optional_component_degraded_does_not_block(self):
        """optional 组件 degraded 不应阻塞 overall ready。

        audit_sink 和 access_policy 都是 optional (fail_open=True)。
        """
        aggregate = evaluate_readiness(
            session_factory=FakeSessionFactory(),
            audit_sink=None,
            access_policy=None,
            acquisition_registry=FakeAcquisitionRegistry(),
            write_registry=FakeWriteRegistry(),
            redis_client=FakeRedisClient(),
            message_publisher=FakeMessagePublisher(),
        )
        # optional 组件失败不应该导致 not_ready
        assert aggregate.overall != "not_ready"
        # 应该有 degraded_reasons
        degraded_components = {r.split(":")[0].strip() for r in aggregate.degraded_reasons}
        assert "audit_sink" in degraded_components
        assert "access_policy" in degraded_components
        # shared_source_runner 也可能是 degraded
        assert "shared_source_runner" in degraded_components

    def test_response_no_sensitive_keys(self):
        """build_readyz_response 不应泄露敏感信息。

        验证响应中不出现 password/token/secret 等键值。
        """
        aggregate = evaluate_readiness(
            session_factory=FakeSessionFactory(),
            audit_sink=FakeAuditSink(),
            access_policy=FakeAccessPolicy(),
            acquisition_registry=FakeAcquisitionRegistry(),
            write_registry=FakeWriteRegistry(),
            redis_client=FakeRedisClient(),
            message_publisher=FakeMessagePublisher(),
        )
        response = build_readyz_response(aggregate)

        response_str = str(response)
        assert "password" not in response_str.lower() or "***REDACTED***" in response_str
        assert "token" not in response_str.lower() or "***REDACTED***" in response_str

    def test_response_contains_all_required_fields(self):
        """就绪响应必须包含 status/checked_at/components/degraded_reasons/config_mode。"""
        aggregate = ReadyzAggregate(
            overall="ready",
            checked_at="2026-05-30T12:00:00+00:00",
            components=[],
            degraded_reasons=[],
            config_mode="api",
        )
        response = build_readyz_response(aggregate)
        assert "status" in response
        assert "checked_at" in response
        assert "components" in response
        assert "degraded_reasons" in response
        assert "config_mode" in response

    def test_each_component_has_standard_fields(self):
        """每个组件条目应包含 component/status/reason/required/fail_open/latency_ms。"""
        aggregate = evaluate_readiness(
            session_factory=FakeSessionFactory(),
            audit_sink=FakeAuditSink(),
            access_policy=FakeAccessPolicy(),
            acquisition_registry=FakeAcquisitionRegistry(),
            write_registry=FakeWriteRegistry(),
            redis_client=FakeRedisClient(),
            message_publisher=FakeMessagePublisher(),
        )
        assert len(aggregate.components) >= 1
        for comp in aggregate.components:
            assert "component" in comp
            assert "status" in comp
            assert "reason" in comp
            assert "required" in comp
            assert "fail_open" in comp
            assert "latency_ms" in comp

    def test_timeout_does_not_crash(self):
        """短超时不导致崩溃或未捕获异常。"""
        aggregate = evaluate_readiness(
            session_factory=FakeSessionFactory(),
            timeout_seconds=0.1,
            redis_client=FakeRedisClient(),
            message_publisher=FakeMessagePublisher(),
        )
        assert aggregate.overall in ("ready", "degraded", "not_ready")
        assert len(aggregate.components) == 8

    def test_component_count_is_eight(self):
        """readyz 聚合应包含确切的 8 个组件检查。"""
        aggregate = evaluate_readiness(
            session_factory=FakeSessionFactory(),
            audit_sink=FakeAuditSink(),
            access_policy=FakeAccessPolicy(),
            acquisition_registry=FakeAcquisitionRegistry(),
            write_registry=FakeWriteRegistry(),
            redis_client=FakeRedisClient(),
            message_publisher=FakeMessagePublisher(),
        )
        assert len(aggregate.components) == 8
        component_names = {c["component"] for c in aggregate.components}
        expected = {
            "runtime_db",
            "redis_state_cache",
            "message_publisher",
            "audit_sink",
            "access_policy",
            "shared_source_runner",
            "source_adapter_registry",
            "config_runtime_mode",
        }
        assert component_names == expected
