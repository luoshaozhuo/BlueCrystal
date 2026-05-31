# Ingest / Source Lab docstring 违规清单 Round 5

> 报告日期: 2026-05-29
> 范围: src/whale/ingest, src/whale/shared/source, tools/source_lab, tests
> 扫描总文件数: 506
> 依据规则: ai_shared/rules/python-docstring-cn.md (Round 5 修订版), ai_shared/rules/coding.md Section 8

## 总览

| 优先级 | 文件数 | 违规条目数 |
|--------|--------|-----------|
| HIGH | 453 | 453 |
| MEDIUM | 3 | 3 |
| LOW | 24 | 24 |
| CLEAN | 26 | 0 |


## Round 5 修复摘要

| 类别 | 本轮修复数 | 状态 |
|------|-----------|------|
| 缺失 module docstring（34个文件） | 34 | FIXED |
| Pydantic schema 类缺少 docstring（20个） | 20 | FIXED |
| 无解释 type:ignore（ingest 关键路径 5个） | 5 | FIXED |
| OPC UA / Modbus / IEC61850 readback() 实现 | 2 adapters | IMPLEMENTED |
| Readback contract 测试 | 6 tests (3 Modbus + 3 IEC61850) | ADDED |
| 双节点真实 DB lease E2E 测试 | 7 tests (SQLite) | ADDED |
| 规则更新（coding.md / python-docstring-cn.md） | 2 files | UPDATED |

### Remaining Inventory（已知原因，后续轮次处理）

| 文件/类别 | 数量（估算） | 原因 |
|-----------|-------------|------|
| English module docstring（__init__.py 和 tools/source_lab） | ~350 | __init__.py 文件简短英文描述需批量替换，tools/source_lab 工具目录涉及大量协议缩写且非生产路径 |
| API route handler 缺少 docstring | ~40 | 需要逐路由补充权限/审计/dry_run 语义，工作量较大 |
| type:ignore 无解释（source_lab tools） | ~50 | 工具代码中 type:ignore 主要因第三方库无 stub，修复价值低于生产路径 |
| 缺失 public 函数 docstring（adapter/observer sinks 等） | ~15 | adapter 的 emit/authorize 等方法需要补充中文 docstring |

### 本轮质量门禁

| 检查 | 命令 | 结果 |
|------|------|------|
| 编译检查 | `python -m compileall ...` | PASS（全部目录） |
| lint | `ruff check ...` | PASS（本轮引入 0 errors） |
| 类型检查 | `mypy` | PASS（修改文件 0 issues） |
| 单元测试 | `pytest` | 61 passed, 0 failed |
| 导入隔离 | `grep -R tools.source_lab src/whale/ingest` | PASS（无违规导入） |


## HIGH 优先级违规

| 文件 | 文件类型 | 违规类型 | 详情 | 修复状态 |
|------|----------|----------|------|----------|
| src/whale/ingest/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Ingestion helpers for registry loading and source collection.'] | PENDING |
| src/whale/ingest/adapters/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Adapters for the ingest module.'] | PENDING |
| src/whale/ingest/adapters/audit/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Audit sink adapters.'] | PENDING |
| src/whale/ingest/adapters/audit/db_audit_sink.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Database-backed audit sink for ingest runtime.'] | PENDING |
| src/whale/ingest/adapters/audit/db_audit_sink.py | production | english_business_docstring | class DbIngestAuditSink docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/audit/db_audit_sink.py | production | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| src/whale/ingest/adapters/audit/http_audit_sink.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['HTTP-based audit sink for forwarding events to an external audit platform / SIEM', "Non-blocking on the main business path: failures record last_error but don't", 'propagate exceptions to the caller.'] | PENDING |
| src/whale/ingest/adapters/audit/http_audit_sink.py | production | english_business_docstring | class HttpIngestAuditSink docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/audit/http_audit_sink.py | production | english_business_docstring | function emit docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/audit/http_audit_sink.py | production | english_business_docstring | function flush docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/audit/multi_audit_sink.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Composable ingest audit sinks.'] | PENDING |
| src/whale/ingest/adapters/audit/multi_audit_sink.py | production | english_business_docstring | class AuditSinkEmitError docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/audit/multi_audit_sink.py | production | english_business_docstring | class DualIngestAuditSink docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/audit/multi_audit_sink.py | production | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| src/whale/ingest/adapters/config/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Configuration adapters for ingest.'] | PENDING |
| src/whale/ingest/adapters/config/opcua_source_acquisition_definition_repository.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Database-backed OPC UA acquisition-definition repository.'] | PENDING |
| src/whale/ingest/adapters/config/opcua_source_acquisition_definition_repository.py | production | english_business_docstring | function get_config docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/config/source_runtime_config_repository.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Database-backed runtime-configuration repository for ingest.'] | PENDING |
| src/whale/ingest/adapters/config/source_runtime_config_repository.py | production | english_business_docstring | function list_enabled docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/config/source_runtime_config_repository.py | production | english_business_docstring | function list_servers docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/config/source_runtime_config_repository.py | production | english_business_docstring | function list_profile_items docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Message publishing adapters for ingest.'] | PENDING |
| src/whale/ingest/adapters/message/kafka_message_publisher.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Kafka publisher for ingest state snapshot messages.'] | PENDING |
| src/whale/ingest/adapters/message/kafka_message_publisher.py | production | english_business_docstring | class KafkaSendFuture docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/kafka_message_publisher.py | production | english_business_docstring | class KafkaProducerClient docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/kafka_message_publisher.py | production | english_business_docstring | class KafkaMessagePublisher docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/kafka_message_publisher.py | production | english_business_docstring | function get docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/kafka_message_publisher.py | production | english_business_docstring | function send docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/kafka_message_publisher.py | production | english_business_docstring | function flush docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/kafka_message_publisher.py | production | english_business_docstring | function publish_snapshot docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/kafka_message_publisher.py | production | unexplained_type_ignore | L110: 无解释的 type: ignore | PENDING |
| src/whale/ingest/adapters/message/redis_streams_message_publisher.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Redis Streams publisher for ingest state snapshot messages.'] | PENDING |
| src/whale/ingest/adapters/message/redis_streams_message_publisher.py | production | english_business_docstring | class RedisStreamsClient docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/redis_streams_message_publisher.py | production | english_business_docstring | class RedisStreamsMessagePublisher docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/redis_streams_message_publisher.py | production | english_business_docstring | function xadd docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/redis_streams_message_publisher.py | production | english_business_docstring | function publish_snapshot docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/relational_outbox_message_publisher.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Relational outbox publisher for ingest state snapshot messages.', 'Deprecated: StateSnapshotOutbox has been removed. This publisher is a no-op.'] | PENDING |
| src/whale/ingest/adapters/message/relational_outbox_message_publisher.py | production | english_business_docstring | class RelationalOutboxMessagePublisher docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/message/relational_outbox_message_publisher.py | production | missing_public_docstring | public function publish_snapshot 缺少 docstring | PENDING |
| src/whale/ingest/adapters/observability/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Observability sink adapters for ingest.'] | PENDING |
| src/whale/ingest/adapters/observability/file_sinks.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Lightweight JSONL sinks for ingest metrics and audit.'] | PENDING |
| src/whale/ingest/adapters/observability/file_sinks.py | production | english_business_docstring | class JsonlIngestMetricsSink docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/observability/file_sinks.py | production | english_business_docstring | class JsonlSourceCommandAuditSink docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/observability/file_sinks.py | production | english_business_docstring | class JsonlIngestAuditSink docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/observability/file_sinks.py | production | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| src/whale/ingest/adapters/observability/file_sinks.py | production | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| src/whale/ingest/adapters/observability/file_sinks.py | production | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| src/whale/ingest/adapters/security/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Security adapters for ingest runtime.'] | PENDING |
| src/whale/ingest/adapters/security/external_access_policy.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['External HTTP-based access policy adapter for ingest runtime.', 'Makes authorization decisions by calling a remote access policy service.', 'Supports fail_closed (default) and fail_open modes.'] | PENDING |
| src/whale/ingest/adapters/security/external_access_policy.py | production | english_business_docstring | class ExternalAccessPolicy docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/security/external_access_policy.py | production | english_business_docstring | function evaluate docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/security/external_access_policy.py | production | missing_public_docstring | public function authorize 缺少 docstring | PENDING |
| src/whale/ingest/adapters/security/file_access_policy.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['File-based access policy adapters for ingest API and write authorization.'] | PENDING |
| src/whale/ingest/adapters/security/file_access_policy.py | production | english_business_docstring | class FileAccessPolicy docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/security/file_access_policy.py | production | english_business_docstring | class AllowAllAccessPolicy docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/security/file_access_policy.py | production | english_business_docstring | class DenyAllAccessPolicy docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/security/file_access_policy.py | production | missing_public_docstring | public function evaluate 缺少 docstring | PENDING |
| src/whale/ingest/adapters/security/file_access_policy.py | production | missing_public_docstring | public function authorize 缺少 docstring | PENDING |
| src/whale/ingest/adapters/security/file_access_policy.py | production | missing_public_docstring | public function evaluate 缺少 docstring | PENDING |
| src/whale/ingest/adapters/security/file_access_policy.py | production | missing_public_docstring | public function authorize 缺少 docstring | PENDING |
| src/whale/ingest/adapters/security/file_access_policy.py | production | missing_public_docstring | public function evaluate 缺少 docstring | PENDING |
| src/whale/ingest/adapters/security/file_access_policy.py | production | missing_public_docstring | public function authorize 缺少 docstring | PENDING |
| src/whale/ingest/adapters/source/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Source adapters for ingest.'] | PENDING |
| src/whale/ingest/adapters/source/iec104_source_acquisition_adapter.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 104 source acquisition adapter.', 'Converts ingest DTOs to shared/source IEC 104 native runner calls', 'and converts ``RawIec104ReadResult`` to ``AcquiredNodeStateBatch``.'] | PENDING |
| src/whale/ingest/adapters/source/iec104_source_acquisition_adapter.py | production | english_business_docstring | class Iec104SourceAcquisitionAdapter docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/iec104_source_acquisition_adapter.py | production | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| src/whale/ingest/adapters/source/iec104_source_acquisition_adapter.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/iec104_source_acquisition_adapter.py | production | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| src/whale/ingest/adapters/source/iec104_source_write_adapter.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 104 source write adapter.', 'Converts ingest DTOs to shared/source IEC 104 native runner calls', '(C_SC_NA_1 single command).'] | PENDING |
| src/whale/ingest/adapters/source/iec104_source_write_adapter.py | production | english_business_docstring | class Iec104SourceWriteAdapter docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/iec104_source_write_adapter.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/iec61850_report_source_acquisition_adapter.py | production | english_business_docstring | class Iec61850ReportSourceAcquisitionAdapter docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/iec61850_report_source_acquisition_adapter.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/iec61850_source_acquisition_adapter.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 MMS source acquisition adapter.', 'Converts ingest DTOs to shared/source libiec61850 MMS calls', 'and converts ``RawMmsReadResult`` to ``AcquiredNodeStateBatch``.'] | PENDING |
| src/whale/ingest/adapters/source/iec61850_source_acquisition_adapter.py | production | english_business_docstring | class Iec61850MmsSourceAcquisitionAdapter docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/iec61850_source_acquisition_adapter.py | production | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| src/whale/ingest/adapters/source/iec61850_source_acquisition_adapter.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/iec61850_source_acquisition_adapter.py | production | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| src/whale/ingest/adapters/source/iec61850_source_write_adapter.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 MMS source write adapter.', 'Converts ingest DTOs to shared/source libiec61850 MMS write calls', 'and converts ``RawWriteItemResult`` to ``SourceWriteResult``.'] | PENDING |
| src/whale/ingest/adapters/source/iec61850_source_write_adapter.py | production | english_business_docstring | class Iec61850MmsSourceWriteAdapter docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/iec61850_source_write_adapter.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/modbus_source_acquisition_adapter.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Modbus TCP source acquisition adapter.', 'Converts ingest DTOs to shared/source modbus native runner calls', 'and converts ``RawModbusReadResult`` to ``AcquiredNodeStateBatch``.'] | PENDING |
| src/whale/ingest/adapters/source/modbus_source_acquisition_adapter.py | production | english_business_docstring | class ModbusSourceAcquisitionAdapter docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/modbus_source_acquisition_adapter.py | production | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| src/whale/ingest/adapters/source/modbus_source_acquisition_adapter.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/modbus_source_acquisition_adapter.py | production | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| src/whale/ingest/adapters/source/modbus_source_write_adapter.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Modbus TCP source write adapter.', 'Converts ingest DTOs to shared/source modbus native runner calls (FC06).'] | PENDING |
| src/whale/ingest/adapters/source/modbus_source_write_adapter.py | production | english_business_docstring | class ModbusSourceWriteAdapter docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/modbus_source_write_adapter.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/opcua_source_acquisition_adapter.py | production | english_business_docstring | class OpcUaSourceAcquisitionAdapter docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/opcua_source_write_adapter.py | production | english_business_docstring | function readback docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/source/static_source_write_port_registry.py | production | missing_public_docstring | public function get 缺少 docstring | PENDING |
| src/whale/ingest/adapters/state/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['State-cache adapters for ingest.'] | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | class RedisPipeline docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | class RedisHashClient docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | class RedisSourceStateCacheSettings docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | class RedisSourceStateCache docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | function hset docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | function execute docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | function hset docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | function hget docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | function hgetall docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | function pipeline docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | function from_config docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | function update docstring 为英文业务描述 | PENDING |
| src/whale/ingest/adapters/state/redis_source_state_cache.py | production | english_business_docstring | function read_snapshot docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['FastAPI app factory for ingest runtime APIs.'] | PENDING |
| src/whale/ingest/api/app.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['FastAPI app factory for ingest runtime CRUD.'] | PENDING |
| src/whale/ingest/api/app.py | production | english_business_docstring | function create_app docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/app.py | production | missing_public_docstring | public function handle_api_error 缺少 docstring | PENDING |
| src/whale/ingest/api/app.py | production | missing_public_docstring | public function handle_validation_error 缺少 docstring | PENDING |
| src/whale/ingest/api/app.py | production | unexplained_type_ignore | L67: 无解释的 type: ignore | PENDING |
| src/whale/ingest/api/audit_middleware.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Request audit context helpers and middleware.'] | PENDING |
| src/whale/ingest/api/audit_middleware.py | production | english_business_docstring | class AuditContext docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/audit_middleware.py | production | english_business_docstring | class IngestAuditMiddleware docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/audit_middleware.py | production | english_business_docstring | function build_audit_event docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/audit_middleware.py | production | missing_public_docstring | public function dispatch 缺少 docstring | PENDING |
| src/whale/ingest/api/audit_middleware.py | production | unexplained_type_ignore | L28: 无解释的 type: ignore | PENDING |
| src/whale/ingest/api/errors.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['API error types and stable error payloads.'] | PENDING |
| src/whale/ingest/api/errors.py | production | english_business_docstring | class ApiError docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/errors.py | production | missing_public_docstring | public function not_found 缺少 docstring | PENDING |
| src/whale/ingest/api/errors.py | production | missing_public_docstring | public function conflict 缺少 docstring | PENDING |
| src/whale/ingest/api/errors.py | production | missing_public_docstring | public function denied 缺少 docstring | PENDING |
| src/whale/ingest/api/errors.py | production | missing_public_docstring | public function to_payload 缺少 docstring | PENDING |
| src/whale/ingest/api/idempotency.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Idempotency key support for ingest runtime CRUD API.'] | PENDING |
| src/whale/ingest/api/idempotency.py | production | english_business_docstring | class IdempotencyService docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/idempotency.py | production | english_business_docstring | class IdempotencyMiddleware docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/idempotency.py | production | english_business_docstring | function get_cached docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/idempotency.py | production | english_business_docstring | function try_claim docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/idempotency.py | production | english_business_docstring | function cache_response docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/idempotency.py | production | missing_public_docstring | public function replay_receive 缺少 docstring | PENDING |
| src/whale/ingest/api/idempotency.py | production | missing_public_docstring | public function send_wrapper 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['API route packages.'] | PENDING |
| src/whale/ingest/api/routes/acquisition_tasks.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Acquisition-task CRUD routes.'] | PENDING |
| src/whale/ingest/api/routes/acquisition_tasks.py | production | missing_public_docstring | public function create_acquisition_task 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/acquisition_tasks.py | production | missing_public_docstring | public function get_acquisition_task 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/acquisition_tasks.py | production | missing_public_docstring | public function list_acquisition_tasks 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/acquisition_tasks.py | production | missing_public_docstring | public function patch_acquisition_task 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/acquisition_tasks.py | production | missing_public_docstring | public function delete_acquisition_task 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/audit_events.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Audit-event query routes for ingest runtime API.'] | PENDING |
| src/whale/ingest/api/routes/audit_events.py | production | missing_public_docstring | public function get_audit_event 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/audit_events.py | production | missing_public_docstring | public function list_audit_events 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/bundles.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Bundle-metadata query routes for ingest runtime API.'] | PENDING |
| src/whale/ingest/api/routes/bundles.py | production | missing_public_docstring | public function get_bundle 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/bundles.py | production | missing_public_docstring | public function list_bundles 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/health.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Health and readiness routes.'] | PENDING |
| src/whale/ingest/api/routes/health.py | production | missing_public_docstring | public function healthz 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/health.py | production | missing_public_docstring | public function readyz 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/leases.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Lease query routes for ingest runtime API.'] | PENDING |
| src/whale/ingest/api/routes/leases.py | production | missing_public_docstring | public function get_lease 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/leases.py | production | missing_public_docstring | public function list_leases 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/nodes.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Node query routes for ingest runtime API.'] | PENDING |
| src/whale/ingest/api/routes/nodes.py | production | missing_public_docstring | public function get_node 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/nodes.py | production | missing_public_docstring | public function list_nodes 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime-config CRUD routes for sources, connections, points, and profiles.'] | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function create_source 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function get_source 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function list_sources 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function patch_source 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function delete_source 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function create_connection 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function get_connection 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function list_connections 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function patch_connection 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function delete_connection 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function create_signal_profile 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function get_signal_profile 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function list_signal_profiles 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function patch_signal_profile 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function delete_signal_profile 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function create_point 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function get_point 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function list_points 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function patch_point 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/runtime_config.py | production | missing_public_docstring | public function delete_point 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/scheduler_jobs.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Scheduler-job CRUD routes for ingest runtime API.'] | PENDING |
| src/whale/ingest/api/routes/scheduler_jobs.py | production | missing_public_docstring | public function create_scheduler_job 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/scheduler_jobs.py | production | missing_public_docstring | public function get_scheduler_job 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/scheduler_jobs.py | production | missing_public_docstring | public function list_scheduler_jobs 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/scheduler_jobs.py | production | missing_public_docstring | public function patch_scheduler_job 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/scheduler_jobs.py | production | missing_public_docstring | public function delete_scheduler_job 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/security_partitions.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Security-partition CRUD routes for ingest runtime API.'] | PENDING |
| src/whale/ingest/api/routes/security_partitions.py | production | english_business_docstring | class SecurityPartitionOrm docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/routes/security_partitions.py | production | missing_public_docstring | public function create_security_partition 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/security_partitions.py | production | missing_public_docstring | public function get_security_partition 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/security_partitions.py | production | missing_public_docstring | public function list_security_partitions 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/security_partitions.py | production | missing_public_docstring | public function patch_security_partition 缺少 docstring | PENDING |
| src/whale/ingest/api/routes/security_partitions.py | production | missing_public_docstring | public function delete_security_partition 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Pydantic schemas for ingest runtime CRUD APIs.'] | PENDING |
| src/whale/ingest/api/schemas.py | production | english_business_docstring | class PaginatedResponse docstring 为英文业务描述 | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class AcquisitionTaskCreate 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class AcquisitionTaskPatch 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class AcquisitionTaskResponse 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SourceCreate 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SourcePatch 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SourceResponse 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class ConnectionCreate 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class ConnectionPatch 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class ConnectionResponse 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SignalProfileCreate 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SignalProfilePatch 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SignalProfileResponse 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class PointCreate 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class PointPatch 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class PointResponse 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SchedulerJobCreate 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SchedulerJobPatch 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SchedulerJobResponse 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SecurityPartitionCreate 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SecurityPartitionPatch 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class SecurityPartitionResponse 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class BundleMetadataResponse 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class NodeResponse 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class LeaseResponse 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_class_docstring | public class AuditEventResponse 缺少 docstring | PENDING |
| src/whale/ingest/api/schemas.py | production | missing_public_docstring | public function from_orm_row 缺少 docstring | PENDING |
| src/whale/ingest/bundle/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Ingest bundle services.'] | PENDING |
| src/whale/ingest/bundle/checksum.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Checksum helpers for ingest bundle payloads.'] | PENDING |
| src/whale/ingest/bundle/checksum.py | production | english_business_docstring | function canonicalize_bundle_payload docstring 为英文业务描述 | PENDING |
| src/whale/ingest/bundle/checksum.py | production | english_business_docstring | function compute_bundle_checksum docstring 为英文业务描述 | PENDING |
| src/whale/ingest/bundle/model.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Bundle model for ingest runtime configuration export/import.'] | PENDING |
| src/whale/ingest/bundle/model.py | production | english_business_docstring | class AcquisitionTaskBundleItem docstring 为英文业务描述 | PENDING |
| src/whale/ingest/bundle/model.py | production | english_business_docstring | class IngestBundle docstring 为英文业务描述 | PENDING |
| src/whale/ingest/bundle/redaction.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Bundle redaction helpers.'] | PENDING |
| src/whale/ingest/bundle/redaction.py | production | english_business_docstring | function redact_bundle docstring 为英文业务描述 | PENDING |
| src/whale/ingest/bundle/service.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Bundle import/export service for ingest runtime.'] | PENDING |
| src/whale/ingest/bundle/service.py | production | english_business_docstring | class BundleImportResult docstring 为英文业务描述 | PENDING |
| src/whale/ingest/bundle/service.py | production | english_business_docstring | class BundleService docstring 为英文业务描述 | PENDING |
| src/whale/ingest/bundle/service.py | production | english_business_docstring | function export_bundle docstring 为英文业务描述 | PENDING |
| src/whale/ingest/bundle/service.py | production | english_business_docstring | function import_bundle docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Explicit ingest composition root for acquisition, latest-state caching, and sour'] | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | class IngestAcquisitionComposition docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | class IngestWriteComposition docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | class _DefaultSourceErrorClassifier docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | class _AllowAllAccessPolicy docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | class _NullAuditEventSink docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | class _NullMetricsSink docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | class _NullDebugTraceSink docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | class IngestPublishComposition docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | function build_source_acquisition_composition docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | function build_source_write_composition docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | function build_default_write_composition docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | english_business_docstring | function build_state_snapshot_publish_composition docstring 为英文业务描述 | PENDING |
| src/whale/ingest/composition.py | production | missing_public_docstring | public function classify 缺少 docstring | PENDING |
| src/whale/ingest/composition.py | production | missing_public_docstring | public function evaluate 缺少 docstring | PENDING |
| src/whale/ingest/composition.py | production | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| src/whale/ingest/composition.py | production | missing_public_docstring | public function increment 缺少 docstring | PENDING |
| src/whale/ingest/composition.py | production | missing_public_docstring | public function observe_duration 缺少 docstring | PENDING |
| src/whale/ingest/composition.py | production | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| src/whale/ingest/composition.py | production | unexplained_type_ignore | L467: 无解释的 type: ignore | PENDING |
| src/whale/ingest/config.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Python-native configuration for the ingest module.'] | PENDING |
| src/whale/ingest/config.py | production | english_business_docstring | function state_cache_backend docstring 为英文业务描述 | PENDING |
| src/whale/ingest/config.py | production | unexplained_type_ignore | L138: 无解释的 type: ignore | PENDING |
| src/whale/ingest/config.py | production | unexplained_type_ignore | L152: 无解释的 type: ignore | PENDING |
| src/whale/ingest/config.py | production | unexplained_type_ignore | L166: 无解释的 type: ignore | PENDING |
| src/whale/ingest/decorators/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Decorator-style port wrappers for ingest crosscutting concerns.'] | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Decorator objects for SourceAcquisitionPort crosscutting concerns.'] | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | english_business_docstring | class LoggingSourceAcquisitionPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | english_business_docstring | class AuditedSourceAcquisitionPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | english_business_docstring | class RetryingSourceAcquisitionPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | english_business_docstring | class AuthorizedSourceAcquisitionPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | english_business_docstring | class DebugSourceAcquisitionPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function read 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function read 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function read 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function read 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function read 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_acquisition.py | production | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| src/whale/ingest/decorators/source_write.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Decorator objects for SourceWritePort crosscutting concerns.'] | PENDING |
| src/whale/ingest/decorators/source_write.py | production | english_business_docstring | class AuthorizedSourceWritePort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/decorators/source_write.py | production | missing_public_docstring | public function write 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Decorator objects for SourceStateCachePort crosscutting concerns.'] | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | english_business_docstring | class LoggingStateCachePort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | english_business_docstring | class AuditedStateCachePort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | english_business_docstring | class MetricsStateCachePort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | english_business_docstring | class DebugStateCachePort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function update 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function mark_alive 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function mark_unavailable 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function update 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function mark_alive 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function mark_unavailable 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function update 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function mark_alive 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function mark_unavailable 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function update 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function mark_alive 缺少 docstring | PENDING |
| src/whale/ingest/decorators/state_cache.py | production | missing_public_docstring | public function mark_unavailable 缺少 docstring | PENDING |
| src/whale/ingest/domain/audit_event.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Structured audit event schema for ingest runtime and API.'] | PENDING |
| src/whale/ingest/domain/audit_event.py | production | english_business_docstring | class IngestAuditEvent docstring 为英文业务描述 | PENDING |
| src/whale/ingest/domain/audit_event.py | production | english_business_docstring | function redact_value docstring 为英文业务描述 | PENDING |
| src/whale/ingest/domain/audit_event.py | production | english_business_docstring | function redact_pair docstring 为英文业务描述 | PENDING |
| src/whale/ingest/domain/audit_event.py | production | english_business_docstring | function sanitized_payload docstring 为英文业务描述 | PENDING |
| src/whale/ingest/domain/write_security_profile.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Write security profile domain model.', 'Controls which protocols are allowed to perform write/control operations,', 'what readback strategy is used, and what authorization is required.'] | PENDING |
| src/whale/ingest/domain/write_security_profile.py | production | english_business_docstring | class ReadbackStrategy docstring 为英文业务描述 | PENDING |
| src/whale/ingest/domain/write_security_profile.py | production | english_business_docstring | class WriteSecurityProfile docstring 为英文业务描述 | PENDING |
| src/whale/ingest/domain/write_security_profile.py | production | english_business_docstring | function profile_for docstring 为英文业务描述 | PENDING |
| src/whale/ingest/domain/write_security_profile.py | production | english_business_docstring | function is_write_allowed docstring 为英文业务描述 | PENDING |
| src/whale/ingest/entities/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Reusable ingest entities.'] | PENDING |
| src/whale/ingest/entities/node_state.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Node-state entity for ingest.', 'This is a minimal reusable ingest entity. Future iterations may extend it with', 'fields such as quality, source timestamp, staleness, and last receive time.'] | PENDING |
| src/whale/ingest/entities/node_state.py | production | english_business_docstring | class NodeState docstring 为英文业务描述 | PENDING |
| src/whale/ingest/entities/source_health_state.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Source-health entity for ingest.', 'This is a minimal reusable ingest entity. Future iterations may extend it with', 'fields such as last success time, error message, and recovery state.'] | PENDING |
| src/whale/ingest/entities/source_health_state.py | production | english_business_docstring | class SourceHealthState docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Public exports for ingest persistence helpers.', 'Keep this module light so importing runtime helpers does not eagerly bind one', 'global engine from stale environment variables.'] | PENDING |
| src/whale/ingest/framework/persistence/base.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['SQLAlchemy base model.'] | PENDING |
| src/whale/ingest/framework/persistence/base.py | production | english_business_docstring | class Base docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/init_db.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Database initialization entrypoint for the ingest framework.'] | PENDING |
| src/whale/ingest/framework/persistence/init_db.py | production | english_business_docstring | function init_db docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/init_db.py | production | english_business_docstring | function initialize_db docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/init_db.py | production | english_business_docstring | function reset_db docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/init_db.py | production | english_business_docstring | function load_default_sample_data docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/init_db.py | production | english_business_docstring | function main docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/orm/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Ingest ORM models — fully consolidated into whale.shared.persistence.orm.', 'All former ingest ORM models have been replaced by shared-ORM equivalents:', '- whale.shared.persistence.orm.AcquisitionTask     (table acq_task)'] | PENDING |
| src/whale/ingest/framework/persistence/runtime_db.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Helpers for ingest runtime DB initialization and migration smoke.'] | PENDING |
| src/whale/ingest/framework/persistence/runtime_db.py | production | english_business_docstring | function create_runtime_engine docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/runtime_db.py | production | english_business_docstring | function create_runtime_session_factory docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/runtime_db.py | production | english_business_docstring | function initialize_runtime_database docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/runtime_db.py | production | english_business_docstring | function migrate_runtime_database docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/runtime_db.py | production | english_business_docstring | function probe_runtime_readiness docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/runtime_db.py | production | english_business_docstring | function resolve_alembic_ini_path docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/session.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['SQLAlchemy engine and session helpers for the ingest framework.'] | PENDING |
| src/whale/ingest/framework/persistence/session.py | production | english_business_docstring | function create_db_url docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/session.py | production | english_business_docstring | function get_session docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/session.py | production | english_business_docstring | function session_scope docstring 为英文业务描述 | PENDING |
| src/whale/ingest/framework/persistence/session.py | production | english_business_docstring | function dispose_engine docstring 为英文业务描述 | PENDING |
| src/whale/ingest/message_pipeline.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Message pipeline abstractions for ingest output.'] | PENDING |
| src/whale/ingest/message_pipeline.py | production | english_business_docstring | class IngestMessagePipeline docstring 为英文业务描述 | PENDING |
| src/whale/ingest/message_pipeline.py | production | english_business_docstring | class InMemoryIngestMessagePipeline docstring 为英文业务描述 | PENDING |
| src/whale/ingest/message_pipeline.py | production | english_business_docstring | function publish docstring 为英文业务描述 | PENDING |
| src/whale/ingest/message_pipeline.py | production | english_business_docstring | function publish docstring 为英文业务描述 | PENDING |
| src/whale/ingest/message_pipeline.py | production | english_business_docstring | function batches docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Ports for ingest use cases.'] | PENDING |
| src/whale/ingest/ports/audit.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Audit sink port for ingest runtime and API.'] | PENDING |
| src/whale/ingest/ports/audit.py | production | english_business_docstring | class IngestAuditSinkPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/audit.py | production | english_business_docstring | function emit docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/command/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Ports for source command/write control.'] | PENDING |
| src/whale/ingest/ports/command/source_command_audit_port.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Structured audit port for source write/control commands.'] | PENDING |
| src/whale/ingest/ports/command/source_command_audit_port.py | production | english_business_docstring | class SourceCommandAuditEvent docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/command/source_command_audit_port.py | production | english_business_docstring | class SourceCommandAuditPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/command/source_command_audit_port.py | production | english_business_docstring | function emit docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/diagnostics.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IngestRuntimeDiagnosticsPort — 采集运行时诊断端口.'] | PENDING |
| src/whale/ingest/ports/diagnostics.py | production | english_business_docstring | class IngestRuntimeDiagnosticsPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/diagnostics.py | production | english_business_docstring | function mark_success docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/diagnostics.py | production | english_business_docstring | function mark_alive docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/message/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Message-related ports for ingest.'] | PENDING |
| src/whale/ingest/ports/message/message_publisher_port.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Publisher ports for ingest snapshot messages.'] | PENDING |
| src/whale/ingest/ports/message/message_publisher_port.py | production | english_business_docstring | class StateSnapshotItem docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/message/message_publisher_port.py | production | english_business_docstring | class StateSnapshotMessage docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/message/message_publisher_port.py | production | english_business_docstring | class MessagePublishResult docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/message/message_publisher_port.py | production | english_business_docstring | class MessagePublisherPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/message/message_publisher_port.py | production | english_business_docstring | function to_dict docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/message/message_publisher_port.py | production | english_business_docstring | function to_dict docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/message/message_publisher_port.py | production | english_business_docstring | function to_json docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/message/message_publisher_port.py | production | english_business_docstring | function publish_snapshot docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/metrics.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Ingest metrics port.'] | PENDING |
| src/whale/ingest/ports/metrics.py | production | missing_class_docstring | public class IngestMetricEvent 缺少 docstring | PENDING |
| src/whale/ingest/ports/metrics.py | production | missing_class_docstring | public class IngestMetricsPort 缺少 docstring | PENDING |
| src/whale/ingest/ports/metrics.py | production | english_business_docstring | function emit docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime-side ports for ingest.'] | PENDING |
| src/whale/ingest/ports/runtime/access_policy_port.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Access policy port for ingest runtime API authorization.'] | PENDING |
| src/whale/ingest/ports/runtime/access_policy_port.py | production | english_business_docstring | class AccessPolicyPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/access_policy_port.py | production | english_business_docstring | function authorize docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/source_runtime_config_port.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Source runtime-configuration port for ingest.'] | PENDING |
| src/whale/ingest/ports/runtime/source_runtime_config_port.py | production | english_business_docstring | class SignalProfileItemRuntimeData docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/source_runtime_config_port.py | production | english_business_docstring | function list_enabled docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/source_runtime_config_port.py | production | english_business_docstring | function list_servers docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/source_runtime_config_port.py | production | english_business_docstring | function list_profile_items docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/write_lease_port.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Write lease port used by SourceCommandUseCase.'] | PENDING |
| src/whale/ingest/ports/runtime/write_lease_port.py | production | english_business_docstring | class WriteLeaseDecisionData docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/write_lease_port.py | production | english_business_docstring | class WriteLeasePort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/write_lease_port.py | production | english_business_docstring | function acquire docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/write_lease_port.py | production | english_business_docstring | function renew docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/write_lease_port.py | production | english_business_docstring | function validate docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/runtime/write_lease_port.py | production | english_business_docstring | function release docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/source/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Source-side ports for ingest.'] | PENDING |
| src/whale/ingest/ports/source/source_acquisition_definition_port.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Source acquisition definition port.'] | PENDING |
| src/whale/ingest/ports/source/source_acquisition_definition_port.py | production | english_business_docstring | class SourceAcquisitionDefinitionPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/source/source_acquisition_definition_port.py | production | english_business_docstring | function get_config docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/source/source_acquisition_port_registry.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Source acquisition port registry for ingest.'] | PENDING |
| src/whale/ingest/ports/source/source_acquisition_port_registry.py | production | english_business_docstring | class SourceAcquisitionPortRegistry docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/source/source_acquisition_port_registry.py | production | english_business_docstring | function get docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/source/source_write_port_registry.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Source write port registry for ingest.'] | PENDING |
| src/whale/ingest/ports/source/source_write_port_registry.py | production | english_business_docstring | class SourceWritePortRegistry docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/source/source_write_port_registry.py | production | english_business_docstring | function get docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/state/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['State-related ports for ingest.'] | PENDING |
| src/whale/ingest/ports/state/source_state_cache_port.py | production | english_business_docstring | class SourceStateCacheError docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/state/source_state_cache_port.py | production | english_business_docstring | class SourceStateCacheWriteError docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/state/source_state_cache_port.py | production | english_business_docstring | class SourceStateCachePort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/state/source_state_snapshot_reader_port.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Snapshot-reader port for the local latest-state cache.'] | PENDING |
| src/whale/ingest/ports/state/source_state_snapshot_reader_port.py | production | english_business_docstring | class CachedNodeValue docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/state/source_state_snapshot_reader_port.py | production | english_business_docstring | class CachedSourceState docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/state/source_state_snapshot_reader_port.py | production | english_business_docstring | class SourceStateSnapshotReaderPort docstring 为英文业务描述 | PENDING |
| src/whale/ingest/ports/state/source_state_snapshot_reader_port.py | production | english_business_docstring | function read_snapshot docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime scheduling helpers for ingest.'] | PENDING |
| src/whale/ingest/runtime/acquisition_mode.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Acquisition mode enumeration for ingest runtime.'] | PENDING |
| src/whale/ingest/runtime/acquisition_mode.py | production | english_business_docstring | class AcquisitionMode docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/cli.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Typer CLI for ingest runtime entrypoints.'] | PENDING |
| src/whale/ingest/runtime/cli.py | production | english_business_docstring | class _NoopJobHandler docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/cli.py | production | english_business_docstring | function migrate docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/cli.py | production | english_business_docstring | function api docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/cli.py | production | english_business_docstring | function worker docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/cli.py | production | english_business_docstring | function api_worker docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/cli.py | production | english_business_docstring | function export_bundle docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/cli.py | production | english_business_docstring | function import_bundle docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/cli.py | production | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| src/whale/ingest/runtime/entrypoint.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Command-line entrypoint for the ingest runtime image.'] | PENDING |
| src/whale/ingest/runtime/entrypoint.py | production | english_business_docstring | function main docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/fencing.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Fencing token helpers.'] | PENDING |
| src/whale/ingest/runtime/fencing.py | production | english_business_docstring | class FencingToken docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/fencing.py | production | english_business_docstring | class FencingTokenRepository docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/fencing.py | production | english_business_docstring | function redact_fencing_token docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/fencing.py | production | english_business_docstring | function next_value docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/fencing.py | production | english_business_docstring | function current_value docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/handlers.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['WorkerRuntime job handlers for ingest.', '本模块定义 WorkerRuntime 使用的 JobHandler 实现。', '- ``AcquisitionJobHandler`` — 最小生产采集 handler（PENDING 完整验证）。'] | PENDING |
| src/whale/ingest/runtime/handlers.py | production | english_business_docstring | class AcquisitionJobHandler docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/handlers.py | production | missing_private_helper_docstring | 复杂 private function _get_int 缺少 docstring | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime job and assignment models.'] | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | class RuntimeJob docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | class JobAssignment docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | class RuntimeJobRepository docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | class JobAssignmentRepository docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | function upsert_job docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | function list_enabled_jobs docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | function get docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | function assign docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | function get_active_assignment docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | function list_active_assignments docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/job_assignment.py | production | english_business_docstring | function deactivate_job docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/job_status.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime job status enumeration for ingest scheduler.'] | PENDING |
| src/whale/ingest/runtime/job_status.py | production | english_business_docstring | class JobStatus docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['DB-backed lease helpers for scheduler jobs and write control.'] | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | class LeaseAcquireResult docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | class JobLease docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | class LeaseRepository docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | class LeaseService docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | function is_expired docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | function get docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | function list_active docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | function acquire docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | function renew docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | function release docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | function expire_due_leases docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | function force_expire docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | function get_snapshot docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/lease.py | production | english_business_docstring | function validate_execution docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/message_pipeline_settings.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Compatibility exports for ingest message pipeline settings.'] | PENDING |
| src/whale/ingest/runtime/message_pipeline_settings.py | production | english_business_docstring | class _LazyMessagePipelineSettingsProxy docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/modes.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime mode parsing for ingest nodes and schedulers.'] | PENDING |
| src/whale/ingest/runtime/modes.py | production | english_business_docstring | class RuntimeMode docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/modes.py | production | english_business_docstring | function parse docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/node_runtime.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Node heartbeat models and persistence helpers.'] | PENDING |
| src/whale/ingest/runtime/node_runtime.py | production | english_business_docstring | class NodeHeartbeat docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/node_runtime.py | production | english_business_docstring | class NodeRuntimeRepository docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/node_runtime.py | production | english_business_docstring | function upsert_heartbeat docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/node_runtime.py | production | english_business_docstring | function get docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/node_runtime.py | production | english_business_docstring | function list_nodes docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/node_runtime.py | production | english_business_docstring | function list_alive_nodes docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['DB-backed ingest scheduler with minimal multi-node semantics.'] | PENDING |
| src/whale/ingest/runtime/scheduler.py | production | english_business_docstring | class SchedulerSnapshot docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler.py | production | english_business_docstring | class SchedulerExecutionDecision docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler.py | production | english_business_docstring | class SourceScheduler docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler.py | production | english_business_docstring | function node_key docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler.py | production | english_business_docstring | function heartbeat docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler.py | production | english_business_docstring | function assign_jobs docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler.py | production | english_business_docstring | function bootstrap docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler.py | production | english_business_docstring | function release_jobs docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler.py | production | english_business_docstring | function validate_execution docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler_factory.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Factory helpers for building APScheduler instances.'] | PENDING |
| src/whale/ingest/runtime/scheduler_factory.py | production | english_business_docstring | function build_scheduler docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler_factory.py | production | unexplained_type_ignore | L5: 无解释的 type: ignore | PENDING |
| src/whale/ingest/runtime/scheduler_factory.py | production | unexplained_type_ignore | L9: 无解释的 type: ignore | PENDING |
| src/whale/ingest/runtime/scheduler_factory.py | production | unexplained_type_ignore | L10: 无解释的 type: ignore | PENDING |
| src/whale/ingest/runtime/scheduler_factory.py | production | unexplained_type_ignore | L13: 无解释的 type: ignore | PENDING |
| src/whale/ingest/runtime/scheduler_factory.py | production | unexplained_type_ignore | L16: 无解释的 type: ignore | PENDING |
| src/whale/ingest/runtime/scheduler_factory.py | production | unexplained_type_ignore | L17: 无解释的 type: ignore | PENDING |
| src/whale/ingest/runtime/scheduler_job.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime job model for ingest scheduler.'] | PENDING |
| src/whale/ingest/runtime/scheduler_job.py | production | english_business_docstring | class AcquisitionStatus docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler_job.py | production | english_business_docstring | class SourceStateAcquisitionResult docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler_job.py | production | english_business_docstring | class ScheduledSourceJob docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler_settings.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Scheduler configuration models for ingest runtime.'] | PENDING |
| src/whale/ingest/runtime/scheduler_settings.py | production | english_business_docstring | class JobStoreSettings docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler_settings.py | production | english_business_docstring | class ExecutorSettings docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler_settings.py | production | english_business_docstring | class JobDefaultSettings docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/scheduler_settings.py | production | english_business_docstring | class SchedulerSettings docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['APScheduler-driven worker runtime for ingest.', 'Pulls enabled jobs from the runtime DB, acquires/renews lease with fencing', 'tokens, executes only when the lease and ownership are valid, and emits metrics'] | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | english_business_docstring | class JobHandler docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | english_business_docstring | class WorkerRuntimeMetrics docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | english_business_docstring | class WorkerRuntime docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | english_business_docstring | function execute docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | missing_public_docstring | public function inc 缺少 docstring | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | missing_public_docstring | public function gauge 缺少 docstring | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | missing_public_docstring | public function snapshot 缺少 docstring | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | missing_public_docstring | public function summary 缺少 docstring | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | missing_public_docstring | public function node_key 缺少 docstring | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | missing_public_docstring | public function metrics_snapshot 缺少 docstring | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | missing_public_docstring | public function metrics_summary 缺少 docstring | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | english_business_docstring | function start docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/worker_runtime.py | production | english_business_docstring | function stop docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/write_lease.py | production | english_business_docstring | class WriteLeaseService docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/write_lease.py | production | english_business_docstring | function acquire docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/write_lease.py | production | english_business_docstring | function renew docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/write_lease.py | production | english_business_docstring | function validate docstring 为英文业务描述 | PENDING |
| src/whale/ingest/runtime/write_lease.py | production | english_business_docstring | function release docstring 为英文业务描述 | PENDING |
| src/whale/ingest/usecases/dtos/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['DTOs for ingest use cases.'] | PENDING |
| src/whale/ingest/usecases/dtos/source_acquisition_start_result.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['SourceAcquisitionStartResult DTO — source 采集启动结果。'] | PENDING |
| src/whale/ingest/usecases/dtos/source_write_result.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Source write result DTOs for the write/control use case.'] | PENDING |
| src/whale/ingest/usecases/dtos/state_publish_request.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['DTO for state snapshot publish requests.'] | PENDING |
| src/whale/ingest/usecases/dtos/state_publish_request.py | production | english_business_docstring | class StateSnapshotPublishRequest docstring 为英文业务描述 | PENDING |
| src/whale/ingest/usecases/dtos/state_publish_result.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['DTO for state snapshot publish results.'] | PENDING |
| src/whale/ingest/usecases/dtos/state_publish_result.py | production | missing_class_docstring | public class PublishStatus 缺少 docstring | PENDING |
| src/whale/ingest/usecases/dtos/state_publish_result.py | production | english_business_docstring | class StateSnapshotPublishResult docstring 为英文业务描述 | PENDING |
| src/whale/ingest/usecases/dtos/state_publish_result.py | production | english_business_docstring | function is_success docstring 为英文业务描述 | PENDING |
| src/whale/ingest/usecases/dtos/state_publish_result.py | production | english_business_docstring | function merge docstring 为英文业务描述 | PENDING |
| src/whale/ingest/usecases/roles/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Role exports for the active source acquisition flow.'] | PENDING |
| src/whale/ingest/usecases/roles/subscription_acquisition_role.py | production | english_business_docstring | function start docstring 为英文业务描述 | PENDING |
| src/whale/ingest/usecases/roles/subscription_acquisition_role.py | production | missing_private_helper_docstring | 复杂 private function _start_with_retry 缺少 docstring | PENDING |
| src/whale/ingest/usecases/source_command_use_case.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Source command/write use case.', '1. 校验 SourceWriteRequest。', '2. 根据 protocol 从 SourceWritePortRegistry 获取对应写端口。'] | PENDING |
| src/whale/ingest/usecases/source_command_use_case.py | production | missing_private_helper_docstring | 复杂 private function _int_param 缺少 docstring | PENDING |
| src/whale/ingest/usecases/state_snapshot_publish_use_case.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Use case: publish a full state-snapshot from cache to message queue.'] | PENDING |
| src/whale/ingest/usecases/state_snapshot_publish_use_case.py | production | english_business_docstring | class StateSnapshotPublishUseCase docstring 为英文业务描述 | PENDING |
| src/whale/ingest/usecases/state_snapshot_publish_use_case.py | production | english_business_docstring | function execute docstring 为英文业务描述 | PENDING |
| src/whale/ingest/usecases/state_snapshot_publish_use_case.py | production | unexplained_type_ignore | L283: 无解释的 type: ignore | PENDING |
| src/whale/ingest/usecases/state_snapshot_publish_use_case.py | production | unexplained_type_ignore | L286: 无解释的 type: ignore | PENDING |
| src/whale/ingest/usecases/state_snapshot_publish_use_case.py | production | unexplained_type_ignore | L293: 无解释的 type: ignore | PENDING |
| src/whale/ingest/usecases/state_snapshot_publish_use_case.py | production | unexplained_type_ignore | L294: 无解释的 type: ignore | PENDING |
| src/whale/ingest/usecases/state_snapshot_publish_use_case.py | production | unexplained_type_ignore | L297: 无解释的 type: ignore | PENDING |
| src/whale/ingest/usecases/state_snapshot_publish_use_case.py | production | unexplained_type_ignore | L299: 无解释的 type: ignore | PENDING |
| src/whale/shared/source/access/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Reusable source access models and adapters.'] | PENDING |
| src/whale/shared/source/access/__init__.py | production | english_business_docstring | function build_source_access_adapter docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/adapter.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Reusable source access adapter interfaces.'] | PENDING |
| src/whale/shared/source/access/adapter.py | production | english_business_docstring | class SourceAccessAdapter docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/adapter.py | production | english_business_docstring | function connect docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/adapter.py | production | english_business_docstring | function prepare_read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/adapter.py | production | english_business_docstring | function read_tick docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/adapter.py | production | english_business_docstring | function close docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/model.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Reusable runtime models for source access adapters.'] | PENDING |
| src/whale/shared/source/access/model.py | production | english_business_docstring | class SourceEndpointSpec docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/model.py | production | english_business_docstring | class SourcePointSpec docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/model.py | production | english_business_docstring | class TickResult docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/opcua.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Reusable OPC UA source access adapter.'] | PENDING |
| src/whale/shared/source/access/opcua.py | production | english_business_docstring | class OpcUaSourceAccessAdapter docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/opcua.py | production | english_business_docstring | function normalize_opcua_node_id docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/opcua.py | production | english_business_docstring | function build_opcua_endpoint_url docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/opcua.py | production | english_business_docstring | function connect docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/opcua.py | production | english_business_docstring | function prepare_read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/opcua.py | production | english_business_docstring | function close docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/access/opcua.py | production | english_business_docstring | function read_tick docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 104 source read/write shared library.'] | PENDING |
| src/whale/shared/source/iec104/backends/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 104 backend abstractions for raw read/write.'] | PENDING |
| src/whale/shared/source/iec104/backends/base.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 104 backend base types.'] | PENDING |
| src/whale/shared/source/iec104/backends/base.py | production | english_business_docstring | class RawIec104ReadResult docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/backends/base.py | production | english_business_docstring | class RawWriteItemResult docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/backends/base.py | production | english_business_docstring | class Iec104PreparedReadPlan docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/backends/base.py | production | english_business_docstring | class Iec104ClientBackend docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/backends/base.py | production | english_business_docstring | function connect docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/backends/base.py | production | english_business_docstring | function disconnect docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/backends/base.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/backends/base.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/backends/lib60870_backend.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 104 client backend backed by native C runner subprocess.'] | PENDING |
| src/whale/shared/source/iec104/backends/lib60870_backend.py | production | english_business_docstring | class Iec104Lib60870Backend docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/backends/lib60870_backend.py | production | english_business_docstring | function resolve_client_runner_path docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/backends/lib60870_backend.py | production | missing_public_docstring | public function connect 缺少 docstring | PENDING |
| src/whale/shared/source/iec104/backends/lib60870_backend.py | production | missing_public_docstring | public function disconnect 缺少 docstring | PENDING |
| src/whale/shared/source/iec104/backends/lib60870_backend.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/backends/lib60870_backend.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/reader.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 104 source reader/writer facade.'] | PENDING |
| src/whale/shared/source/iec104/reader.py | production | english_business_docstring | class Iec104SourceReader docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/reader.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec104/reader.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 MMS source implementations.'] | PENDING |
| src/whale/shared/source/iec61850/backends/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 backend implementations.'] | PENDING |
| src/whale/shared/source/iec61850/backends/base.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 MMS backend base types.'] | PENDING |
| src/whale/shared/source/iec61850/backends/base.py | production | english_business_docstring | class RawMmsReadResult docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/base.py | production | english_business_docstring | class RawWriteItemResult docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/base.py | production | english_business_docstring | class Iec61850MmsClientBackend docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/base.py | production | english_business_docstring | function connect docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/base.py | production | english_business_docstring | function disconnect docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/base.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/base.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_backend.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['libiec61850-based IEC 61850 MMS client backend (subprocess runner).'] | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_backend.py | production | english_business_docstring | class _MmsConnectionParams docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_backend.py | production | english_business_docstring | class LibIec61850MmsClientBackend docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_backend.py | production | english_business_docstring | function resolve_client_runner_path docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_backend.py | production | missing_public_docstring | public function connect 缺少 docstring | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_backend.py | production | missing_public_docstring | public function disconnect 缺少 docstring | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_backend.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_backend.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_report_backend.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['libiec61850-based IEC 61850 Report backend (subprocess runner).', 'Connects to an IEC 61850 server, subscribes to a Report Control Block,', 'and delivers REPORT events via async callback.'] | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_report_backend.py | production | english_business_docstring | class LibIec61850ReportBackend docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_report_backend.py | production | english_business_docstring | function resolve_report_runner_path docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_report_backend.py | production | english_business_docstring | function is_active docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_report_backend.py | production | english_business_docstring | function subscribe docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/libiec61850_report_backend.py | production | english_business_docstring | function close docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/report_base.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 Report backend base types.', 'Report 是 IEC 61850 的订阅/事件能力，与 MMS polling read/write 不同。', 'Report 通过 RCB (ReportControlBlock) 配置，由 server 主动推送数据变化。'] | PENDING |
| src/whale/shared/source/iec61850/backends/report_base.py | production | english_business_docstring | class RawReportEvent docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/report_base.py | production | english_business_docstring | class Iec61850ReportClientBackend docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/report_base.py | production | english_business_docstring | function subscribe docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/backends/report_base.py | production | english_business_docstring | function close docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/reader.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 MMS source reader facade.'] | PENDING |
| src/whale/shared/source/iec61850/reader.py | production | english_business_docstring | class Iec61850MmsSourceReader docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/reader.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/reader.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/report_reader.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 Report source reader facade.', 'Wraps LibIec61850ReportBackend and provides a clean API for', 'report subscription.'] | PENDING |
| src/whale/shared/source/iec61850/report_reader.py | production | english_business_docstring | class Iec61850ReportSourceReader docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/report_reader.py | production | english_business_docstring | function subscribe docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/report_reader.py | production | english_business_docstring | function is_active docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/iec61850/report_reader.py | production | english_business_docstring | function close docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Modbus TCP source read/write shared library.'] | PENDING |
| src/whale/shared/source/modbus/backends/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Modbus backend abstractions for raw read/write.'] | PENDING |
| src/whale/shared/source/modbus/backends/base.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Modbus TCP backend base types.'] | PENDING |
| src/whale/shared/source/modbus/backends/base.py | production | english_business_docstring | class RawModbusReadResult docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/base.py | production | english_business_docstring | class RawWriteItemResult docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/base.py | production | english_business_docstring | class ModbusPreparedReadPlan docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/base.py | production | english_business_docstring | class ModbusClientBackend docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/base.py | production | english_business_docstring | function connect docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/base.py | production | english_business_docstring | function disconnect docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/base.py | production | english_business_docstring | function prepare_read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/base.py | production | english_business_docstring | function read_prepared docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/base.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/libmodbus_backend.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Modbus TCP client backend backed by native C runner subprocess.'] | PENDING |
| src/whale/shared/source/modbus/backends/libmodbus_backend.py | production | english_business_docstring | class ModbusTcpClientBackend docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/libmodbus_backend.py | production | english_business_docstring | function resolve_client_runner_path docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/libmodbus_backend.py | production | missing_public_docstring | public function connect 缺少 docstring | PENDING |
| src/whale/shared/source/modbus/backends/libmodbus_backend.py | production | missing_public_docstring | public function disconnect 缺少 docstring | PENDING |
| src/whale/shared/source/modbus/backends/libmodbus_backend.py | production | missing_public_docstring | public function prepare_read 缺少 docstring | PENDING |
| src/whale/shared/source/modbus/backends/libmodbus_backend.py | production | english_business_docstring | function read_prepared docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/backends/libmodbus_backend.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/reader.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Modbus TCP source reader/writer facade.'] | PENDING |
| src/whale/shared/source/modbus/reader.py | production | english_business_docstring | class ModbusSourceReader docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/reader.py | production | english_business_docstring | function prepare_read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/reader.py | production | english_business_docstring | function read_prepared docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/reader.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/modbus/reader.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['OPC UA source implementations.'] | PENDING |
| src/whale/shared/source/opcua/backends/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['OPC UA client backend abstractions for raw polling.'] | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | missing_module_docstring | 无 module docstring | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | class PreparedReadPlan docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | class Open62541PreparedReadPlan docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | class RawDataValue docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | class RawOpcUaReadResult docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | class RawWriteItemResult docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | class OpcUaClientBackend docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | function node_paths docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | function connect docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | function disconnect docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | function namespace_index docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | function prepare_read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | function read_prepared_raw docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/base.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/factory.py | production | missing_module_docstring | 无 module docstring | PENDING |
| src/whale/shared/source/opcua/backends/factory.py | production | english_business_docstring | function normalize_client_backend_name docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/factory.py | production | english_business_docstring | function resolve_client_backend_name docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/factory.py | production | english_business_docstring | function build_client_backend docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | missing_module_docstring | 无 module docstring | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | english_business_docstring | class Open62541ReadDebugTiming docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | english_business_docstring | class _CachedPlanRuntime docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | english_business_docstring | class Open62541OpcUaClientBackend docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | english_business_docstring | function resolve_client_runner_path docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | missing_private_helper_docstring | 复杂 private function _datetime_from_runner_timestamp 缺少 docstring | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | missing_public_docstring | public function connect 缺少 docstring | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | missing_public_docstring | public function disconnect 缺少 docstring | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | missing_public_docstring | public function namespace_index 缺少 docstring | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | missing_public_docstring | public function prepare_read 缺少 docstring | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | missing_public_docstring | public function read_prepared_raw 缺少 docstring | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/backends/open62541_backend.py | production | english_business_docstring | function write_batch docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/reader.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Open62541-backed OPC UA raw polling facade.'] | PENDING |
| src/whale/shared/source/opcua/reader.py | production | english_business_docstring | class OpcUaSubscriptionHandle docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/reader.py | production | english_business_docstring | class OpcUaSourceReader docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/reader.py | production | missing_public_docstring | public function close 缺少 docstring | PENDING |
| src/whale/shared/source/opcua/reader.py | production | missing_public_docstring | public function endpoint 缺少 docstring | PENDING |
| src/whale/shared/source/opcua/reader.py | production | english_business_docstring | function prepare_read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/reader.py | production | english_business_docstring | function read_prepared_raw docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/reader.py | production | english_business_docstring | function write docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/reader.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/reader.py | production | english_business_docstring | function start_subscription docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/reader.py | production | english_business_docstring | function list_nodes docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/opcua/reader.py | production | english_business_docstring | function list_readable_variable_nodes docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/ports.py | production | english_business_docstring | class SourceReaderPort docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Public exports for the worker-local source polling kernel.', 'This package contains protocol-agnostic scheduling primitives used by', 'SourceRuntime/worker layers to run high-frequency source polling inside one'] | PENDING |
| src/whale/shared/source/scheduling/concurrency.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Worker-local read concurrency control for high-frequency source polling.', 'This module provides protocol-agnostic concurrency limiting for read operations', 'inside a single worker process and a single asyncio event loop. It is the'] | PENDING |
| src/whale/shared/source/scheduling/concurrency.py | production | english_business_docstring | class ConcurrencySnapshot docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/concurrency.py | production | english_business_docstring | class ReadConcurrencyLimiter docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/concurrency.py | production | english_business_docstring | function max_concurrent docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/concurrency.py | production | english_business_docstring | function run docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/concurrency.py | production | english_business_docstring | function snapshot docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/concurrency.py | production | english_business_docstring | function reset_counters docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/fixed_rate.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Diagnostic-only high-frequency fixed-rate scheduler.', 'This module exists only for historical profile comparisons.', 'It is not a production scheduler and it must not be used as an acceptance mode.'] | PENDING |
| src/whale/shared/source/scheduling/fixed_rate.py | production | english_business_docstring | class HighFrequencyFixedRateScheduler docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/fixed_rate.py | production | english_business_docstring | function add_job docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/fixed_rate.py | production | english_business_docstring | function start docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/fixed_rate.py | production | english_business_docstring | function stop docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/fixed_rate.py | production | english_business_docstring | function task_creation_snapshot docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/fixed_rate.py | production | missing_private_helper_docstring | 复杂 private function _run_job 缺少 docstring | PENDING |
| src/whale/shared/source/scheduling/fixed_rate.py | production | missing_public_docstring | public function run_once 缺少 docstring | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Worker-local fixed-rate polling primitives for source acquisition.', 'This module provides the production worker-local polling kernel used by', 'runtime/worker layers. It intentionally keeps a narrow scope:'] | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | class PollingTickDiagnostics docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | class PollingTaskCreationDiagnostics docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | class _MutablePollingTaskCreationDiagnostics docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | class PollingResultEvent docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | class PollingErrorEvent docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | class PollingJobSpec docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | class PollingJobStats docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | class _MutablePollingJobStats docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | class SourcePollingScheduler docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | function reset_for_start docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | function snapshot docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | function snapshot docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | function add_job docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | function start docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | function stop docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | english_business_docstring | function job_stats docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | missing_public_docstring | public function mark_started 缺少 docstring | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | missing_public_docstring | public function mark_limiter_wait_start 缺少 docstring | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | missing_public_docstring | public function mark_limiter_acquired 缺少 docstring | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | missing_public_docstring | public function mark_operation_finished 缺少 docstring | PENDING |
| src/whale/shared/source/scheduling/polling.py | production | missing_public_docstring | public function run_once 缺少 docstring | PENDING |
| src/whale/shared/source/scheduling/stagger.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Deterministic stagger-offset helpers for worker-local source polling.', 'This module only calculates stable offsets. It does not schedule tasks, does', 'not manage polling loops, and is not an APScheduler replacement. The helpers'] | PENDING |
| src/whale/shared/source/scheduling/stagger.py | production | english_business_docstring | class StaggerAssignment docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/stagger.py | production | english_business_docstring | function build_even_stagger_offsets docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/stagger.py | production | english_business_docstring | function build_stagger_assignments docstring 为英文业务描述 | PENDING |
| src/whale/shared/source/scheduling/stagger.py | production | english_business_docstring | function assign_even_stagger docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Shared pytest fixtures for current ingest and OPC UA simulator tests.'] | PENDING |
| tests/conftest.py | test | english_business_docstring | function pytest_configure docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | function pytest_sessionstart docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | function pytest_sessionfinish docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | function real_redis_url docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | function real_redis_client docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | function real_redis_hash_key docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | function sample_nodeset_path docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | function sample_opcua_connections_path docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | function free_ports docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | function local_opcua_connections_path docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | function opcua_server_runtime docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | english_business_docstring | function opcua_sim_fleet docstring 为英文业务描述 | PENDING |
| tests/conftest.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/e2e/__init__.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tests/e2e/conftest.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['E2E test fixtures: PostgreSQL + Redis + Kafka infrastructure.', 'Usage::', 'docker compose -f docker-compose.ingest-dev.yaml up -d'] | PENDING |
| tests/e2e/conftest.py | test | english_business_docstring | function pytest_configure docstring 为英文业务描述 | PENDING |
| tests/e2e/conftest.py | test | missing_public_docstring | public function pg_db_url 缺少 docstring | PENDING |
| tests/e2e/conftest.py | test | english_business_docstring | function pg_engine docstring 为英文业务描述 | PENDING |
| tests/e2e/conftest.py | test | english_business_docstring | function pg_session docstring 为英文业务描述 | PENDING |
| tests/e2e/conftest.py | test | english_business_docstring | function session_factory docstring 为英文业务描述 | PENDING |
| tests/e2e/conftest.py | test | english_business_docstring | function redis_client docstring 为英文业务描述 | PENDING |
| tests/e2e/conftest.py | test | missing_private_helper_docstring | 复杂 private function _factory 缺少 docstring | PENDING |
| tests/e2e/conftest.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/e2e/helpers.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Shared helpers for e2e tests — importable utilities and constants.'] | PENDING |
| tests/e2e/helpers.py | test | english_business_docstring | function get_free_port docstring 为英文业务描述 | PENDING |
| tests/e2e/helpers.py | test | english_business_docstring | function ensure_src_on_path docstring 为英文业务描述 | PENDING |
| tests/e2e/helpers.py | test | english_business_docstring | function seed_postgres_for_e2e docstring 为英文业务描述 | PENDING |
| tests/e2e/helpers.py | test | english_business_docstring | function wait_for_redis docstring 为英文业务描述 | PENDING |
| tests/e2e/helpers.py | test | english_business_docstring | function wait_for_kafka docstring 为英文业务描述 | PENDING |
| tests/e2e/helpers.py | test | unexplained_type_ignore | L191: 无解释的 type: ignore | PENDING |
| tests/e2e/helpers.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/__init__.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tests/integration/test_framework_db_init.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for framework database initialization.'] | PENDING |
| tests/integration/test_ingest_api_acquisition_task_crud.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Acquisition-task CRUD integration tests.'] | PENDING |
| tests/integration/test_ingest_api_audit.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['API audit integration tests.'] | PENDING |
| tests/integration/test_ingest_api_audit.py | test | missing_public_docstring | public function access_evaluator 缺少 docstring | PENDING |
| tests/integration/test_ingest_api_authorization_deny.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Authorization deny E2E tests for ingest runtime API.'] | PENDING |
| tests/integration/test_ingest_api_authorization_deny.py | test | missing_public_docstring | public function access_evaluator 缺少 docstring | PENDING |
| tests/integration/test_ingest_api_authorization_deny.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_api_bundle_metadata_crud.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Bundle-metadata query API integration tests.'] | PENDING |
| tests/integration/test_ingest_api_dry_run_all_mutating_routes.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Dry-run coverage across all mutating CRUD routes.', 'Each route group: POST dry_run does not persist, PATCH dry_run validates but', 'does not persist, DELETE dry_run validates but does not delete.'] | PENDING |
| tests/integration/test_ingest_api_dry_run_all_mutating_routes.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_api_full_audit_matrix.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Full audit matrix integration tests — verify every API action emits audit.'] | PENDING |
| tests/integration/test_ingest_api_full_audit_matrix.py | test | missing_private_helper_docstring | 复杂 private function _audit_count 缺少 docstring | PENDING |
| tests/integration/test_ingest_api_idempotency_all_mutating_routes.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Idempotency-Key coverage across all mutating CRUD route groups.', 'IdempotencyMiddleware is ASGI-level so it covers all routes automatically.', 'These tests verify that non-scheduler routes also get idempotency protection.'] | PENDING |
| tests/integration/test_ingest_api_idempotency_all_mutating_routes.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_api_idempotency_dry_run.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for API idempotency key and dry-run support.'] | PENDING |
| tests/integration/test_ingest_api_idempotency_dry_run_interaction.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Idempotency-Key + dry_run=true interaction tests.', 'Scenarios:', '1. dry_run=true + Idempotency-Key first request not persisted'] | PENDING |
| tests/integration/test_ingest_api_idempotency_dry_run_interaction.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_api_node_lease_audit_query.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Node / Lease / Audit-event query API integration tests.'] | PENDING |
| tests/integration/test_ingest_api_runtime_config_audit.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime-config API audit tests.'] | PENDING |
| tests/integration/test_ingest_api_runtime_config_audit.py | test | missing_public_docstring | public function access_evaluator 缺少 docstring | PENDING |
| tests/integration/test_ingest_api_runtime_config_audit.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_api_runtime_config_crud.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime-config CRUD integration tests.'] | PENDING |
| tests/integration/test_ingest_api_scheduler_job_crud.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Scheduler-job CRUD integration tests.'] | PENDING |
| tests/integration/test_ingest_api_security_partition_crud.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Security-partition CRUD integration tests.'] | PENDING |
| tests/integration/test_ingest_audit_db_jsonl_consistency.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Audit DB/JSONL sink consistency tests.'] | PENDING |
| tests/integration/test_ingest_audit_db_jsonl_consistency.py | test | missing_public_docstring | public function session_factory 缺少 docstring | PENDING |
| tests/integration/test_ingest_audit_db_jsonl_consistency.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_audit_matrix_api_bundle_scheduler_write.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Audit matrix tests covering API, bundle, scheduler, and write events.'] | PENDING |
| tests/integration/test_ingest_audit_matrix_api_bundle_scheduler_write.py | test | missing_public_docstring | public function session_factory 缺少 docstring | PENDING |
| tests/integration/test_ingest_audit_matrix_api_bundle_scheduler_write.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_bundle_import_export.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Bundle import/export integration tests.'] | PENDING |
| tests/integration/test_ingest_bundle_offline_one_way_flow.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Offline one-way bundle flow tests.'] | PENDING |
| tests/integration/test_ingest_bundle_offline_one_way_flow.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_cache_to_kafka_pipeline.py | test | english_business_docstring | class _FakeKafkaFuture docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_cache_to_kafka_pipeline.py | test | english_business_docstring | class _FakeKafkaProducer docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_cache_to_kafka_pipeline.py | test | english_business_docstring | class _FakeSnapshotReader docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_cache_to_kafka_pipeline.py | test | missing_public_docstring | public function get 缺少 docstring | PENDING |
| tests/integration/test_ingest_cache_to_kafka_pipeline.py | test | missing_public_docstring | public function send 缺少 docstring | PENDING |
| tests/integration/test_ingest_cache_to_kafka_pipeline.py | test | missing_public_docstring | public function flush 缺少 docstring | PENDING |
| tests/integration/test_ingest_cache_to_kafka_pipeline.py | test | missing_public_docstring | public function read_snapshot 缺少 docstring | PENDING |
| tests/integration/test_ingest_external_access_policy_contract.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['External access policy contract tests with a local HTTP stub server.'] | PENDING |
| tests/integration/test_ingest_external_access_policy_contract.py | test | english_business_docstring | class _StubPolicyHandler docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_external_access_policy_contract.py | test | missing_class_docstring | public class TestExternalAccessPolicyContract 缺少 docstring | PENDING |
| tests/integration/test_ingest_external_access_policy_contract.py | test | missing_public_docstring | public function do_POST 缺少 docstring | PENDING |
| tests/integration/test_ingest_external_access_policy_contract.py | test | missing_public_docstring | public function log_message 缺少 docstring | PENDING |
| tests/integration/test_ingest_external_access_policy_contract.py | test | unexplained_type_ignore | L22: 无解释的 type: ignore | PENDING |
| tests/integration/test_ingest_external_audit_sink_contract.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['External audit/SIEM sink contract tests with a local HTTP stub server.'] | PENDING |
| tests/integration/test_ingest_external_audit_sink_contract.py | test | english_business_docstring | class _StubAuditHandler docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_external_audit_sink_contract.py | test | missing_class_docstring | public class TestExternalAuditSinkContract 缺少 docstring | PENDING |
| tests/integration/test_ingest_external_audit_sink_contract.py | test | missing_public_docstring | public function do_POST 缺少 docstring | PENDING |
| tests/integration/test_ingest_external_audit_sink_contract.py | test | missing_public_docstring | public function log_message 缺少 docstring | PENDING |
| tests/integration/test_ingest_external_audit_sink_contract.py | test | unexplained_type_ignore | L25: 无解释的 type: ignore | PENDING |
| tests/integration/test_ingest_iec61850_mms_source_write.py | test | english_business_docstring | class TestIec61850MmsSourceWrite docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_iec61850_mms_source_write.py | test | missing_public_docstring | public function setup_class 缺少 docstring | PENDING |
| tests/integration/test_ingest_iec61850_report_subscription.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 Report subscription integration tests.', 'Tests the full pipeline: simulator -> report runner -> backend -> adapter -> cal'] | PENDING |
| tests/integration/test_ingest_iec61850_report_subscription.py | test | english_business_docstring | function simulator_port docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_iec61850_report_subscription.py | test | missing_public_docstring | public function on_batch 缺少 docstring | PENDING |
| tests/integration/test_ingest_iec61850_report_subscription.py | test | missing_public_docstring | public function on_batch 缺少 docstring | PENDING |
| tests/integration/test_ingest_lightweight_load_gate.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Lightweight ingest load gate with in-memory/test sinks.'] | PENDING |
| tests/integration/test_ingest_lightweight_load_gate.py | test | missing_public_docstring | public function item_count_for_acquisition 缺少 docstring | PENDING |
| tests/integration/test_ingest_lightweight_load_gate.py | test | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| tests/integration/test_ingest_lightweight_load_gate.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/integration/test_ingest_lightweight_load_gate.py | test | missing_public_docstring | public function read_snapshot 缺少 docstring | PENDING |
| tests/integration/test_ingest_lightweight_load_gate.py | test | missing_public_docstring | public function publish_snapshot 缺少 docstring | PENDING |
| tests/integration/test_ingest_lightweight_load_gate.py | test | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tests/integration/test_ingest_lightweight_load_gate.py | test | missing_public_docstring | public function update 缺少 docstring | PENDING |
| tests/integration/test_ingest_lightweight_load_gate.py | test | missing_public_docstring | public function mark_alive 缺少 docstring | PENDING |
| tests/integration/test_ingest_lightweight_load_gate.py | test | missing_public_docstring | public function mark_unavailable 缺少 docstring | PENDING |
| tests/integration/test_ingest_lightweight_load_gate.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_observability_sink_smoke.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Smoke test for deployment-ready JSONL observability sinks.'] | PENDING |
| tests/integration/test_ingest_observability_sink_smoke.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/integration/test_ingest_observability_sink_smoke.py | test | missing_public_docstring | public function read_snapshot 缺少 docstring | PENDING |
| tests/integration/test_ingest_observability_sink_smoke.py | test | missing_public_docstring | public function publish_snapshot 缺少 docstring | PENDING |
| tests/integration/test_ingest_observability_sink_smoke.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for polling retry semantics against Redis latest-state cache.'] | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | english_business_docstring | class FakeSequenceAcquisitionPort docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | english_business_docstring | class FakeAcquisitionPortByLd docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | english_business_docstring | class FakePipeline docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | english_business_docstring | class FakeRedisClient docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function hset 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function hset 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function hget 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function hgetall 缺少 docstring | PENDING |
| tests/integration/test_ingest_polling_retry_to_redis.py | test | missing_public_docstring | public function pipeline 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_access_policy.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Production-like access policy integration tests.', 'Tests FileAccessPolicy, DenyAllAccessPolicy, and their', 'integration with the API audit sink.'] | PENDING |
| tests/integration/test_ingest_prodlike_access_policy.py | test | missing_public_docstring | public function policy_file 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_access_policy.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_audit_metrics_resilience.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Audit and metrics resilience tests under prodlike dependency failures.'] | PENDING |
| tests/integration/test_ingest_prodlike_audit_metrics_resilience.py | test | missing_public_docstring | public function prodlike_resilience_stack 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_audit_metrics_resilience.py | test | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_audit_metrics_resilience.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_prodlike_audit_sink.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Production-like audit sink integration tests.', 'Verifies audit events flow to PostgreSQL and/or JSONL.'] | PENDING |
| tests/integration/test_ingest_prodlike_audit_sink.py | test | missing_public_docstring | public function pg_engine 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_audit_sink.py | test | missing_public_docstring | public function pg_sf 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_endurance_smoke.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Short-duration endurance smoke for the prodlike ingest compose profile.'] | PENDING |
| tests/integration/test_ingest_prodlike_endurance_smoke.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_prodlike_kafka_fault_injection.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Kafka fault injection and recovery tests for prodlike ingest runtime.'] | PENDING |
| tests/integration/test_ingest_prodlike_kafka_fault_injection.py | test | missing_public_docstring | public function prodlike_kafka_stack 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_kafka_fault_injection.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_prodlike_kafka_publish.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Production-like Kafka publish integration tests.', 'Requires real Kafka reachable via WHALE_INGEST_KAFKA_BOOTSTRAP_SERVERS.'] | PENDING |
| tests/integration/test_ingest_prodlike_kafka_publish.py | test | missing_public_docstring | public function kafka_settings 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_kafka_publish.py | test | missing_private_helper_docstring | 复杂 private function _skip_no_kafka 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_performance_profile.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Performance profile conformance tests for ingest runtime.'] | PENDING |
| tests/integration/test_ingest_prodlike_performance_profile.py | test | missing_class_docstring | public class TestPerformanceProfileConformance 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_performance_profile.py | test | missing_public_docstring | public function perf_config 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_performance_profile.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_prodlike_postgres_fault_injection.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['PostgreSQL fault injection and recovery tests for prodlike ingest runtime.'] | PENDING |
| tests/integration/test_ingest_prodlike_postgres_fault_injection.py | test | missing_private_helper_docstring | 复杂 private function _http_status 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_postgres_fault_injection.py | test | missing_public_docstring | public function prodlike_pg_stack 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_postgres_fault_injection.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_prodlike_postgres_runtime_db.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Production-like PostgreSQL runtime DB integration tests.', 'Uses the compose-managed PostgreSQL instance. Requires:', 'WHALE_INGEST_TEST_PG_DSN env var'] | PENDING |
| tests/integration/test_ingest_prodlike_postgres_runtime_db.py | test | missing_public_docstring | public function pg_engine 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_postgres_runtime_db.py | test | missing_public_docstring | public function pg_session 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_redis_cache.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Production-like Redis cache integration tests.', 'Requires real Redis reachable via WHALE_INGEST_REDIS_HOST / port.'] | PENDING |
| tests/integration/test_ingest_prodlike_redis_cache.py | test | missing_public_docstring | public function redis_settings 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_redis_cache.py | test | missing_public_docstring | public function cache 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_redis_cache.py | test | missing_public_docstring | public function raw_client 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_redis_fault_injection.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Redis fault injection and recovery tests for prodlike ingest runtime.'] | PENDING |
| tests/integration/test_ingest_prodlike_redis_fault_injection.py | test | missing_public_docstring | public function prodlike_redis_stack 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_redis_fault_injection.py | test | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_redis_fault_injection.py | test | missing_public_docstring | public function increment 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_redis_fault_injection.py | test | missing_public_docstring | public function observe_duration 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_redis_fault_injection.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_prodlike_scheduler_backpressure.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Scheduler backpressure, missed-tick, and assignment-lag tests.'] | PENDING |
| tests/integration/test_ingest_prodlike_scheduler_backpressure.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_scheduler_backpressure.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_prodlike_worker_failover.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Worker crash, restart, fencing, and failover tests.'] | PENDING |
| tests/integration/test_ingest_prodlike_worker_failover.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/integration/test_ingest_prodlike_worker_failover.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_runtime_alembic_migration.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Alembic migration integration tests.'] | PENDING |
| tests/integration/test_ingest_runtime_alembic_postgres_matrix.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Alembic PostgreSQL migration matrix — upgrade head & verify schema.', 'PostgreSQL must be accessible for these tests.  They are skipped when no', 'PostgreSQL is available (e.g. CI without PG service).'] | PENDING |
| tests/integration/test_ingest_runtime_alembic_postgres_matrix.py | test | missing_private_helper_docstring | 复杂 private function _pg_reachable 缺少 docstring | PENDING |
| tests/integration/test_ingest_runtime_alembic_postgres_matrix.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_runtime_alembic_sqlite_matrix.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Alembic SQLite migration matrix — upgrade head & downgrade base.'] | PENDING |
| tests/integration/test_ingest_runtime_alembic_sqlite_matrix.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_runtime_db_init.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime DB initialization smoke.'] | PENDING |
| tests/integration/test_ingest_runtime_db_init.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_runtime_entrypoint_smoke.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['CLI smoke tests for ingest runtime entrypoints.'] | PENDING |
| tests/integration/test_ingest_runtime_entrypoint_smoke.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_runtime_migrate_entrypoint.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for the migrate CLI entrypoint.'] | PENDING |
| tests/integration/test_ingest_scheduler_active_standby_failover.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Active-standby scheduler failover tests.'] | PENDING |
| tests/integration/test_ingest_scheduler_active_standby_failover.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_scheduler_apscheduler_runtime.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for WorkerRuntime / APScheduler-driven ingestion.'] | PENDING |
| tests/integration/test_ingest_scheduler_apscheduler_runtime.py | test | english_business_docstring | class _NoopHandler docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_scheduler_apscheduler_runtime.py | test | missing_class_docstring | public class SlowWorker 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_apscheduler_runtime.py | test | missing_public_docstring | public function sqlite_session_factory 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_apscheduler_runtime.py | test | missing_public_docstring | public function settings 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_apscheduler_runtime.py | test | missing_public_docstring | public function repos 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_apscheduler_runtime.py | test | missing_public_docstring | public function seeded_job_repo 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_apscheduler_runtime.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_cluster_assignment.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Cluster scheduler assignment tests.'] | PENDING |
| tests/integration/test_ingest_scheduler_cluster_assignment.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_scheduler_dual_active_partitioned.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Dual-active partitioned scheduler tests.'] | PENDING |
| tests/integration/test_ingest_scheduler_dual_active_partitioned.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_scheduler_graceful_shutdown.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for WorkerRuntime graceful shutdown.'] | PENDING |
| tests/integration/test_ingest_scheduler_graceful_shutdown.py | test | missing_public_docstring | public function session_factory 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_graceful_shutdown.py | test | missing_public_docstring | public function settings 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_graceful_shutdown.py | test | missing_public_docstring | public function repos 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_missed_tick_and_stagger.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for missed_tick and stagger_offset behavior.'] | PENDING |
| tests/integration/test_ingest_scheduler_missed_tick_and_stagger.py | test | missing_class_docstring | public class SlowWorker 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_missed_tick_and_stagger.py | test | missing_public_docstring | public function session_factory 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_missed_tick_and_stagger.py | test | missing_public_docstring | public function settings 缺少 docstring | PENDING |
| tests/integration/test_ingest_scheduler_missed_tick_and_stagger.py | test | missing_public_docstring | public function repos 缺少 docstring | PENDING |
| tests/integration/test_ingest_security_partition_bundle_flow.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Security partition one-way bundle flow tests for ingest.', 'Simulates management zone export → collection zone import without', 'live API access between the two zones.'] | PENDING |
| tests/integration/test_ingest_security_partition_bundle_flow.py | test | missing_class_docstring | public class TestOneWayBundleFlow 缺少 docstring | PENDING |
| tests/integration/test_ingest_security_partition_bundle_flow.py | test | missing_public_docstring | public function session_factory 缺少 docstring | PENDING |
| tests/integration/test_ingest_security_partition_bundle_flow.py | test | missing_public_docstring | public function audit_sink 缺少 docstring | PENDING |
| tests/integration/test_ingest_security_partition_bundle_flow.py | test | missing_public_docstring | public function service 缺少 docstring | PENDING |
| tests/integration/test_ingest_security_partition_bundle_flow.py | test | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| tests/integration/test_ingest_security_partition_bundle_flow.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_security_partition_smoke.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Security partition sample-config smoke.'] | PENDING |
| tests/integration/test_ingest_security_partition_smoke.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_source_acquisition_to_redis.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration test for source server -> Redis latest-state cache.'] | PENDING |
| tests/integration/test_ingest_source_cache_message_e2e.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration test for source -> cache -> message chain.'] | PENDING |
| tests/integration/test_ingest_source_cache_message_e2e.py | test | missing_public_docstring | public function publish_snapshot 缺少 docstring | PENDING |
| tests/integration/test_ingest_source_cache_message_kafka_e2e.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Kafka container E2E for source -> cache -> message.', 'If Docker/testcontainers is unavailable, this test is skipped with CI guidance.'] | PENDING |
| tests/integration/test_ingest_source_cache_message_kafka_e2e.py | test | missing_private_helper_docstring | 复杂 private function _require_testcontainers 缺少 docstring | PENDING |
| tests/integration/test_ingest_source_cache_message_kafka_e2e.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/integration/test_ingest_subscription_strategy.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for current subscription strategy boundaries.'] | PENDING |
| tests/integration/test_ingest_subscription_strategy.py | test | missing_public_docstring | public function close 缺少 docstring | PENDING |
| tests/integration/test_ingest_subscription_strategy.py | test | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| tests/integration/test_ingest_subscription_strategy.py | test | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tests/integration/test_ingest_subscription_strategy.py | test | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_executes_usecase_handlers.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for WorkerRuntime job-type handler dispatch.'] | PENDING |
| tests/integration/test_ingest_worker_runtime_executes_usecase_handlers.py | test | english_business_docstring | class _RecordingHandler docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_worker_runtime_executes_usecase_handlers.py | test | english_business_docstring | class _RaisingHandler docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_worker_runtime_executes_usecase_handlers.py | test | missing_public_docstring | public function session_factory 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_executes_usecase_handlers.py | test | missing_public_docstring | public function settings 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_executes_usecase_handlers.py | test | missing_public_docstring | public function repos 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_executes_usecase_handlers.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_executes_usecase_handlers.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_handler_failure.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for WorkerRuntime handler failure and missing handler.'] | PENDING |
| tests/integration/test_ingest_worker_runtime_handler_failure.py | test | english_business_docstring | class _RaisingHandler docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_worker_runtime_handler_failure.py | test | missing_public_docstring | public function session_factory 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_handler_failure.py | test | missing_public_docstring | public function settings 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_handler_failure.py | test | missing_public_docstring | public function repos 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_handler_failure.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_handler_failure.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_shutdown_inflight.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for WorkerRuntime shutdown with inflight jobs.'] | PENDING |
| tests/integration/test_ingest_worker_runtime_shutdown_inflight.py | test | english_business_docstring | class _SlowHandler docstring 为英文业务描述 | PENDING |
| tests/integration/test_ingest_worker_runtime_shutdown_inflight.py | test | missing_public_docstring | public function session_factory 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_shutdown_inflight.py | test | missing_public_docstring | public function settings 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_shutdown_inflight.py | test | missing_public_docstring | public function repos 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_shutdown_inflight.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/integration/test_ingest_worker_runtime_shutdown_inflight.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/integration/test_ingest_write_lease_fencing_e2e.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Write lease / fencing / readback integration tests.'] | PENDING |
| tests/integration/test_ingest_write_lease_fencing_e2e.py | test | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| tests/integration/test_ingest_write_lease_fencing_e2e.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/integration/test_ingest_write_lease_fencing_e2e.py | test | missing_public_docstring | public function precheck 缺少 docstring | PENDING |
| tests/integration/test_ingest_write_lease_fencing_e2e.py | test | missing_public_docstring | public function readback 缺少 docstring | PENDING |
| tests/integration/test_redis_state_cache_faults.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for live Redis latest-state cache fault handling.'] | PENDING |
| tests/integration/test_sqlite_config_init.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Integration tests for the SQLite config initialization script.'] | PENDING |
| tests/performance/__init__.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tests/performance/endurance/__init__.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tests/performance/load/__init__.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tests/performance/load/conftest.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Load test fixtures: PostgreSQL + Redis + Kafka, large NodeSets.'] | PENDING |
| tests/performance/load/conftest.py | test | missing_public_docstring | public function pytest_configure 缺少 docstring | PENDING |
| tests/performance/load/conftest.py | test | missing_public_docstring | public function pg_db_url 缺少 docstring | PENDING |
| tests/performance/load/conftest.py | test | missing_public_docstring | public function pg_engine 缺少 docstring | PENDING |
| tests/performance/load/conftest.py | test | english_business_docstring | function pg_session docstring 为英文业务描述 | PENDING |
| tests/performance/load/conftest.py | test | missing_public_docstring | public function session_factory 缺少 docstring | PENDING |
| tests/performance/load/conftest.py | test | missing_public_docstring | public function redis_client 缺少 docstring | PENDING |
| tests/performance/load/conftest.py | test | missing_private_helper_docstring | 复杂 private function _factory 缺少 docstring | PENDING |
| tests/performance/load/conftest.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/performance/stress/__init__.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tests/performance/stress/test_acquisition_pipeline_stress.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Current-architecture stress smoke for ingest acquisition -> Redis latest-state c'] | PENDING |
| tests/performance/stress/test_acquisition_pipeline_stress.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Shared helpers for prodlike ingest compose, endurance, and fault tests.'] | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function compose_env 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function docker_available 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function require_docker 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function compose 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function runtime_dsn 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | english_business_docstring | function clear_runtime_engine_cache docstring 为英文业务描述 | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function runtime_session_factory 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function ensure_prodlike_stack 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function migrate_prodlike_database 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function stop_prodlike_stack 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function stop_service 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function start_service 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function restart_service 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function service_logs 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function wait_until 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | english_business_docstring | function wait_for_kafka docstring 为英文业务描述 | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function wait_for_http 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function truncate_runtime_tables 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function seed_runtime_job 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function active_assignments 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function wait_for_assignment_count 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function count_audit_events 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_public_docstring | public function read_worker_summary 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_private_helper_docstring | 复杂 private function _kafka_ok 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_private_helper_docstring | 复杂 private function _ok 缺少 docstring | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | unexplained_type_ignore | L189: 无解释的 type: ignore | PENDING |
| tests/support/ingest_prodlike_runtime.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/support/source_lab_runtime.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Helpers for using source_lab runtime modules without package-level side effects.'] | PENDING |
| tests/support/source_lab_runtime.py | test | english_business_docstring | function prepare_source_lab_runtime_imports docstring 为英文业务描述 | PENDING |
| tests/support/source_lab_runtime.py | test | english_business_docstring | function import_source_lab_module docstring 为英文业务描述 | PENDING |
| tests/support/source_lab_runtime.py | test | unexplained_type_ignore | L21: 无解释的 type: ignore | PENDING |
| tests/support/source_lab_runtime.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/__init__.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tests/unit/shared/persistence/test_scada_protocol_params.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for the new protocol parameter ORM tables (scada_protocol_param_def,', 'scada_endpoint_param_value, scada_signal_param_def, scada_signal_profile_item_pa', 'Uses in-memory SQLite to verify table creation, unique constraints, FK constrain'] | PENDING |
| tests/unit/shared/persistence/test_scada_protocol_params.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_acquisition_job_handler.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['AcquisitionJobHandler 单元测试。', '测试 handler 从 job.config_json 构造 SourceAcquisitionRequest', '并调用 SourceAcquisitionUseCase 的行为。'] | PENDING |
| tests/unit/test_acquisition_job_handler.py | test | english_business_docstring | class TestAcquisitionJobHandler docstring 为英文业务描述 | PENDING |
| tests/unit/test_acquisition_job_handler.py | test | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tests/unit/test_acquisition_job_handler.py | test | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tests/unit/test_acquisition_job_handler.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_config.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for ingest configuration resolution.'] | PENDING |
| tests/unit/test_dual_node_write_lease_conflict.py | test | english_business_docstring | class _StubFencingTokenRepository docstring 为英文业务描述 | PENDING |
| tests/unit/test_dual_node_write_lease_conflict.py | test | missing_public_docstring | public function acquire 缺少 docstring | PENDING |
| tests/unit/test_dual_node_write_lease_conflict.py | test | missing_public_docstring | public function renew 缺少 docstring | PENDING |
| tests/unit/test_dual_node_write_lease_conflict.py | test | missing_public_docstring | public function release 缺少 docstring | PENDING |
| tests/unit/test_dual_node_write_lease_conflict.py | test | missing_public_docstring | public function generate 缺少 docstring | PENDING |
| tests/unit/test_dual_node_write_lease_conflict.py | test | missing_public_docstring | public function get 缺少 docstring | PENDING |
| tests/unit/test_dual_node_write_lease_conflict.py | test | missing_public_docstring | public function validate 缺少 docstring | PENDING |
| tests/unit/test_dual_node_write_lease_conflict.py | test | missing_public_docstring | public function get 缺少 docstring | PENDING |
| tests/unit/test_dual_node_write_lease_conflict.py | test | missing_public_docstring | public function try_acquire 缺少 docstring | PENDING |
| tests/unit/test_fleet_update_selection.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for fleet update-point selection and write generation.'] | PENDING |
| tests/unit/test_iec104_backend.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for IEC 104 backend (stdout protocol parsing).'] | PENDING |
| tests/unit/test_iec104_backend.py | test | english_business_docstring | class TestIec104ParseSampleLine docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec104_backend.py | test | english_business_docstring | class TestIec104ParseWriteResult docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec104_backend.py | test | english_business_docstring | class TestIec104RawReadResult docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec104_backend.py | test | english_business_docstring | class TestIec104PreparedReadPlan docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec104_backend.py | test | english_business_docstring | class TestIec104RawWriteItemResult docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec104_source_acquisition_adapter.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for IEC 104 source acquisition adapter.'] | PENDING |
| tests/unit/test_iec104_source_write_adapter.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for IEC 104 source write adapter.'] | PENDING |
| tests/unit/test_iec61850_mms_backend.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['libiec61850 backend 单元测试。', '直接覆盖 native runner READ_RESULT/WRITE_RESULT 协议到 RawMmsReadResult/RawWriteItemRes'] | PENDING |
| tests/unit/test_iec61850_mms_backend.py | test | missing_public_docstring | public function readline 缺少 docstring | PENDING |
| tests/unit/test_iec61850_mms_backend.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_iec61850_mms_backend.py | test | missing_public_docstring | public function drain 缺少 docstring | PENDING |
| tests/unit/test_iec61850_mms_backend.py | test | unexplained_type_ignore | L60: 无解释的 type: ignore | PENDING |
| tests/unit/test_iec61850_mms_backend.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_iec61850_report_acquisition_adapter.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for Iec61850ReportSourceAcquisitionAdapter.'] | PENDING |
| tests/unit/test_iec61850_report_acquisition_adapter.py | test | missing_class_docstring | public class TestReportAdapterSupportsSubscription 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_acquisition_adapter.py | test | missing_class_docstring | public class TestReportAdapterRead 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_acquisition_adapter.py | test | missing_class_docstring | public class TestReportAdapterStartSubscription 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_acquisition_adapter.py | test | english_business_docstring | class TestReportAdapterNoSourceLabImport docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec61850_report_acquisition_adapter.py | test | missing_class_docstring | public class TestReportEventToBatch 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_acquisition_adapter.py | test | english_business_docstring | class TestReportAdapterComposition docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec61850_report_acquisition_adapter.py | test | missing_public_docstring | public function on_batch 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_acquisition_adapter.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for LibIec61850ReportBackend — report event parsing & subprocess protocol.'] | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | english_business_docstring | class TestReportLineParsing docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | english_business_docstring | class TestReportBackendErrors docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | english_business_docstring | class TestReportLineIntegration docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | english_business_docstring | class TestReportBackendErrorCallback docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | english_business_docstring | class TestReportBackendReconnect docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | missing_public_docstring | public function on_event 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | missing_public_docstring | public function on_event 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | missing_public_docstring | public function on_event 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | missing_public_docstring | public function on_event 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_iec61850_report_backend.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_iec61850_source_acquisition_adapter.py | test | english_business_docstring | class TestIec61850MmsSourceAcquisitionAdapter docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec61850_source_acquisition_adapter.py | test | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tests/unit/test_iec61850_source_acquisition_adapter.py | test | missing_public_docstring | public function setup_method 缺少 docstring | PENDING |
| tests/unit/test_iec61850_source_write_adapter.py | test | english_business_docstring | class TestIec61850MmsSourceWriteAdapter docstring 为英文业务描述 | PENDING |
| tests/unit/test_iec61850_source_write_adapter.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_iec61850_source_write_adapter.py | test | missing_public_docstring | public function setup_method 缺少 docstring | PENDING |
| tests/unit/test_iec61850_source_write_adapter.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_ingest_api_app.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['FastAPI app factory tests.'] | PENDING |
| tests/unit/test_ingest_api_app.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_audit_event_schema.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Structured ingest audit event tests.'] | PENDING |
| tests/unit/test_ingest_audit_event_schema.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_audit_redaction.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for audit event redaction.'] | PENDING |
| tests/unit/test_ingest_bundle_checksum.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Bundle checksum tests.'] | PENDING |
| tests/unit/test_ingest_bundle_checksum.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_bundle_redaction.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Bundle redaction tests.'] | PENDING |
| tests/unit/test_ingest_bundle_redaction.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_composition_injection.py | test | english_business_docstring | class _TrackingMetricsSink docstring 为英文业务描述 | PENDING |
| tests/unit/test_ingest_composition_injection.py | test | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| tests/unit/test_ingest_composition_injection.py | test | missing_public_docstring | public function increment 缺少 docstring | PENDING |
| tests/unit/test_ingest_composition_injection.py | test | missing_public_docstring | public function observe_duration 缺少 docstring | PENDING |
| tests/unit/test_ingest_composition_injection.py | test | missing_public_docstring | public function acquire 缺少 docstring | PENDING |
| tests/unit/test_ingest_composition_injection.py | test | missing_public_docstring | public function renew 缺少 docstring | PENDING |
| tests/unit/test_ingest_composition_injection.py | test | missing_public_docstring | public function validate 缺少 docstring | PENDING |
| tests/unit/test_ingest_composition_injection.py | test | missing_public_docstring | public function release 缺少 docstring | PENDING |
| tests/unit/test_ingest_composition_injection.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_job_lease.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['DB-backed lease semantics tests.'] | PENDING |
| tests/unit/test_ingest_job_lease.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Metrics event emission tests for ingest core chains.'] | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | missing_public_docstring | public function read_snapshot 缺少 docstring | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | missing_public_docstring | public function publish_snapshot 缺少 docstring | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | missing_public_docstring | public function update 缺少 docstring | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | missing_public_docstring | public function mark_alive 缺少 docstring | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | missing_public_docstring | public function mark_unavailable 缺少 docstring | PENDING |
| tests/unit/test_ingest_metrics_events.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_no_source_lab_imports.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Ensure ingest production code does not import tools.source_lab.'] | PENDING |
| tests/unit/test_ingest_no_source_lab_imports.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_observability_sink.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for lightweight ingest observability sinks.'] | PENDING |
| tests/unit/test_ingest_runtime_entrypoint.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['CLI entrypoint tests for ingest runtime.'] | PENDING |
| tests/unit/test_ingest_runtime_entrypoint.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_runtime_modes.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime mode parsing tests.'] | PENDING |
| tests/unit/test_ingest_runtime_modes.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_runtime_orm_models.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Runtime ORM model registration tests.'] | PENDING |
| tests/unit/test_ingest_runtime_orm_models.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_runtime_scheduler_import.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Import smoke for the ingest runtime scheduler package.'] | PENDING |
| tests/unit/test_ingest_runtime_scheduler_import.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_security_partition_config.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Security partition config guard tests.'] | PENDING |
| tests/unit/test_ingest_security_partition_config.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_source_adapter_capability_matrix.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Ingest adapter capability matrix guard.'] | PENDING |
| tests/unit/test_ingest_source_adapter_capability_matrix.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_write_lease.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Write lease service tests.'] | PENDING |
| tests/unit/test_ingest_write_lease.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_write_lease_fencing.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Write lease fencing tests.'] | PENDING |
| tests/unit/test_ingest_write_lease_fencing.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_ingest_write_security_profile.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for WriteSecurityProfile domain model.'] | PENDING |
| tests/unit/test_kafka_message_publisher.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for the Kafka snapshot publisher.'] | PENDING |
| tests/unit/test_kafka_message_publisher.py | test | english_business_docstring | class FakeKafkaFuture docstring 为英文业务描述 | PENDING |
| tests/unit/test_kafka_message_publisher.py | test | english_business_docstring | class FakeKafkaProducer docstring 为英文业务描述 | PENDING |
| tests/unit/test_kafka_message_publisher.py | test | english_business_docstring | class FailingKafkaProducer docstring 为英文业务描述 | PENDING |
| tests/unit/test_kafka_message_publisher.py | test | english_business_docstring | function get docstring 为英文业务描述 | PENDING |
| tests/unit/test_kafka_message_publisher.py | test | english_business_docstring | function send docstring 为英文业务描述 | PENDING |
| tests/unit/test_kafka_message_publisher.py | test | english_business_docstring | function flush docstring 为英文业务描述 | PENDING |
| tests/unit/test_kafka_message_publisher.py | test | missing_public_docstring | public function send 缺少 docstring | PENDING |
| tests/unit/test_kafka_message_publisher.py | test | missing_public_docstring | public function get 缺少 docstring | PENDING |
| tests/unit/test_kafka_message_publisher.py | test | unexplained_type_ignore | L54: 无解释的 type: ignore | PENDING |
| tests/unit/test_modbus_source_acquisition_adapter.py | test | english_business_docstring | class _MockModbusReader docstring 为英文业务描述 | PENDING |
| tests/unit/test_modbus_source_acquisition_adapter.py | test | english_business_docstring | class TestModbusSourceAcquisitionAdapter docstring 为英文业务描述 | PENDING |
| tests/unit/test_modbus_source_acquisition_adapter.py | test | missing_public_docstring | public function prepare_read 缺少 docstring | PENDING |
| tests/unit/test_modbus_source_acquisition_adapter.py | test | missing_public_docstring | public function read_prepared 缺少 docstring | PENDING |
| tests/unit/test_modbus_source_acquisition_adapter.py | test | missing_public_docstring | public function setup_method 缺少 docstring | PENDING |
| tests/unit/test_modbus_source_write_adapter.py | test | english_business_docstring | class TestModbusSourceWriteAdapter docstring 为英文业务描述 | PENDING |
| tests/unit/test_modbus_source_write_adapter.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_modbus_source_write_adapter.py | test | missing_public_docstring | public function setup_method 缺少 docstring | PENDING |
| tests/unit/test_modbus_source_write_adapter.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_opcua_source_acquisition_adapter.py | test | missing_public_docstring | public function prepare_read 缺少 docstring | PENDING |
| tests/unit/test_opcua_source_acquisition_adapter.py | test | missing_public_docstring | public function read_prepared_raw 缺少 docstring | PENDING |
| tests/unit/test_opcua_source_acquisition_adapter.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_opcua_source_write_adapter.py | test | english_business_docstring | class TestOpcUaSourceWriteAdapter docstring 为英文业务描述 | PENDING |
| tests/unit/test_opcua_source_write_adapter.py | test | english_business_docstring | class _MockReadbackReader docstring 为英文业务描述 | PENDING |
| tests/unit/test_opcua_source_write_adapter.py | test | english_business_docstring | class TestOpcUaSourceWriteAdapterReadback docstring 为英文业务描述 | PENDING |
| tests/unit/test_opcua_source_write_adapter.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_opcua_source_write_adapter.py | test | missing_public_docstring | public function setup_method 缺少 docstring | PENDING |
| tests/unit/test_opcua_source_write_adapter.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_opcua_source_write_adapter.py | test | missing_public_docstring | public function prepare_read 缺少 docstring | PENDING |
| tests/unit/test_opcua_source_write_adapter.py | test | missing_public_docstring | public function read_prepared_raw 缺少 docstring | PENDING |
| tests/unit/test_opcua_source_write_adapter.py | test | missing_public_docstring | public function setup_method 缺少 docstring | PENDING |
| tests/unit/test_opcua_source_write_adapter.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['open62541 backend 单元测试。', '这些测试直接覆盖 native runner VALUE 协议到 RawOpcUaReadResult 的解析。'] | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_public_docstring | public function readline 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_public_docstring | public function drain 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_open62541_backend.py | test | unexplained_type_ignore | L64: 无解释的 type: ignore | PENDING |
| tests/unit/test_open62541_backend.py | test | unexplained_type_ignore | L65: 无解释的 type: ignore | PENDING |
| tests/unit/test_open62541_backend.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_polling_acquisition_role.py | test | missing_public_docstring | public function update 缺少 docstring | PENDING |
| tests/unit/test_polling_acquisition_role.py | test | missing_public_docstring | public function mark_alive 缺少 docstring | PENDING |
| tests/unit/test_polling_acquisition_role.py | test | missing_public_docstring | public function mark_unavailable 缺少 docstring | PENDING |
| tests/unit/test_polling_acquisition_role.py | test | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tests/unit/test_polling_acquisition_role.py | test | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| tests/unit/test_polling_acquisition_role.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_redis_source_state_cache.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for the Redis latest-state cache adapter.'] | PENDING |
| tests/unit/test_redis_source_state_cache.py | test | english_business_docstring | class FakePipeline docstring 为英文业务描述 | PENDING |
| tests/unit/test_redis_source_state_cache.py | test | english_business_docstring | class FakeRedisClient docstring 为英文业务描述 | PENDING |
| tests/unit/test_redis_source_state_cache.py | test | missing_public_docstring | public function hset 缺少 docstring | PENDING |
| tests/unit/test_redis_source_state_cache.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/unit/test_redis_source_state_cache.py | test | missing_public_docstring | public function hset 缺少 docstring | PENDING |
| tests/unit/test_redis_source_state_cache.py | test | missing_public_docstring | public function hget 缺少 docstring | PENDING |
| tests/unit/test_redis_source_state_cache.py | test | missing_public_docstring | public function hgetall 缺少 docstring | PENDING |
| tests/unit/test_redis_source_state_cache.py | test | missing_public_docstring | public function pipeline 缺少 docstring | PENDING |
| tests/unit/test_redis_streams_message_publisher.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for the Redis Streams snapshot publisher.'] | PENDING |
| tests/unit/test_redis_streams_message_publisher.py | test | english_business_docstring | class FakeRedisStreamsClient docstring 为英文业务描述 | PENDING |
| tests/unit/test_redis_streams_message_publisher.py | test | english_business_docstring | function xadd docstring 为英文业务描述 | PENDING |
| tests/unit/test_relational_outbox_message_publisher.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for the relational outbox snapshot publisher.'] | PENDING |
| tests/unit/test_source_acquisition_port_registry.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['StaticSourceAcquisitionPortRegistry 单元测试。'] | PENDING |
| tests/unit/test_source_acquisition_port_registry.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_source_command_audit.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['SourceCommandUseCase audit tests.'] | PENDING |
| tests/unit/test_source_command_audit.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_source_command_audit.py | test | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| tests/unit/test_source_command_audit.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for AuthorizedSourceWritePort.'] | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | english_business_docstring | class _RecordingWritePort docstring 为英文业务描述 | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | english_business_docstring | class _AllowAllPolicy docstring 为英文业务描述 | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | english_business_docstring | class _DenyAllPolicy docstring 为英文业务描述 | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | english_business_docstring | class _RecordPolicy docstring 为英文业务描述 | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | missing_public_docstring | public function principal 缺少 docstring | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | missing_public_docstring | public function connection 缺少 docstring | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | missing_public_docstring | public function execution 缺少 docstring | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | english_business_docstring | function asyncio_run docstring 为英文业务描述 | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | missing_public_docstring | public function evaluate 缺少 docstring | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | missing_public_docstring | public function evaluate 缺少 docstring | PENDING |
| tests/unit/test_source_command_authorization_guard.py | test | missing_public_docstring | public function evaluate 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | english_business_docstring | class _ReleaseTrackingLease docstring 为英文业务描述 | PENDING |
| tests/unit/test_source_command_lease_release.py | test | english_business_docstring | class _PrecheckFailingPort docstring 为英文业务描述 | PENDING |
| tests/unit/test_source_command_lease_release.py | test | english_business_docstring | class _WriteFailingPort docstring 为英文业务描述 | PENDING |
| tests/unit/test_source_command_lease_release.py | test | english_business_docstring | class _ReadbackMismatchPort docstring 为英文业务描述 | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function acquire 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function renew 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function validate 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function release 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function precheck 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function readback 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function readback 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_source_command_lease_release.py | test | missing_public_docstring | public function readback 缺少 docstring | PENDING |
| tests/unit/test_source_command_use_case.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['SourceCommandUseCase 单元测试。'] | PENDING |
| tests/unit/test_source_command_use_case.py | test | english_business_docstring | class TestSourceCommandUseCase docstring 为英文业务描述 | PENDING |
| tests/unit/test_source_command_use_case.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_source_command_use_case.py | test | missing_public_docstring | public function setup_method 缺少 docstring | PENDING |
| tests/unit/test_source_command_use_case.py | test | missing_public_docstring | public function teardown_method 缺少 docstring | PENDING |
| tests/unit/test_source_command_use_case.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_source_command_use_case.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_source_command_use_case.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_source_command_use_case.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_source_command_use_case.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_source_command_use_case.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_source_command_use_case.py | test | missing_private_helper_docstring | 复杂 private function _run 缺少 docstring | PENDING |
| tests/unit/test_source_command_use_case.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_source_command_write_lease_guard.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Source command write lease guard tests.'] | PENDING |
| tests/unit/test_source_command_write_lease_guard.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_source_command_write_lease_guard.py | test | missing_public_docstring | public function acquire 缺少 docstring | PENDING |
| tests/unit/test_source_command_write_lease_guard.py | test | missing_public_docstring | public function release 缺少 docstring | PENDING |
| tests/unit/test_source_command_write_lease_guard.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_source_runtime_config_repository.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for the runtime-config repository.'] | PENDING |
| tests/unit/test_source_runtime_config_repository.py | test | missing_private_helper_docstring | 复杂 private function _session_scope 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Unit tests for the worker-local source polling kernel.'] | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function scenario 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function return_one 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function hold_slot 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function fail 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function slow_operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function fast_operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function operation 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_result 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | missing_public_docstring | public function on_error 缺少 docstring | PENDING |
| tests/unit/test_source_scheduling.py | test | unexplained_type_ignore | L182: 无解释的 type: ignore | PENDING |
| tests/unit/test_source_scheduling.py | test | unexplained_type_ignore | L542: 无解释的 type: ignore | PENDING |
| tests/unit/test_source_simulation_support_sources.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tests/unit/test_source_write_port_registry.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Source write port registry 单元测试。'] | PENDING |
| tests/unit/test_source_write_port_registry.py | test | english_business_docstring | class TestStaticSourceWritePortRegistry docstring 为英文业务描述 | PENDING |
| tests/unit/test_source_write_port_registry.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tests/unit/test_source_write_port_registry.py | test | missing_public_docstring | public function setup_method 缺少 docstring | PENDING |
| tests/unit/test_source_write_port_registry.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | english_business_docstring | class FakeSnapshotReader docstring 为英文业务描述 | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | english_business_docstring | class FakePublisher docstring 为英文业务描述 | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | english_business_docstring | class FakeFailingPublisher docstring 为英文业务描述 | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | english_business_docstring | class TestStateSnapshotPublishUseCase docstring 为英文业务描述 | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | missing_class_docstring | public class BrokenReader 缺少 docstring | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | english_business_docstring | class AlternatingPublisher docstring 为英文业务描述 | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | missing_public_docstring | public function read_snapshot 缺少 docstring | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | missing_public_docstring | public function publish_snapshot 缺少 docstring | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | missing_public_docstring | public function publish_snapshot 缺少 docstring | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | missing_public_docstring | public function read_snapshot 缺少 docstring | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | missing_public_docstring | public function publish_snapshot 缺少 docstring | PENDING |
| tests/unit/test_state_snapshot_publish_use_case.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_subscription_acquisition_role.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['SubscriptionAcquisitionRole unit tests.'] | PENDING |
| tests/unit/test_subscription_acquisition_role.py | test | english_business_docstring | class FakeStateCachePort docstring 为英文业务描述 | PENDING |
| tests/unit/test_subscription_acquisition_role.py | test | english_business_docstring | class FakeSubscriptionHandle docstring 为英文业务描述 | PENDING |
| tests/unit/test_subscription_acquisition_role.py | test | english_business_docstring | class FakeAcquisitionPort docstring 为英文业务描述 | PENDING |
| tests/unit/test_subscription_acquisition_role.py | test | missing_public_docstring | public function update 缺少 docstring | PENDING |
| tests/unit/test_subscription_acquisition_role.py | test | missing_public_docstring | public function mark_alive 缺少 docstring | PENDING |
| tests/unit/test_subscription_acquisition_role.py | test | missing_public_docstring | public function mark_unavailable 缺少 docstring | PENDING |
| tests/unit/test_subscription_acquisition_role.py | test | missing_public_docstring | public function close 缺少 docstring | PENDING |
| tests/unit/test_subscription_acquisition_role.py | test | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| tests/unit/test_subscription_acquisition_role.py | test | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tests/unit/test_subscription_acquisition_role.py | test | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_baseline.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Reconnect baseline read strategy tests for SubscriptionAcquisitionRole.'] | PENDING |
| tests/unit/test_subscription_reconnect_baseline.py | test | missing_public_docstring | public function close 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_baseline.py | test | missing_public_docstring | public function update 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_baseline.py | test | missing_public_docstring | public function mark_alive 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_baseline.py | test | missing_public_docstring | public function mark_unavailable 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_baseline.py | test | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_baseline.py | test | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_baseline.py | test | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_baseline.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_subscription_reconnect_runtime.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Subscription runtime reconnect/backoff/max-retry tests.'] | PENDING |
| tests/unit/test_subscription_reconnect_runtime.py | test | missing_public_docstring | public function close 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_runtime.py | test | missing_public_docstring | public function emit 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_runtime.py | test | missing_public_docstring | public function update 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_runtime.py | test | missing_public_docstring | public function mark_alive 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_runtime.py | test | missing_public_docstring | public function mark_unavailable 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_runtime.py | test | missing_public_docstring | public function supports_subscription 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_runtime.py | test | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_runtime.py | test | missing_public_docstring | public function start_subscription 缺少 docstring | PENDING |
| tests/unit/test_subscription_reconnect_runtime.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_worker_runtime_do_execute.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['WorkerRuntime._do_execute handler dispatch 单元测试。', '覆盖 _do_execute 的 handler dispatch 路径，不依赖数据库或 APScheduler。', '1. 存在的 handler — dispatch 并返回 True'] | PENDING |
| tests/unit/test_worker_runtime_do_execute.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/unit/test_worker_runtime_do_execute.py | test | missing_public_docstring | public function execute 缺少 docstring | PENDING |
| tests/unit/test_worker_runtime_do_execute.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Repository-local source lab tools for simulator, native runners, and profiling.', 'This package is for development and testing workflows. It is not a production', 'Clean Architecture boundary.'] | PENDING |
| tools/source_lab/access/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Protocol-agnostic source capacity scanning and field probing utilities.'] | PENDING |
| tools/source_lab/access/capacity.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Unified capacity façade that dispatches by access mode.'] | PENDING |
| tools/source_lab/access/capacity.py | production | english_business_docstring | function scan_capacity docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Shared access utilities used by polling, subscribe, and probe flows.'] | PENDING |
| tools/source_lab/access/common/access_model.py | production | english_business_docstring | class AccessMode docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/access_model.py | production | english_business_docstring | class AccessBatch docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/access_model.py | production | english_business_docstring | class AccessRunSummary docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/cpu.py | production | english_business_docstring | class CpuSampleSummary docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/cpu.py | production | english_business_docstring | class CpuSampler docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/cpu.py | production | english_business_docstring | function start docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/cpu.py | production | english_business_docstring | function stop docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/cpu.py | production | unexplained_type_ignore | L64: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/common/io.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Field export loaders that build runtime sources from DB-derived files.'] | PENDING |
| tools/source_lab/access/common/io.py | production | english_business_docstring | class FieldEndpointMetadata docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/io.py | production | english_business_docstring | class FieldServerRow docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/io.py | production | english_business_docstring | class SignalProfileItemRow docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/io.py | production | missing_private_helper_docstring | 复杂 private function _build_item_address 缺少 docstring | PENDING |
| tools/source_lab/access/common/io.py | production | english_business_docstring | function load_field_servers docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/io.py | production | english_business_docstring | function load_signal_profile_items docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/io.py | production | english_business_docstring | function build_field_runtime_sources docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/io.py | production | unexplained_type_ignore | L10: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/common/progress.py | production | english_business_docstring | class CapacityProgressBar docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/progress.py | production | english_business_docstring | function update docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/progress.py | production | english_business_docstring | function close docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/scheduling.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Scheduling helpers for capacity scan orchestration.'] | PENDING |
| tools/source_lab/access/common/scheduling.py | production | english_business_docstring | class RunnerEndpointPlan docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/scheduling.py | production | english_business_docstring | function parse_int_list_or_ramp docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/scheduling.py | production | english_business_docstring | function parse_float_list_or_ramp docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/scheduling.py | production | english_business_docstring | function iter_int_ramp docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/scheduling.py | production | english_business_docstring | function iter_float_ramp docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/scheduling.py | production | english_business_docstring | function build_source_specs docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/scheduling.py | production | english_business_docstring | function partition_specs_round_robin docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/scheduling.py | production | english_business_docstring | function resolve_mp_context docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/table.py | production | english_business_docstring | function render_fixed_width_table docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/common/utils.py | production | english_business_docstring | function normalize_protocol docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/config.py | production | english_business_docstring | class SimulatorSubscribeCapacityArgs docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/config.py | production | english_business_docstring | function from_env_for_simulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/config.py | production | english_business_docstring | function from_env_for_simulator_polling_capacity_args docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/config.py | production | english_business_docstring | function from_env_for_field_capacity docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/config.py | production | english_business_docstring | function from_env_for_probe docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/config.py | production | english_business_docstring | function from_env_for_simulator_subscribe docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/config.py | production | english_business_docstring | function from_env_for_simulator_subscribe_capacity_args docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | english_business_docstring | class FieldCapacityRow docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | english_business_docstring | class FieldCapacityRequest docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | english_business_docstring | class FieldCapacityArtifacts docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | english_business_docstring | class FieldCapacityServiceResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | missing_class_docstring | public class CpuSnapshot 缺少 docstring | PENDING |
| tools/source_lab/access/field_capacity.py | production | english_business_docstring | function print_capacity_table docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | english_business_docstring | function write_capacity_reports docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | english_business_docstring | function print_capacity_summary docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | english_business_docstring | function build_polling_capacity_rows docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | english_business_docstring | function build_subscribe_capacity_rows docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | missing_private_helper_docstring | 复杂 private function _run_polling_field_capacity 缺少 docstring | PENDING |
| tools/source_lab/access/field_capacity.py | production | english_business_docstring | function run_field_capacity docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | english_business_docstring | function run_field_capacity_from_files docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/field_capacity.py | production | missing_public_docstring | public function cpu_mean_pct 缺少 docstring | PENDING |
| tools/source_lab/access/field_capacity.py | production | missing_public_docstring | public function cpu_max_pct 缺少 docstring | PENDING |
| tools/source_lab/access/field_capacity.py | production | missing_public_docstring | public function rss_mb 缺少 docstring | PENDING |
| tools/source_lab/access/field_capacity.py | production | missing_public_docstring | public function warning 缺少 docstring | PENDING |
| tools/source_lab/access/polling/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Polling capacity scan models, metrics, and orchestration.'] | PENDING |
| tools/source_lab/access/polling/capacity.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Protocol-agnostic orchestration for capacity scan ramps.'] | PENDING |
| tools/source_lab/access/polling/capacity.py | production | english_business_docstring | function scan_source_capacity docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/capacity_rows.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Polling-specific field-capacity row builders.'] | PENDING |
| tools/source_lab/access/polling/capacity_rows.py | production | missing_class_docstring | public class CpuSnapshot 缺少 docstring | PENDING |
| tools/source_lab/access/polling/capacity_rows.py | production | english_business_docstring | function polling_row docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/capacity_rows.py | production | english_business_docstring | function build_polling_capacity_rows docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/capacity_rows.py | production | missing_public_docstring | public function cpu_mean_pct 缺少 docstring | PENDING |
| tools/source_lab/access/polling/capacity_rows.py | production | missing_public_docstring | public function cpu_max_pct 缺少 docstring | PENDING |
| tools/source_lab/access/polling/capacity_rows.py | production | missing_public_docstring | public function rss_mb 缺少 docstring | PENDING |
| tools/source_lab/access/polling/capacity_rows.py | production | missing_public_docstring | public function warning 缺少 docstring | PENDING |
| tools/source_lab/access/polling/metrics.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Metrics helpers for capacity scan evaluation.'] | PENDING |
| tools/source_lab/access/polling/metrics.py | production | english_business_docstring | class ReaderStats docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/metrics.py | production | english_business_docstring | class RunnerTrace docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/metrics.py | production | english_business_docstring | class RunnerSummary docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/metrics.py | production | english_business_docstring | class WorkerRawStats docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/metrics.py | production | english_business_docstring | function record_tick docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/metrics.py | production | english_business_docstring | function evaluate_response_periods docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/metrics.py | production | english_business_docstring | function build_level_metrics docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/metrics.py | production | english_business_docstring | function build_skip_result docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Data models for protocol-agnostic capacity scans and standalone field probes.'] | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | class CapacityMode docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | class CapacityStatus docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | class PeriodGap docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | class ResponsePeriodStats docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | class TickResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | class CapacityLevelMetrics docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | class ConfirmedLevelResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | class CapacityScanResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | class ProbeLatencyStats docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | class ServerProbeResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | class ProbeResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | function final_metrics docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | function from_env_for_simulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | english_business_docstring | function has_accepted_level docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/model.py | production | unexplained_type_ignore | L9: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/polling/profile.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Single-configuration polling profile service.'] | PENDING |
| tools/source_lab/access/polling/profile.py | production | english_business_docstring | class PollingProfileResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/profile.py | production | missing_private_helper_docstring | 复杂 private function _new_profiler 缺少 docstring | PENDING |
| tools/source_lab/access/polling/profile.py | production | english_business_docstring | function run_polling_profile docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/profile.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/access/polling/profile.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/access/polling/profile.py | production | missing_public_docstring | public function output_text 缺少 docstring | PENDING |
| tools/source_lab/access/polling/profile.py | production | unexplained_type_ignore | L30: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Legacy polling progress/detail helpers for profile and debug paths.', 'Capacity matrix output does not use this module for user-facing progress.', 'Capacity uses ``CapacityProgressBar`` for runtime progress and'] | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | class ServerCountSummary docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | function print_scan_started docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | function print_level_started docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | function print_measurement_started docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | function print_measurement_progress docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | function print_runner_started docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | function print_worker_diagnostics docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | function print_level_done docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | function print_stop_hz_ramp docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | function print_scan_finished docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | function summarize_server_count_levels docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/reporter.py | production | english_business_docstring | function print_capacity_report docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/worker.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Worker execution helpers for protocol-agnostic capacity levels.'] | PENDING |
| tools/source_lab/access/polling/worker.py | production | english_business_docstring | function run_worker_level docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/polling/worker.py | production | english_business_docstring | function run_level_once docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/probe.py | production | english_business_docstring | class ProbeWarning docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/probe.py | production | english_business_docstring | function run_probe docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/profile.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Unified profile service and façade for single-configuration profiling.'] | PENDING |
| tools/source_lab/access/profile.py | production | english_business_docstring | class FieldProfileRequest docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/profile.py | production | english_business_docstring | class FieldProfileArtifacts docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/profile.py | production | english_business_docstring | class FieldProfileServiceResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/profile.py | production | english_business_docstring | function write_profile_reports docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/profile.py | production | english_business_docstring | function print_profile_summary docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/profile.py | production | english_business_docstring | function run_field_profile docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/profile.py | production | english_business_docstring | function run_field_profile_from_files docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/profile.py | production | english_business_docstring | function run_profile docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Capacity source providers by mode and input source.'] | PENDING |
| tools/source_lab/access/providers/base.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Source providers used by protocol-agnostic polling and subscribe scans.'] | PENDING |
| tools/source_lab/access/providers/base.py | production | english_business_docstring | class SourceRuntimeSpec docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/base.py | production | english_business_docstring | class SourceProvider docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/base.py | production | english_business_docstring | function build_sources docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/base.py | production | english_business_docstring | function started docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/base.py | production | unexplained_type_ignore | L9: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/providers/expanded_field.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Decorator provider that expands field-export templates into simulator-backed sou'] | PENDING |
| tools/source_lab/access/providers/expanded_field.py | production | english_business_docstring | class ExpandedFieldSourceProvider docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/expanded_field.py | production | english_business_docstring | function build_sources docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/expanded_field.py | production | english_business_docstring | function started docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/expanded_field.py | production | unexplained_type_ignore | L10: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/providers/field.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Field-mode source provider for real endpoints without simulator lifecycle.'] | PENDING |
| tools/source_lab/access/providers/field.py | production | english_business_docstring | class FieldSourceProvider docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/field.py | production | english_business_docstring | function build_sources docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/field.py | production | english_business_docstring | function started docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/file_field.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['File-backed field source provider that only exposes validated runtime sources.'] | PENDING |
| tools/source_lab/access/providers/file_field.py | production | english_business_docstring | class FieldFileSourceProvider docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/file_field.py | production | english_business_docstring | function build_field_source_provider docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/file_field.py | production | english_business_docstring | function build_sources docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/file_field.py | production | english_business_docstring | function started docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/simulator.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Simulator-mode source provider for polling and subscribe scans.'] | PENDING |
| tools/source_lab/access/providers/simulator.py | production | english_business_docstring | class SimulatorSourceProvider docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/simulator.py | production | english_business_docstring | function from_env docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/simulator.py | production | english_business_docstring | function build_sources docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/simulator.py | production | english_business_docstring | function started docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/providers/simulator.py | production | unexplained_type_ignore | L11: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/providers/simulator.py | production | unexplained_type_ignore | L12: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/runners/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Runner helpers and adapters for polling and subscribe access scans.'] | PENDING |
| tools/source_lab/access/runners/base.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Runner interfaces used by protocol-agnostic access worker orchestration.'] | PENDING |
| tools/source_lab/access/runners/base.py | production | english_business_docstring | class CapacityRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/base.py | production | english_business_docstring | class SubscriptionRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/base.py | production | english_business_docstring | function name docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/base.py | production | english_business_docstring | function run_worker docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/base.py | production | english_business_docstring | function name docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/base.py | production | english_business_docstring | function run_worker docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/http_rest_polling.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['HTTP REST polling runner（HTTP GET 读取）。'] | PENDING |
| tools/source_lab/access/runners/http_rest_polling.py | production | english_business_docstring | class HttpRestPollingRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/http_rest_polling.py | production | missing_public_docstring | public function read_once 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec101_event.py | production | english_business_docstring | class Iec101EventRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/iec101_event.py | production | missing_public_docstring | public function read_stream_sample 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec101_event.py | production | missing_private_helper_docstring | 复杂 private function _read_serial 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec101_event.py | production | missing_private_helper_docstring | 复杂 private function _read_tcp_gateway 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec101_event.py | production | unexplained_type_ignore | L30: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/runners/iec101_polling.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 60870-5-101 polling runner（串口链路探测）。'] | PENDING |
| tools/source_lab/access/runners/iec101_polling.py | production | missing_public_docstring | public function read_once 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec101_polling.py | production | missing_private_helper_docstring | 复杂 private function _read_serial 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec101_polling.py | production | missing_private_helper_docstring | 复杂 private function _read_tcp_gateway 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec101_polling.py | production | unexplained_type_ignore | L27: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/runners/iec104_event.py | production | english_business_docstring | class Iec104EventRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/iec104_event.py | production | missing_public_docstring | public function read_stream_sample 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec104_polling.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 60870-5-104 polling runner（TCP 探测 + TESTFR）。'] | PENDING |
| tools/source_lab/access/runners/iec104_polling.py | production | english_business_docstring | class Iec104PollingRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/iec104_polling.py | production | missing_public_docstring | public function read_once 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec61850_l2_streaming.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 GOOSE/SV native L2 subscription runners.'] | PENDING |
| tools/source_lab/access/runners/iec61850_l2_streaming.py | production | english_business_docstring | class _Iec61850L2StreamingRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/iec61850_l2_streaming.py | production | english_business_docstring | class Iec61850GooseStreamingRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/iec61850_l2_streaming.py | production | english_business_docstring | class Iec61850SvStreamingRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/iec61850_l2_streaming.py | production | missing_private_helper_docstring | 复杂 private function _app_id 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec61850_l2_streaming.py | production | missing_public_docstring | public function run_worker 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec61850_mms_polling.py | production | english_business_docstring | class Iec61850MmsPollingRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/iec61850_mms_polling.py | production | missing_public_docstring | public function read_once 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec61850_report.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 Report runner backed by the native report subscriber.'] | PENDING |
| tools/source_lab/access/runners/iec61850_report.py | production | english_business_docstring | class Iec61850ReportRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/iec61850_report.py | production | missing_public_docstring | public function read_stream_sample 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec61850_report.py | production | missing_private_helper_docstring | 复杂 private function _read_lightweight_sample 缺少 docstring | PENDING |
| tools/source_lab/access/runners/iec61850_report.py | production | missing_private_helper_docstring | 复杂 private function _read_native_sample 缺少 docstring | PENDING |
| tools/source_lab/access/runners/modbus_rtu_polling.py | production | english_business_docstring | class ModbusRtuPollingRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/modbus_rtu_polling.py | production | missing_public_docstring | public function read_once 缺少 docstring | PENDING |
| tools/source_lab/access/runners/modbus_rtu_polling.py | production | missing_private_helper_docstring | 复杂 private function _read_once_serial 缺少 docstring | PENDING |
| tools/source_lab/access/runners/modbus_rtu_polling.py | production | missing_private_helper_docstring | 复杂 private function _read_once_tcp_gateway 缺少 docstring | PENDING |
| tools/source_lab/access/runners/modbus_rtu_polling.py | production | unexplained_type_ignore | L56: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/runners/modbus_tcp_polling.py | production | english_business_docstring | class ModbusTcpPollingRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/modbus_tcp_polling.py | production | missing_public_docstring | public function read_once 缺少 docstring | PENDING |
| tools/source_lab/access/runners/mqtt_subscription.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['MQTT topic subscribe runner（原生 socket 协议握手）。'] | PENDING |
| tools/source_lab/access/runners/mqtt_subscription.py | production | english_business_docstring | class MqttSubscriptionRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/mqtt_subscription.py | production | missing_public_docstring | public function read_stream_sample 缺少 docstring | PENDING |
| tools/source_lab/access/runners/native_cmd.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Native C executable capacity runner — delegates timing loop to the C process.', 'The C executable handles the full timing loop internally. Python manages process', 'lifecycle and parses the stdout protocol: READY / SAMPLE / BATCH / SUMMARY / DON'] | PENDING |
| tools/source_lab/access/runners/native_cmd.py | production | english_business_docstring | class NativeRunnerUnavailableError docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/native_cmd.py | production | english_business_docstring | class _NativeSession docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/native_cmd.py | production | english_business_docstring | class NativeCmdCapacityRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/native_cmd.py | production | english_business_docstring | function check_available docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/native_cmd.py | production | english_business_docstring | function build_command docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/native_cmd.py | production | missing_public_docstring | public function run_worker 缺少 docstring | PENDING |
| tools/source_lab/access/runners/native_process.py | production | english_business_docstring | function stop_native_process docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/native_runner_map.py | production | missing_public_docstring | public function build_command 缺少 docstring | PENDING |
| tools/source_lab/access/runners/native_runner_map.py | production | missing_public_docstring | public function check_available 缺少 docstring | PENDING |
| tools/source_lab/access/runners/native_runner_map.py | production | missing_public_docstring | public function build_command 缺少 docstring | PENDING |
| tools/source_lab/access/runners/native_runner_map.py | production | missing_public_docstring | public function build_command 缺少 docstring | PENDING |
| tools/source_lab/access/runners/native_runner_map.py | production | missing_public_docstring | public function check_available 缺少 docstring | PENDING |
| tools/source_lab/access/runners/native_runner_map.py | production | missing_public_docstring | public function build_command 缺少 docstring | PENDING |
| tools/source_lab/access/runners/native_runner_map.py | production | missing_public_docstring | public function build_command 缺少 docstring | PENDING |
| tools/source_lab/access/runners/open62541_serial_polling.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['OPC UA open62541 serial polling runner adapter for capacity scans and short prob'] | PENDING |
| tools/source_lab/access/runners/open62541_serial_polling.py | production | english_business_docstring | class ParsedRunnerResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_serial_polling.py | production | english_business_docstring | class _RunnerSessionResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_serial_polling.py | production | english_business_docstring | class OpcUaOpen62541CapacityRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_serial_polling.py | production | english_business_docstring | function parse_result_line docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_serial_polling.py | production | english_business_docstring | function parse_summary_line docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_serial_polling.py | production | english_business_docstring | function run_serial_polling_probe docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_serial_polling.py | production | english_business_docstring | function run_serial_polling_worker docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_serial_polling.py | production | english_business_docstring | function run_worker docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_serial_polling.py | production | unexplained_type_ignore | L13: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['OPC UA open62541 subscription runner adapter for subscription scans.'] | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | english_business_docstring | class ParsedSubscribeNotify docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | english_business_docstring | class ParsedSubscribeSummary docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | english_business_docstring | class ParsedSubscribeEndpointDiag docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | english_business_docstring | class _RunnerSessionResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | english_business_docstring | class OpcUaOpen62541SubscribeRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | english_business_docstring | function parse_notify_line docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | english_business_docstring | function parse_summary_line docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | english_business_docstring | function parse_endpoint_diag_line docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | english_business_docstring | function run_open62541_subscribe_worker docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | english_business_docstring | function run_worker docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/open62541_subscription.py | production | unexplained_type_ignore | L12: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/runners/protocol.py | production | english_business_docstring | function read_protocol_line docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/protocol.py | production | english_business_docstring | function drain_stderr docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/protocol.py | production | english_business_docstring | function start_stderr_drain_thread docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/protocol.py | production | english_business_docstring | function record_stdout_noise docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/protocol.py | production | english_business_docstring | function record_stderr docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/protocol.py | production | english_business_docstring | function render_context docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Multi-protocol runner registry with unified triple capability model.', 'The capability model has been upgraded from protocol-only to a triple of', '``(application_protocol, service_type, transport)``.  CLI flags and'] | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | class RunnerInfo docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function normalize_protocol docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function list_supported_protocols docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function get_protocol_capability docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function get_implementation_level docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function get_backend docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function get_limitation docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function get_current_implementation_level docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function get_target_implementation_level docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function supports_access_mode docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function probe_mode_for_protocol docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function list_service_capabilities docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function get_service_capability docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function resolve_service_triple docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function build_capacity_runner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function build_subscription_runner docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runners/registry.py | production | english_business_docstring | function actual_runtime_availability docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/runtime/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Dynamic endpoint runtime API for source_lab round1.'] | PENDING |
| tools/source_lab/access/runtime/continuity_model.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Continuity metric models for endpoint-level runtime validation.'] | PENDING |
| tools/source_lab/access/runtime/continuity_model.py | production | missing_class_docstring | public class EndpointContinuityMetrics 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_model.py | production | missing_public_docstring | public function to_dict 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_model.py | production | missing_public_docstring | public function from_dict 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Continuity monitor for endpoint-level dynamic runtime validation.'] | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_class_docstring | public class ContinuityMonitor 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function ensure_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function bind_runtime 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function record_start 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function record_stop 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function record_pause 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function record_expected_tick 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function record_stream_drop 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function record_sample 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function record_event 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function tag_operation 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function snapshot 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/continuity_monitor.py | production | missing_public_docstring | public function load_snapshot 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/dynamic_cli.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Stable JSON CLI for dynamic endpoint runtime operations.'] | PENDING |
| tools/source_lab/access/runtime/dynamic_cli.py | production | missing_public_docstring | public function build_registry 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/dynamic_cli.py | production | missing_private_helper_docstring | 复杂 private function _validate_endpoint_payload 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/dynamic_cli.py | production | missing_public_docstring | public function validate_accepted_state_payload 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/dynamic_cli.py | production | missing_public_docstring | public function main 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Endpoint runtime registry with journaling, validation and recovery.'] | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_class_docstring | public class RegistryOperationResult 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_class_docstring | public class EndpointRuntimeRegistry 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_public_docstring | public function add_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_public_docstring | public function update_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_public_docstring | public function pause_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_public_docstring | public function resume_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_public_docstring | public function stop_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_public_docstring | public function delete_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_public_docstring | public function replace_points 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_public_docstring | public function status 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_public_docstring | public function list_status 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_public_docstring | public function get_config 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_public_docstring | public function recover 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_registry.py | production | missing_private_helper_docstring | 复杂 private function _restore_old_session 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_runtime.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Endpoint-level runtime models for dynamic source_lab adjustment.'] | PENDING |
| tools/source_lab/access/runtime/endpoint_runtime.py | production | missing_class_docstring | public class EndpointMode 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_runtime.py | production | missing_class_docstring | public class EndpointRuntimeState 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_runtime.py | production | missing_class_docstring | public class EndpointRuntime 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_runtime.py | production | missing_public_docstring | public function utc_now_iso 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_runtime.py | production | missing_public_docstring | public function redact_sensitive_mapping 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_runtime.py | production | missing_public_docstring | public function expected_period_ms 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_runtime.py | production | missing_public_docstring | public function to_dict 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_runtime.py | production | missing_public_docstring | public function from_dict 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_runtime.py | production | missing_public_docstring | public function to_dict 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/endpoint_runtime.py | production | missing_public_docstring | public function from_dict 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/native_interactive_control.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Capability metadata for native runner interactive control boundaries.'] | PENDING |
| tools/source_lab/access/runtime/operation_journal.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Operation journal for endpoint-level runtime mutations.'] | PENDING |
| tools/source_lab/access/runtime/operation_journal.py | production | missing_class_docstring | public class OperationJournalEntry 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/operation_journal.py | production | missing_public_docstring | public function to_dict 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/operation_journal.py | production | missing_public_docstring | public function create 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/session_manager.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Endpoint session manager using endpoint-scoped replacement threads.'] | PENDING |
| tools/source_lab/access/runtime/session_manager.py | production | missing_class_docstring | public class NativeSessionHandle 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/session_manager.py | production | missing_class_docstring | public class EndpointSessionManager 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/session_manager.py | production | missing_public_docstring | public function start_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/session_manager.py | production | missing_public_docstring | public function pause_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/session_manager.py | production | missing_public_docstring | public function resume_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/session_manager.py | production | missing_public_docstring | public function stop_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/session_manager.py | production | missing_public_docstring | public function replace_endpoint 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/session_manager.py | production | missing_private_helper_docstring | 复杂 private function _run_endpoint_loop 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/session_manager.py | production | missing_private_helper_docstring | 复杂 private function _run_polling_loop 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/session_manager.py | production | missing_private_helper_docstring | 复杂 private function _run_subscription_loop 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/stagger_coordinator.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Endpoint stagger offset coordinator.'] | PENDING |
| tools/source_lab/access/runtime/stagger_coordinator.py | production | missing_class_docstring | public class StaggerCoordinator 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/stagger_coordinator.py | production | missing_public_docstring | public function assign_offset 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/stagger_coordinator.py | production | missing_public_docstring | public function preserve_offset 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/stagger_coordinator.py | production | missing_public_docstring | public function delete_offset 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/stagger_coordinator.py | production | missing_public_docstring | public function snapshot 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/stagger_coordinator.py | production | missing_public_docstring | public function load_snapshot 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['File-backed runtime state store with lock, checksum, retention and repair.'] | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_class_docstring | public class SnapshotLoadResult 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_class_docstring | public class RecoveryLoadBundle 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_class_docstring | public class RuntimeStateStore 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function errors 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function selected_backups 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function locked 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function save_accepted_endpoints 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function load_accepted_endpoints 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function save_registry 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function load_registry 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function save_runtime_snapshot 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function load_runtime_snapshot 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function save_continuity_snapshot 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function load_continuity_snapshot 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function load_recovery_bundle 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function export_accepted_state 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function import_accepted_state 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function dump_continuity 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function dump_registry 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function inspect_state_store 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function repair_state_store 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function append_journal_entry 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function load_journal_entries 缺少 docstring | PENDING |
| tools/source_lab/access/runtime/state_store.py | production | missing_public_docstring | public function validate_accepted_state_bundle 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Subscribe scan models, metrics, capacity, and orchestration.'] | PENDING |
| tools/source_lab/access/subscribe/capacity.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Subscribe capacity service facade and public exports.', 'This module is the stable subscribe-capacity entrypoint for callers that need', 'matrix planning plus execution in one call.'] | PENDING |
| tools/source_lab/access/subscribe/capacity.py | production | english_business_docstring | function scan_subscribe_capacity_service docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/capacity_model.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Subscribe capacity result models.'] | PENDING |
| tools/source_lab/access/subscribe/capacity_model.py | production | english_business_docstring | class SubscribeCapacityComboResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/capacity_model.py | production | english_business_docstring | class SubscribeCapacityLimitSummary docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/capacity_model.py | production | english_business_docstring | class SubscribeCapacityResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/capacity_plan.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Subscribe capacity matrix planning helpers.'] | PENDING |
| tools/source_lab/access/subscribe/capacity_plan.py | production | english_business_docstring | class SubscribeCapacityMatrixPlan docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/capacity_plan.py | production | english_business_docstring | function combo_count docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/capacity_plan.py | production | english_business_docstring | function validate docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/capacity_rows.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Subscribe-specific capacity row builders and status helpers.'] | PENDING |
| tools/source_lab/access/subscribe/capacity_rows.py | production | missing_class_docstring | public class CpuSnapshot 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/capacity_rows.py | production | english_business_docstring | function sample_hz_to_interval_ms docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/capacity_rows.py | production | english_business_docstring | function status_for_subscribe_level docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/capacity_rows.py | production | english_business_docstring | function subscribe_row docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/capacity_rows.py | production | english_business_docstring | function build_subscribe_capacity_rows docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/capacity_rows.py | production | missing_public_docstring | public function cpu_mean_pct 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/capacity_rows.py | production | missing_public_docstring | public function cpu_max_pct 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/capacity_rows.py | production | missing_public_docstring | public function rss_mb 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/capacity_rows.py | production | missing_public_docstring | public function warning 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/capacity_scan.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Subscribe capacity matrix execution.'] | PENDING |
| tools/source_lab/access/subscribe/capacity_scan.py | production | english_business_docstring | function scan_subscribe_capacity docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/metrics.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Metrics helpers for subscription scan evaluation.'] | PENDING |
| tools/source_lab/access/subscribe/metrics.py | production | english_business_docstring | function build_subscribe_level_metrics docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Models for protocol-agnostic subscription scans and reporting.'] | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | class SubscribeRunnerTrace docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | class SubscribePeriodGapTrace docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | class SubscribeFlushLagTrace docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | class SubscribeEndpointDispatchTrace docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | class SubscribeWorkerRawStats docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | class SubscribeLevelMetrics docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | class SubscribeLevelResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | class SubscribeScanResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | class SubscribeReportRow docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | class _GroupedBatches docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | function final_metrics docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/model.py | production | english_business_docstring | function has_accepted_level docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/profile.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Single-configuration subscribe profile service.'] | PENDING |
| tools/source_lab/access/subscribe/profile.py | production | english_business_docstring | class SubscribeProfileResult docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/profile.py | production | missing_private_helper_docstring | 复杂 private function _new_profiler 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/profile.py | production | english_business_docstring | function run_subscribe_profile docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/profile.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/profile.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/profile.py | production | missing_public_docstring | public function output_text 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/profile.py | production | unexplained_type_ignore | L30: 无解释的 type: ignore | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Legacy subscribe progress/detail helpers for profile and debug paths.', 'Capacity matrix output does not use this module for progress or table rendering.', 'Capacity uses ``CapacityProgressBar`` for runtime progress and'] | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | english_business_docstring | class SubscribeProgressReporter docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | english_business_docstring | function print_subscribe_scan_started docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | english_business_docstring | function print_subscribe_level_started docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | english_business_docstring | function print_subscribe_level_done docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | english_business_docstring | function print_subscribe_stop_ramp docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | english_business_docstring | function print_subscribe_scan_finished docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | english_business_docstring | function print_subscribe_capacity_table docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | english_business_docstring | function print_subscribe_report docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | missing_public_docstring | public function from_config 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | missing_public_docstring | public function scan_started 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | missing_public_docstring | public function level_started 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | missing_public_docstring | public function level_done 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | missing_public_docstring | public function stop_ramp 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/reporter.py | production | missing_public_docstring | public function scan_finished 缺少 docstring | PENDING |
| tools/source_lab/access/subscribe/scan.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Protocol-agnostic orchestration for subscription scan ramps.'] | PENDING |
| tools/source_lab/access/subscribe/scan.py | production | english_business_docstring | function scan_source_subscriptions docstring 为英文业务描述 | PENDING |
| tools/source_lab/access/subscribe/worker.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Worker execution helpers for protocol-agnostic subscription levels.'] | PENDING |
| tools/source_lab/access/subscribe/worker.py | production | english_business_docstring | function run_subscribe_level_once docstring 为英文业务描述 | PENDING |
| tools/source_lab/contracts.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Internal typing contracts for source_lab.', 'This module is a lightweight tool-side typing helper. It is not a', 'production ports/adapters architecture boundary.'] | PENDING |
| tools/source_lab/contracts.py | production | english_business_docstring | class SourceSimulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/contracts.py | production | missing_public_docstring | public function endpoint 缺少 docstring | PENDING |
| tools/source_lab/contracts.py | production | missing_public_docstring | public function name 缺少 docstring | PENDING |
| tools/source_lab/contracts.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/contracts.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/contracts.py | production | missing_public_docstring | public function writes 缺少 docstring | PENDING |
| tools/source_lab/factory.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Factory helpers for source_lab simulators.'] | PENDING |
| tools/source_lab/factory.py | production | english_business_docstring | function build_simulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/field_capacity.py | production | english_business_docstring | function main docstring 为英文业务描述 | PENDING |
| tools/source_lab/field_probe.py | production | english_business_docstring | function main docstring 为英文业务描述 | PENDING |
| tools/source_lab/field_profile.py | production | english_business_docstring | function main docstring 为英文业务描述 | PENDING |
| tools/source_lab/fleet.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Simulator fleet lifecycle helpers for source_lab tests and profiles.'] | PENDING |
| tools/source_lab/fleet.py | production | english_business_docstring | class SourceSimulatorFleet docstring 为英文业务描述 | PENDING |
| tools/source_lab/fleet.py | production | english_business_docstring | function create docstring 为英文业务描述 | PENDING |
| tools/source_lab/fleet.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/fleet.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/fleet.py | production | missing_public_docstring | public function start_source 缺少 docstring | PENDING |
| tools/source_lab/fleet.py | production | missing_public_docstring | public function stop_source 缺少 docstring | PENDING |
| tools/source_lab/fleet.py | production | missing_public_docstring | public function restart_source 缺少 docstring | PENDING |
| tools/source_lab/fleet.py | production | missing_public_docstring | public function status_source 缺少 docstring | PENDING |
| tools/source_lab/fleet.py | production | missing_public_docstring | public function update_source_values 缺少 docstring | PENDING |
| tools/source_lab/fleet.py | production | missing_private_helper_docstring | 复杂 private function _resolve_source_index 缺少 docstring | PENDING |
| tools/source_lab/fleet.py | production | unexplained_type_ignore | L265: 无解释的 type: ignore | PENDING |
| tools/source_lab/model.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Data models for source lab simulators and profile tests.'] | PENDING |
| tools/source_lab/model.py | production | english_business_docstring | class SourceConnection docstring 为英文业务描述 | PENDING |
| tools/source_lab/model.py | production | english_business_docstring | class SimulatedPoint docstring 为英文业务描述 | PENDING |
| tools/source_lab/model.py | production | english_business_docstring | class SimulatedSource docstring 为英文业务描述 | PENDING |
| tools/source_lab/model.py | production | english_business_docstring | function from_protocol docstring 为英文业务描述 | PENDING |
| tools/source_lab/model.py | production | missing_public_docstring | public function key 缺少 docstring | PENDING |
| tools/source_lab/model.py | production | missing_public_docstring | public function locator 缺少 docstring | PENDING |
| tools/source_lab/model.py | production | missing_public_docstring | public function display_name 缺少 docstring | PENDING |
| tools/source_lab/model.py | production | missing_public_docstring | public function point_kind 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['BaseSimulatorFacade — 默认 NOT_IMPLEMENTED 的基类。'] | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | missing_public_docstring | public function health 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | missing_public_docstring | public function load_points 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | missing_public_docstring | public function subscribe 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | missing_public_docstring | public function report 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_base_facade.py | production | missing_public_docstring | public function update_values 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_interactive_runner.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Native interactive runner — subprocess stdin/stdout protocol helper.', 'Launches a compiled C runner in interactive mode (no CLI args) and', 'communicates via tab-separated commands on stdin, tab-separated result'] | PENDING |
| tools/source_lab/protocols/common/_interactive_runner.py | production | english_business_docstring | class NativeInteractiveRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/_interactive_runner.py | production | missing_public_docstring | public function running 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/_interactive_runner.py | production | english_business_docstring | function start docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/_interactive_runner.py | production | english_business_docstring | function command docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/_interactive_runner.py | production | english_business_docstring | function stop docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulator_facade.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['ServerSimulatorFacade — 统一的 Server Simulator Facade 契约。'] | PENDING |
| tools/source_lab/protocols/common/simulator_facade.py | production | english_business_docstring | class ServerSimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulator_facade.py | production | english_business_docstring | function report docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulator_models.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['ServerSimulatorFacade 数据模型。'] | PENDING |
| tools/source_lab/protocols/common/simulator_models.py | production | english_business_docstring | class SimulatorHealth docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulator_models.py | production | english_business_docstring | class SimulatorCapabilities docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | english_business_docstring | class ModbusTcpSimulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | english_business_docstring | class Iec104Simulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | english_business_docstring | class Iec61850MmsSimulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | english_business_docstring | class Iec61850ReportSimulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | english_business_docstring | class MqttSimulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | english_business_docstring | class HttpRestSimulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | english_business_docstring | class ModbusRtuSimulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | english_business_docstring | class Iec101Simulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function endpoint 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function name 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function writes 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function endpoint 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function name 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function writes 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function do_GET 缺少 docstring | PENDING |
| tools/source_lab/protocols/common/simulators.py | production | missing_public_docstring | public function log_message 缺少 docstring | PENDING |
| tools/source_lab/protocols/http_rest/simulator.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['HTTP REST ServerSimulatorFacade 实现。'] | PENDING |
| tools/source_lab/protocols/http_rest/simulator.py | production | english_business_docstring | class HttpRestSimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/http_rest/simulator.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/http_rest/simulator.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/http_rest/simulator.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/http_rest/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/http_rest/simulator.py | production | missing_public_docstring | public function health 缺少 docstring | PENDING |
| tools/source_lab/protocols/http_rest/simulator.py | production | missing_public_docstring | public function load_points 缺少 docstring | PENDING |
| tools/source_lab/protocols/http_rest/simulator.py | production | missing_public_docstring | public function update_values 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec101/simulator.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC101 ServerSimulatorFacade 实现。'] | PENDING |
| tools/source_lab/protocols/iec101/simulator.py | production | english_business_docstring | class Iec101SimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/iec101/simulator.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec101/simulator.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec101/simulator.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec101/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec101/simulator.py | production | missing_public_docstring | public function health 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec101/simulator.py | production | missing_public_docstring | public function load_points 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec101/simulator.py | production | missing_public_docstring | public function update_values 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | english_business_docstring | class Iec104SimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | missing_public_docstring | public function health 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | missing_public_docstring | public function load_points 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | missing_public_docstring | public function update_values 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | unexplained_type_ignore | L45: 无解释的 type: ignore | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | unexplained_type_ignore | L48: 无解释的 type: ignore | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | unexplained_type_ignore | L51: 无解释的 type: ignore | PENDING |
| tools/source_lab/protocols/iec104/simulator.py | production | unexplained_type_ignore | L54: 无解释的 type: ignore | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['IEC61850 ServerSimulatorFacade 实现（MMS / Report / GOOSE / SV）。', 'MMS 和 Report facade 分别启动对应的 native C runner 子进程，', 'MMS 读写使用 iec61850_mms_client_runner（交互模式），'] | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | english_business_docstring | class Iec61850MmsSimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | english_business_docstring | class Iec61850ReportSimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | english_business_docstring | class Iec61850GooseSimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | english_business_docstring | class Iec61850SvSimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_private_helper_docstring | 复杂 private function _l2_app_id 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_private_helper_docstring | 复杂 private function _l2_interval_ms 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_private_helper_docstring | 复杂 private function _l2_sample_rate_hz 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_private_helper_docstring | 复杂 private function _start_l2_publisher 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_private_helper_docstring | 复杂 private function _stop_l2_publisher 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_private_helper_docstring | 复杂 private function _probe_l2_subscriber 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function health 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function load_points 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function update_values 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | english_business_docstring | function subscribe docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | english_business_docstring | function report docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function health 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function subscribe 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function health 缺少 docstring | PENDING |
| tools/source_lab/protocols/iec61850/simulator.py | production | missing_public_docstring | public function subscribe 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Modbus ServerSimulatorFacade 实现（含 modbus_tcp / modbus_rtu）。'] | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | english_business_docstring | class ModbusTcpSimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | english_business_docstring | class ModbusRtuSimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_private_helper_docstring | 复杂 private function _start_sim 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function health 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function load_points 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function update_values 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | english_business_docstring | function read docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/modbus/simulator.py | production | unexplained_type_ignore | L58: 无解释的 type: ignore | PENDING |
| tools/source_lab/protocols/mqtt/simulator.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['MQTT ServerSimulatorFacade 实现。'] | PENDING |
| tools/source_lab/protocols/mqtt/simulator.py | production | english_business_docstring | class MqttSimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/mqtt/simulator.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/mqtt/simulator.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/mqtt/simulator.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/mqtt/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/mqtt/simulator.py | production | missing_public_docstring | public function health 缺少 docstring | PENDING |
| tools/source_lab/protocols/mqtt/simulator.py | production | missing_public_docstring | public function load_points 缺少 docstring | PENDING |
| tools/source_lab/protocols/mqtt/simulator.py | production | missing_public_docstring | public function read 缺少 docstring | PENDING |
| tools/source_lab/protocols/mqtt/simulator.py | production | missing_public_docstring | public function update_values 缺少 docstring | PENDING |
| tools/source_lab/protocols/opcua/__init__.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['OPC UA simulator backends and helpers for source_lab.'] | PENDING |
| tools/source_lab/protocols/opcua/address_space.py | production | english_business_docstring | function render_nodeset_xml docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['OPC UA ServerSimulatorFacade 实现。'] | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | english_business_docstring | class OpcUaSimulatorFacade docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | missing_public_docstring | public function protocol 缺少 docstring | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | missing_public_docstring | public function capabilities 缺少 docstring | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | missing_public_docstring | public function stop 缺少 docstring | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | missing_public_docstring | public function health 缺少 docstring | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | missing_public_docstring | public function load_points 缺少 docstring | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | missing_public_docstring | public function update_values 缺少 docstring | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | missing_public_docstring | public function datachange_notification 缺少 docstring | PENDING |
| tools/source_lab/protocols/opcua/simulator.py | production | unexplained_type_ignore | L124: 无解释的 type: ignore | PENDING |
| tools/source_lab/protocols/registry.py | production | english_business_docstring | function create_server_simulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/protocols/registry.py | production | unexplained_type_ignore | L99: 无解释的 type: ignore | PENDING |
| tools/source_lab/sources.py | production | english_business_docstring | module docstring 疑似英文业务描述: ['Shared source-building helpers for OPC UA load tests.'] | PENDING |
| tools/source_lab/sources.py | production | missing_class_docstring | public class PortAllocator 缺少 docstring | PENDING |
| tools/source_lab/sources.py | production | missing_private_helper_docstring | 复杂 private function _env_int_inclusive 缺少 docstring | PENDING |
| tools/source_lab/sources.py | production | english_business_docstring | function choose_available_port docstring 为英文业务描述 | PENDING |
| tools/source_lab/sources.py | production | english_business_docstring | function assign_dynamic_port docstring 为英文业务描述 | PENDING |
| tools/source_lab/sources.py | production | english_business_docstring | function build_opcua_source_from_repository docstring 为英文业务描述 | PENDING |
| tools/source_lab/sources.py | production | english_business_docstring | function build_multi_sources docstring 为英文业务描述 | PENDING |
| tools/source_lab/sources.py | production | english_business_docstring | function build_opcua_endpoint docstring 为英文业务描述 | PENDING |
| tools/source_lab/sources.py | production | english_business_docstring | function from_env docstring 为英文业务描述 | PENDING |
| tools/source_lab/sources.py | production | english_business_docstring | function from_range docstring 为英文业务描述 | PENDING |
| tools/source_lab/sources.py | production | english_business_docstring | function allocate_many docstring 为英文业务描述 | PENDING |
| tools/source_lab/sources.py | production | unexplained_type_ignore | L11: 无解释的 type: ignore | PENDING |
| tools/source_lab/tests/__init__.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/__init__.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function choose_port 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function build_http_source 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function build_modbus_source 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function build_mqtt_source 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function build_opcua_source 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function build_iec61850_report_source 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function build_goose_source 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function build_sv_source 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function runtime_spec 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function polling_config 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function subscribe_config 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function report_config 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function streaming_config 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function build_registry 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function build_native_registry 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function shutdown_registry 缺少 docstring | PENDING |
| tools/source_lab/tests/access/_dynamic_runtime_test_utils.py | test | missing_public_docstring | public function wait_for_metric_growth 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_config.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for capacity and probe config env parsing.'] | PENDING |
| tools/source_lab/tests/access/test_access_config.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_access_facades.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for unified access facades that dispatch by access_mode.'] | PENDING |
| tools/source_lab/tests/access/test_access_facades.py | test | missing_public_docstring | public function build_sources 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_facades.py | test | missing_public_docstring | public function started 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_facades.py | test | missing_public_docstring | public function run_worker 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_facades.py | test | missing_public_docstring | public function run_worker 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_facades.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_access_metrics.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for access metrics helpers.'] | PENDING |
| tools/source_lab/tests/access/test_access_metrics.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_access_probe.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for standalone field probe behavior.'] | PENDING |
| tools/source_lab/tests/access/test_access_probe.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_access_probe_protocol_handshake.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Protocol-specific probe handshake dispatch tests.'] | PENDING |
| tools/source_lab/tests/access/test_access_probe_protocol_handshake.py | test | unexplained_type_ignore | L7: 无解释的 type: ignore | PENDING |
| tools/source_lab/tests/access/test_access_probe_protocol_handshake.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_access_probe_protocol_semantics.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Protocol semantic probe tests for MQTT and IEC61850 report.'] | PENDING |
| tools/source_lab/tests/access/test_access_probe_protocol_semantics.py | test | missing_public_docstring | public function settimeout 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_probe_protocol_semantics.py | test | missing_public_docstring | public function sendall 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_probe_protocol_semantics.py | test | missing_public_docstring | public function recv 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_probe_protocol_semantics.py | test | unexplained_type_ignore | L10: 无解释的 type: ignore | PENDING |
| tools/source_lab/tests/access/test_access_probe_protocol_semantics.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_access_progress_reporting.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for runtime progress output during capacity scans.'] | PENDING |
| tools/source_lab/tests/access/test_access_progress_reporting.py | test | missing_public_docstring | public function build_sources 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_progress_reporting.py | test | missing_public_docstring | public function started 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_progress_reporting.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_access_reporter.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for capacity reporter summary semantics.'] | PENDING |
| tools/source_lab/tests/access/test_access_reporter.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_access_scheduling.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for access scheduling helpers.'] | PENDING |
| tools/source_lab/tests/access/test_access_scheduling.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_access_structure.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for access package structure and entrypoint imports.'] | PENDING |
| tools/source_lab/tests/access/test_access_structure.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_access_worker.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for runner-injected worker orchestration.'] | PENDING |
| tools/source_lab/tests/access/test_access_worker.py | test | missing_public_docstring | public function run_worker 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_worker.py | test | missing_public_docstring | public function result 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_worker.py | test | missing_public_docstring | public function submit 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_access_worker.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_capacity_progress.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for capacity progress bar rendering.'] | PENDING |
| tools/source_lab/tests/access/test_capacity_progress.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_capacity_reporter.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for summary-only capacity table rendering.'] | PENDING |
| tools/source_lab/tests/access/test_capacity_reporter.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_capacity_rows.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for final-attempt metric selection in capacity rows.'] | PENDING |
| tools/source_lab/tests/access/test_capacity_rows.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_capacity_service.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for production field-capacity service functions.'] | PENDING |
| tools/source_lab/tests/access/test_capacity_service.py | test | missing_public_docstring | public function build_sources 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_capacity_service.py | test | missing_public_docstring | public function started 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_capacity_service.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_public_docstring | public function to_dict 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_public_docstring | public function list_status 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_public_docstring | public function add_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_public_docstring | public function update_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_public_docstring | public function pause_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_public_docstring | public function resume_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_public_docstring | public function stop_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_public_docstring | public function delete_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_public_docstring | public function replace_points 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_public_docstring | public function status 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli.py | test | missing_public_docstring | public function recover 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_cli_accepted_state.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_endpoint_patch_matrix.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_goose_sv_permission_gate.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py | test | missing_private_helper_docstring | 复杂 private function _l2_runtime_status 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py | test | missing_private_helper_docstring | 复杂 private function _wait_for_event_growth 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_iec61850_report_endpoint_adjustment.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_iec61850_report_endpoint_adjustment.py | test | missing_public_docstring | public function fail_once 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_iec61850_report_endpoint_adjustment.py | test | missing_public_docstring | public function fail_once 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_native_interactive_control_boundary.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_native_runner_isolation.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_native_runner_isolation.py | test | missing_public_docstring | public function fail_target 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_opcua_polling_endpoint_adjustment.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_opcua_polling_endpoint_adjustment.py | test | missing_public_docstring | public function fail_target 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_opcua_subscription_endpoint_adjustment.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_opcua_subscription_endpoint_adjustment.py | test | missing_public_docstring | public function deny_resume 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_opcua_subscription_endpoint_adjustment.py | test | missing_public_docstring | public function fail_target 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_operation_journal_audit.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_operation_journal_audit.py | test | missing_public_docstring | public function start_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_operation_journal_audit.py | test | missing_public_docstring | public function pause_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_operation_journal_audit.py | test | missing_public_docstring | public function resume_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_operation_journal_audit.py | test | missing_public_docstring | public function stop_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_operation_journal_audit.py | test | missing_public_docstring | public function replace_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_operation_journal_audit.py | test | missing_public_docstring | public function deny_status 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_polling_endpoint_adjustment.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_polling_endpoint_adjustment.py | test | missing_private_helper_docstring | 复杂 private function _choose_port 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_runtime_state_recovery.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_runtime_state_recovery.py | test | missing_private_helper_docstring | 复杂 private function _choose_port 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_runtime_state_store_integrity.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_runtime_state_store_integrity.py | test | missing_public_docstring | public function writer 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_runtime_state_store_repair_cli.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_runtime_state_store_resilience.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_runtime_state_store_resilience.py | test | missing_public_docstring | public function recording_replace 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_runtime_state_store_retention.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_subscription_endpoint_adjustment.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_subscription_endpoint_adjustment.py | test | missing_private_helper_docstring | 复杂 private function _choose_port 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_subscription_endpoint_adjustment.py | test | missing_public_docstring | public function start_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_subscription_endpoint_adjustment.py | test | missing_public_docstring | public function pause_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_subscription_endpoint_adjustment.py | test | missing_public_docstring | public function resume_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_subscription_endpoint_adjustment.py | test | missing_public_docstring | public function stop_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_dynamic_subscription_endpoint_adjustment.py | test | missing_public_docstring | public function replace_endpoint 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_field_capacity_cli.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for the formal ``field_capacity`` CLI wiring.'] | PENDING |
| tools/source_lab/tests/access/test_field_capacity_cli.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_field_probe_cli.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for the formal ``field_probe`` CLI wiring.'] | PENDING |
| tools/source_lab/tests/access/test_field_probe_cli.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_field_profile_cli.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for the formal ``field_profile`` CLI wiring.'] | PENDING |
| tools/source_lab/tests/access/test_field_profile_cli.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_field_provider.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for file-backed field source loading and provider behavior.'] | PENDING |
| tools/source_lab/tests/access/test_field_provider.py | test | missing_private_helper_docstring | 复杂 private function _find_contiguous_port_start 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_field_provider.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_iec104_client_runner_write_protocol.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 104 client runner WRITE 协议测试。', '验证 C runner 的 WRITE 指令格式、WRITE_RESULT 输出以及 stdout/stderr 协议治理。'] | PENDING |
| tools/source_lab/tests/access/test_iec104_client_runner_write_protocol.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 GOOSE/SV streaming facade and E2E tests.', 'GOOSE/SV use Linux L2 raw sockets. In developer environments without', 'CAP_NET_RAW/root or a suitable interface these tests skip with CI commands'] | PENDING |
| tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py | test | missing_private_helper_docstring | 复杂 private function _has_cap_net_raw 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py | test | missing_private_helper_docstring | 复杂 private function _assert_facade_subscribe 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_iec61850_l2_native_runner_failure_modes.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/access/test_iec61850_lightweight_semantics.py | test | english_business_docstring | class _FakeSocket docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_iec61850_lightweight_semantics.py | test | missing_public_docstring | public function settimeout 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_iec61850_lightweight_semantics.py | test | missing_public_docstring | public function sendall 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_iec61850_lightweight_semantics.py | test | missing_public_docstring | public function recv 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_iec61850_lightweight_semantics.py | test | unexplained_type_ignore | L15: 无解释的 type: ignore | PENDING |
| tools/source_lab/tests/access/test_iec61850_lightweight_semantics.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_iec61850_production_capacity_profile_gate.py | test | english_business_docstring | class TestIec61850MmsCapacityProfileGate docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_iec61850_production_capacity_profile_gate.py | test | missing_private_helper_docstring | 复杂 private function _wait_for_port 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_iec61850_production_capacity_profile_gate.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_iec61850_report_capacity_profile_gate.py | test | english_business_docstring | function simulator_port docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_iec61850_report_capacity_profile_gate.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_iec61850_report_runner_protocol.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['IEC 61850 Report runner protocol tests.', 'Tests the stdin/stdout protocol of the iec61850_report_runner C executable.'] | PENDING |
| tools/source_lab/tests/access/test_iec61850_report_runner_protocol.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_modbus_tcp_production_capacity_profile_gate.py | test | english_business_docstring | class TestModbusTcpCapacityProfileGate docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_modbus_tcp_production_capacity_profile_gate.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_native_cmd_runner_preflight.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['NativeCmdCapacityRunner 预检单元测试。', '2. 二进制缺失 → NativeRunnerUnavailableError', '3. 错误消息包含 protocol/runner_name/expected_path/build_hint'] | PENDING |
| tools/source_lab/tests/access/test_native_cmd_runner_preflight.py | test | english_business_docstring | class _TestNativeRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_native_cmd_runner_preflight.py | test | english_business_docstring | class _RealNativeRunner docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_native_cmd_runner_preflight.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_native_process_protocol.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Native process protocol helper tests.'] | PENDING |
| tools/source_lab/tests/access/test_native_process_protocol.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_opcua_access_adapter.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Lightweight tests for OPC UA capacity adapter helpers.'] | PENDING |
| tools/source_lab/tests/access/test_opcua_access_adapter.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for the OPC UA open62541 runner adapter and protocol parsing.'] | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function flush 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function close 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for the OPC UA open62541 subscription runner adapter.'] | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function write 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function flush 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function close 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function terminate 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_public_docstring | public function kill 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_polling_metrics.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for polling delivery and data-period aggregation semantics.'] | PENDING |
| tools/source_lab/tests/access/test_polling_metrics.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_port_allocator.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for simulator port probing and allocation.'] | PENDING |
| tools/source_lab/tests/access/test_port_allocator.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_profile_service.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for the field profile production service.'] | PENDING |
| tools/source_lab/tests/access/test_profile_service.py | test | missing_public_docstring | public function build_sources 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_profile_service.py | test | missing_public_docstring | public function started 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_profile_service.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_protocol_directory_structure.py | test | missing_public_docstring | public function protocol_dir 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_protocol_directory_structure.py | test | missing_public_docstring | public function protocol_dir 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_protocol_directory_structure.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_protocol_production_readiness_gate.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Protocol production readiness gate.', 'production_client_read=true 必须满足：', '1. shared/source/{protocol}/ 存在生产 client/backend/reader。'] | PENDING |
| tools/source_lab/tests/access/test_protocol_production_readiness_gate.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_protocol_simulator_factory.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Protocol simulator factory tests.'] | PENDING |
| tools/source_lab/tests/access/test_protocol_simulator_factory.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py | test | english_business_docstring | class _FacadeE2EProvider docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py | test | missing_public_docstring | public function build_sources 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py | test | missing_public_docstring | public function started 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py | test | unexplained_type_ignore | L34: 无解释的 type: ignore | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py | test | unexplained_type_ignore | L168: 无解释的 type: ignore | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py | test | unexplained_type_ignore | L194: 无解释的 type: ignore | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_contract.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['ServerSimulatorFacade 契约测试。', '验证每个 facade 满足 ServerSimulatorFacade Protocol 要求的方法签名。'] | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_contract.py | test | english_business_docstring | class TestNotImplementedReturnsCorrectStatus docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_contract.py | test | english_business_docstring | class TestFacadeCapabilitiesConsistency docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_contract.py | test | missing_public_docstring | public function facade_cls 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_contract.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_server_simulator_factory.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['ServerSimulatorFacade 工厂测试。'] | PENDING |
| tools/source_lab/tests/access/test_server_simulator_factory.py | test | english_business_docstring | class TestCreateServerSimulator docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_server_simulator_factory.py | test | english_business_docstring | class TestGetServerSimulatorCapabilities docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_server_simulator_factory.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Final source_lab protocol matrix gates for Round 5-5.', 'These tests guard against overclaiming simulator closure as production', 'readiness. GOOSE/SV L2 true-pass remains permission-gated by the dedicated'] | PENDING |
| tools/source_lab/tests/access/test_subscribe_capacity_entrypoint.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for subscribe-specific capacity service entrypoint.'] | PENDING |
| tools/source_lab/tests/access/test_subscribe_capacity_entrypoint.py | test | missing_public_docstring | public function build_sources 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_subscribe_capacity_entrypoint.py | test | missing_public_docstring | public function started 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_subscribe_capacity_entrypoint.py | test | missing_public_docstring | public function run_worker 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_subscribe_capacity_entrypoint.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_subscribe_capacity_reporter.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for subscribe capacity/profile reporting helpers.'] | PENDING |
| tools/source_lab/tests/access/test_subscribe_capacity_reporter.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_subscribe_scan.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for subscribe scan attempt selection and result presentation.'] | PENDING |
| tools/source_lab/tests/access/test_subscribe_scan.py | test | english_business_docstring | class _Provider docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_subscribe_scan.py | test | english_business_docstring | class _Runner docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_subscribe_scan.py | test | english_business_docstring | function build_sources docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_subscribe_scan.py | test | english_business_docstring | function started docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/access/test_subscribe_scan.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_subscribe_update_policy.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for subscribe source update policy validation.'] | PENDING |
| tools/source_lab/tests/access/test_subscribe_update_policy.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_subscription_metrics.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for subscription metric aggregation and pass/fail evaluation.'] | PENDING |
| tools/source_lab/tests/access/test_subscription_metrics.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/conftest.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Pytest bootstrap for source_simulation tests.', 'Auto-skips @pytest.mark.load tests unless -m load is explicitly requested.'] | PENDING |
| tools/source_lab/tests/conftest.py | test | english_business_docstring | function pytest_collection_modifyitems docstring 为英文业务描述 | PENDING |
| tools/source_lab/tests/conftest.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/test_factory.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for source_lab simulator factory.'] | PENDING |
| tools/source_lab/tests/test_factory.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/test_fleet_partial_lifecycle.py | test | missing_module_docstring | 无 module docstring | PENDING |
| tools/source_lab/tests/test_fleet_partial_lifecycle.py | test | missing_private_helper_docstring | 复杂 private function _choose_port 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Tests for fleet startup concurrency and stagger controls.'] | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_public_docstring | public function set 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_public_docstring | public function is_set 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_public_docstring | public function wait 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_public_docstring | public function get_nowait 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_public_docstring | public function close 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_public_docstring | public function join_thread 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_public_docstring | public function start 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_public_docstring | public function is_alive 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_public_docstring | public function Queue 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_public_docstring | public function Event 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_public_docstring | public function Process 缺少 docstring | PENDING |
| tools/source_lab/tests/test_fleet_startup_controls.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/test_open62541_source_simulation_single_server_smoke.py | test | english_business_docstring | module docstring 疑似英文业务描述: ['Smoke test for open62541 OPC UA source simulator backend.'] | PENDING |
| tools/source_lab/tests/test_open62541_source_simulation_single_server_smoke.py | test | missing_private_helper_docstring | 复杂 private function _read_tick 缺少 docstring | PENDING |
| tools/source_lab/tests/test_open62541_source_simulation_single_server_smoke.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |

## MEDIUM 优先级违规

| 文件 | 文件类型 | 违规类型 | 详情 | 修复状态 |
|------|----------|----------|------|----------|
| tests/integration/test_ingest_iec104_source_write.py | test | unexplained_type_ignore | L85: 无解释的 type: ignore | PENDING |
| tools/source_lab/tests/access/test_iec104_production_capacity_profile_gate.py | test | unexplained_type_ignore | L82: 无解释的 type: ignore | PENDING |
| tools/source_lab/tests/access/test_iec104_production_capacity_profile_gate.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_real_protocol_smoke.py | test | missing_private_helper_docstring | 复杂 private function _choose_available_port 缺少 docstring | PENDING |
| tools/source_lab/tests/access/test_server_simulator_facade_real_protocol_smoke.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |

## LOW 优先级违规

| 文件 | 文件类型 | 违规类型 | 详情 | 修复状态 |
|------|----------|----------|------|----------|
| tests/__init__.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_opcua_adapter_resolution.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_scheduler_job_routes.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tests/unit/test_source_acquisition_use_case.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_ai_shared_report_template_references.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_all_protocols_polling_capacity.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_all_protocols_polling_profile.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_all_protocols_probe.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_all_protocols_streaming_capacity.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_all_protocols_streaming_profile.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_iec61850_mms_client_runner_write_protocol.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_modbus_client_runner_write_protocol.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_native_cmd_timeout.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_native_runners_availability.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_open62541_client_runner_write_protocol.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_protocol_matrix.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_protocol_registry.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/access/test_protocol_service_capabilities.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/support/__init__.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/support/sources.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/test_source_simulation_multi_server_polling_capacity.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/test_source_simulation_multi_server_polling_profile.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/test_source_simulation_multi_server_subscribe_capacity.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |
| tools/source_lab/tests/test_source_simulation_multi_server_subscribe_profile.py | test | missing_test_evidence_label | 测试文件头未标注证据等级 L1-L5 | PENDING |