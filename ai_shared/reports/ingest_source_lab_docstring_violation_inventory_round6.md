# Ingest / Source Lab docstring 违规清单 Round 6

> 报告日期: 2026-05-29 12:45:07
> 范围: src/whale/ingest, src/whale/shared/source, tools/source_lab, tests, tools/source_lab/tests
> 扫描总文件数: 602
> 存在违规文件数: 445
> 违规总条目数: 3919
> 依据规则: ai_shared/rules/python-docstring-cn.md, ai_shared/rules/coding.md Section 8

## 总览

| 范围 | 文件数 | 违规条目数 | 目标 |
|------|--------|-----------|------|
| src/whale/ingest | 107 | 563 | 0 remaining（本轮必须清零） |
| src/whale/shared/source | 32 | 213 | 尽可能清零 |
| tools/source_lab | 173 | 2095 | 优先修复 access/runners/runtime/protocols/factory/registry |
| tests | 133 | 1048 | 优先修复复杂 fixture 和 module docstring |
| tools/source_lab/tests | 82 | 1422 | 优先修复复杂 fixture 和 module docstring |

## 违规类型分布

| 违规类型 | 数量 |
|----------|------|
| public 对象缺少 docstring | 1985 |
| 英文业务 docstring | 1498 |
| 英文 module docstring | 365 |
| 无解释 type:ignore | 71 |

## 逐文件违规清单

### src/whale/ingest/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/adapters/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/adapters/audit/db_audit_sink.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | DbIngestAuditSink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/adapters/audit/http_audit_sink.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | HttpIngestAuditSink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | emit | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | flush | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _flush | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _serialize | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/audit/multi_audit_sink.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | AuditSinkEmitError | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | DualIngestAuditSink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/adapters/config/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/adapters/config/opcua_source_acquisition_definition_repository.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/adapters/config/source_runtime_config_repository.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | SourceRuntimeConfigRepository | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | list_enabled | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | list_servers | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | list_profile_items | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/message/__init__.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | __getattr__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/message/kafka_message_publisher.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | KafkaSendFuture | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | KafkaProducerClient | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | KafkaMessagePublisher | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _classify_kafka_error | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | get | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | send | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | __init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | publish_snapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_key | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_producer | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 无解释 type:ignore | line 110 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### src/whale/ingest/adapters/message/redis_streams_message_publisher.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | RedisStreamsClient | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | RedisStreamsMessagePublisher | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | xadd | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | __init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | publish_snapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_client | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/message/relational_outbox_message_publisher.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | RelationalOutboxMessagePublisher | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | publish_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/adapters/observability/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/adapters/observability/file_sinks.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | JsonlIngestMetricsSink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | JsonlSourceCommandAuditSink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | JsonlIngestAuditSink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/adapters/security/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/adapters/security/external_access_policy.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | ExternalAccessPolicy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _principal_from_request | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | evaluate | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | authorize | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/adapters/security/file_access_policy.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | FileAccessPolicy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | AllowAllAccessPolicy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | DenyAllAccessPolicy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _principal_from_request | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | evaluate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | authorize | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | evaluate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | authorize | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | evaluate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | authorize | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/adapters/source/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/adapters/source/iec104_source_acquisition_adapter.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | Iec104SourceAcquisitionAdapter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 docstring | read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 docstring | _resolve_ioa_list | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_reader | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/source/iec104_source_write_adapter.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | Iec104SourceWriteAdapter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _resolve_ioa | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _resolve_command_type | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/source/iec61850_report_source_acquisition_adapter.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 docstring | _on_report_event | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _on_error | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/source/iec61850_source_acquisition_adapter.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | Iec61850MmsSourceAcquisitionAdapter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 docstring | read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 docstring | _resolve_obj_refs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _resolve_fc | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_reader | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _to_acquired_batch_from_raw | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/source/iec61850_source_write_adapter.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | Iec61850MmsSourceWriteAdapter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/source/modbus_source_acquisition_adapter.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | ModbusSourceAcquisitionAdapter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 docstring | read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 docstring | _resolve_reg_addrs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_reader | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/source/modbus_source_write_adapter.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | ModbusSourceWriteAdapter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _resolve_reg_addr | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/source/opcua_source_write_adapter.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 docstring | readback | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/adapters/source/static_source_write_port_registry.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 缺少 public docstring | get | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/adapters/state/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/adapters/state/redis_source_state_cache.py

违规数: 21

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 docstring | RedisPipeline | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | RedisHashClient | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | RedisSourceStateCacheSettings | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | RedisSourceStateCache | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _classify_redis_error | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _parse_datetime | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _optional_int | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | hset | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | execute | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | hset | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | hget | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | hgetall | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | pipeline | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | from_config | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | __init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _execute_pipeline | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_write_error | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_client | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _decode_value | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _dump_payload | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _optional_str | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/api/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/api/app.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | create_app | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | handle_api_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | handle_validation_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 无解释 type:ignore | line 67 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### src/whale/ingest/api/audit_middleware.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | AuditContext | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | IngestAuditMiddleware | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | build_audit_event | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | dispatch | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 无解释 type:ignore | line 28 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### src/whale/ingest/api/errors.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | ApiError | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | not_found | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | conflict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | denied | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | to_payload | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/api/idempotency.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | _get_idempotency_key | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | IdempotencyService | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _read_and_buffer_body | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | IdempotencyMiddleware | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | get_cached | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | try_claim | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | cache_response | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | replay_receive | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | send_wrapper | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/api/routes/acquisition_tasks.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 缺少 public docstring | create_acquisition_task | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | get_acquisition_task | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | list_acquisition_tasks | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | patch_acquisition_task | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | delete_acquisition_task | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/api/routes/audit_events.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 缺少 public docstring | get_audit_event | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | list_audit_events | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/api/routes/bundles.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 缺少 public docstring | get_bundle | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | list_bundles | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/api/routes/health.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 缺少 public docstring | healthz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | readyz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/api/routes/leases.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 缺少 public docstring | get_lease | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | list_leases | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/api/routes/nodes.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 缺少 public docstring | get_node | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | list_nodes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/api/routes/runtime_config.py

违规数: 21

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 缺少 public docstring | create_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | get_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | list_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | patch_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | delete_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | create_connection | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | get_connection | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | list_connections | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | patch_connection | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | delete_connection | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | create_signal_profile | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | get_signal_profile | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | list_signal_profiles | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | patch_signal_profile | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | delete_signal_profile | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | create_point | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | get_point | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | list_points | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | patch_point | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | delete_point | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/api/routes/scheduler_jobs.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 缺少 public docstring | create_scheduler_job | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | get_scheduler_job | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | list_scheduler_jobs | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | patch_scheduler_job | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | delete_scheduler_job | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/api/routes/security_partitions.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | SecurityPartitionOrm | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | create_security_partition | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | get_security_partition | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | list_security_partitions | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | patch_security_partition | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | delete_security_partition | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/bundle/checksum.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | canonicalize_bundle_payload | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | compute_bundle_checksum | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/bundle/model.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | AcquisitionTaskBundleItem | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | IngestBundle | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/bundle/redaction.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 docstring | redact_bundle | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/bundle/service.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | BundleImportResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | BundleService | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | export_bundle | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | import_bundle | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/composition.py

违规数: 23

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | IngestAcquisitionComposition | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | IngestWriteComposition | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | build_source_acquisition_composition | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _DefaultSourceErrorClassifier | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _AllowAllAccessPolicy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _NullAuditEventSink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _NullMetricsSink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _NullDebugTraceSink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _normalize_error_code | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | build_source_write_composition | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | build_default_write_composition | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | IngestPublishComposition | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | build_state_snapshot_publish_composition | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | classify | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | evaluate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | increment | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | observe_duration | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 无解释 type:ignore | line 387 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 388 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 467 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### src/whale/ingest/config.py

违规数: 18

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | SqliteDatabaseConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | PostgresDatabaseConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | DatabaseEngineConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | RedisStateCacheConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | RelationalOutboxMessageConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | RedisStreamsMessageConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | KafkaMessageConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | EnvironmentConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _resolve_database_backend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _resolve_state_cache_backend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _resolve_message_backend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _require_env_vars | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_config | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | state_cache_backend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 无解释 type:ignore | line 138 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 152 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 166 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### src/whale/ingest/decorators/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/decorators/source_acquisition.py

违规数: 22

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | LoggingSourceAcquisitionPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | AuditedSourceAcquisitionPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | RetryingSourceAcquisitionPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | AuthorizedSourceAcquisitionPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | DebugSourceAcquisitionPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _emit_audit_best_effort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/decorators/source_write.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | AuthorizedSourceWritePort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/decorators/state_cache.py

违规数: 18

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | LoggingStateCachePort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | AuditedStateCachePort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | MetricsStateCachePort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | DebugStateCachePort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _emit_audit_best_effort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | mark_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | mark_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | mark_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | mark_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/ingest/domain/audit_event.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | redact_value | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | redact_pair | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | IngestAuditEvent | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | sanitized_payload | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/domain/write_security_profile.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | ReadbackStrategy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | ProtocolWriteProfile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | WriteSecurityProfile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | profile_for | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | is_write_allowed | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/entities/node_state.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | NodeState | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/entities/source_health_state.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | SourceHealthState | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/framework/persistence/__init__.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | __getattr__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/framework/persistence/base.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 docstring | Base | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/framework/persistence/init_db.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | init_db | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | initialize_db | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | reset_db | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | load_default_sample_data | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _resolve_database_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _has_existing_schema | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _clear_existing_storage | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _storage_display_name | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_delete_confirmation_prompt | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_argument_parser | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | main | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/framework/persistence/orm/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/framework/persistence/runtime_db.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | create_runtime_engine | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | create_runtime_session_factory | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | initialize_runtime_database | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | migrate_runtime_database | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | probe_runtime_readiness | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | resolve_alembic_ini_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/framework/persistence/session.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | create_db_url | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | get_session | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | session_scope | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | dispose_engine | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/message_pipeline.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | IngestMessagePipeline | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | InMemoryIngestMessagePipeline | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | publish | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | __init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | publish | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | batches | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/ports/audit.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | IngestAuditSinkPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | emit | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/command/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/ports/command/source_command_audit_port.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | SourceCommandAuditEvent | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | SourceCommandAuditPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | emit | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/message/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/ports/message/message_publisher_port.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | StateSnapshotItem | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | StateSnapshotMessage | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | MessagePublishResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | MessagePublisherPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _serialize_datetime | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | to_dict | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | to_dict | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | to_json | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | publish_snapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/metrics.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 缺少 public docstring | IngestMetricEvent | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | IngestMetricsPort | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 docstring | emit | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/runtime/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/ports/runtime/access_policy_port.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | AccessPolicyPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | authorize | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/runtime/source_runtime_config_port.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | SourceRuntimeConfigData | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | ServerRuntimeConfigData | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | SignalProfileItemRuntimeData | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | SourceRuntimeConfigPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | list_enabled | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | list_servers | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | list_profile_items | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/runtime/write_lease_port.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | WriteLeaseDecisionData | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | WriteLeasePort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | acquire | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | renew | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | validate | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | release | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/source/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/ports/source/source_acquisition_definition_port.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | SourceAcquisitionDefinitionPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | get_config | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/source/source_acquisition_port_registry.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | SourceAcquisitionPortRegistry | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | get | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/source/source_write_port_registry.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | SourceWritePortRegistry | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | get | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/state/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/ports/state/source_state_cache_port.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 docstring | SourceStateCacheError | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | SourceStateCacheWriteError | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/ports/state/source_state_snapshot_reader_port.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | CachedNodeValue | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | CachedSourceState | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | SourceStateSnapshotReaderPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | read_snapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/runtime/acquisition_mode.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/runtime/cli.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | _NoopJobHandler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | migrate | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | api | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | worker | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | api_worker | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | export_bundle | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | import_bundle | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 无解释 type:ignore | line 145 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### src/whale/ingest/runtime/entrypoint.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | main | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/fencing.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 docstring | FencingToken | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | redact_fencing_token | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | current_value | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/job_assignment.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | RuntimeJob | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | JobAssignment | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | RuntimeJobRepository | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | JobAssignmentRepository | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | upsert_job | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | list_enabled_jobs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | get | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | assign | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | get_active_assignment | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | list_active_assignments | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | deactivate_job | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/job_status.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | JobStatus | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/lease.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | LeaseAcquireResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | JobLease | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | LeaseRepository | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | LeaseService | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _as_utc | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | is_expired | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | get | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | list_active | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | acquire | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | renew | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | release | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | expire_due_leases | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | force_expire | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | get_snapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | validate_execution | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/message_pipeline_settings.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | _LazyMessagePipelineSettingsProxy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | __getattr__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/modes.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | RuntimeMode | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | parse | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/node_runtime.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | NodeHeartbeat | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | NodeRuntimeRepository | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | upsert_heartbeat | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | get | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | list_nodes | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | list_alive_nodes | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/scheduler.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | SchedulerSnapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | SchedulerExecutionDecision | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | SourceScheduler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | node_key | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | heartbeat | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | assign_jobs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | bootstrap | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | release_jobs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | validate_execution | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/scheduler_factory.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | build_scheduler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_jobstore | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 无解释 type:ignore | line 5 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 9 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 10 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 13 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 16 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 17 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### src/whale/ingest/runtime/scheduler_job.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | AcquisitionStatus | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | SourceStateAcquisitionResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | ScheduledSourceJob | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/scheduler_settings.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | JobStoreSettings | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | JobDefaultSettings | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | SchedulerSettings | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/worker_runtime.py

违规数: 19

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | JobHandler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | WorkerRuntimeMetrics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | WorkerRuntime | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _get_interval_ms | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _get_stagger_ms | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _percentile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | execute | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 缺少 public docstring | inc | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | gauge | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | summary | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | node_key | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | metrics_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 缺少 public docstring | metrics_summary | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 docstring | start | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | stop | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _tick_heartbeat | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _tick_reconcile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/runtime/write_lease.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 docstring | renew | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | validate | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | release | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/usecases/dtos/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/usecases/dtos/source_write_result.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/usecases/dtos/state_publish_request.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | StateSnapshotPublishRequest | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/usecases/dtos/state_publish_result.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 缺少 public docstring | PublishStatus | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 docstring | StateSnapshotPublishResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | is_success | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | merge | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/usecases/roles/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/ingest/usecases/roles/polling_acquisition_role.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 docstring | _normalize_source_error_code | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _mark_connection_unavailable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/usecases/roles/subscription_acquisition_role.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 docstring | _build_failure_reason | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _mark_unavailable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/ingest/usecases/state_snapshot_publish_use_case.py

违规数: 17

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P0 | 英文 docstring | StateSnapshotPublishUseCase | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _generate_snapshot_id | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _extract_attributes | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | __init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | execute | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _apply_filters | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _build_messages | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _map_item | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _assemble_message | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 docstring | _publish_all | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 无解释 type:ignore | line 283 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 286 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 293 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 294 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 297 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 无解释 type:ignore | line 299 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### src/whale/shared/source/access/__init__.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | build_source_access_adapter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/access/adapter.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | SourceAccessAdapter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | connect | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | prepare_read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read_tick | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | close | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/access/model.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | SourceEndpointSpec | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SourcePointSpec | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | TickResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/access/opcua.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | normalize_opcua_node_id | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_opcua_endpoint_url | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | OpcUaSourceAccessAdapter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | __init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | connect | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | prepare_read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | close | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read_tick | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/iec104/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/shared/source/iec104/backends/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/shared/source/iec104/backends/base.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | RawIec104ReadResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | RawWriteItemResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec104PreparedReadPlan | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec104ClientBackend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/iec104/backends/lib60870_backend.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | resolve_client_runner_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec104Lib60870Backend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | connect | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | disconnect | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _parse_sample_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _parse_write_result_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/iec104/reader.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | Iec104SourceReader | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/iec61850/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/shared/source/iec61850/backends/base.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | RawMmsReadResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | RawWriteItemResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec61850MmsClientBackend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/iec61850/backends/libiec61850_backend.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | resolve_client_runner_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _MmsConnectionParams | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | LibIec61850MmsClientBackend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | connect | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | disconnect | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _parse_read_result_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _parse_write_result_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/iec61850/backends/libiec61850_report_backend.py

违规数: 15

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | resolve_report_runner_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | LibIec61850ReportBackend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | is_active | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | subscribe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _start_subprocess | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _wait_for_ready | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | close | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _reader_loop | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _on_runner_error | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _on_unexpected_exit | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _reconnect | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _read_protocol_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _close_runner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _parse_report_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/iec61850/backends/report_base.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | RawReportEvent | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec61850ReportClientBackend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | subscribe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | close | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/iec61850/reader.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | Iec61850MmsSourceReader | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/iec61850/report_reader.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | Iec61850ReportSourceReader | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | subscribe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | is_active | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | close | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/modbus/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/shared/source/modbus/backends/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/shared/source/modbus/backends/base.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | RawModbusReadResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | RawWriteItemResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ModbusPreparedReadPlan | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ModbusClientBackend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | prepare_read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read_prepared | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/modbus/backends/libmodbus_backend.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | resolve_client_runner_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ModbusTcpClientBackend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | connect | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | disconnect | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | prepare_read | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | read_prepared | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _parse_write_result_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/modbus/reader.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | ModbusSourceReader | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | prepare_read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read_prepared | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/opcua/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/shared/source/opcua/backends/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/shared/source/opcua/backends/base.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | PreparedReadPlan | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Open62541PreparedReadPlan | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | RawDataValue | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | RawOpcUaReadResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | RawWriteItemResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | OpcUaClientBackend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | node_paths | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | namespace_index | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | prepare_read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read_prepared_raw | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/opcua/backends/factory.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | normalize_client_backend_name | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | resolve_client_backend_name | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_client_backend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/opcua/backends/open62541_backend.py

违规数: 13

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | Open62541ReadDebugTiming | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _CachedPlanRuntime | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | resolve_client_runner_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _normalize_open62541_node_id | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Open62541OpcUaClientBackend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | connect | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | disconnect | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | namespace_index | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | prepare_read | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_prepared_raw | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write_batch | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _parse_write_result_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/opcua/reader.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | OpcUaSubscriptionHandle | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | OpcUaSourceReader | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | close | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | prepare_read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read_prepared_raw | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | start_subscription | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | list_nodes | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | list_readable_variable_nodes | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/scheduling/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### src/whale/shared/source/scheduling/concurrency.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | ConcurrencySnapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ReadConcurrencyLimiter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | max_concurrent | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | snapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | reset_counters | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _on_acquire | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _on_release | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### src/whale/shared/source/scheduling/fixed_rate.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | HighFrequencyFixedRateScheduler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | add_job | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | start | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | stop | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | task_creation_snapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_once | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/shared/source/scheduling/polling.py

违规数: 37

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | PollingTickDiagnostics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | PollingTaskCreationDiagnostics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _MutablePollingTaskCreationDiagnostics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | PollingResultEvent | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | PollingErrorEvent | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | PollingJobSpec | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | PollingJobStats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _MutablePollingJobStats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SourcePollingScheduler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | reset_for_start | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | snapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | __post_init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | snapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | add_job | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | start | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | stop | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | job_stats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _task_creation_snapshot | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_job | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _execute_job | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_operation | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _schedule_callback | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _emit_event_sink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_tick_diagnostics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _dispatch_result_callback | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _dispatch_error_callback | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_callback_worker | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _record_success | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _record_error | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _record_skipped_ticks | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _update_common_stats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_limiter_wait_start | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_limiter_acquired | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_operation_finished | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_once | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### src/whale/shared/source/scheduling/stagger.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | StaggerAssignment | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_even_stagger_offsets | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_stagger_assignments | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | assign_even_stagger | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/conftest.py

违规数: 14

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _cleanup_root_output_artifacts | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | pytest_configure | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | pytest_sessionstart | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | pytest_sessionfinish | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | real_redis_url | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | real_redis_client | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | real_redis_hash_key | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | sample_nodeset_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | sample_opcua_connections_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | free_ports | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | local_opcua_connections_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | opcua_server_runtime | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | opcua_sim_fleet | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/e2e/conftest.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | pytest_configure | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | pg_db_url | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | pg_engine | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _pg_tables_created | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | pg_session | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | session_factory | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | redis_client | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _kafka_ready | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/e2e/helpers.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | get_free_port | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ensure_src_on_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | seed_postgres_for_e2e | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | wait_for_redis | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | wait_for_kafka | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 191 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tests/integration/test_framework_db_init.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _create_sqlite_engine | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_init_db_creates_all_framework_tables | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_api_acquisition_task_crud.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_acquisition_task_crud_round_trip | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_api_audit.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_api_audit_covers_success_failure_conflict_validation_and_deny | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | access_evaluator | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_api_authorization_deny.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _seed | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_on_scheduler_job_create | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_on_scheduler_job_list | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_on_scheduler_job_read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_on_scheduler_job_update | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_on_scheduler_job_delete | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_on_acquisition_task_crud | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_on_security_partition_crud | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_on_node_list | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_on_lease_list | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_on_audit_event_query | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_on_bundle_read | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_allow_when_not_denied | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_healthz_readyz_not_blocked_by_deny | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | access_evaluator | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_api_bundle_metadata_crud.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_bundle_list_and_get | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_api_dry_run_all_mutating_routes.py

违规数: 21

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_dry_run_acquisition_task_create_does_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_acquisition_task_patch_validates_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_acquisition_task_patch_version_conflict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_acquisition_task_delete_validates_not_delete | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_acquisition_task_delete_version_conflict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_security_partition_create_does_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_security_partition_patch_validates_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_security_partition_delete_validates_not_delete | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_source_create_does_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_source_patch_validates_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_source_delete_validates_not_delete | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_connection_create_does_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_connection_patch_validates_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_connection_delete_validates_not_delete | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_signal_profile_create_does_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_signal_profile_patch_validates_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_signal_profile_delete_validates_not_delete | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_point_create_does_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_point_patch_validates_not_persist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_point_delete_validates_not_delete | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_api_full_audit_matrix.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_healthz_emits_audit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_readyz_emits_audit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_404_emits_not_found_audit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_validation_error_emits_audit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_conflict_emits_audit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_api_idempotency_all_mutating_routes.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_idempotency_acquisition_task_post | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_idempotency_acquisition_task_post_different_payload_422 | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_idempotency_security_partition_post | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_idempotency_source_post | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_idempotency_connection_post | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_idempotency_signal_profile_post | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_idempotency_point_post | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_api_idempotency_dry_run.py

违规数: 13

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_idempotency_post_returns_cached_response | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_idempotency_different_key_is_not_cached | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_idempotency_different_payload_returns_422 | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_idempotency_no_key_is_not_cached | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_idempotency_patch_returns_cached_response | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_idempotency_delete_not_cached | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_create_does_not_persist | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_create_still_validates_auth | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_patch_validates_but_does_not_persist | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_patch_rejects_version_conflict | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_delete_validates_but_does_not_persist | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_delete_rejects_version_conflict | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_api_idempotency_dry_run_interaction.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_dry_run_idempotency_first_request_not_persisted | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_idempotency_same_key_same_payload_consistent | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_idempotency_same_key_different_payload_422 | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_cache_not_reused_by_non_dry_run_same_key_422 | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_cache_bypassed_without_idempotency_key | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_non_dry_run_not_skipped_by_prior_dry_run_different_key | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_non_dry_run_not_skipped_by_prior_dry_run_422_on_same_key | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_idempotency_patch_does_not_persist | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_idempotency_delete_does_not_delete | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_api_node_lease_audit_query.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_node_query | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_lease_query | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_audit_event_query | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_api_runtime_config_audit.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_query_success_and_query_failure_are_audited | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_validation_error_and_conflict_are_audited | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_delete_is_audited | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_deny_is_audited | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | access_evaluator | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_api_runtime_config_crud.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_source_crud_roundtrip | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_connection_crud_roundtrip | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_point_crud_roundtrip | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_signal_profile_crud_roundtrip | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_expected_version_conflict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_api_scheduler_job_crud.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_scheduler_job_create_and_read | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_scheduler_job_list | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_scheduler_job_patch | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_scheduler_job_delete | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_scheduler_job_version_conflict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_api_security_partition_crud.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_security_partition_crud_roundtrip | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_audit_db_jsonl_consistency.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | session_factory | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_db_and_jsonl_sink_consistent_schema | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_audit_matrix_api_bundle_scheduler_write.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | session_factory | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_audit_event_sink_persists_minimal_fields | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_audit_event_sink_persists_bundle_events | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_audit_event_sink_persists_scheduler_events | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_audit_event_sink_persists_write_events | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_audit_event_redaction | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_bundle_import_export.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_bundle_export_and_import_round_trip | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_bundle_offline_one_way_flow.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_offline_raw_bundle_export_import_roundtrip | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_redacted_bundle_cannot_be_imported_as_accepted_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_corrupt_checksum_import_rolls_back | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_bundle_import_success_and_failure_are_audited | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_cache_to_kafka_pipeline.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _FakeKafkaFuture | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _FakeKafkaProducer | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _FakeSnapshotReader | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_cache_to_kafka_full_pipeline | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_cache_to_kafka_dry_run_does_not_send | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_cache_to_kafka_no_data_no_send | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_cache_to_kafka_multi_message_split | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_cache_to_kafka_with_filter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | get | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | send | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | flush | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_external_access_policy_contract.py

违规数: 13

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _StubPolicyHandler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _stub_url | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fake_request | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | TestExternalAccessPolicyContract | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | do_POST | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | log_message | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_external_policy_allow | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_external_policy_deny | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_external_policy_timeout_fail_closed | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_external_policy_fail_open_requires_explicit_config | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_external_policy_redacts_token_in_errors | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 22 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tests/integration/test_ingest_external_audit_sink_contract.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _StubAuditHandler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | TestExternalAuditSinkContract | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | do_POST | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | log_message | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_http_audit_sink_sends_event_to_stub | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_http_audit_sink_batches_events | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_http_audit_sink_failure_records_last_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_http_audit_sink_jsonl_fallback | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_http_audit_sink_redacts_sensitive_fields | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 25 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tests/integration/test_ingest_iec104_source_write.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _run_simulator | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 85 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tests/integration/test_ingest_iec61850_mms_source_write.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | TestIec61850MmsSourceWrite | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | setup_class | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_iec61850_report_subscription.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _find_free_port | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | simulator_port | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_batch | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_batch | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_lightweight_load_gate.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | item_count_for_acquisition | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_ingest_lightweight_load_gate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | publish_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_modbus_source_write.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _build_source | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_observability_sink_smoke.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_jsonl_observability_sinks_capture_publish_and_command | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | publish_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_polling_retry_to_redis.py

违规数: 21

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_polling_offline_online_offline_recovered_with_real_simulator | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_polling_multi_device_partial_failure_isolated_per_connection | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FakeSequenceAcquisitionPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FakeAcquisitionPortByLd | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_polling_batch_mismatch_and_stale_update_keep_retry_semantics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FakePipeline | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FakeRedisClient | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_polling_redis_write_failures_and_oom_do_not_advance_alive_state | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | hset | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | hset | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | hget | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | hgetall | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pipeline | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_access_policy.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | policy_file | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_file_policy_allows_configured_actor_action | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_file_policy_denies_unconfigured_action | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_file_policy_role_based_match | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_deny_all_policy_denies_everything | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_file_policy_deny_returns_reason | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_api_deny_written_to_audit_sink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_write_deny_blocks_inner_write_port | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_audit_metrics_resilience.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | prodlike_resilience_stack | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_audit_events_continue_during_redis_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_metrics_continue_during_kafka_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_audit_db_failure_visible_and_jsonl_fallback_works | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sensitive_fields_redacted_in_failure_events | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_audit_sink.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | pg_engine | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pg_sf | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_api_audit_written_to_postgres | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_scheduler_audit_written_to_postgres | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_bundle_audit_written_to_postgres | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_write_deny_audit_written_to_postgres | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_jsonl_and_db_audit_sink_consistency | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_audit_redacts_sensitive_fields_in_prodlike_sink | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_endurance_smoke.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_endurance_smoke_script_emits_report | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_kafka_fault_injection.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | prodlike_kafka_stack | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_kafka_publish_failure_classified_without_blocking_cache | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_kafka_publish_recovers_after_broker_restart | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_kafka_publish_retry_metrics_emitted | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_kafka_backpressure_does_not_unbounded_queue | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_kafka_publish.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | kafka_settings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_kafka_publish_state_snapshot_envelope | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_kafka_publish_key_strategy_source_id | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_kafka_publish_error_is_classified | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_performance_profile.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | perf_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | TestPerformanceProfileConformance | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_config_has_required_sections | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_baseline_throughput_targets_positive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_baseline_latency_thresholds_positive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_baseline_resources_positive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_limits_threadpool_sensible | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_timeouts_sensible | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_scheduler_params_sensible | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_scheduler_defaults_conform_to_limits | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_error_budget_sensible | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_postgres_fault_injection.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _safe_count_audit_events | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _safe_active_assignments | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | prodlike_pg_stack | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_api_readyz_fails_when_postgres_down_and_recovers | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_worker_pauses_or_fails_safe_when_lease_db_down | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_scheduler_recovers_assignment_after_postgres_restart | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_audit_sink_degrades_or_buffers_with_explicit_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_postgres_runtime_db.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | pg_engine | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pg_session | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_postgres_runtime_db_api_crud_roundtrip | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_postgres_runtime_db_scheduler_lease_unique_owner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_postgres_runtime_db_audit_event_persisted | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_postgres_runtime_db_readyz_fails_when_db_unavailable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_redis_cache.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | redis_settings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | cache | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | raw_client | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | _skip_no_redis | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_state_cache_writes_to_real_redis | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_state_cache_reads_snapshot_from_real_redis | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_state_cache_error_when_redis_unavailable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_redis_fault_injection.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | prodlike_redis_stack | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_source_cache_write_failure_is_classified | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_source_cache_recovers_after_redis_restart | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_cache_failure_does_not_crash_api_runtime | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_cache_failure_metrics_and_audit_are_emitted | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | increment | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | observe_duration | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_scheduler_backpressure.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_job_overrun_records_missed_tick | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_assignment_lag_metric_under_multi_job_load | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_backpressure_limits_inflight_jobs | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_scheduler_does_not_create_unbounded_tasks | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_prodlike_worker_failover.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_worker_crash_releases_or_expires_lease | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_standby_worker_takes_over_after_lease_expiry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_old_worker_fencing_token_rejected_after_restart | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_no_duplicate_execution_during_failover_window | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_graceful_shutdown_records_final_audit_and_metrics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_runtime_alembic_migration.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_alembic_upgrade_head_creates_runtime_tables | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_migrate_entrypoint_runs_upgrade_head | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_orm_metadata_matches_migrated_schema_minimum | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_alembic_revision_is_not_empty | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_runtime_alembic_postgres_matrix.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _reset_ingest_schema | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_postgres_upgrade_head_creates_all_tables | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_postgres_upgrade_head_has_audit_index | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_postgres_downgrade_base_then_upgrade_head | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_runtime_alembic_sqlite_matrix.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_sqlite_upgrade_head_creates_all_tables | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_sqlite_upgrade_head_has_audit_index | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sqlite_upgrade_head_has_stagger_column | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sqlite_downgrade_base_removes_stagger_column | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sqlite_upgrade_has_idempotency_table | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sqlite_downgrade_upgrade_idempotent | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_runtime_db_init.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_runtime_db_init_creates_runtime_tables | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_runtime_entrypoint_smoke.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_runtime_entrypoints_smoke | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_runtime_migrate_entrypoint.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_migrate_entrypoint_runs_via_alembic | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_migrate_database_function_direct | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_migrate_idempotent | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_scheduler_active_standby_failover.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_active_standby_failover_reassigns_expired_job_once | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_recovered_old_active_is_fenced_after_failover | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_scheduler_apscheduler_runtime.py

违规数: 13

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _NoopHandler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | sqlite_session_factory | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | settings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | repos | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | seeded_job_repo | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_executes_enabled_job_with_lease | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_does_not_execute_without_lease | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_records_missed_tick_on_overrun | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_preserves_stagger_offset | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_graceful_shutdown_releases_or_expires_lease | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | SlowWorker | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_scheduler_cluster_assignment.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_cluster_assignment_has_no_duplicate_job_owner | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_lease_renewal_rejects_non_owner | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_fencing_token_mismatch_rejects_execution | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_scheduler_dual_active_partitioned.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_dual_active_partitioned_assigns_different_partitions_to_different_nodes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dual_active_partitioned_prevents_duplicate_partition_execution | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_partition_lease_expiry_allows_reassignment | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_scheduler_graceful_shutdown.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | session_factory | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | settings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | repos | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_graceful_shutdown_releases_leases | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_graceful_shutdown_with_no_active_jobs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_graceful_shutdown_releases_only_owned_leases | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_scheduler_missed_tick_and_stagger.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | session_factory | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | settings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | repos | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_records_missed_tick_on_overrun | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_stagger_offset_delays_execution | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | SlowWorker | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_security_partition_bundle_flow.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | session_factory | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | audit_sink | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | service | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | TestOneWayBundleFlow | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_bundle_export_from_management_zone | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_redacted_bundle_cannot_be_imported | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_raw_bundle_import_dry_run_then_accept | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_bundle_checksum_mismatch_rolls_back | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_bundle_import_audited | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_security_partition_smoke.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_security_partition_example_config_declares_required_zones_and_flows | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_source_acquisition_to_redis.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_source_acquisition_read_once_updates_redis_cache_with_real_values | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_ingest_source_cache_message_e2e.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_source_cache_message_chain_e2e | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_publish_failure_does_not_corrupt_cached_state | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | publish_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_source_cache_message_kafka_e2e.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_source_cache_message_kafka_e2e | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_subscription_strategy.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_subscription_unsupported_fails_fast_without_baseline_cache_write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_subscription_supported_strategy_baseline_before_start_with_real_redis_cache | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | close | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_worker_runtime_executes_usecase_handlers.py

违规数: 13

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _RecordingHandler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _RaisingHandler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | session_factory | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | settings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | repos | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_executes_acquisition_handler_with_lease | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_executes_publish_snapshot_handler_with_lease | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_missing_handler_records_failed_metric | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_handler_exception_records_failure | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_multiple_handlers_dispatched_correctly | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_worker_runtime_handler_failure.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _RaisingHandler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | session_factory | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | settings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | repos | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_missing_handler_records_failed_metric | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_handler_exception_records_failure_and_completes | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_assigns_and_executes_mixed_handlers | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_worker_runtime_shutdown_inflight.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _SlowHandler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | session_factory | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | settings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | repos | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_shutdown_does_not_block_with_no_active_jobs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_shutdown_waits_for_short_inflight_job | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_worker_runtime_shutdown_releases_leases_only_for_owned_jobs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_ingest_write_lease_fencing_e2e.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_write_command_readback_success | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_write_command_readback_mismatch_is_audited | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_write_lease_conflict_is_audited | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_old_primary_fencing_token_rejects_command | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | precheck | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | readback | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/integration/test_redis_state_cache_faults.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_live_redis_oom_is_classified_and_does_not_leave_partial_state | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/integration/test_sqlite_config_init.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_sqlite_config_init_script_creates_db_from_default_templates | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/performance/load/conftest.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | pytest_configure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pg_db_url | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pg_engine | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | pg_session | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | session_factory | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | redis_client | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/performance/stress/test_acquisition_pipeline_stress.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_acquisition_pipeline_stress_smoke_uses_current_open62541_and_redis_chain | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/support/ingest_prodlike_runtime.py

违规数: 25

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | compose_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | docker_available | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | require_docker | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | compose | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | runtime_dsn | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | clear_runtime_engine_cache | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | runtime_session_factory | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | ensure_prodlike_stack | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | migrate_prodlike_database | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_prodlike_stack | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_service | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_service | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | restart_service | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | service_logs | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait_until | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | wait_for_kafka | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait_for_http | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | truncate_runtime_tables | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | seed_runtime_job | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | active_assignments | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait_for_assignment_count | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | count_audit_events | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_worker_summary | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 189 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tests/support/source_lab_runtime.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _ensure_namespace_package | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | prepare_source_lab_runtime_imports | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | import_source_lab_module | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 21 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tests/unit/shared/persistence/test_scada_protocol_params.py

违规数: 21

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _init_tables | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_param_def_table_created | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_endpoint_param_value_table_created | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_signal_param_def_table_created | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_signal_param_value_table_created | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_param_def_unique_constraint | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_endpoint_param_value_fk | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_param_def_insert_and_query | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_endpoint_param_value_insert | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_endpoint_params_defined | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sv_endpoint_params_defined | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modbus_tcp_endpoint_params_defined | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_endpoint_params_defined | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_mms_signal_params_defined | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modbus_signal_params_defined | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_signal_params_defined | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_signal_param_def_unique_constraint | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_param_defs_registry_completeness | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_protocol_views_sql_syntax | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_service_type_field_on_endpoint | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/unit/test_acquisition_job_handler.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_config.py

违规数: 15

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_resolve_database_backend_defaults_to_sqlite | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_state_cache_backend_defaults_to_redis | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_message_backend_defaults_to_relational_outbox | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_database_backend_accepts_supported_values | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_state_cache_backend_accepts_only_redis | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_message_backend_accepts_supported_values | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_database_backend_rejects_unknown_value | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_state_cache_backend_rejects_non_redis_values | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_message_backend_rejects_unknown_value | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_build_config_defaults_to_sqlite_and_redis | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_build_config_reports_missing_postgres_env_vars | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_build_config_requires_redis_env_vars | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_build_config_assembles_redis_and_kafka_backends | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_config_module_level_object_is_valid | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/unit/test_dual_node_write_lease_conflict.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | acquire | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | renew | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | release | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | generate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | get | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | validate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | get | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | try_acquire | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_fleet_update_selection.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_create_keeps_external_fleet_api | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_create_rejects_empty_sources | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_select_points_uses_update_count_before_update_ratio | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_select_points_uses_ratio_when_count_is_absent | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_select_points_returns_empty_when_no_points_exist | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_normalize_point_data_type_matches_legacy_semantics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_build_update_writes_uses_point_key_instead_of_full_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/unit/test_iec104_backend.py

违规数: 20

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | TestIec104ParseSampleLine | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | TestIec104ParseWriteResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | TestIec104RawReadResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | TestIec104PreparedReadPlan | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_sp_sample | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_short_sample | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_sp_zero | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_malformed_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_empty_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_non_sample | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_ok | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_failed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_malformed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_protocol_error_format | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_ok_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_failed_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_plan | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_ok_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_failed_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_iec104_source_acquisition_adapter.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | TestIec104AcquisitionAdapterDTO | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_supports_subscription_returns_false | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_start_subscription_raises | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_ioa_list_from_items | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_ioa_invalid_path_raises | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_to_acquired_batch_with_valid_data | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_to_acquired_batch_with_unmatched_ioa | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_to_acquired_batch_with_failed_raw | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_reader_validates_host | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_reader_validates_port | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_iec104_source_write_adapter.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | TestIec104WriteAdapterDTO | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_returns_no_writes | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dry_run_all_items | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_ioa_valid | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_ioa_invalid | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_command_type_bool | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_command_type_float | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_command_type_explicit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_command_type_unknown | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_host_resolution_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_iec61850_mms_backend.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | readline | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | drain | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 60 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tests/unit/test_iec61850_report_acquisition_adapter.py

违规数: 18

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | TestReportAdapterSupportsSubscription | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | TestReportAdapterRead | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | TestReportAdapterStartSubscription | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | TestReportEventToBatch | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_supports_subscription_returns_true | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_returns_empty_batch | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_batch_source_id_is_dash | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_start_subscription_calls_reader_subscribe | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_start_subscription_invalid_connection | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_start_subscription_runner_not_available | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_handle_close_releases_resources | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_report_event_maps_to_batch | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_report_event_maps_attributes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_report_event_failed_returns_none | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_report_event_no_values_returns_none | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_report_event_fewer_values_than_items | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_batch | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_iec61850_report_backend.py

违规数: 25

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | TestReportLineParsing | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | TestReportBackendErrors | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | TestReportLineIntegration | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | TestReportBackendErrorCallback | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_report_line_full | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_report_line_minimal | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_report_line_no_values | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_report_line_malformed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_report_line_empty | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_report_runner_not_found | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_close_without_subscribe | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_close_idempotent | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_is_active_false_by_default | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_double_subscribe_fails | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_event | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_event | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_event | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_event | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_iec61850_source_acquisition_adapter.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | setup_method | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_iec61850_source_write_adapter.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | setup_method | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | setup_method | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_api_app.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_api_app_contains_expected_routes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_audit_event_schema.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_audit_event_redacts_sensitive_attributes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_audit_redaction.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_redact_password_in_attributes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_redact_token_in_attributes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_redact_private_key_in_attributes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_redact_nested_attributes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_bundle_checksum.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_bundle_checksum_ignores_existing_checksum_field | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_bundle_redaction.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_redacted_bundle_masks_sensitive_protocol_params | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_composition_injection.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | increment | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | observe_duration | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | acquire | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | renew | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | validate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | release | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_job_lease.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_job_lease_acquire_renew_release_and_expire | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_metrics_events.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_metrics_events_emitted_for_command_publish_and_polling | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | publish_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_no_source_lab_imports.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_ingest_production_code_does_not_import_source_lab | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_observability_sink.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_jsonl_metrics_sink_persists_event | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_jsonl_audit_sink_persists_event | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_runtime_entrypoint.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_runtime_entrypoint_rejects_invalid_command | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_entrypoint_api_smoke | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_runtime_modes.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_runtime_mode_parse_known_values | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_mode_parse_rejects_unknown_value | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_runtime_orm_models.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_runtime_tables_are_registered_in_metadata | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_runtime_scheduler_import.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_runtime_scheduler_module_imports | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_security_partition_config.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_security_partition_config_exists_and_contains_required_guards | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_source_adapter_capability_matrix.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_acquisition_capability_matrix_no_overclaim | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_write_capability_matrix_no_overclaim | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_write_lease.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_write_lease_conflict_and_reuse | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_write_lease_fencing.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_write_lease_renewal_extends_expiry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_expired_write_lease_rejects_command | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_old_primary_fencing_token_rejects_command | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_ingest_write_security_profile.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_default_profile_denies_all_protocols | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_explicitly_allowed_protocol_is_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_profile_for_normalizes_protocol_name | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_profile_for_returns_default_for_unknown_protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_protocol_write_profile_readback_strategy | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_protocol_write_profile_custom_roles | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_write_security_profile_immutable_by_default | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_readback_strategy_enum_values | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_kafka_message_publisher.py

违规数: 14

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | FakeKafkaFuture | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FakeKafkaProducer | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FailingKafkaProducer | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_publish_snapshot_calls_kafka_send | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_publish_snapshot_uses_source_id_key_strategy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_publish_snapshot_returns_classified_error | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | __init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | get | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | send | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | flush | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | send | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | get | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 54 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tests/unit/test_modbus_source_acquisition_adapter.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | prepare_read | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_prepared | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | setup_method | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_modbus_source_write_adapter.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | setup_method | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | prepare_read | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_prepared | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | setup_method | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_opcua_adapter_resolution.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_resolve_endpoint_from_protocol_transport_host_and_port | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_endpoint_empty_when_host_or_port_is_missing | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_node_paths_adds_namespace_uri_for_relative_paths | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_node_paths_without_namespace_uri_uses_string_nodeid | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resolve_node_paths_preserves_prequalified_path | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_opcua_source_acquisition_adapter.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_read_prepared_raw_success_returns_acquired_batch | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_endpoint_uses_opc_tcp_scheme | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_value_count_mismatch_raises_source_batch_mismatch_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_raw_error_raises_source_read_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_timeout_raises_source_read_timeout_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_start_subscription_raises_unsupported_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | prepare_read | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_prepared_raw | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_opcua_source_write_adapter.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | setup_method | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | prepare_read | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_prepared_raw | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | setup_method | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_open62541_backend.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_read_prepared_raw_parses_real_values_from_value_lines | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_prepared_raw_reorders_value_lines_by_value_index | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_prepared_raw_fails_when_result_value_count_does_not_match_plan | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_prepared_raw_fails_when_value_lines_are_missing | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_prepared_raw_fails_when_value_index_is_duplicated | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_prepared_raw_fails_when_value_index_is_out_of_range | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | readline | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | drain | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 64 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P2 | 无解释 type:ignore | line 65 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tests/unit/test_polling_acquisition_role.py

违规数: 13

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_single_connection_success_updates_cache_and_marks_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_empty_batch_does_not_update_cache_or_mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_failure_marks_connection_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_once_all_failed_raises_aggregate_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_cache_write_failure_does_not_mark_connection_alive_or_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_one_connection_failure_does_not_block_other_connections | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_max_iteration_one_finishes_normally | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_close_stops_long_running_polling_session | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_redis_source_state_cache.py

违规数: 23

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | FakePipeline | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FakeRedisClient | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_update_writes_ld_meta_and_variable_state | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_mark_unavailable_keeps_last_valid_value | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_older_server_timestamp_does_not_override_newer_value | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_client_sequence_protects_against_out_of_order_updates | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_stale_update_does_not_restore_valid_after_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_fresh_update_restores_valid_and_clears_reason | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_mark_alive_does_not_promote_error_without_new_update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_snapshot_returns_ld_level_state_with_utc_datetimes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_snapshot_supports_bytes_backed_redis_payloads | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_pipeline_execute_failure_raises_classified_write_error_and_preserves_meta_state | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_transaction_pipeline_failure_does_not_leave_partial_writes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_mark_unavailable_uses_transaction_pipeline_without_partial_downgrade | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_redis_failures_are_classified_to_stable_error_codes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_transaction_failure_is_classified_for_mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | hset | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | hset | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | hget | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | hgetall | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pipeline | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_redis_streams_message_publisher.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | FakeRedisStreamsClient | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_publish_snapshot_calls_xadd | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | __init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | xadd | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/unit/test_relational_outbox_message_publisher.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _build_message | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_publish_snapshot_returns_success_for_noop_outbox | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/unit/test_scheduler_job_routes.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | test_patch_scheduler_job_updates_stagger_offset | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/unit/test_source_acquisition_port_registry.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_protocol_keys_are_normalized | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_unknown_protocol_raises_value_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_source_acquisition_use_case.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_read_once_routes_to_polling_role | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_routes_to_polling_role | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_fails_fast_when_current_reader_does_not_support_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_once_propagates_one_shot_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_read_requires_max_iteration_equal_to_one | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_request_validation_errors | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_source_command_audit.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_source_command_emits_success_audit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_source_command_emits_rejected_audit_when_write_disabled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_source_command_authorization_guard.py

违规数: 20

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _RecordingWritePort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _AllowAllPolicy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _DenyAllPolicy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _RecordPolicy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | principal | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | connection | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | execution | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_rejects_when_protocol_not_allowed | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_rejects_when_access_policy_denies | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_delegates_to_inner_when_allowed | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_passess_correct_permission_to_policy | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_rejects_when_both_disallowed_and_denied | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolves_ied_name_or_ld_name_for_resource_id | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modifies_nothing_on_inner_result | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | asyncio_run | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | evaluate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | evaluate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | evaluate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_source_command_lease_release.py

违规数: 14

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | acquire | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | renew | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | validate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | release | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | precheck | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | readback | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | readback | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | readback | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_source_command_use_case.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | setup_method | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | teardown_method | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_source_command_write_lease_guard.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_source_command_rejects_when_write_lease_denies | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | acquire | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | release | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_source_runtime_config_repository.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_repository_lists_servers_and_profile_items | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_repository_can_limit_servers_to_first_group | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tests/unit/test_source_scheduling.py

违规数: 87

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_read_concurrency_limiter_rejects_non_positive_max_concurrent | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_read_concurrency_limiter_run_returns_operation_result | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_read_concurrency_limiter_snapshot_and_reset_counters_keep_async_api | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_read_concurrency_limiter_recovers_active_count_after_exception | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_read_concurrency_limiter_respects_max_observed_active_under_parallel_load | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_polling_job_spec_validates_local_scheduler_fields | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_rejects_duplicate_and_late_add_job | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_result_event_and_stats_include_timing | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_started_at_tracks_actual_operation_start | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_slow_callback_does_not_block_future_ticks | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_without_diagnostics_keeps_default_stats_and_returns_raw_result | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_does_not_treat_result_ok_false_as_error | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_timeout_error_updates_stats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_high_frequency_fixed_rate_scheduler_emits_result_events | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_exception_routes_to_on_error_without_diagnostics_stats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_exception_updates_stats_when_diagnostics_enabled | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_timeout_without_diagnostics_keeps_default_timeout_stats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_skip_missed_records_overrun | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_polling_scheduler_skip_missed_without_diagnostics_keeps_default_stats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_build_even_stagger_offsets_and_assign_even_stagger_behave_deterministically | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scenario | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | return_one | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | hold_slot | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fail | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | slow_operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fast_operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | operation | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_result | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | on_error | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 182 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P2 | 无解释 type:ignore | line 542 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tests/unit/test_source_simulation_support_sources.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_build_multi_sources_allocates_unique_ports_in_configured_range | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_port_allocator_allocate_many_returns_unique_ports | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_port_allocator_skips_temporarily_occupied_port | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_tcp_port_probe_detects_loopback_binding | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_tcp_port_probe_detects_any_binding | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_tcp_port_probe_detects_ipv6_binding_when_supported | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_multi_sources_skips_temporarily_occupied_port | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_multi_sources_uses_explicit_ports | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_multi_sources_rejects_wrong_port_count | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_multi_sources_raises_when_range_is_too_small | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_multi_sources_reuses_range_defaults_for_invalid_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_source_write_port_registry.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | setup_method | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_state_snapshot_publish_use_case.py

违规数: 27

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | FakePublisher | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FakeFailingPublisher | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | TestStateSnapshotPublishUseCase | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | publish_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | publish_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_publish_one_source_one_value | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_publish_multiple_sources | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_empty_cache_returns_no_data | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_filter_by_source_id | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_filter_by_ld_name | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_filter_no_match_returns_no_data | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_dry_run_does_not_publish | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_cache_read_error_returns_failed | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_publish_error_returns_failed | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_publish_unsuccessful_result | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_message_item_field_mapping | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_item_has_model_id_fallback | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_multi_message_splitting | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_single_message_no_seq_suffix | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_snapshot_message_structure | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_snapshot_id_uniqueness | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_partial_failure_aggregation | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | BrokenReader | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | AlternatingPublisher | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | publish_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_subscription_acquisition_role.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | FakeStateCachePort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FakeSubscriptionHandle | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FakeAcquisitionPort | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscription_unsupported_marks_connection_unavailable_and_raises | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_supported_subscription_reads_baseline_before_starting_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | close | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_subscription_reconnect_baseline.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_reconnect_attempt_replays_baseline_before_resubscribe | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | close | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_subscription_reconnect_runtime.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_subscription_reconnect_runtime_succeeds_before_max_retry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscription_reconnect_runtime_fails_after_max_retry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | close | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | emit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | mark_unavailable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | supports_subscription | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_subscription | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tests/unit/test_worker_runtime_do_execute.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | execute | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### tools/source_lab/access/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### tools/source_lab/access/capacity.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _explicit_subscribe_source_update_hz | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | scan_capacity | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/common/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### tools/source_lab/access/common/access_model.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | AccessMode | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | AccessBatch | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | AccessRunSummary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/common/cpu.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | CpuSampleSummary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _percentile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _safe_mean | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | CpuSampler | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | __init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | stop | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 64 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/common/io.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | FieldEndpointMetadata | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FieldServerRow | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SignalProfileItemRow | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _detect_dialect | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _required_value | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _optional_value | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _first_present | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _parse_enabled | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _load_rows | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | load_field_servers | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | load_signal_profile_items | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _group_profile_items | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _known_profile_ids | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_field_runtime_sources | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 10 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/common/progress.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | CapacityProgressBar | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | update | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | close | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/common/scheduling.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | RunnerEndpointPlan | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | parse_int_list_or_ramp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | parse_float_list_or_ramp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | iter_int_ramp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | iter_float_ramp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_source_specs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | partition_specs_round_robin | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | resolve_mp_context | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/common/table.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | render_fixed_width_table | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/common/utils.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | normalize_protocol | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/config.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _env_flag | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _env_int | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _env_float | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _env_first_int | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _env_first_float | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _env_first_flag | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _env_first_int_or_none | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _env_first_float_or_none | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _check_deprecated_load_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | from_env_for_simulator | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | from_env_for_simulator_polling_capacity_args | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | from_env_for_field_capacity | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | from_env_for_probe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | from_env_for_simulator_subscribe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SimulatorSubscribeCapacityArgs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | from_env_for_simulator_subscribe_capacity_args | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/field_capacity.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | FieldCapacityRow | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FieldCapacityRequest | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FieldCapacityArtifacts | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FieldCapacityServiceResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | CpuSnapshot | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | print_capacity_table | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write_capacity_reports | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_capacity_summary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_polling_capacity_rows | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_subscribe_capacity_rows | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_field_capacity | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_field_capacity_from_files | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | cpu_mean_pct | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | cpu_max_pct | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | rss_mb | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | warning | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/polling/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### tools/source_lab/access/polling/capacity.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _run_confirmed_level | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | scan_source_capacity | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/polling/capacity_rows.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | CpuSnapshot | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | polling_row | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_polling_capacity_rows | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | cpu_mean_pct | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | cpu_max_pct | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | rss_mb | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | warning | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/polling/metrics.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | ReaderStats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | RunnerTrace | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | RunnerSummary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | WorkerRawStats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | record_tick | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _percentile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | evaluate_response_periods | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_level_metrics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_skip_result | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/polling/model.py

违规数: 18

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | CapacityStatus | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | PeriodGap | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ResponsePeriodStats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | TickResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | CapacityLevelMetrics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ConfirmedLevelResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | CapacityScanConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | CapacityScanResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ProbeConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ProbeLatencyStats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ServerProbeResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ProbeResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | final_metrics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | __post_init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | from_env_for_simulator | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | has_accepted_level | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 9 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/polling/profile.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | PollingProfileResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_polling_profile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | output_text | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 30 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/polling/reporter.py

违规数: 14

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _emit_progress_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_scan_started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_level_started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_measurement_started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_measurement_progress | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_runner_started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_worker_diagnostics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_level_done | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_stop_hz_ramp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_scan_finished | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ServerCountSummary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | summarize_server_count_levels | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_capacity_report | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/polling/worker.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _run_worker_entry | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_worker_level | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_level_once | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/probe.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | ProbeWarning | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _canonical_protocol_name | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _skip_result | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _probe_capacity_config | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _metadata_from_source | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _tcp_reachable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _percentile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_latency | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _probe_one_source | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _is_valid_mqtt_publish | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_probe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/profile.py

违规数: 9

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | FieldProfileRequest | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FieldProfileArtifacts | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | FieldProfileServiceResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | write_profile_reports | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_profile_summary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_field_profile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_field_profile_from_files | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_profile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/providers/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### tools/source_lab/access/providers/base.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | SourceRuntimeSpec | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SourceProvider | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_sources | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 9 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/providers/expanded_field.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | ExpandedFieldSourceProvider | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_sources | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 10 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/providers/field.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | FieldSourceProvider | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_sources | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/providers/file_field.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | FieldFileSourceProvider | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_field_source_provider | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | __init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_sources | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/providers/simulator.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | SimulatorSourceProvider | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | from_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_sources | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 11 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P2 | 无解释 type:ignore | line 12 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/runners/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### tools/source_lab/access/runners/base.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | CapacityRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscriptionRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | name | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_worker | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | name | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_worker | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/runners/http_rest_polling.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | HttpRestPollingRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_once | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runners/iec101_event.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | Iec101EventRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_stream_sample | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 30 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/runners/iec101_polling.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | read_once | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 27 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/runners/iec104_event.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | Iec104EventRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_stream_sample | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runners/iec104_polling.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | read_once | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runners/iec61850_l2_streaming.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _Iec61850L2StreamingRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec61850GooseStreamingRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec61850SvStreamingRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_worker | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runners/iec61850_mms_polling.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _is_valid_mms_like_response | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec61850MmsPollingRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_once | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runners/iec61850_report.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | Iec61850ReportRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | read_stream_sample | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runners/modbus_rtu_polling.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | read_once | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 56 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/runners/modbus_tcp_polling.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | read_once | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runners/mqtt_subscription.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | read_stream_sample | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runners/native_cmd.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | NativeRunnerUnavailableError | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _NativeSession | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | NativeCmdCapacityRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | check_available | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_command | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_worker | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runners/native_runner_map.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | build_command | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | check_available | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_command | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_command | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | check_available | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_command | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_command | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runners/open62541_serial_polling.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | ParsedRunnerResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _RunnerSessionResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | OpcUaOpen62541CapacityRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _resolve_runner_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _write_endpoint_file | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | parse_result_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | parse_summary_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _tick_result_from_parsed | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _stop_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_serial_polling_session | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _empty_worker_stats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_serial_polling_probe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_serial_polling_worker | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_worker | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 13 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/runners/open62541_subscription.py

违规数: 18

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | ParsedSubscribeNotify | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ParsedSubscribeSummary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ParsedSubscribeEndpointDiag | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _RunnerSessionResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | OpcUaOpen62541SubscribeRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _resolve_runner_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _write_endpoint_file | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | parse_notify_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | parse_summary_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | parse_endpoint_diag_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _stop_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_subscription_session | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _metadata_from_source | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _empty_worker_stats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_open62541_subscribe_worker | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_worker | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 12 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/runners/protocol.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | ProtocolDiagnostics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | read_protocol_line | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | drain_stderr | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | start_stderr_drain_thread | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | record_stdout_noise | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | record_stderr | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | render_context | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/runners/registry.py

违规数: 15

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _normalize_alias_key | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | normalize_protocol | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | list_supported_protocols | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | get_protocol_capability | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | get_implementation_level | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | get_backend | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | get_limitation | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | get_current_implementation_level | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | get_target_implementation_level | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | supports_access_mode | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | probe_mode_for_protocol | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | list_service_capabilities | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | get_service_capability | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | resolve_service_triple | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/runtime/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### tools/source_lab/access/runtime/continuity_model.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | EndpointContinuityMetrics | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | to_dict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | from_dict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runtime/continuity_monitor.py

违规数: 14

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | ContinuityMonitor | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | ensure_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | bind_runtime | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | record_start | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | record_stop | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | record_pause | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | record_expected_tick | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | record_stream_drop | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | record_sample | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | record_event | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | tag_operation | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runtime/dynamic_cli.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | build_registry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | validate_accepted_state_payload | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | main | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runtime/endpoint_registry.py

违规数: 14

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | RegistryOperationResult | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | EndpointRuntimeRegistry | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | add_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pause_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | resume_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | delete_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | replace_points | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | list_status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | get_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | recover | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runtime/endpoint_runtime.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | EndpointMode | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | EndpointRuntimeState | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | utc_now_iso | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | redact_sensitive_mapping | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | EndpointRuntimeConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | EndpointRuntime | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | expected_period_ms | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | to_dict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | from_dict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | to_dict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | from_dict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runtime/native_interactive_control.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### tools/source_lab/access/runtime/operation_journal.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | OperationJournalEntry | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | to_dict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | create | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runtime/session_manager.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | NativeSessionHandle | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | EndpointSessionManager | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pause_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | resume_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | replace_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runtime/stagger_coordinator.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | StaggerCoordinator | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | assign_offset | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | preserve_offset | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | delete_offset | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/runtime/state_store.py

违规数: 25

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | SnapshotLoadResult | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | RecoveryLoadBundle | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | RuntimeStateStore | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | errors | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | selected_backups | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | locked | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | save_accepted_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_accepted_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | save_registry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_registry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | save_runtime_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_runtime_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | save_continuity_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_continuity_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_recovery_bundle | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | export_accepted_state | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | import_accepted_state | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | dump_continuity | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | dump_registry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | inspect_state_store | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | repair_state_store | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | append_journal_entry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_journal_entries | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | validate_accepted_state_bundle | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/subscribe/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### tools/source_lab/access/subscribe/capacity.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | scan_subscribe_capacity_service | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/subscribe/capacity_model.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | SubscribeCapacityComboResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscribeCapacityLimitSummary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscribeCapacityResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/subscribe/capacity_plan.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | SubscribeCapacityMatrixPlan | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | combo_count | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | validate | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/subscribe/capacity_rows.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | CpuSnapshot | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | sample_hz_to_interval_ms | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | status_for_subscribe_level | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | subscribe_row | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_subscribe_capacity_rows | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | cpu_mean_pct | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | cpu_max_pct | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | rss_mb | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | warning | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/subscribe/capacity_scan.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | scan_subscribe_capacity | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _failure_stage | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/subscribe/metrics.py

违规数: 15

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _percentile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _stat_bundle | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _periods_from_int_ns | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _publish_gaps_ms | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _notify_periods_ms | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _data_notify_batches | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _notify_period_gap_traces | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _callback_to_flush_lag_values_ms | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _callback_to_flush_lag_samples | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _top_flush_lag_traces | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _source_periods_ms | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _data_periods_ms | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _top_dispatch_gap_traces | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_subscribe_level_metrics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/subscribe/model.py

违规数: 15

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | SubscribeRunnerTrace | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscribePeriodGapTrace | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscribeFlushLagTrace | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscribeEndpointDispatchTrace | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscribeWorkerRawStats | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscribeScanConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscribeLevelMetrics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscribeLevelResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscribeScanResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SubscribeReportRow | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _GroupedBatches | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | __post_init__ | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | final_metrics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | has_accepted_level | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/subscribe/profile.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | SubscribeProfileResult | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_subscribe_profile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | output_text | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 30 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/access/subscribe/reporter.py

违规数: 15

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | SubscribeProgressReporter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_subscribe_scan_started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_subscribe_level_started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_subscribe_level_done | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_subscribe_stop_ramp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_subscribe_scan_finished | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_subscribe_capacity_table | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | print_subscribe_report | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | from_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scan_started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | level_started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | level_done | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_ramp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | scan_finished | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/access/subscribe/scan.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _run_confirmed_level | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | scan_source_subscriptions | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/access/subscribe/worker.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _run_worker_entry | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | run_subscribe_level_once | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/contracts.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | SourceSimulator | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | name | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | writes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/factory.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _normalize_protocol | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_simulator | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/field_capacity.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _parse_bool | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _resolve_run_id | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _parse_source_update_hz_values | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_parser | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | main | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/field_probe.py

违规数: 3

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _build_parser | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _format_metric | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | main | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/field_profile.py

违规数: 5

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _resolve_run_id | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _parse_bool | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _print_profile_report | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_parser | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | main | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/fleet.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _resolve_startup_timeout_seconds | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _resolve_start_concurrency | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _resolve_start_stagger_ms | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_simulator_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_facade_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SourceSimulatorFleet | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | create | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | restart_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | status_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_source_values | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 265 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/model.py

违规数: 13

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | UpdateConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SecurityConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | AuthConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | HeartbeatConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | TimeoutConfig | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SimulatedPoint | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | SimulatedSource | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | from_protocol | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | key | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | locator | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | display_name | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | point_kind | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/protocols/common/_base_facade.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | health | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_points | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | subscribe | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | report | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_values | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/protocols/common/_interactive_runner.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | NativeInteractiveRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _resolve_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | start | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | command | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | stop | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/protocols/common/simulators.py

违规数: 15

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | MqttSimulator | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ModbusRtuSimulator | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec101Simulator | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | name | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | writes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | name | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | writes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | do_GET | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | log_message | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/protocols/http_rest/simulator.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | HttpRestSimulatorFacade | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | health | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_points | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_values | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/protocols/iec101/simulator.py

违规数: 7

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | health | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_points | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_values | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/protocols/iec104/simulator.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | health | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_points | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_values | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 45 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P2 | 无解释 type:ignore | line 48 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P2 | 无解释 type:ignore | line 51 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P2 | 无解释 type:ignore | line 54 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/protocols/iec61850/simulator.py

违规数: 38

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _infer_fc | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _point_to_mms_ref | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _value_type_from_data_type | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _parse_read_result | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec61850MmsSimulatorFacade | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _coerce_value | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec61850ReportSimulatorFacade | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _collect_report_events | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec61850GooseSimulatorFacade | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | Iec61850SvSimulatorFacade | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | health | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_points | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_values | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | subscribe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | report | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | health | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | subscribe | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | health | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | subscribe | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/protocols/modbus/simulator.py

违规数: 18

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | ModbusTcpSimulatorFacade | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | ModbusRtuSimulatorFacade | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | health | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_points | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_values | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 58 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/protocols/mqtt/simulator.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | health | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_points | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | read | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_values | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/protocols/opcua/__init__.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |

### tools/source_lab/protocols/opcua/simulator.py

违规数: 11

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | OpcUaSimulatorFacade | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | health | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | load_points | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_values | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | datachange_notification | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 124 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/protocols/registry.py

违规数: 1

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P2 | 无解释 type:ignore | line 99 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/sources.py

违规数: 13

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _resolve_bind_host | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _is_tcp_port_available | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | PortAllocator | public ClassDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | choose_available_port | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | assign_dynamic_port | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_opcua_source_from_repository | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_multi_sources | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_opcua_endpoint | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | from_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | from_range | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | allocate_many | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 11 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/tests/access/_dynamic_runtime_test_utils.py

违规数: 34

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | choose_port | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_http_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_modbus_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_mqtt_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_opcua_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_iec61850_report_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_goose_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sv_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | runtime_spec | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | polling_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | subscribe_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | report_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | streaming_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_registry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_native_registry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | shutdown_registry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait_for_metric_growth | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | choose_port | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_http_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_modbus_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_mqtt_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_opcua_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_iec61850_report_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_goose_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sv_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | runtime_spec | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | polling_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | subscribe_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | report_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | streaming_config | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_registry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_native_registry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | shutdown_registry | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait_for_metric_growth | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_access_config.py

违规数: 46

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_from_env_supports_start_step_max | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_from_env_supports_alias_server_count_and_target_hz | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_from_env_fixed_defaults | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_capacity_config_does_not_expose_preflight_fields | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_from_env_supports_progress_flags | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_supports_polling_tolerance_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_rejects_negative_polling_tolerances | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_supports_subscribe_data_period_tolerance_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_for_subscribe_defaults_to_auto_match_source_rate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_for_subscribe_marks_explicit_source_rate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_keeps_subscribe_tolerance_default | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_rejects_negative_subscribe_tolerance | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_ignores_removed_legacy_coroutine_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_does_not_expose_backend_fields | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_supports_runner_trace_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_env_loader_parses_probe_settings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_from_env_rejects_deprecated_load_variables | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_args_parse_ramps | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_args_prefers_lists | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_capacity_args_parse_ramps_from_poll_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_polling_capacity_args_poll_env_precedence_over_load_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_from_env_poll_aliases_take_priority | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_from_env_supports_start_step_max | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_from_env_supports_alias_server_count_and_target_hz | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_from_env_fixed_defaults | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_capacity_config_does_not_expose_preflight_fields | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_from_env_supports_progress_flags | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_supports_polling_tolerance_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_rejects_negative_polling_tolerances | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_supports_subscribe_data_period_tolerance_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_for_subscribe_defaults_to_auto_match_source_rate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_for_subscribe_marks_explicit_source_rate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_keeps_subscribe_tolerance_default | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_rejects_negative_subscribe_tolerance | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_ignores_removed_legacy_coroutine_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_does_not_expose_backend_fields | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_from_env_supports_runner_trace_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_env_loader_parses_probe_settings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_from_env_rejects_deprecated_load_variables | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_args_parse_ramps | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_args_prefers_lists | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_capacity_args_parse_ramps_from_poll_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_polling_capacity_args_poll_env_precedence_over_load_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_from_env_poll_aliases_take_priority | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_access_facades.py

违规数: 38

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_dispatches_polling | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_dispatches_subscribe | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_subscribe_uses_source_update_hz_dimension | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_subscribe_executes_when_sample_hz_below_explicit_source_rate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_subscribe_explicit_source_update_keeps_all_lower_hz_runnable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_matrix_plan_validates_and_counts | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_matrix_plan_rejects_empty_dimensions | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_subscribe_matrix_keeps_all_runtime_combos_after_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_polling_process_ramp_builds_independent_results | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_polling_stop_hz_ramp_only_for_current_server | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_rejects_invalid_access_mode | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_profile_facade_dispatches_polling | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_profile_facade_dispatches_subscribe | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_profile_facade_rejects_invalid_access_mode | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_worker | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_worker | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_dispatches_polling | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_dispatches_subscribe | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_subscribe_uses_source_update_hz_dimension | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_subscribe_executes_when_sample_hz_below_explicit_source_rate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_subscribe_explicit_source_update_keeps_all_lower_hz_runnable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_matrix_plan_validates_and_counts | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_matrix_plan_rejects_empty_dimensions | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_subscribe_matrix_keeps_all_runtime_combos_after_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_polling_process_ramp_builds_independent_results | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_polling_stop_hz_ramp_only_for_current_server | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_facade_rejects_invalid_access_mode | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_profile_facade_dispatches_polling | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_profile_facade_dispatches_subscribe | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_profile_facade_rejects_invalid_access_mode | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_worker | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_worker | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_access_metrics.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_evaluate_response_periods_basic | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_skip_result_status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_level_metrics_contains_data_period_max_reason | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_worker_raw_stats_diagnostics_do_not_change_metrics_semantics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_evaluate_response_periods_basic | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_skip_result_status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_level_metrics_contains_data_period_max_reason | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_worker_raw_stats_diagnostics_do_not_change_metrics_semantics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_access_probe.py

违规数: 22

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _config | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _source | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_fails_when_tcp_is_unreachable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_marks_non_target_protocol_as_filtered | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_marks_unknown_protocol_as_unsupported | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_reports_runner_exception | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_short_read_ok | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_detects_value_count_mismatch | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_detects_missing_timestamp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_latency_samples_include_percentiles | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _config | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _source | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_fails_when_tcp_is_unreachable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_marks_non_target_protocol_as_filtered | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_marks_unknown_protocol_as_unsupported | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_reports_runner_exception | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_short_read_ok | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_detects_value_count_mismatch | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_detects_missing_timestamp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_probe_latency_samples_include_percentiles | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_access_probe_protocol_handshake.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_polling_probe_dispatches_modbus_tcp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_probe_dispatches_iec104 | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_streaming_probe_dispatches_mqtt | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_streaming_probe_dispatches_iec61850_report | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 7 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_polling_probe_dispatches_modbus_tcp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_probe_dispatches_iec104 | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_streaming_probe_dispatches_mqtt | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_streaming_probe_dispatches_iec61850_report | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 7 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/tests/access/test_access_probe_protocol_semantics.py

违规数: 18

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_mqtt_probe_passes_with_publish_payload | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_mqtt_probe_fails_when_publish_invalid | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_report_probe_requires_mms_like_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_report_probe_fails_on_invalid_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | settimeout | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | sendall | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | recv | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 10 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_mqtt_probe_passes_with_publish_payload | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_mqtt_probe_fails_when_publish_invalid | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_report_probe_requires_mms_like_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_report_probe_fails_on_invalid_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | settimeout | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | sendall | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | recv | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 10 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/tests/access/test_access_progress_reporting.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_scan_progress_output_contains_main_stages | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_scan_progress_output_can_be_disabled | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_scan_progress_output_contains_main_stages | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_scan_progress_output_can_be_disabled | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_access_reporter.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_summary_distinguishes_stable_flaky_fail | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_summary_can_accept_flaky_when_enabled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_progress_output_contains_key_fields | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_progress_output_can_be_disabled | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_worker_diagnostics_prints_summaries_and_top_traces | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_worker_diagnostics_skips_top_trace_when_disabled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_report_omits_preflight_and_keeps_core_columns | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_summary_distinguishes_stable_flaky_fail | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_summary_can_accept_flaky_when_enabled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_progress_output_contains_key_fields | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_progress_output_can_be_disabled | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_worker_diagnostics_prints_summaries_and_top_traces | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_worker_diagnostics_skips_top_trace_when_disabled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_capacity_report_omits_preflight_and_keeps_core_columns | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_access_scheduling.py

违规数: 22

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_iter_int_ramp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iter_float_ramp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_partition_specs_round_robin | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_source_specs_offset_distribution | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_source_specs_returns_empty_for_empty_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_int_list_or_ramp_prefers_list | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_int_list_or_ramp_uses_ramp_when_list_missing | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_float_list_or_ramp_defaults_when_no_inputs | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_float_list_or_ramp_rejects_invalid_step | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_int_list_or_ramp_rejects_partial_ramp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_iter_int_ramp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iter_float_ramp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_partition_specs_round_robin | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_source_specs_offset_distribution | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_source_specs_returns_empty_for_empty_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_int_list_or_ramp_prefers_list | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_int_list_or_ramp_uses_ramp_when_list_missing | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_float_list_or_ramp_defaults_when_no_inputs | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_float_list_or_ramp_rejects_invalid_step | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_int_list_or_ramp_rejects_partial_ramp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_access_structure.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_legacy_access_shim_files_do_not_exist | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_common_package_does_not_host_mode_specific_capacity_rows | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_cli_entrypoints_import_after_access_regrouping | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_legacy_access_shim_files_do_not_exist | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_common_package_does_not_host_mode_specific_capacity_rows | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_cli_entrypoints_import_after_access_regrouping | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_access_worker.py

违规数: 18

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_worker_exports | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_worker_depends_on_runner_protocol_not_open62541_module | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_level_once_process_count_one_uses_injected_runner | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_level_forwards_arguments_to_runner | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_level_once_partitions_sources_across_workers | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_worker | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | submit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_worker_exports | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_worker_depends_on_runner_protocol_not_open62541_module | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_level_once_process_count_one_uses_injected_runner | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_level_forwards_arguments_to_runner | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_level_once_partitions_sources_across_workers | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_worker | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | submit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_all_protocols_polling_capacity.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | test_all_polling_capacity_protocols_are_supported | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_polling_capacity_protocols_are_supported | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_all_protocols_polling_profile.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | test_all_polling_profile_protocols_build_capacity_runner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_polling_profile_protocols_build_capacity_runner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_all_protocols_probe.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | test_all_protocols_have_probe_mode_or_explicit_support | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_protocols_have_probe_mode_or_explicit_support | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_all_protocols_streaming_capacity.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | test_all_streaming_capacity_protocols_are_supported | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_streaming_capacity_protocols_are_supported | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_all_protocols_streaming_profile.py

违规数: 2

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | test_all_streaming_profile_protocols_build_subscription_runner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_streaming_profile_protocols_build_subscription_runner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_capacity_progress.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_progress_bar_uses_carriage_return_on_tty | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_progress_bar_close_clears_rendered_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_progress_bar_is_silent_on_non_tty | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_progress_bar_uses_carriage_return_on_tty | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_progress_bar_close_clears_rendered_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_progress_bar_is_silent_on_non_tty | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_capacity_reporter.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_summary_table_is_default_and_short | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_detail_mode_is_deprecated_and_summary_only | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_unknown_table_mode_falls_back_to_summary | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_print_capacity_summary_reuses_summary_table | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_summary_uses_subscribe_headers_and_data_period_values | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_summary_table_is_default_and_short | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_detail_mode_is_deprecated_and_summary_only | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_unknown_table_mode_falls_back_to_summary | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_print_capacity_summary_reuses_summary_table | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_summary_uses_subscribe_headers_and_data_period_values | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_capacity_rows.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_polling_flaky_row_uses_recovered_attempt_metrics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_fail_row_uses_final_failed_attempt_metrics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_pass_row_uses_pass_attempt_metrics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_row_uses_final_metrics_and_not_value_ratio_for_status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_polling_flaky_row_uses_recovered_attempt_metrics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_fail_row_uses_final_failed_attempt_metrics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_pass_row_uses_pass_attempt_metrics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_row_uses_final_metrics_and_not_value_ratio_for_status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_capacity_service.py

违规数: 20

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_polling_pass_keeps_reason_empty_and_cpu_warning_in_warnings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_pass_keeps_reason_empty_and_cpu_warning_in_warnings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_fail_keeps_business_reason_when_cpu_warning_present | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_derives_interval_and_source_update_per_sample_hz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_uses_explicit_publishing_interval_for_all_sample_hz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_keeps_pass_when_source_update_hz_below_sample_hz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_source_update_disabled_adds_warning_without_overwriting_reason | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_polling_pass_keeps_reason_empty_and_cpu_warning_in_warnings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_pass_keeps_reason_empty_and_cpu_warning_in_warnings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_fail_keeps_business_reason_when_cpu_warning_present | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_derives_interval_and_source_update_per_sample_hz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_uses_explicit_publishing_interval_for_all_sample_hz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_keeps_pass_when_source_update_hz_below_sample_hz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_source_update_disabled_adds_warning_without_overwriting_reason | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_cli.py

违规数: 30

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_cli_list_status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_add_update_pause_resume_stop_delete_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_replace_points_expected_version_conflict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_recover_writes_journal | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | to_dict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | list_status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | add_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pause_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | resume_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | delete_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | replace_points | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | recover | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_list_status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_add_update_pause_resume_stop_delete_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_replace_points_expected_version_conflict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_recover_writes_journal | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | to_dict | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | list_status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | add_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | update_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pause_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | resume_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | delete_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | replace_points | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | recover | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_cli_accepted_state.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_cli_export_import_accepted_state_roundtrip | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_validate_accepted_state_rejects_invalid_schema | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_import_failure_does_not_mutate_existing_state | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_schema_outputs_stable_json | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_dump_continuity_and_journal | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_redacts_sensitive_values | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_validate_accepted_state_rejects_duplicate_deleted_and_bad_checksum | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_import_rejects_redacted_bundle | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_export_import_accepted_state_roundtrip | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_validate_accepted_state_rejects_invalid_schema | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_import_failure_does_not_mutate_existing_state | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_schema_outputs_stable_json | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_dump_continuity_and_journal | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_redacts_sensitive_values | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_validate_accepted_state_rejects_duplicate_deleted_and_bad_checksum | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_import_rejects_redacted_bundle | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_endpoint_patch_matrix.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_patch_points_only_replaces_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_patch_host_port_replaces_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_patch_protocol_params_replaces_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_patch_mode_change_replaces_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_patch_protocol_change_replaces_target_endpoint_or_returns_validation_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_patch_security_params_redacts_sensitive_values_in_journal | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_patch_points_only_replaces_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_patch_host_port_replaces_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_patch_protocol_params_replaces_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_patch_mode_change_replaces_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_patch_protocol_change_replaces_target_endpoint_or_returns_validation_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_patch_security_params_redacts_sensitive_values_in_journal | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_goose_sv_permission_gate.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_goose_sv_permission_gate_reports_raw_socket_permission_missing_without_false_pass | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_sv_dynamic_gate_does_not_count_skip_as_pass | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_sv_permission_gate_reports_raw_socket_permission_missing_without_false_pass | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_sv_dynamic_gate_does_not_count_skip_as_pass | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py

违规数: 14

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_goose_stop_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_goose_pause_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_goose_replace_params_keeps_unaffected_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_sv_stop_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_sv_pause_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_sv_replace_params_keeps_unaffected_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_goose_sv_permission_skip_reason_is_explicit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_goose_stop_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_goose_pause_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_goose_replace_params_keeps_unaffected_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_sv_stop_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_sv_pause_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_sv_replace_params_keeps_unaffected_app_id_receiving_when_raw_socket_allowed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_goose_sv_permission_skip_reason_is_explicit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_iec61850_report_endpoint_adjustment.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_report_stop_one_rcb_keeps_other_rcb_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_report_pause_one_rcb_keeps_other_rcb_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_report_replace_points_keeps_unaffected_rcb_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_report_host_port_patch_rolls_back_without_affecting_others | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_report_continuity_metrics_for_unaffected_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_report_journal_records_success_failed_rollback | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fail_once | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fail_once | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_report_stop_one_rcb_keeps_other_rcb_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_report_pause_one_rcb_keeps_other_rcb_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_report_replace_points_keeps_unaffected_rcb_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_report_host_port_patch_rolls_back_without_affecting_others | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_report_continuity_metrics_for_unaffected_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_report_journal_records_success_failed_rollback | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fail_once | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fail_once | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_native_interactive_control_boundary.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_native_interactive_control_boundary | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_replacement_only_runner_is_not_marked_interactive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_native_interactive_control_boundary | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_replacement_only_runner_is_not_marked_interactive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_native_runner_isolation.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_native_polling_process_is_endpoint_scoped_when_replacement_required | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_native_subscription_process_is_endpoint_scoped_when_replacement_required | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_native_runner_failure_marks_only_target_endpoint_failed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_native_runner_stop_cleans_only_target_process | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_native_unaffected_runner_process_ids_stable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fail_target | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_native_polling_process_is_endpoint_scoped_when_replacement_required | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_native_subscription_process_is_endpoint_scoped_when_replacement_required | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_native_runner_failure_marks_only_target_endpoint_failed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_native_runner_stop_cleans_only_target_process | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_native_unaffected_runner_process_ids_stable | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fail_target | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_opcua_polling_endpoint_adjustment.py

违规数: 14

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_stop_one_endpoint_keeps_others_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_replace_points_keeps_others_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_patch_host_port_replaces_only_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_replacement_failure_does_not_restart_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_stagger_offset_preserved_for_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_continuity_metrics_for_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fail_target | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_stop_one_endpoint_keeps_others_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_replace_points_keeps_others_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_patch_host_port_replaces_only_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_replacement_failure_does_not_restart_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_stagger_offset_preserved_for_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_polling_continuity_metrics_for_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fail_target | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_opcua_subscription_endpoint_adjustment.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_pause_one_endpoint_keeps_others_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_replace_points_keeps_others_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_patch_host_port_replaces_only_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_replacement_failure_does_not_restart_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_callback_gap_metrics_for_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_journal_records_success_failed_conflict_denied | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | deny_resume | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fail_target | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_pause_one_endpoint_keeps_others_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_replace_points_keeps_others_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_patch_host_port_replaces_only_target_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_replacement_failure_does_not_restart_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_callback_gap_metrics_for_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_opcua_subscription_journal_records_success_failed_conflict_denied | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | deny_resume | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | fail_target | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_operation_journal_audit.py

违规数: 24

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_status_success_and_not_found_are_journaled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_status_denied_is_journaled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_update_version_conflict_is_journaled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_invalid_patch_validation_error_is_journaled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_replacement_failure_rolls_back_or_marks_failed_and_is_journaled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_journal_contains_affected_and_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pause_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | resume_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | replace_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | deny_status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_status_success_and_not_found_are_journaled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_status_denied_is_journaled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_update_version_conflict_is_journaled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_invalid_patch_validation_error_is_journaled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_replacement_failure_rolls_back_or_marks_failed_and_is_journaled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_journal_contains_affected_and_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pause_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | resume_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | replace_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | deny_status | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_polling_endpoint_adjustment.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_polling_stop_one_modbus_endpoint_keeps_others_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_polling_update_one_http_endpoint_points_keeps_others_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_polling_stagger_offset_preserved_for_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_polling_continuity_metrics_for_unaffected_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_polling_stop_one_modbus_endpoint_keeps_others_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_polling_update_one_http_endpoint_points_keeps_others_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_polling_stagger_offset_preserved_for_unaffected_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_polling_continuity_metrics_for_unaffected_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_runtime_state_recovery.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_runtime_state_recovery_restores_enabled_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_runtime_state_recovery_keeps_paused_endpoint_paused | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_runtime_state_recovery_does_not_restore_deleted_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_runtime_state_recovery_preserves_config_version | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_runtime_state_recovery_records_recovery_event | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_runtime_state_recovery_restores_enabled_endpoints | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_runtime_state_recovery_keeps_paused_endpoint_paused | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_runtime_state_recovery_does_not_restore_deleted_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_runtime_state_recovery_preserves_config_version | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_runtime_state_recovery_records_recovery_event | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_runtime_state_store_integrity.py

违规数: 14

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_state_store_writes_checksum | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_state_store_recovers_from_backup_when_primary_checksum_fails | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_state_store_reports_error_when_primary_and_backup_corrupt | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_state_store_lock_prevents_interleaved_writes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_state_store_recovery_journal_records_checksum_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_state_store_does_not_leak_sensitive_values_in_errors | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | writer | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_state_store_writes_checksum | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_state_store_recovers_from_backup_when_primary_checksum_fails | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_state_store_reports_error_when_primary_and_backup_corrupt | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_state_store_lock_prevents_interleaved_writes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_state_store_recovery_journal_records_checksum_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_state_store_does_not_leak_sensitive_values_in_errors | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | writer | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_runtime_state_store_repair_cli.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_cli_inspect_state_store_outputs_snapshot_summary | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_repair_state_store_restores_from_backup_and_journals | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_repair_state_store_requires_from_backup_flag | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_inspect_state_store_outputs_snapshot_summary | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_repair_state_store_restores_from_backup_and_journals | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_cli_repair_state_store_requires_from_backup_flag | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_runtime_state_store_resilience.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_runtime_state_store_uses_atomic_write_for_snapshots | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_recovery_handles_corrupt_continuity_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_recovery_handles_corrupt_registry_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_recovery_journals_partial_recovery_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_recovery_does_not_start_deleted_or_invalid_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | recording_replace | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_store_uses_atomic_write_for_snapshots | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_recovery_handles_corrupt_continuity_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_recovery_handles_corrupt_registry_snapshot | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_recovery_journals_partial_recovery_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_recovery_does_not_start_deleted_or_invalid_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | recording_replace | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_runtime_state_store_retention.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_runtime_state_store_retains_recent_versioned_backups | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_store_recovery_prefers_recent_valid_backup | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_store_inspect_reports_backup_metadata | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_store_repair_restores_primary_from_backup | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_store_repair_reports_failure_without_backup | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_store_retains_recent_versioned_backups | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_store_recovery_prefers_recent_valid_backup | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_store_inspect_reports_backup_metadata | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_store_repair_restores_primary_from_backup | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runtime_state_store_repair_reports_failure_without_backup | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_dynamic_subscription_endpoint_adjustment.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_dynamic_mqtt_pause_one_topic_keeps_others_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_mqtt_replace_one_topic_keeps_others_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_subscription_journal_records_allow_deny_success_failed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pause_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | resume_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | replace_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_mqtt_pause_one_topic_keeps_others_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_mqtt_replace_one_topic_keeps_others_receiving | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dynamic_subscription_journal_records_allow_deny_success_failed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | pause_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | resume_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | stop_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | replace_endpoint | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_field_capacity_cli.py

违规数: 32

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _result | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _capture_request | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _write_input_files | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_polling_list_calls_service_with_list_values | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_polling_ramp_calls_service_with_ramp_values | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_subscribe_ramp_calls_service_with_ramp_values | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_subscribe_single_source_update_hz_stays_scalar | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_list_takes_priority_over_ramp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_rejects_invalid_ramp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_rejects_conflicting_source_update_hz_inputs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_with_service_type | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_subscribe_rejects_sampling_interval_arg | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fake_run | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _result | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _capture_request | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _write_input_files | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_polling_list_calls_service_with_list_values | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_polling_ramp_calls_service_with_ramp_values | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_subscribe_ramp_calls_service_with_ramp_values | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_subscribe_single_source_update_hz_stays_scalar | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_list_takes_priority_over_ramp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_rejects_invalid_ramp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_rejects_conflicting_source_update_hz_inputs | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_with_service_type | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_capacity_subscribe_rejects_sampling_interval_arg | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fake_run | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_field_probe_cli.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _write_input_files | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_probe_cli_builds_probe_config_and_prints_tsv | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_probe_cli_with_service_type | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fake_run_probe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _write_input_files | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_probe_cli_builds_probe_config_and_prints_tsv | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_probe_cli_with_service_type | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fake_run_probe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_field_profile_cli.py

违规数: 22

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _write_input_files | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _result | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_profile_polling_cli_builds_request_and_prints_report | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_profile_subscribe_cli_builds_request_and_prints_report | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_profile_cli_with_service_type | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_print_profile_report_dispatches_to_polling_reporter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_print_profile_report_dispatches_to_subscribe_reporter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fake_service | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fake_service | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _write_input_files | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _result | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_profile_polling_cli_builds_request_and_prints_report | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_profile_subscribe_cli_builds_request_and_prints_report | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_field_profile_cli_with_service_type | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_print_profile_report_dispatches_to_polling_reporter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_print_profile_report_dispatches_to_subscribe_reporter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fake_service | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fake_service | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_field_provider.py

违规数: 36

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_field_provider_builds_sources_from_profile_binding | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_multiple_servers_can_share_one_profile_id | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_different_servers_can_use_different_profile_ids | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_relative_path_takes_precedence_over_legacy_address | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_missing_profile_reference_raises_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_profile_with_no_enabled_items_raises_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_non_opcua_protocol_can_load_and_provider_filters_by_protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_protocol_mismatch_is_reported | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_provider_raises_when_server_count_exceeds_filtered_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_provider_raises_on_config_protocol_mismatch | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_server_and_item_signal_profile_id_aliases_are_supported | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_expanded_field_provider_overrides_host_and_skips_occupied_ports | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_field_source_provider_uses_expanded_provider_for_simulator_runtime | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_field_source_provider_keeps_real_field_provider_for_default_runtime | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_expanded_field_provider_started_cleans_up_on_success | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_expanded_field_provider_started_passes_effective_source_update_rate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_expanded_field_provider_started_cleans_up_on_exception | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_field_provider_builds_sources_from_profile_binding | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_multiple_servers_can_share_one_profile_id | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_different_servers_can_use_different_profile_ids | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_relative_path_takes_precedence_over_legacy_address | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_missing_profile_reference_raises_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_profile_with_no_enabled_items_raises_error | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_non_opcua_protocol_can_load_and_provider_filters_by_protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_protocol_mismatch_is_reported | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_provider_raises_when_server_count_exceeds_filtered_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_provider_raises_on_config_protocol_mismatch | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_server_and_item_signal_profile_id_aliases_are_supported | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_expanded_field_provider_overrides_host_and_skips_occupied_ports | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_field_source_provider_uses_expanded_provider_for_simulator_runtime | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_field_source_provider_keeps_real_field_provider_for_default_runtime | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_expanded_field_provider_started_cleans_up_on_success | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_expanded_field_provider_started_passes_effective_source_update_rate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_expanded_field_provider_started_cleans_up_on_exception | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_iec104_production_capacity_profile_gate.py

违规数: 18

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _run_simulator_server | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_supports_polling_access_mode | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_capacity_runner_can_be_built | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_python_simulator_can_start_and_stop | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_client_runner_binary_exists | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_simulator_server_binary_exists | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_read_once_via_acquisition_adapter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_write_then_readback | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 82 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P1 | 英文 docstring | _run_simulator_server | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_supports_polling_access_mode | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_capacity_runner_can_be_built | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_python_simulator_can_start_and_stop | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_client_runner_binary_exists | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_simulator_server_binary_exists | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_read_once_via_acquisition_adapter | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_write_then_readback | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 82 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py

违规数: 14

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_goose_facade_real_subscribe_event | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_facade_real_subscribe_sample | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_streaming_capacity_e2e_via_facade | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_streaming_capacity_e2e_via_facade | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_streaming_profile_e2e_via_facade | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_streaming_profile_e2e_via_facade | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_goose_facade_real_subscribe_event | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_facade_real_subscribe_sample | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_streaming_capacity_e2e_via_facade | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_streaming_capacity_e2e_via_facade | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_streaming_profile_e2e_via_facade | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_streaming_profile_e2e_via_facade | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_iec61850_l2_native_runner_failure_modes.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_goose_invalid_interface_returns_error_not_segfault | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_invalid_app_id_returns_error_not_segfault | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_timeout_without_events_prints_summary_and_done | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_invalid_interface_returns_error_not_segfault | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_timeout_without_events_prints_summary_and_done | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_invalid_interface_returns_error_not_segfault | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_invalid_app_id_returns_error_not_segfault | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_timeout_without_events_prints_summary_and_done | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_invalid_interface_returns_error_not_segfault | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_timeout_without_events_prints_summary_and_done | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_iec61850_lightweight_semantics.py

违规数: 18

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _FakeSocket | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_mms_polling_runner_validates_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_mms_polling_runner_rejects_invalid_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_report_runner_validates_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_report_runner_rejects_invalid_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | settimeout | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | sendall | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | recv | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 15 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P1 | 英文 docstring | _FakeSocket | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_mms_polling_runner_validates_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_mms_polling_runner_rejects_invalid_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_report_runner_validates_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_report_runner_rejects_invalid_response | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | settimeout | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | sendall | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | recv | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 15 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/tests/access/test_iec61850_production_capacity_profile_gate.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _start_simulator | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_spec | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _start_simulator | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_spec | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_iec61850_report_capacity_profile_gate.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | simulator_port | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_report_in_protocol_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_production_client_subscribe_is_true | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_production_client_read_is_false | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_production_client_write_is_false | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_no_goose_or_sv_falsely_marked | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_supported_subscription_operations | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_service_capability_real_native_runner | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | simulator_port | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_report_in_protocol_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_production_client_subscribe_is_true | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_production_client_read_is_false | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_production_client_write_is_false | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_no_goose_or_sv_falsely_marked | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_supported_subscription_operations | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_service_capability_real_native_runner | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_iec61850_report_runner_protocol.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_version_flag | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_version_short_flag | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_no_args_prints_usage | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_invalid_host_empty_args_fails | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_version_flag | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_version_short_flag | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_no_args_prints_usage | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_invalid_host_empty_args_fails | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_native_cmd_runner_preflight.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _TestNativeRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _RealNativeRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _TestNativeRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _RealNativeRunner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_native_process_protocol.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_ensure_executable_raises_for_missing_binary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_read_ready_line_skips_noise_and_returns_ready | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_ensure_executable_raises_for_missing_binary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_read_ready_line_skips_noise_and_returns_ready | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_native_runners_availability.py

违规数: 32

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | test_modbus_tcp_native_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modbus_rtu_native_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modbus_simulator_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_client_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec101_client_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_mms_client_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_goose_subscriber_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_goose_publisher_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_sv_subscriber_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_sv_publisher_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_l2_native_runner_version_contract | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_native_runner_map_has_entries | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_capacity_runner_fallback | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_libmodbus_available | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_lib60870_available | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_libiec61850_available | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modbus_tcp_native_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modbus_rtu_native_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modbus_simulator_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec104_client_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec101_client_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_mms_client_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_goose_subscriber_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_goose_publisher_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_sv_subscriber_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_sv_publisher_executable | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_l2_native_runner_version_contract | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_native_runner_map_has_entries | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_capacity_runner_fallback | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_libmodbus_available | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_lib60870_available | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_libiec61850_available | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_opcua_access_adapter.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_normalize_node_id_adds_s_prefix | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_normalize_node_id_keeps_existing_s_prefix | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_normalize_node_id_adds_s_prefix | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_normalize_node_id_keeps_existing_s_prefix | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_open62541_serial_polling_runner.py

违规数: 80

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_parse_result_line_parses_local_and_global_index | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_result_line_maps_error_semantics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_ignores_value_lines | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_result_line_rejects_malformed_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_summary_line_parses_measurement_and_warmup_fields | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_summary_line_rejects_malformed_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_stop_process_terminates_then_kills_after_timeouts | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_raises_on_non_zero_exit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_raises_on_error_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_records_small_protocol_noise | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_fails_on_protocol_noise_overflow | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_returns_summary_and_top_traces | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_probe_returns_tick_results | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_probe_returns_empty_when_session_has_no_results | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_adapter_class_delegates_to_worker_runner | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | flush | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | close | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_parse_result_line_parses_local_and_global_index | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_result_line_maps_error_semantics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_ignores_value_lines | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_result_line_rejects_malformed_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_summary_line_parses_measurement_and_warmup_fields | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_summary_line_rejects_malformed_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_stop_process_terminates_then_kills_after_timeouts | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_raises_on_non_zero_exit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_raises_on_error_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_records_small_protocol_noise | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_fails_on_protocol_noise_overflow | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_worker_returns_summary_and_top_traces | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_probe_returns_tick_results | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_serial_polling_probe_returns_empty_when_session_has_no_results | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_adapter_class_delegates_to_worker_runner | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | flush | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | close | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_open62541_subscription_runner.py

违规数: 68

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_parse_notify_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_notify_line_pre_flush_protocol_without_flush_timestamp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_notify_line_legacy_without_notify_timestamp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_summary_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_summary_line_covers_recovery_counters_and_reason | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_endpoint_diag_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_lines_reject_malformed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runner_adapter_delegates | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_trace_disabled_drops_traces | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_trace_enabled_keeps_top_n | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_raises_on_non_zero_exit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_raises_on_error_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_records_small_protocol_noise | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_fails_when_protocol_noise_exceeds_limit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_stop_process_terminates_then_kills_after_timeouts | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | flush | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | close | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_parse_notify_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_notify_line_pre_flush_protocol_without_flush_timestamp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_notify_line_legacy_without_notify_timestamp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_summary_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_summary_line_covers_recovery_counters_and_reason | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_endpoint_diag_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_parse_lines_reject_malformed | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_runner_adapter_delegates | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_trace_disabled_drops_traces | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_trace_enabled_keeps_top_n | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_raises_on_non_zero_exit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_raises_on_error_line | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_records_small_protocol_noise | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_run_worker_fails_when_protocol_noise_exceeds_limit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_stop_process_terminates_then_kills_after_timeouts | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | write | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | flush | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | close | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | terminate | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | kill | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_polling_metrics.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_polling_expected_value_and_ratio_metrics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_data_period_metrics_use_response_timestamp_diffs | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_low_ratio_does_not_change_pass_fail_by_default | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_polling_expected_value_and_ratio_metrics | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_data_period_metrics_use_response_timestamp_diffs | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_low_ratio_does_not_change_pass_fail_by_default | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_port_allocator.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_allocate_many_skips_occupied_port | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_allocate_many_reports_diagnostics_when_range_exhausted | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_allocate_many_skips_occupied_port | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_allocate_many_reports_diagnostics_when_range_exhausted | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_profile_service.py

违规数: 20

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_run_field_profile_from_files_dispatches_provider_and_service | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_profile_service_writes_reports_and_json | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_profile_service_adds_pyinstrument_warning_when_missing | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_profile_service_derives_intervals_and_writes_reports | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_profile_service_allows_explicit_intervals | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_profile_service_allows_lower_update_hz_than_sample_hz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_profile_service_warns_when_updates_disabled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_run_field_profile_from_files_dispatches_provider_and_service | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_profile_service_writes_reports_and_json | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_polling_profile_service_adds_pyinstrument_warning_when_missing | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_profile_service_derives_intervals_and_writes_reports | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_profile_service_allows_explicit_intervals | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_profile_service_allows_lower_update_hz_than_sample_hz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_profile_service_warns_when_updates_disabled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_protocol_directory_structure.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_old_opcua_directory_does_not_exist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol_dir | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_protocol_directory_exists | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_protocol_init_py_exists_and_non_empty | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol_dir | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_simulator_file_exists | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_common_modules_exist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_registry_has_factory_functions | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_old_opcua_directory_does_not_exist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol_dir | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_protocol_directory_exists | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_protocol_init_py_exists_and_non_empty | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | protocol_dir | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_simulator_file_exists | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_common_modules_exist | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_registry_has_factory_functions | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_protocol_production_readiness_gate.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | test_python_lightweight_runners_must_not_claim_production_write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_production_client_write_requires_supported_operations | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_python_lightweight_runners_must_not_claim_production_write | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_production_client_write_requires_supported_operations | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_protocol_service_capabilities.py

违规数: 84

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | test_all_service_capabilities_have_required_fields | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_service_capabilities_have_valid_implementation_levels | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_service_capabilities_have_valid_access_mode | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_service_capabilities_count | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_service_capabilities_goose_exists | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_service_capabilities_sv_exists | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_not_in_list_supported_protocols | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sv_not_in_list_supported_protocols | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_alias_resolves_through_normalize | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sv_alias_resolves_through_normalize | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_alias_no_capability | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sv_alias_no_capability | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_opcua_polling | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_opcua_subscribe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_modbus_tcp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_modbus_rtu | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec101_polling | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec101_subscribe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec104_polling | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec104_subscribe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec61850_mms | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec61850_report | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_mqtt | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_http_rest | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_opcua_current_is_real_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modbus_current_is_real_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec101_iec104_current_is_real_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_current_is_real_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_mqtt_http_current_is_lightweight | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_real_native_runners_compiled | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_core_industrial_protocols_target_real_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_mqtt_http_target_not_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_protocols_have_target_implementation_level | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_application_protocols_include_all_families | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_service_types_include_goose_and_sv | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_transport_types_include_ethernet_l2 | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_and_sv_use_ethernet_l2_transport | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_protocols_have_write_operation_fields | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modbus_tcp_write_operations_are_explicit | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_production_client_write_protocols_have_supported_operations | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_production_client_write_false_protocols_have_empty_supported_operations | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_protocol_capabilities_have_triple_fields | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_service_capabilities_have_required_fields | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_service_capabilities_have_valid_implementation_levels | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_service_capabilities_have_valid_access_mode | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_service_capabilities_count | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_service_capabilities_goose_exists | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_service_capabilities_sv_exists | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_not_in_list_supported_protocols | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sv_not_in_list_supported_protocols | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_alias_resolves_through_normalize | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sv_alias_resolves_through_normalize | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_alias_no_capability | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sv_alias_no_capability | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_opcua_polling | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_opcua_subscribe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_modbus_tcp | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_modbus_rtu | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec101_polling | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec101_subscribe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec104_polling | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec104_subscribe | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec61850_mms | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_iec61850_report | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_mqtt | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_resolve_triple_http_rest | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_opcua_current_is_real_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modbus_current_is_real_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec101_iec104_current_is_real_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_iec61850_current_is_real_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_mqtt_http_current_is_lightweight | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_real_native_runners_compiled | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_core_industrial_protocols_target_real_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_mqtt_http_target_not_native | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_protocols_have_target_implementation_level | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_application_protocols_include_all_families | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_service_types_include_goose_and_sv | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_transport_types_include_ethernet_l2 | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_and_sv_use_ethernet_l2_transport | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_protocols_have_write_operation_fields | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_modbus_tcp_write_operations_are_explicit | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_production_client_write_protocols_have_supported_operations | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_production_client_write_false_protocols_have_empty_supported_operations | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_all_protocol_capabilities_have_triple_fields | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_protocol_simulator_factory.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_non_opcua_protocol_simulators_can_be_built_and_lifecycle_started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_non_opcua_protocol_simulators_can_be_built_and_lifecycle_started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _build_subscription_runner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 34 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P2 | 无解释 type:ignore | line 168 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P2 | 无解释 type:ignore | line 194 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P1 | 英文 docstring | _build_subscription_runner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P2 | 无解释 type:ignore | line 34 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P2 | 无解释 type:ignore | line 168 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |
| P2 | 无解释 type:ignore | line 194 | 无解释的 type:ignore | 添加注释说明忽略原因 | PENDING |

### tools/source_lab/tests/access/test_server_simulator_facade_contract.py

违规数: 56

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | facade_cls | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_has_protocol_property | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_has_capabilities_property | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_start_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_stop_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_health_returns_simulator_health | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_load_points_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_read_returns_read_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_write_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_subscribe_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_report_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_update_values_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_all_not_implemented | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_all_not_implemented | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_opcua_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_opcua_protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_modbus_tcp_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_modbus_tcp_protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_modbus_rtu_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec104_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_mms_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_report_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_goose_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_sv_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_mqtt_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_http_rest_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec101_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_capabilities_subset_of_protocol_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | facade_cls | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_has_protocol_property | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_has_capabilities_property | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_start_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_stop_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_health_returns_simulator_health | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_load_points_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_read_returns_read_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_write_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_subscribe_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_report_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_update_values_returns_simulator_result | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_goose_all_not_implemented | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_sv_all_not_implemented | public AsyncFunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_opcua_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_opcua_protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_modbus_tcp_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_modbus_tcp_protocol | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_modbus_rtu_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec104_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_mms_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_report_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_goose_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec61850_sv_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_mqtt_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_http_rest_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_iec101_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_capabilities_subset_of_protocol_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_server_simulator_facade_real_protocol_smoke.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _modbus_read_registers | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_facade_real_subscribe_event | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sv_facade_real_subscribe_sample | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _modbus_read_registers | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_goose_facade_real_subscribe_event | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_sv_facade_real_subscribe_sample | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_server_simulator_factory.py

违规数: 36

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_create_opcua | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_modbus_tcp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_modbus_rtu | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec104 | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec61850_mms | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec61850_report | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec61850_goose | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec61850_sv | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec101 | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_mqtt | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_http_rest | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_unknown_protocol_raises | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_properties_after_create | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_opcua_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_modbus_tcp_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_unknown_protocol_raises | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_lists_all_registered_protocols | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_no_duplicates | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_opcua | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_modbus_tcp | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_modbus_rtu | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec104 | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec61850_mms | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec61850_report | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec61850_goose | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec61850_sv | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_iec101 | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_mqtt | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_create_http_rest | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_unknown_protocol_raises | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_facade_properties_after_create | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_opcua_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_modbus_tcp_capabilities | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_unknown_protocol_raises | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_lists_all_registered_protocols | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_no_duplicates | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py

违规数: 8

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_final_protocol_capability_matrix_no_overclaim | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_supported_capabilities_have_tests | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_not_implemented_boundaries | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | test_final_protocol_capability_matrix_no_overclaim | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_supported_capabilities_have_tests | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_not_implemented_boundaries | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_subscribe_capacity_entrypoint.py

违规数: 12

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_service_builds_matrix_plan_and_delegates | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_service_uses_config_source_update_hz_when_not_overridden | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_worker | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_service_builds_matrix_plan_and_delegates | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_capacity_service_uses_config_source_update_hz_when_not_overridden | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | build_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | started | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | run_worker | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_subscribe_capacity_reporter.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_print_subscribe_capacity_table_outputs_summary_only | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_progress_reporter_defaults_to_quiet_on_non_tty | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_progress_reporter_uses_inline_tty_update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_report_remains_profile_friendly | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_report_summary_uses_data_period_not_response_period | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_subscribe_capacity_wrapper_calls_formal_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fake_run_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_print_subscribe_capacity_table_outputs_summary_only | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_progress_reporter_defaults_to_quiet_on_non_tty | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_progress_reporter_uses_inline_tty_update | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_report_remains_profile_friendly | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_report_summary_uses_data_period_not_response_period | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_subscribe_capacity_wrapper_calls_formal_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fake_run_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_subscribe_scan.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _Provider | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _Runner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _config | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _metrics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_scan_uses_passing_attempt_as_primary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_sources | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _Provider | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _Runner | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _config | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _metrics | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_scan_uses_passing_attempt_as_primary | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | build_sources | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | started | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/access/test_subscribe_update_policy.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_subscribe_config_allows_update_hz_below_sample_hz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_config_allows_lower_update_hz_when_updates_disabled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_subscribe_config_allows_update_hz_below_sample_hz | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_config_allows_lower_update_hz_when_updates_disabled | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/access/test_subscription_metrics.py

违规数: 46

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_subscribe_data_period_metrics_use_notify_receive_diffs_per_server | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_data_period_metrics_prefer_notify_timestamp_over_received_ns | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_data_period_falls_back_to_received_ns_when_notify_timestamp_missing | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_low_value_delivery_ratio_does_not_fail_by_default | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_data_period_max_within_tolerance_passes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_data_period_max_over_tolerance_fails | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_data_period_tolerance_ratio_changes_reason_limit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_allowed_data_period_uses_source_update_hz_when_sample_hz_is_higher | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_source_period_remains_detail_only_diagnostic | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_source_period_stays_separate_from_notify_period | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_response_period_limit_only_warns_and_does_not_fail | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_keepalive_only_batches_do_not_contribute_to_data_period | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resubscribe_success_only_warns | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_unrecovered_endpoint_fails | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_insufficient_data_period_samples_only_warns | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_no_data_fails | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_created_items_is_hard_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_bad_missing_timestamp_and_noise_are_hard_failures | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_callback_to_flush_lag_uses_flush_timestamp_and_not_received_ns | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_callback_to_flush_lag_warns_when_flush_timestamp_missing | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_callback_to_flush_lag_warns_on_negative_samples | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dispatch_gap_diagnostics_flow_into_metrics_and_warnings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_subscribe_data_period_metrics_use_notify_receive_diffs_per_server | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_data_period_metrics_prefer_notify_timestamp_over_received_ns | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_subscribe_data_period_falls_back_to_received_ns_when_notify_timestamp_missing | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_low_value_delivery_ratio_does_not_fail_by_default | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_data_period_max_within_tolerance_passes | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_data_period_max_over_tolerance_fails | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_data_period_tolerance_ratio_changes_reason_limit | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_allowed_data_period_uses_source_update_hz_when_sample_hz_is_higher | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_source_period_remains_detail_only_diagnostic | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_source_period_stays_separate_from_notify_period | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_response_period_limit_only_warns_and_does_not_fail | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_keepalive_only_batches_do_not_contribute_to_data_period | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_resubscribe_success_only_warns | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_unrecovered_endpoint_fails | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_insufficient_data_period_samples_only_warns | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_no_data_fails | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_created_items_is_hard_failure | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_bad_missing_timestamp_and_noise_are_hard_failures | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_callback_to_flush_lag_uses_flush_timestamp_and_not_received_ns | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_callback_to_flush_lag_warns_when_flush_timestamp_missing | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_callback_to_flush_lag_warns_on_negative_samples | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_dispatch_gap_diagnostics_flow_into_metrics_and_warnings | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/conftest.py

违规数: 4

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | pytest_collection_modifyitems | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | pytest_collection_modifyitems | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/test_factory.py

违规数: 10

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _build_source | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_build_simulator_uses_open62541_backend_by_default | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_simulator_returns_open62541_for_opcua_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_build_simulator_rejects_unknown_protocol | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 英文 docstring | _build_source | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_build_simulator_uses_open62541_backend_by_default | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_build_simulator_returns_open62541_for_opcua_sources | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 英文 docstring | test_build_simulator_rejects_unknown_protocol | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/test_fleet_partial_lifecycle.py

违规数: 6

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 缺少 public docstring | test_fleet_stop_one_source_keeps_other_sources_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_fleet_restart_one_source_keeps_other_sources_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_fleet_status_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_fleet_stop_one_source_keeps_other_sources_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_fleet_restart_one_source_keeps_other_sources_running | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_fleet_status_source | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/test_fleet_startup_controls.py

违规数: 28

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_create_reads_startup_controls_from_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_start_processes_applies_concurrency_and_stagger | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | set | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | is_set | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | get_nowait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | close | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | join_thread | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | is_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | Queue | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | Event | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | Process | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_create_reads_startup_controls_from_env | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_start_processes_applies_concurrency_and_stagger | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | set | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | is_set | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | wait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | get_nowait | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | close | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | join_thread | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | start | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | is_alive | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | Queue | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | Event | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | Process | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/test_open62541_source_simulation_single_server_smoke.py

违规数: 14

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_open62541_source_simulation_single_server_smoke | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_open62541_source_simulator_writes_smoke | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_open62541_source_simulator_rejects_invalid_write_string | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_open62541_source_simulator_prefers_runtime_update_params | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_open62541_source_simulator_internal_updates | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_open62541_fleet_internal_updates | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P0 | 英文 module docstring | module | module docstring 为英文业务描述 | 替换为中文 module docstring，说明架构位置、主要职责、边界 | PENDING |
| P1 | 缺少 public docstring | test_open62541_source_simulation_single_server_smoke | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_open62541_source_simulator_writes_smoke | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_open62541_source_simulator_rejects_invalid_write_string | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_open62541_source_simulator_prefers_runtime_update_params | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_open62541_source_simulator_internal_updates | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |
| P1 | 缺少 public docstring | test_open62541_fleet_internal_updates | public FunctionDef 缺少 docstring | 补充中文 docstring | PENDING |

### tools/source_lab/tests/test_source_simulation_multi_server_polling_capacity.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _env_text | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fixture_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _output_dir | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _command_args | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _print_completed_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_simulation_multi_server_polling_capacity | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _env_text | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fixture_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _output_dir | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _command_args | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _print_completed_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_simulation_multi_server_polling_capacity | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/test_source_simulation_multi_server_polling_profile.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _env_text | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fixture_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _output_dir | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _command_args | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _print_completed_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_simulation_multi_server_polling_profile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _env_text | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fixture_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _output_dir | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _command_args | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _print_completed_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_simulation_multi_server_polling_profile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/test_source_simulation_multi_server_subscribe_capacity.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _env_text | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fixture_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _output_dir | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _command_args | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _print_completed_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_simulation_multi_server_subscribe_capacity | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _env_text | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fixture_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _output_dir | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _command_args | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _print_completed_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_simulation_multi_server_subscribe_capacity | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

### tools/source_lab/tests/test_source_simulation_multi_server_subscribe_profile.py

违规数: 16

| 优先级 | 违规类型 | 对象 | 问题 | 修复建议 | 状态 |
|--------|----------|------|------|----------|------|
| P1 | 英文 docstring | _env_text | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fixture_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _output_dir | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _command_args | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _print_completed_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_simulation_multi_server_subscribe_profile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _env_text | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _fixture_path | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _output_dir | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _build_env | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _command_args | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _run_cli | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | _print_completed_process | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |
| P1 | 英文 docstring | test_source_simulation_multi_server_subscribe_profile | docstring 为英文业务描述 | 替换为中文 docstring | PENDING |

