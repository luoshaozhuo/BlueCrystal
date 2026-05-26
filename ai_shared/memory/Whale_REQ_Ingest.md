# Whale_REQ_Ingest

## 一、文件定位

本文件描述 Whale `src/whale/ingest` 模块承担的接入编排、状态缓存、消息发布、写入控制、异常恢复和验收需求。

本文件不描述 source_lab simulator 内部实现，不描述 shared_source production client 内部实现。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-001 | 编排 source -> cache、cache -> message、write/control |
| P-FR-002 | 作为 Kappa 实时入口，将数据发布到 message pipeline |
| P-NFR-001 | 接受 profile/capacity 和 E2E 验收 |
| P-SCR-001 | 落实写入控制、安全分区和审计边界 |

## 三、链路能力矩阵

| 链路 | use case | port | adapter | E2E | 状态 |
|---|---|---|---|---|---|
| source -> cache | SourceAcquisitionUseCase | SourceAcquisitionPort / StateCachePort | source adapter / cache adapter | 已有分段集成 | 测试通过 |
| source write/control | SourceCommandUseCase | SourceWritePort | write adapter | 已有协议写入集成 | 部分实现 |
| cache -> message | StateSnapshotPublishUseCase | MessagePublisherPort | Kafka 或等价 publisher | FakeKafka 集成通过 | 测试通过 |
| source -> cache -> message | 组合链路 | 多 port | 多 adapter | 缺单条完整 E2E | 部分实现 |

## 三、功能需求

### I-FR-001 source -> cache 采集链路

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块应从生产 source client 读取数据，转换为统一状态批次，并写入状态缓存。
  - 采集链路应支持 polling、subscription、report/event 等模式。
- 验收要点：
  - 支持 SourceAcquisitionUseCase。
  - 支持 polling、subscription、report/event。
  - 支持启动 subscription 前 baseline read。
  - 支持 Redis 或等价 cache 后端。
  - 支持 source unavailable、timeout、partial failure 分类。

### I-FR-002 cache -> message pipeline 发布链路

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块应从 cache 读取状态快照或状态变更，并发布到 message pipeline。
  - 默认目标为 Kafka，同时必须通过 MessagePublisherPort 保持可替换。
- 验收要点：
  - 提供独立 StateSnapshotPublishUseCase。
  - 不与 SourceAcquisitionUseCase 耦合。
  - 支持 message envelope、schema_version、trace_id、message_id、item_count。
  - 发布失败不得破坏 source -> cache 主链路。

### I-FR-003 设备命令与写入控制

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块应支持面向 source 的写入、设点、控制和命令下发。
  - 写入/控制必须与采集链路隔离。
- 验收要点：
  - 提供 SourceWritePort。
  - 提供 SourceCommandUseCase。
  - 支持 dry_run。
  - 真实写入默认关闭。
  - 支持 actor、trace_id、command_id。
  - 支持写入后 readback 或状态确认。

### I-FR-004 多协议 ingest adapter

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块应通过 adapter 接入 shared_source production client，实现多协议采集、订阅、报告和写入控制。
- 验收要点：
  - 每个声明支持的协议必须具备 acquisition adapter。
  - 每个声明支持写入的协议必须具备 write adapter。
  - adapter 不得 import source_lab。
  - 不支持能力必须返回 NOT_IMPLEMENTED 或等价错误。

### I-FR-005 统一配置加载

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块应从统一配置源加载 source、connection、point、signal profile、protocol params。
- 验收要点：
  - 支持 source_id、protocol、endpoint、protocol-specific params。
  - 支持 node_key、address、IOA、NodeId、LD/LN/DO/DA。
  - 支持 value_type、writable、subscribable、reportable。
  - schema 与字段必须以 ORM 和配置模型为准。

### I-FR-006 端到端 ingest 管道

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块必须支持从 source simulator 到 cache，再到 message pipeline 的完整链路验证。
- 验收要点：
  - E2E 使用 source_lab server simulator。
  - E2E 使用 production source client。
  - E2E 写入真实或测试 cache。
  - E2E 发布到真实 Kafka、test container Kafka 或可验证 publisher。
  - E2E 验证消息 payload、质量码、时间戳和 trace_id。

## 四、非功能需求

### I-NFR-001 性能与容量

- 类型：非功能
- 优先级：高
- 需求描述：
  - ingest 模块应满足多设备、高频、长期采集要求。
- 验收要点：
  - 支持 profile/capacity 验证。
  - 支持 p95/p99 延迟、jitter、missed tick、period_samples、values/sec。
  - 新增协议不得绕过 profile/capacity。

### I-NFR-002 稳定性与故障恢复

- 类型：非功能
- 优先级：高
- 需求描述：
  - ingest 模块应处理 source 断连、协议超时、cache 异常、message queue 异常、runner 崩溃和进程退出。
- 验收要点：
  - polling timeout 可恢复。
  - subscription/report 断线不静默停止。
  - reconnect 后 baseline read。
  - Kafka 发布失败不阻塞 source -> cache。
  - 支持 backoff、最大重试次数和 graceful shutdown。

### I-NFR-003 可观测性、审计与安全

- 类型：非功能
- 优先级：高
- 需求描述：
  - ingest 模块应对采集、缓存、发布、写入和调度链路输出结构化日志、指标、审计和诊断上下文。
- 验收要点：
  - 日志包含 source_id、protocol、batch_id、trace_id、command_id、error_code、duration_ms。
  - 指标包含 read/write/cache/kafka/reconnect 相关计数和耗时。
  - 写命令记录 actor、command_id、trace_id、result、failure_reason、timestamp。

## 五、架构约束

### I-AR-001 use case / role / port / adapter 边界

- 类型：架构约束
- 优先级：高
- 需求描述：
  - ingest 模块必须保持 use case、role、port、adapter、composition 的职责边界。
- 验收要点：
  - SourceAcquisitionUseCase 只处理采集。
  - SourceCommandUseCase 只处理写入/控制。
  - StateSnapshotPublishUseCase 只处理 cache -> message。
  - composition 负责装配。

### I-AR-002 source_lab 隔离

- 类型：架构约束
- 优先级：高
- 需求描述：
  - ingest 生产路径不得直接依赖 source_lab。
- 验收要点：
  - ingest 不 import tools.source_lab。
  - source_lab runner 不作为 production client。

## 六、安全合规需求

### I-SCR-001 电力监控系统安全分区

- 类型：安全合规
- 优先级：高
- 需求描述：
  - ingest 部署、source 接入、cache、message queue 和控制写入必须服从电力监控系统安全分区和边界防护要求。
- 验收要点：
  - 明确 ingest、source、cache、MQ 所在区。
  - 明确跨区流向。
  - 控制命令链路需单独安全评估。
  - simulator 不进入生产控制链路。

## 七、测试与验收需求

### I-TEST-001 分层测试与协议准入测试

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - ingest 模块必须具备 unit、integration、E2E、performance、fault injection、security smoke 测试。
- 验收要点：
  - use case 有 unit test。
  - adapter 有 unit/integration test。
  - source->cache->message 有 E2E。
  - write/control 有 dry-run 和真实写入测试。
  - skipped 不得作为完成证据。

## 八、禁止事项

- 不得 import tools.source_lab。
- SourceAcquisitionUseCase 不得处理 write/control。
- SourceCommandUseCase 不得处理 acquisition。
- Kafka 发布不得塞入 SourceAcquisitionUseCase。
- 真实写入不得默认开启。

## 九、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I-FR-001 | P-FR-001/P-FR-002 | source -> cache 采集链路 | FR | 高 | ingest | L3 | 运行闭环通过 | `SourceAcquisitionUseCase`; `PollingAcquisitionRole`; `SubscriptionAcquisitionRole`; `RedisSourceStateCache`; `tests/integration/test_ingest_source_cache_message_e2e.py` | `pytest tests/unit/test_source_acquisition_use_case.py -q` -> 12 passed; `pytest tests/unit/test_subscription_acquisition_role.py -q tests/unit/test_polling_acquisition_role.py -q` -> 10 passed; `pytest tests/integration/test_ingest_source_cache_message_e2e.py -q` -> 2 passed; `pytest tests/integration -q` -> 37 passed, 1 skipped | Report/runtime subscription 在长连接断线后的真实协议级恢复仍依赖 adapter/backend 能力 | 保持 role 级重连门禁，后续补更多协议级运行态恢复归档 | 2026-05-26 |
| I-FR-002 | P-FR-002 | cache -> message pipeline 发布链路 | FR | 高 | ingest | L3 | 运行闭环通过 | `StateSnapshotPublishUseCase`; `MessagePublisherPort`; `KafkaMessagePublisher`; `tests/integration/test_ingest_source_cache_message_e2e.py`; `tests/integration/test_ingest_source_cache_message_kafka_e2e.py` | `pytest tests/unit/test_state_snapshot_publish_use_case.py -q` -> 17 passed; `pytest tests/integration/test_ingest_cache_to_kafka_pipeline.py -q` -> 5 passed; `pytest tests/integration/test_ingest_source_cache_message_e2e.py -q` -> 2 passed; `pytest tests/integration/test_ingest_source_cache_message_kafka_e2e.py -q` -> 1 passed | 真实 Kafka E2E 已归档；发布 sink 仍是 Kafka adapter 级验证，非生产平台部署完成 | 后续补真实部署环境 topic/ACL/retention smoke | 2026-05-26 |
| I-FR-003 | P-FR-001/P-SCR-001 | 设备命令与写入控制 | FR | 高 | ingest | L2 | 测试通过 | `SourceCommandUseCase` 已支持 `command_id/trace_id`; `SourceCommandAuditPort`; `tests/unit/test_source_command_audit.py`; 协议 write adapters 与写入集成测试 | `pytest tests/unit/test_source_command_use_case.py tests/unit/test_source_command_audit.py -q` -> 12 passed; `pytest tests/integration/test_ingest_opcua_source_write.py -q` -> 3 passed | readback/确认仅覆盖已实现协议；审计 sink 目前是可替换端口+测试内存实现，生产 sink 未落地 | 第3轮补生产审计 sink 接入策略与更多协议写入验收 | 2026-05-26 |
| I-FR-004 | P-FR-001 | 多协议 ingest adapter | FR | 高 | ingest | L2 | 部分实现 | `src/whale/ingest/adapters/source/`; static acquisition/write registries; `tests/unit/test_ingest_source_adapter_capability_matrix.py`; `tests/unit/test_ingest_no_source_lab_imports.py` | `pytest tests/unit/test_ingest_source_adapter_capability_matrix.py -q` -> 2 passed; `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed; `pytest tests/integration -q` -> 37 passed, 1 skipped | 已支持 OPC UA/Modbus TCP/IEC104/IEC61850 MMS+Report；IEC101/Modbus RTU/MQTT/HTTP REST/GOOSE/SV 仍未纳入 ingest production registry | 保持 unsupported 明确失败语义，GOOSE/SV production boundary 另起 ADR | 2026-05-26 |
| I-FR-005 | P-DGR-001 | 统一配置加载 | FR | 高 | ingest | L1 | 部分实现 | `SourceRuntimeConfigRepository`; `OpcUaSourceAcquisitionDefinitionRepository`; config DTO/ORM | `pytest tests/unit/test_source_runtime_config_repository.py -q` -> 2 passed | 统一 source/connection/point/profile/protocol params 到 use case 的端到端装配证据不足 | 第2轮补配置加载到 composition/use case 的集成测试 | 2026-05-25 |
| I-FR-006 | P-FR-002 | 端到端 ingest 管道 | FR | 高 | ingest | L3 | 运行闭环通过 | `tests/integration/test_ingest_source_cache_message_e2e.py`; `tests/integration/test_ingest_source_cache_message_kafka_e2e.py` | `pytest tests/integration/test_ingest_source_cache_message_e2e.py -q` -> 2 passed; `pytest tests/integration/test_ingest_source_cache_message_kafka_e2e.py -q` -> 1 passed; `pytest tests/integration -q` -> 41 passed | 当前闭环基于 testcontainer Kafka + real Redis + source_lab simulator；仍不等同生产部署 readiness | 后续补部署环境 smoke 与 topic/consumer policy 验证 | 2026-05-26 |
| I-NFR-001 | P-NFR-001 | 性能与容量 | NFR | 高 | ingest | L2 | 测试通过 | `tests/integration/test_ingest_lightweight_load_gate.py`; `IngestMetricsPort`; source_lab capacity/profile 仍不作为 ingest load 替代 | `pytest tests/integration/test_ingest_lightweight_load_gate.py -q` -> 1 passed | 已完成 lightweight load gate，但未执行重型 performance/stress；不等同完整容量画像 | 后续在 CI 继续执行 `pytest tests/performance -q` 并补压力归档 | 2026-05-26 |
| I-NFR-002 | P-NFR-002 | 稳定性与故障恢复 | NFR | 高 | ingest | L2 | 测试通过 | `SubscriptionAcquisitionRole` 支持 `subscription_max_retry/subscription_backoff_ms` 重试启动；`tests/unit/test_subscription_reconnect_runtime.py`; `tests/integration/test_ingest_source_cache_message_e2e.py`（publish failure 不污染 cache） | `pytest tests/unit/test_subscription_reconnect_baseline.py -q` -> 1 passed; `pytest tests/unit/test_subscription_reconnect_runtime.py -q` -> 2 passed; `pytest tests/integration/test_ingest_source_cache_message_e2e.py -q` -> 2 passed | 运行态长期 reconnect + graceful shutdown 仍以 role/runtime 级证据为主，真实协议长时断线恢复覆盖仍有限 | 保持重试参数边界，后续补长时断线与协议级 soak 归档 | 2026-05-26 |
| I-NFR-003 | P-NFR-004/P-NFR-005 | 可观测性、审计与安全 | NFR | 高 | ingest | L2 | 测试通过 | `SourceCommandAuditPort`; `SourceCommandAuditEvent`; `IngestMetricsPort` / `IngestMetricEvent`; `JsonlIngestMetricsSink`; `JsonlSourceCommandAuditSink`; `tests/unit/test_ingest_metrics_events.py`; `tests/integration/test_ingest_observability_sink_smoke.py` | `pytest tests/unit/test_source_command_audit.py -q` -> 2 passed; `pytest tests/unit/test_ingest_metrics_events.py -q` -> 1 passed; `pytest tests/unit/test_ingest_observability_sink.py -q` -> 2 passed; `pytest tests/integration/test_ingest_observability_sink_smoke.py -q` -> 1 passed | 已验证可替换 file/JSONL sink；当前未发现 production observability/audit backend 配置或 adapter，仍属 deployment pending | 后续按部署环境接入真实 sink 并补 production backend smoke | 2026-05-26 |
| I-AR-001 | P-AR-001 | use case / role / port / adapter 边界 | AR | 高 | ingest | L2 | 测试通过 | `SourceAcquisitionUseCase`; `SourceCommandUseCase`; `StateSnapshotPublishUseCase`; `composition.py` | `pytest tests/unit/test_source_acquisition_use_case.py -q` -> 12 passed; `pytest tests/unit/test_state_snapshot_publish_use_case.py -q` -> 17 passed; `pytest tests/integration -q` -> 35 passed | 无主要边界破坏；composition 默认 acquisition 当前偏 OPC UA raw port，registry 多协议仍需完善 | 第3轮复核边界不回退 | 2026-05-25 |
| I-AR-002 | P-AR-002 | source_lab 隔离 | AR | 高 | ingest | L2 | 测试通过 | `src/whale/ingest/`; `tests/unit/test_ingest_no_source_lab_imports.py`; source_lab 仅测试侧导入 | `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed; `pytest tests/integration -q` -> 37 passed | 测试侧使用 source_lab simulator 合法；生产路径需持续禁止 import | 第3轮复核生产 import 边界 | 2026-05-26 |
| I-SCR-001 | P-SCR-001 | 电力监控系统安全分区 | SCR | 高 | ingest | L2 | 测试通过 | `ai_shared/reports/ingest_security_partition_boundary.md`; `config/ingest/security_partition.example.yaml`; `tests/unit/test_ingest_security_partition_config.py`; `tests/integration/test_ingest_security_partition_smoke.py` | `pytest tests/unit/test_ingest_security_partition_config.py -q` -> 1 passed; `pytest tests/integration/test_ingest_security_partition_smoke.py -q` -> 1 passed; `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed | 当前仅发现 example config，无 production security profile；样例配置 smoke 不等同生产部署态完全通过 | 后续补 production profile/部署流水线的安全分区验证 | 2026-05-26 |
| I-TEST-001 | P-NFR-001/P-NFR-004 | 分层测试与协议准入测试 | TEST | 高 | ingest | L2 | 测试通过 | `tests/unit/`; `tests/integration/`; command 审计、metrics、adapter matrix、source->cache->message、Kafka true E2E、load gate、security smoke | `pytest tests/unit -q` -> 318 passed; `pytest tests/integration -q` -> 41 passed | 性能/故障注入/security smoke 仍未形成完整部署级矩阵 | 保持 L2，后续补 performance/fault/security 专项门禁 | 2026-05-26 |
