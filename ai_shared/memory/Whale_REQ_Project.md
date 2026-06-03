# Whale_REQ_Project

## 一、文件定位

本文件描述 Whale 项目的项目级功能需求、非功能需求、架构约束、数据治理需求和安全合规需求。

本文件不展开模块内部实现细节。模块级需求以对应模块需求文件为准。

项目背景、业务范围和长期边界以《业务目标与价值愿景.md》为准；总体逻辑边界以《总体逻辑设计.md》为准。

## 二、功能需求

### P-FR-001 多源异构数据统一接入

- 类型：功能
- 优先级：高
- 需求描述：
  - 平台应支持并网风光储电厂生产运行数据、第三方系统数据、离线数据、仿真模型与仿真结果数据的统一接入。
  - 平台应支持多场站、多设备、多协议、多频率数据源。
- 验收要点：
  - 声明支持的生产协议必须具备 production client、ingest adapter、server simulator、probe、profile、capacity 和 E2E 验证。
  - 不支持能力必须返回 NOT_IMPLEMENTED 或等价状态。

### P-FR-002 Kappa + Lambda 混合数据链路

- 类型：功能
- 优先级：高
- 需求描述：
  - 平台应采用 Kappa 与 Lambda 混合数据架构。
  - 实时链路通过 message pipeline 和 speed layer 支撑近实时状态、原始层写入和业务侧缓存更新。
  - 批处理链路从 raw storage 读取数据，完成清洗、标准化、质量处理、聚合和数仓分层。
- 验收要点：
  - ingest 不承担数仓处理职责。
  - speed layer 消费 message pipeline 并写入 raw storage。
  - batch layer 从 raw storage 读取并写入 standard layer。
  - aggregation 从 standard、speed 或 warehouse 层构建业务聚合。

### P-FR-003 高频时序数据持续接入与处理

- 类型：功能
- 优先级：高
- 需求描述：
  - 平台应支持风机、储能、POC、测风塔、激光雷达等高频时序数据持续接入、缓存、处理、存储和查询。
- 验收要点：
  - 提供 profile 与 capacity 验证。
  - 提供吞吐、延迟、抖动、丢失率、周期样本等指标。

### P-FR-004 数据治理与统一信息模型

- 类型：功能
- 优先级：高
- 需求描述：
  - 平台应建立场站、设备、测点、事件、告警、模型对象、文件对象、结果对象的统一信息模型。
- 验收要点：
  - 核心对象具备统一标识。
  - 测点、设备、协议地址和业务语义可追溯。
  - 数据值携带质量码和关键时间戳。

### P-FR-005 数据服务与共享

- 类型：功能
- 优先级：高
- 需求描述：
  - 平台应对内支撑采集、治理、分析、监测、建模等模块。
  - 平台应对外提供规范化、可管控、可配置、可演进的数据服务接口。
- 验收要点：
  - 支持实时数据、历史数据、主题数据、模型数据和文件数据服务。
  - 支持权限控制、审计、限流和接口版本治理。

## 三、非功能需求

### P-NFR-001 性能与容量扩展

- 类型：非功能
- 优先级：高
- 需求描述：
  - 平台应支持单台设备约 10Hz、约 600 字段规模的数据接入目标，并支持随场站规模横向扩展。
- 验收要点：
  - profile 与 capacity 结果可归档。
  - 支持最大稳定容量评估。
  - 支持 p95/p99 延迟和周期抖动统计。

### P-NFR-002 稳定性与长期运行

- 类型：非功能
- 优先级：高
- 需求描述：
  - 平台应支持 7x24 运行，并对断连、超时、缓存异常、消息异常、runner 崩溃、协议错误具备恢复能力。
- 验收要点：
  - 支持错误分类、重试、退避、降级和恢复。
  - 关键链路支持 graceful shutdown。

### P-NFR-003 可替换与可扩展

- 类型：非功能
- 优先级：高
- 需求描述：
  - 平台的 source client、cache、message queue、数据库、对象存储、接口实现应可替换。
- 验收要点：
  - 通过 port-adapter 或等价机制隔离基础设施。
  - 新增后端不得破坏 use case。

### P-NFR-004 可观测性与运维诊断

- 类型：非功能
- 优先级：高
- 需求描述：
  - 平台应提供日志、指标、追踪、审计、诊断和运行报告。
- 验收要点：
  - 关键链路输出结构化日志。
  - 支持 trace_id、batch_id、command_id、source_id、protocol。
  - profile/capacity 输出可归档报告。

### P-NFR-005 安全合规

- 类型：非功能
- 优先级：高
- 需求描述：
  - 平台必须服从电力监控系统安全防护、网络安全、数据安全、等级保护、关键信息基础设施保护及现场安全分区分域要求。
- 验收要点：
  - 明确部署区域、数据流向、通信方向和边界防护。
  - 写入控制默认关闭，并具备授权、审计、trace 和风险控制。

## 四、架构约束

### P-AR-001 Clean Architecture / Port-Adapter

- 类型：架构约束
- 优先级：高
- 需求描述：
  - 平台应保持 use case、role、port、adapter、runtime、infrastructure 的职责边界。
- 验收要点：
  - use case 不直接依赖具体基础设施。
  - adapter 负责外部系统连接。
  - composition 负责依赖装配。

### P-AR-002 生产路径与工具路径分离

- 类型：架构约束
- 优先级：高
- 需求描述：
  - source_lab 是测试与验证工具层，shared_source 是生产 source client 层，ingest 是业务编排层。
- 验收要点：
  - ingest 不直接依赖 source_lab。
  - source_lab runner 存在不能等同于 production client 完成。

### P-AR-003 全系统公共基础库边界

- 类型：架构约束
- 优先级：高
- 需求描述：
  - 平台应设置 `platform_shared` 作为全系统公共基础库。
  - Whale、Turtle、Octopus、Dolphin、Orca、Manta 可以依赖 `platform_shared`。
  - `platform_shared` 不得依赖任何上层组件。
  - `whale.shared` 只服务 Whale 数据底座内部，不得作为全系统公共库。
- 验收要点：
  - `src/whale/shared/crosscutting` 删除。
  - `debug/observability/resilience` 迁入 `src/platform_shared/crosscutting`。
  - 全仓无 `whale.shared.crosscutting` import。
  - import boundary gate 覆盖依赖方向。

## 五、数据治理需求

### P-DGR-001 Schema 与配置治理

- 类型：数据治理
- 优先级：高
- 需求描述：
  - 数据库 schema、字段名、表关系必须以当前 ORM、migration、schema 文件为准。
  - 配置项必须以当前配置模型、环境变量解析、示例配置和测试为准。
- 验收要点：
  - 禁止凭记忆推断字段。
  - 禁止创建无来源字段。
  - 禁止用测试结构替代生产契约。

## 六、安全合规需求

### P-SCR-001 电力监控系统安全边界

- 类型：安全合规
- 优先级：高
- 需求描述：
  - 平台应明确生产控制大区、管理信息区、边界区域的功能部署、数据范围、通信方向、访问控制和最小开放面。
- 验收要点：
  - 不形成未经论证的跨安全分区自由数据交换通道。
  - 控制反向下发必须具备授权、审计和风险控制。
  - simulator 不进入生产控制链路。

## 七、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P-FR-001 | - | 多源异构数据统一接入 | FR | 高 | Project | L3/L4 | 已实现 | IEC104/OPC UA/Modbus TCP/IEC61850 MMS production client + ingest adapter + source_lab simulator/capacity/profile/E2E 门禁通过；IEC101/Modbus RTU/MQTT/HTTP REST acquisition-ready（L3 simulator，env-pending）；3 adapters 全 contract-passed | 48 source_lab gate tests, capacity/profile matrix, 各协议 E2E chain tests, 全协议 8 polling+5 streaming matrix | Beckhoff ADS real device=environment-pending，串口协议真实硬件未覆盖 | Beckhoff ADS real device + 串口真实硬件 environment 验证 | 2026-06-03 |
| P-FR-002 | - | Kappa + Lambda 混合数据链路 | FR | 高 | Project | L4/L5 (L5: Kafka/PostgreSQL/Redis/S3-MinIO/TDengine verified; Pulsar/Flink/HDFS env-pending) | 实时链路 (Kappa) Kafka/PostgreSQL/Redis/S3-MinIO/TDengine L5 verified；批处理链路 (Lambda) env-pending；warehouse/mart=batch layer=stub/未实现 | Round 3: Kafka+PG L5 verified (real pub/consume, consumer group isolation)；Round 4: SP-FR-004 L1+L4 integrated；Round 5: S3/MinIO L5 verified (3 E2E + 2 integration: head_bucket/write gzip+readback/manifest)，TDengine L5 verified (3 E2E + 2 integration: REST API write+readback 10 fields/raw_index/health)，Redis L5 verified (4 E2E + 1 integration: SET/GET/TTL/stale/out-of-order/health)；120 tests passed, 0 failures, 4 skipped (Pulsar/HDFS/Flink env-pending) | test_whale_l5_kafka_pipeline_e2e (L5: 4 tests), test_whale_l5_storage_e2e (L5: 10 tests all passed: S3 3/TDengine 3/Redis 4 E2E), test_whale_field_minimal_smoke (L4: 7 tests), test_whale_writer_failure_recovery (L4), test_whale_writer_switchover (L4), test_message_pipeline_kafka_e2e (4+2 contract), run_whale_l5_external_dependency_probe.sh (multi-level 16 probes), test_l5_external_dependency_verification, test_speed_layer_pipeline_runner (44 tests), test_speed_layer_light_processor (26 tests), TestSpeedLayerWiringWithLightProcessor (6 tests L4) | warehouse/mart 仅 stub/port；batch layer 未实现；Pulsar/Flink/HDFS=environment-pending | Pulsar/Flink/HDFS 真实环境 L5 验证 + batch layer 实现 + warehouse/mart 实现 | 2026-06-03 (Round 6: 现场部署前可交付基线已收口 — L5 verified: Kafka/PG/Redis; S3/TDengine L5 code ready需Docker容器; 未实现: batch_layer/warehouse/mart; env-pending: Pulsar/Flink/HDFS) |
| P-FR-003 | - | 高频时序数据持续接入与处理 | FR | 高 | Project | L3/L5 (L5: Kafka/PG/S3/TDengine/Redis verified; Pulsar/Flink/HDFS env-pending) | Kafka/PostgreSQL/S3-MinIO/TDengine/Redis L5 verified，性能指标 env-pending | Round 3: Kafka pipeline L5 E2E verified (4 tests)；source_lab capacity/profile gate 全协议 matrix 通过；Round 5: S3/MinIO L5 verified (3 E2E + 2 integration)，TDengine L5 verified (3 E2E + 2 integration)，Redis L5 verified (4 E2E + 1 integration)；120 tests passed, 0 failures | source_lab capacity/profile gate tests, test_ingest_cache_to_kafka_pipeline, performance baseline 9 tests, run_whale_l5_external_dependency_probe.sh (multi-level), test_whale_l5_kafka_pipeline_e2e (4 tests), test_whale_l5_storage_e2e (10 tests L5 all passed) | 吞吐/延迟/抖动/丢失率指标未采集 | 真实环境下性能指标采集 | 2026-06-03 (Round 6) |
| P-FR-004 | - | 数据治理与统一信息模型 | FR | 高 | Project | L3 | 已实现 | ORM 模型（scada_ingest/scada_protocol_param 等）、Envelope schema_version、统一标识与质量码透传；16 组协议参数模板定义 | test_scada_protocol_params, test_scada_sample_data_protocol_coverage, test_message_pipeline_envelope | 完整 schema evolution 和血缘追踪未实现 | schema registry + 血缘追踪 | 2026-06-03 |
| P-FR-005 | - | 数据服务与共享 | FR | 高 | Project | L3 | 部分实现 | ingest Web API（CRUD routes + health + audit）、serving cache port；Kafka/Pulsar 消息发布已验证（contract）；warehouse/mart 仅 stub | ingest API integration tests, test_ingest_cache_to_kafka_pipeline | 对外数据服务接口、warehouse/mart 查询接口未实现 | 实现对外规范化数据服务接口 | 2026-06-03 |
| P-NFR-001 | - | 性能与容量扩展 | NFR | 高 | Project | L3 | 部分实现 | source_lab capacity/profile gate 全协议矩阵通过（polling+streaming），ingest 性能基线 9 tests passed | source_lab capacity/profile gate tests, test_ingest_prodlike_performance_profile | p95/p99 延迟和周期抖动未在真实 broker/TDengine 环境采集 | 真实环境下性能指标采集 | 2026-06-03 (Round 6: capacity/profile gate通过但真实环境性能指标未采集) |
| P-NFR-002 | - | 稳定性与长期运行 | NFR | 高 | Project | L3/L4 | 已实现 | 错误分类、重试、退避、熔断、DLQ 恢复、missed tick、worker crash/failover、graceful shutdown、writer failure recovery 8/8、writer switchover 8/8、Kafka/PostgreSQL/Redis fault injection 集成测试通过 | test_ingest_prodlike_kafka_fault_injection, test_ingest_prodlike_postgres_fault_injection, test_ingest_prodlike_redis_fault_injection, test_ingest_prodlike_worker_failover, test_whale_writer_failure_recovery, test_whale_writer_switchover, test_speed_layer_dlq_replay | 7x24 长时间运行未验证；真实 broker/TDengine 环境未覆盖 | 真实环境长时间运行验证 | 2026-06-03 (Round 6) |
| P-NFR-003 | - | 可替换与可扩展 | NFR | 高 | Project | L3 | 已验证 | port-adapter 架构：message_pipeline 3 adapters (Kafka/Pulsar/InMemory)，speed_layer 2 runners (Local/Flink)，storage 6 layers multiple backends；import boundary 30 passed 验证模块隔离 | test_turtle_octopus_import_boundary, test_ingest_no_source_lab_imports, test_message_pipeline_ports, port-adapter contract tests | 新增 backend 的 use case 不变性未做形式化验证 | 新增 backend 时回归 use case contract | 2026-06-03 |
| P-NFR-004 | - | 可观测性与运维诊断 | NFR | 高 | Project | L3/L5 | 已实现 | JSONL metrics/audit sink、structured logging、trace_id/batch_id/command_id/source_id/protocol、DB+JSONL dual audit、profile/capacity 报告可归档；L5 Round 3: L5 外部依赖环境探测脚本 (16 probes, 多级输出: tcp_ok/driver_ok/auth_ok/service_health_ok/e2e_ok, JSON+human 双格式，8 services 全覆盖, Redis 端口修正为 16379) | test_ingest_observability_sink, test_ingest_prodlike_audit_metrics_resilience, test_ingest_audit_db_jsonl_consistency, source_lab capacity/profile report tests, run_whale_l5_external_dependency_probe.sh (16 probes, multi-level + e2e_ok) | 分布式 tracing 集成未实现 | OpenTelemetry 集成 | 2026-06-03 (Round 6: 新增 run_whale_field_ready_smoke.sh 一键预检脚本，8-step 覆盖 Kafka/PG/Redis/S3/TDengine + message pipeline + raw/index/standard + serving cache) |
| P-NFR-005 | - | 安全合规 | NFR | 高 | Project | L3 | 已实现 | 安全分区配置、写入控制默认关闭、写入授权装饰器 (AuthorizedSourceWritePort)、命令审计、external access policy、file access policy、凭据不硬编码、日志脱敏 | test_ingest_security_partition_config, test_source_write_port_registry, test_source_command_authorization_guard, test_source_command_audit, test_ingest_audit_redaction, test_ingest_external_access_policy_contract | 真实电力监控系统安全分区部署未执行 | 真实安全分区部署与审计 | 2026-06-03 |
| P-AR-001 | - | Clean Architecture / Port-Adapter | AR | 高 | Project | L3 | 已验证 | use case/role/port/adapter/runtime/composition 分离，import boundary 30 passed，turtle/octopus/whale 三层组件边界 | test_turtle_octopus_import_boundary (30 tests), test_ingest_no_source_lab_imports, import boundary tests | 无 | 持续维护 | 2026-06-03 |
| P-AR-002 | - | 生产路径与工具路径分离 | AR | 高 | Project | L3 | 已验证 | ingest 不直接依赖 source_lab；source_lab runner 存在不等于 production client 完成；shared_source production runner artifact 与 source_lab build 边界明确 | test_ingest_no_source_lab_imports, test_turtle_octopus_import_boundary, ADR-010 shared_source runner boundary | 无 | 持续维护 | 2026-06-03 |
| P-DGR-001 | - | Schema 与配置治理 | DGR | 高 | Project | L3 | 已验证 | ORM/migration/schema 以当前源码为准，16 组协议参数模板，config 示例配置完整 | test_scada_protocol_params, test_scada_sample_data_protocol_coverage, config template validation | 无 | 持续维护 | 2026-06-02 |
| P-AR-003 | - | 全系统公共基础库边界 | AR | 高 | Project | L3 | 已验证并收口 | `src/platform_shared/` 22 .py 文件已建成；`src/whale/shared/crosscutting/` 整棵目录已物理删除；全仓 AST 扫描 0 个 whale.shared.crosscutting import；platform_shared AST 确认 0 个上层依赖；6 个业务文件 import 已更新为 platform_shared.*；关键集成测试和 source_lab 门禁不回退 | boundary 79 tests + compileall/ruff/mypy strict clean | contracts/kernel/messaging 为空壳骨架 | 实现 contracts/kernel/messaging 完整能力 | 2026-06-03 |
| P-SCR-001 | - | 电力监控系统安全边界 | SCR | 高 | Project | L3 | 已设计 | 安全分区部署拓扑、写入控制、审计、external access policy 已设计实现 | test_ingest_security_partition_config, test_source_command_authorization_guard, test_ingest_external_access_policy_contract | 真实电力监控系统安全分区部署未执行 | 真实安全分区部署验证 | 2026-06-03 |
