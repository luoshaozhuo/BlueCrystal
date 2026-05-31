# Round 11: ingest 外部依赖准入矩阵

## 结论

本报告补齐 `I-READY-002` 所需的统一依赖矩阵，但不自动代表 ingest 已 production-ready。
当前状态：

1. 矩阵与证据映射已补齐。
2. 多数依赖已具备 timeout / retry / fail-open or fail-closed 语义。
3. `readyz` 当前仍只硬检查 runtime DB；Redis/Kafka/audit/access policy/shared_source 仍以分散 smoke / integration / contract 证据覆盖，未并入统一运行时就绪探针。

## 依赖矩阵

| 依赖 | required/optional | 主要入口 | failure mode | timeout | retry/backoff | readiness check | degradation behavior | fail-open/fail-closed | 现有证据 | remaining gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Runtime DB (PostgreSQL/SQLite) | Required | `src/whale/ingest/framework/persistence/`; `src/whale/ingest/api/routes/health.py` | DB 不可达、迁移缺失、事务失败、lease/state/audit 持久化失败 | DB 驱动/SQLAlchemy 默认；上层 job/request timeout 间接受限 | 无统一应用层 retry；依赖 DB 驱动/调用方重试 | `readyz` 直接调用 `readiness_probe()` | API `healthz` 仍可活着；`readyz` 降为 not ready；worker/scheduler 应安全失败 | Fail-closed | `pytest tests/integration/test_ingest_prodlike_postgres_runtime_db.py -q`; `pytest tests/integration/test_ingest_prodlike_postgres_fault_injection.py -q`; `pytest tests/integration/test_ingest_dual_node_db_lease_e2e.py -q` | PostgreSQL 双进程与 fault injection 已有入口，但本轮环境未提供 `WHALE_INGEST_TEST_PG_DSN`，网络分区和旧主恢复仍 pending |
| Redis state cache | Optional for API-only；Required for cache->message/state-cache production path | `src/whale/ingest/adapters/state/redis_source_state_cache.py` | 连接失败、写入失败、读取超时 | Redis client/socket timeout 为主；无独立 readiness timeout 汇总 | 无统一 retry/backoff 编排 | 无统一 `readyz`；依赖 integration smoke | 可退化为无缓存或上游失败；取决于部署路径 | 实际上偏 fail-closed（生产链路要求状态缓存时） | `pytest tests/integration/test_ingest_prodlike_redis_cache.py -q`; `pytest tests/integration/test_ingest_prodlike_redis_fault_injection.py -q` | 缺统一 readiness 聚合与明确“API-only optional / runtime required”运行时告警 |
| Kafka message publisher | Optional for API-only；Required for cache->message pipeline | `src/whale/ingest/adapters/message/kafka_message_publisher.py` | broker 不可达、topic/acks 超时、publish 失败 | `WHALE_INGEST_KAFKA_REQUEST_TIMEOUT_MS` | `WHALE_INGEST_KAFKA_RETRIES`; broker/client retry | 无统一 `readyz`；依赖 publish smoke/integration | 可降级为 publish 失败并上抛/记录；不应伪装成功 | Fail-closed | `tests/integration/test_ingest_cache_to_kafka_pipeline.py`; `tests/integration/test_ingest_source_cache_message_kafka_e2e.py`; `scripts/run_ingest_prodlike_dependency_smoke.sh` | 仍缺统一消息依赖 readiness 聚合与 backpressure 观测矩阵 |
| Audit sink (DB / JSONL / HTTP) | Required for合规部署；JSONL/HTTP 具体通道可选 | `src/whale/ingest/adapters/audit/` | 远端不可达、DB sink 写失败、双写不一致 | `HttpIngestAuditSink(timeout_seconds)` | `retry_count` + 指数 backoff | 无统一 `readyz`；依赖 sink contract/integration | DB+JSONL 双写中任一失败保留 `last_error`；HTTP sink 失败记录 warning，不抛到主路径 | DB sink 偏 fail-closed；HTTP 外发可 degrade with explicit error | `pytest tests/integration/test_ingest_prodlike_audit_sink.py -q`; `pytest tests/integration/test_ingest_audit_db_jsonl_consistency.py -q` | 缺“审计远端不可达但本地审计保底”的部署级 runbook |
| Access policy / authz | Required for production write/control；allow-all 仅 dev/test | `src/whale/ingest/adapters/security/external_access_policy.py`; `runtime/cli.py` | 外部授权服务超时、返回非法 JSON、HTTP 错误 | `timeout_seconds` | 无内建 retry；依赖调用重试/缓存 TTL | 无统一 `readyz`；通过策略 smoke/contract | fail_closed=True 时拒绝；fail_closed=False 时显式 fail-open reason | Configurable; production 应 fail-closed | `pytest tests/integration/test_ingest_prodlike_access_policy.py -q`; `pytest tests/unit/test_source_command_use_case.py -q` | 生产部署仍需把 `allow-all` 明确禁用，且将策略模式纳入发布检查 |
| Crosscutting observability / redaction | Required for production operations；部分 sink optional | `src/whale/ingest/adapters/observability/`; `bundle/redaction.py`; `shared/crosscutting/` | 日志/指标/trace sink 丢失、脱敏遗漏 | 依赖 sink 实现；无统一超时汇总 | 无统一 retry/backoff 汇总 | 无统一 `readyz` | 通常降级为可观测性缺失但主功能继续；脱敏错误不应 fail-open 泄露敏感数据 | Mixed | `tests/integration/test_ingest_security_partition_bundle_flow.py`; bundle/redaction tests | 指标/trace 仍以接线存在为主，缺统一 prodlike 观测验收脚本 |
| shared_source production client | Required for真实 source read/write jobs | `src/whale/shared/source/` 与 ingest source adapters | runner 缺失、协议连接失败、认证失败、read/write timeout | 各协议 connection/request timeout | 依赖协议/调用方；无统一全局 retry | 无统一 `readyz`；依赖 source-specific tests | 当前会显式报错；本轮已从默认 source_lab build 脱耦 | Fail-closed | `mypy src/whale/ingest src/whale/shared/source`; source write/read tests；`tests/unit/test_shared_source_runner_resolution.py` | 仍需独立 production runner artifact 安装/交付与 field 资格证据 |
| source adapter (ingest adapters/source) | Required for对应协议 job | `src/whale/ingest/adapters/source/` | DTO->source client 转换失败、协议异常、租约/授权拒绝 | request timeout / protocol timeout | 依赖 use case / scheduler retry | 无统一 `readyz` | 失败应转为 job failure/audit，不可默默成功 | Fail-closed | `pytest tests/unit/test_source_command_use_case.py -q`; 协议 adapter unit/integration tests | 真实设备与生产授权注入仍未闭合，见 `I-READY-005` |

## 本轮同步的实现边界

1. `shared_source` native runner 默认不再指向 `tools/source_lab/native/build`。
2. 生产 runner 解析优先走：
   - 单 runner 环境变量；
   - `WHALE_SHARED_SOURCE_RUNNER_DIR`；
   - PATH / 约定安装目录。
3. `tools/source_lab/native/build` 仅在显式设置 `WHALE_SHARED_SOURCE_ALLOW_DEV_RUNNER_FALLBACK=1` 时作为 dev/test fallback。

## 阻塞结论

`I-READY-002` 的“矩阵缺失”阻塞已修复，但 ingest 仍不能因此标 production-ready。剩余阻塞：

1. `readyz` 尚未聚合 Redis/Kafka/access-policy/audit/shared_source 的运行态就绪判断。
2. shared_source 需要独立 production runner artifact 的交付/安装证据。
3. field readback 与 PostgreSQL 网络分区/旧主恢复仍需更高等级验证。
