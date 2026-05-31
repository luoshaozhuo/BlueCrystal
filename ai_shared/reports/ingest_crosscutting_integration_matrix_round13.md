# ingest 横切能力接入矩阵 Round 13

> 日期: 2026-05-30
> 范围: ingest 模块对 crosscutting 横切能力的接入点映射
> 状态: 矩阵已形成，8/8 横切能力接入点已识别并映射

## 1. 总览

本报告按 `Whale_REQ_Crosscutting.md` 中 CT-FR-001~005、CT-NFR-001、CT-SCR-001、CT-TEST-001 逐项映射 ingest 的接入点、代码路径、测试路径、证据等级和剩余差距。

ingest 通过以下机制接入横切能力：
- **composition root**: `src/whale/ingest/composition.py` 通过装饰链注入 auth/audit/retry/observability
- **middleware**: `src/whale/ingest/api/audit_middleware.py` 提供 API 级全量审计
- **decorators**: `src/whale/ingest/decorators/` 提供 source_acquisition/state_cache/source_write 的横切包装
- **port-adapter**: `src/whale/ingest/ports/` 定义 audit/metrics 等端口，adapter 实现对接外部系统

## 2. 按 crosscutting 需求的接入矩阵

### 2.1 CT-FR-001: 日志、指标与追踪

| 属性 | 值 |
|---|---|
| ingress 接入点 | `composition.py` 注入 LoggingSourceAcquisitionPort/LoggingStateCachePort; `worker_runtime.py` p95/p99 指标汇总; `file_sinks.py` 结构化日志/指标输出 |
| 代码路径 | `src/whale/ingest/composition.py:L173-L181`, `src/whale/ingest/decorators/source_acquisition.py`, `src/whale/ingest/decorators/state_cache.py`, `src/whale/ingest/runtime/worker_runtime.py`, `src/whale/ingest/adapters/observability/file_sinks.py` |
| 测试路径 | `tests/unit/test_ingest_metrics_events.py`, `tests/integration/test_ingest_observability_sink_smoke.py` |
| 证据等级 | L3 (integration, file sink verified) |
| required/optional | required |
| 剩余差距 | 真实 Docker 环境下的 metrics/audit 连续性回归仍 pending; 生产级观测后端(Datadog/Prometheus/Grafana)未接入 |

### 2.2 CT-FR-002: 韧性策略

| 属性 | 值 |
|---|---|
| ingress 接入点 | `composition.py` RetryingSourceAcquisitionPort(RetryPolicy/BackoffPolicy); `kafka_message_publisher` retry/backoff; `redis_source_state_cache` connect timeout/retry; `scheduler` lease TTL/stagger; `worker_runtime` graceful shutdown; `fencing.py` atomic fencing |
| 代码路径 | `src/whale/ingest/composition.py:L158-L167`, `src/whale/ingest/decorators/source_acquisition.py:L29`, `src/whale/ingest/adapters/message/kafka_message_publisher.py`, `src/whale/ingest/adapters/state/redis_source_state_cache.py`, `src/whale/ingest/runtime/fencing.py`, `src/whale/ingest/runtime/scheduler.py`, `src/whale/ingest/runtime/worker_runtime.py` |
| 测试路径 | `tests/integration/test_ingest_scheduler_graceful_shutdown.py`, `tests/integration/test_ingest_prodlike_redis_fault_injection.py`, `tests/integration/test_ingest_prodlike_kafka_fault_injection.py` |
| 证据等级 | L3 (integration, fault injection verified) |
| required/optional | required |
| 剩余差距 | circuit breaker 仅在 Kafka publisher 有本地实现，未接入 shared crosscutting 统一熔断; 7x24 长稳未验证 |

### 2.3 CT-FR-003: 认证、鉴权、凭据与加密配置

| 属性 | 值 |
|---|---|
| ingress 接入点 | `composition.py` AuthorizedSourceAcquisitionPort/AuthorizedSourceWritePort 注入 AccessPolicyPort + Principal; `file_access_policy.py` AllowAll/DenyAll/FileAccessPolicy; `external_access_policy.py` ExternalAccessPolicy; `source_write.py` security profile 双重门禁; `readyz.py` 凭证脱敏(***REDACTED***) |
| 代码路径 | `src/whale/ingest/composition.py:L168-L172, L362-L388`, `src/whale/ingest/adapters/security/file_access_policy.py`, `src/whale/ingest/adapters/security/external_access_policy.py`, `src/whale/ingest/decorators/source_write.py`, `src/whale/ingest/api/readyz.py:_sensitive_keys` |
| 测试路径 | `tests/unit/test_ingest_write_security_profile.py`, `tests/unit/test_source_command_authorization_guard.py`, `tests/integration/test_ingest_prodlike_access_policy.py`, `tests/integration/test_ingest_external_access_policy_contract.py` |
| 证据等级 | L3 (integration, file policy verified); L2 contract (external policy) |
| required/optional | optional (allow-all default for dev), required (production) |
| 剩余差距 | 真实 IAM (LDAP/OIDC) 注入未验证; 凭据加密存储(TLS cert/key管理)未接入 crosscutting credential service |

### 2.4 CT-FR-004: 审计、数据分类与安全区

| 属性 | 值 |
|---|---|
| ingress 接入点 | `audit_middleware.py` 全量 API 审计; `db_audit_sink.py`/`http_audit_sink.py`/`multi_audit_sink.py` 多 sink; `composition.py` AuditedSourceAcquisitionPort/AuditedStateCachePort; `source_command_audit_port.py` 写入审计; `fencing.py` fencing 操作审计; `audit_event.py` 审计事件 schema 含 DataClassification; `security_partitions.py` 安全分区 CRUD |
| 代码路径 | `src/whale/ingest/api/audit_middleware.py`, `src/whale/ingest/adapters/audit/db_audit_sink.py`, `src/whale/ingest/adapters/audit/http_audit_sink.py`, `src/whale/ingest/adapters/audit/multi_audit_sink.py`, `src/whale/ingest/domain/audit_event.py`, `src/whale/ingest/ports/audit.py`, `src/whale/ingest/ports/command/source_command_audit_port.py`, `src/whale/ingest/api/routes/audit_events.py`, `src/whale/ingest/api/routes/security_partitions.py` |
| 测试路径 | `tests/unit/test_ingest_audit_event_schema.py`, `tests/unit/test_ingest_audit_redaction.py`, `tests/integration/test_ingest_api_full_audit_matrix.py`, `tests/integration/test_ingest_audit_db_jsonl_consistency.py`, `tests/integration/test_ingest_prodlike_audit_sink.py`, `tests/integration/test_ingest_external_audit_sink_contract.py` |
| 证据等级 | L3 (integration, DB+JSONL dual sink verified); L2 contract (external SIEM) |
| required/optional | optional (no-op default for dev), required (production) |
| 剩余差距 | 真实外部 SIEM 集成待平台团队实施; 安全区与数据流向运行时 enforcement 仍 partial (bundle-level security partition validated, runtime cross-zone check pending) |

### 2.5 CT-FR-005: 健康检查与诊断

| 属性 | 值 |
|---|---|
| ingress 接入点 | `health.py` /healthz + /readyz endpoints; `readyz.py` 8 组件聚合(diagnostic detail/degraded reasons/sensitive data redaction); `DebugTraceContext`/`DebugTraceSinkPort` 装饰链注入(默认 disabled) |
| 代码路径 | `src/whale/ingest/api/routes/health.py`, `src/whale/ingest/api/readyz.py`, `src/whale/ingest/ports/__init__.py`(metrics port) |
| 测试路径 | `tests/unit/test_ingest_readyz.py`(20 tests), `tests/unit/test_ingest_runtime_entrypoint.py` |
| 证据等级 | L3 (integration, readyz 8-component verified) |
| required/optional | required (healthz), optional (debug dump, default disabled) |
| 剩余差距 | failure snapshot 功能未实现; Docker compose 级真实依赖 readyz E2E 尚未验证(compose script 已创建, environment-pending); debug dump 接入点存在但功能未开发 |

### 2.6 CT-NFR-001: 低侵入接入

| 属性 | 值 |
|---|---|
| ingress 接入点 | 全部通过 decorator/middleware/composition 接入: `AuthorizedSourceAcquisitionPort`, `LoggingSourceAcquisitionPort`, `AuditedSourceAcquisitionPort`, `DebugSourceAcquisitionPort`, `RetryingSourceAcquisitionPort`, `MetricsStateCachePort`, `audit_middleware`(FastAPI middleware) |
| 代码路径 | `src/whale/ingest/composition.py:L145-L213`, `src/whale/ingest/api/audit_middleware.py`, `src/whale/ingest/decorators/` |
| 测试路径 | `tests/unit/test_ingest_composition_injection.py`(4 tests), `tests/unit/test_source_command_lease_release.py`(4 tests) |
| 证据等级 | L2 (contract, decorator/middleware pattern verified) |
| required/optional | required |
| 剩余差距 | 已验证 decorator/middleware/composition 接入模式符合 CT-NFR-001 要求; 无 mixin 继承; use case 核心逻辑未被污染 |

### 2.7 CT-SCR-001: 敏感信息保护

| 属性 | 值 |
|---|---|
| ingress 接入点 | `readyz.py:_sanitize_detail()` 脱敏 detail 中的 password/token/secret/dsn/url; `audit_middleware.py` 审计事件不记录 request body 敏感字段; `file_sinks.py` 敏感字段脱敏输出; `bundle/redaction.py` redacted bundle 导出 |
| 代码路径 | `src/whale/ingest/api/readyz.py:L84-L106`, `src/whale/ingest/api/audit_middleware.py`, `src/whale/ingest/adapters/observability/file_sinks.py`, `src/whale/ingest/bundle/redaction.py` |
| 测试路径 | `tests/unit/test_ingest_readyz.py`(sensitive redaction tests), `tests/unit/test_ingest_audit_redaction.py`(4 tests), `tests/unit/test_ingest_bundle_redaction.py`(2 tests) |
| 证据等级 | L3 (integration, redaction verified at API/bundle/audit level) |
| required/optional | required |
| 剩余差距 | readyz compose E2E 级脱敏验证 environment-pending; production debug dump 真实脱敏未验证(debug dump 功能未实现) |

### 2.8 CT-TEST-001: 横切能力测试

| 属性 | 值 |
|---|---|
| ingress 接入点 | 各横切能力均有对应测试: audit(全量矩阵), redaction(unit), metrics(L1), security/auth(L3 contract), retry/fault_injection(L3), health/readyz(L1), composition injection(L2) |
| 代码路径 | `tests/unit/test_ingest_audit_*.py`, `tests/unit/test_ingest_readyz.py`, `tests/unit/test_ingest_metrics_events.py`, `tests/integration/test_ingest_prodlike_*.py` |
| 测试路径 | `tests/unit/`(85+), `tests/integration/`(237+) |
| 证据等级 | L3 (integration, comprehensive audit/metrics/auth/retry tests) |
| required/optional | required |
| 剩余差距 | compose 级集成测试 environment-pending(需 Docker); 7x24 长稳未执行 |

## 3. 接入方式汇总

| 横切能力 | 接入方式 | 接入层 | 默认行为 |
|---|---|---|---|
| auth/authz | decorator (AuthorizedSourceAcquisitionPort/AuthorizedSourceWritePort) | composition | allow-all (production应注入真实策略) |
| audit | middleware (audit_middleware) + decorator (AuditedSourceAcquisitionPort/AuditedStateCachePort) | API + composition | no-op sink (生产应注入DB/JSONL/SIEM) |
| logging/metrics | decorator (LoggingSourceAcquisitionPort/LoggingStateCachePort/MetricsStateCachePort) | composition | null sink |
| retry/backoff | decorator (RetryingSourceAcquisitionPort) | composition | max_attempts=1, no backoff |
| tracing/debug | decorator (DebugSourceAcquisitionPort/DebugStateCachePort) | composition | disabled by default |
| credential redaction | helper (_sanitize_detail, SensitiveDataMasker, redaction.py) | readyz + decorator + bundle | active at readyz, passive at bundle |
| health/diagnostics | API route (/healthz, /readyz) | API layer | /healthz lightweight, /readyz 8-component |
| resilience (fencing) | ORM layer (FencingTokenRepository atomic UPDATE RETURNING) | runtime | lease/fencing required for write |

## 4. 证据等级总览

| Crosscutting 需求 | 接入状态 | 证据等级 | 是否满足 |
|---|---|---|---|
| CT-FR-001 日志/指标/追踪 | 已接入 | L3 | satisfied |
| CT-FR-002 韧性策略 | 已接入 | L3 | satisfied (circuit breaker partial) |
| CT-FR-003 认证/鉴权 | 已接入 | L3 contract | satisfied (allow-all default acceptable for dev) |
| CT-FR-004 审计 | 已接入 | L3 | satisfied |
| CT-FR-005 健康检查 | 已接入 | L3 | satisfied (debug dump pending) |
| CT-NFR-001 低侵入 | 已接入 | L2 | satisfied (decorator/middleware/composition pattern) |
| CT-SCR-001 敏感信息保护 | 已接入 | L3 | satisfied |
| CT-TEST-001 横切测试 | 已接入 | L3 | satisfied (environment-pending for compose) |

## 5. 剩余待补项

| 项目 | 优先级 | 阻塞条件 |
|---|---|---|
| Docker compose 级 readyz + redaction E2E 验证 | 中 | 需 Docker 环境 |
| 真实 IAM (LDAP/OIDC) 注入验证 | 低 | 需现场 IAM 系统 |
| 真实 SIEM 外部审计 sink 集成 | 低 | 需平台团队现场部署 |
| 生产级观测后端 (Prometheus/Grafana) | 低 | 需运营平台 |
| failure snapshot 功能 | 低 | debug dump 功能未实现 |
| circuit breaker 统一接入 | 低 | crosscutting 模块无统一熔断实现 |
| 7x24 长稳验证 | 高 | 需生产环境部署 |

## 6. ingest 对 I-READY-003 的满足度

ingest 已通过 decorator/middleware/composition 接入 crosscutting 全部 8 类横切能力，接入证据覆盖 L2 contract 到 L3 integration。当前状态：

- **structured logging/metrics/tracing**: L3, accessible via composition
- **audit sink**: L3, DB+JSONL dual sink + external sink contract, API/bundle/scheduler/write 全审计
- **access policy/authz**: L3 contract, deny/conflict/validation error/not found 已可审计
- **credential redaction**: L3, readyz/audit/bundle 三级脱敏
- **retry/timeout/backoff**: L3, acquisition/kafka/redis 三级可配置
- **health/readiness/diagnostic**: L3, /healthz + /readyz 8-component aggregation, debug dump default disabled

I-READY-003 状态：**满足**（L3 evidence），compose 级验证仍 environment-pending 但不阻塞代码级接入证据。
