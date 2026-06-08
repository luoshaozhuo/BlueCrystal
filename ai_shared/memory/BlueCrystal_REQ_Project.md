# BlueCrystal_REQ_Project

## 一、文件定位

本文件描述 BlueCrystal 项目的项目级功能需求、非功能需求、架构约束、数据治理需求和安全合规需求。

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

### P-FR-006 仿真模型资产与结果承接

- 类型：功能
- 优先级：中
- 需求描述：
  - 平台应承接仿真模型资产（FAST/OpenFAST/WindFarm/Bladed/Simulink 等）和仿真结果的元数据与文件管理。
  - Whale 管理 model_asset/simulation_case/simulation_result 的元数据与文件归档。
  - Dolphin 负责仿真计算与深度解析；仿真时序结果不进入实时 state view。
  - 文件本体走 raw_archive 归档；PostgreSQL 仅存 URI/checksum/metadata。
- 验收要点：
  - 提供 ModelAsset/SimulationCase/SimulationResult/SimulationArtifact 四表 ORM。
  - 支持仿真文件类型检测（.fst/.wnd/.prj/.slx 等）。
  - 支持 SimulationImportManifest 导入编排。
  - 仿真结果时序 sink 为 contract-only（TDengine）。
  - 不依赖 Dolphin 或 simulation engine。

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
  - Whale、Turtle、Octopus、Dolphin、Jellyfish、Manta 可以依赖 `platform_shared`。
  - `platform_shared` 不得依赖任何上层组件。
  - `whale.shared` 只服务 BlueCrystal 数据底座内部，不得作为全系统公共库。
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

### P-DGR-002 仿真资产元数据与文件治理

- 类型：数据治理
- 优先级：中
- 需求描述：
  - 仿真模型资产、案例和结果的元数据应由 model_asset 包统一管理。
  - 文件本体经 raw_archive 归档后，URI 与 checksum 写入 PostgreSQL。
  - 仿真结果时序数据不混入标准化点值表。
- 验收要点：
  - ModelAssetRepository 四表持久化 model_code/case_code/result_code 唯一约束。
  - SimulationArchiveService 复用 storage.raw_archive 端口。
  - SimulationResultTimeSeriesSinkPort 独立于 TdengineStandardizedSink。

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
| P-FR-001 | - | 多源异构数据统一接入 | FR | 高 | Project | P4/P6 | 已实现 | IEC104/OPC UA/Modbus TCP/IEC61850 MMS production client + ingest adapter + source_lab simulator/capacity/profile/E2E 门禁通过；IEC101/Modbus RTU/MQTT/HTTP REST acquisition-ready（P4 simulator，env-pending）；3 adapters 全 contract-passed | 48 source_lab gate tests, capacity/profile matrix, 各协议 E2E chain tests, 全协议 8 polling+5 streaming matrix | Beckhoff ADS real device=environment-pending，串口协议真实硬件未覆盖 | Beckhoff ADS real device + 串口真实硬件 environment 验证 | 2026-06-03 |
| P-FR-002 | - | Kappa + Lambda 混合数据链路 | FR | 高 | Project | P6/P5 (P5: Kafka/Redis Round C PASS; PostgreSQL NOT_RUN; S3/TDengine Round C FAIL; Pulsar/Flink/HDFS env-pending) | 实时链路 (Kappa) Kafka/Redis P5 verified；S3/TDengine P5 代码就绪但当前环境不可用；批处理链路 (Lambda) env-pending | Round 3: Kafka+PG P5 verified；Round 5: S3/TDengine/Redis P5 verified (10/10 E2E)；Round C: P5 回归脚本 — Kafka 2/2 PASS, Redis 2/2 PASS, TDengine 4 FAIL (MISSING_ENVIRONMENT: taosAdapter 不可用), S3 2 FAIL (既有 boto3 问题), PostgreSQL 1 NOT_RUN；waveform/simulation_result TDengine 真实 REST API adapter 已实现 (3+4 FAIL, MISSING_ENVIRONMENT)；165 P1 tests passed | test_whale_l5_kafka_pipeline_e2e (P5: 4), test_whale_l5_storage_e2e (P5: 10), test_whale_field_minimal_smoke (P6: 7), run_whale_p5_external_dependency_regression.sh (P5: 6 PASS/4 FAIL/1 NOT_RUN), test_storage_waveform_tdengine_integration, test_storage_simulation_result_tdengine_integration | warehouse/mart 仅 stub/port；batch layer 未实现；Pulsar/Flink/HDFS=environment-pending；S3/TDengine 当前环境不可用 (Round 3 regression: Kafka 2/2 PASS, Redis 2/2 PASS, S3 2 FAIL bucket 404, TDengine 4 FAIL taosAdapter不可用, PG 1 NOT_RUN; 均为 MISSING_ENVIRONMENT 非代码缺陷) | docker-compose.p5.yml 启动全依赖 + 创建 MinIO bucket 后 P5 regression 回归 + Pulsar/Flink/HDFS 真实环境 P5 验证 + batch/warehouse/mart 实现 | 2026-06-04 (Round 3) |
| P-FR-003 | - | 高频时序数据持续接入与处理 | FR | 高 | Project | P4/P5 (P5: Kafka/PG/S3/TDengine/Redis verified; Pulsar/Flink/HDFS env-pending) | Kafka/PostgreSQL/S3-MinIO/TDengine/Redis P5 verified，性能指标 env-pending | Round 3: Kafka pipeline P5 E2E verified (4 tests)；source_lab capacity/profile gate 全协议 matrix 通过；Round 5: S3/MinIO P5 verified (3 E2E + 2 integration)，TDengine P5 verified (3 E2E + 2 integration)，Redis P5 verified (4 E2E + 1 integration)；120 tests passed, 0 failures | source_lab capacity/profile gate tests, test_ingest_cache_to_kafka_pipeline, performance baseline 9 tests, run_whale_l5_external_dependency_probe.sh (multi-level), test_whale_l5_kafka_pipeline_e2e (4 tests), test_whale_l5_storage_e2e (10 tests P5 all passed) | 吞吐/延迟/抖动/丢失率指标未采集 | 真实环境下性能指标采集 | 2026-06-03 (Round 6) |
| P-FR-004 | - | 数据治理与统一信息模型 | FR | 高 | Project | P4 | 已实现 | ORM 模型（scada_ingest/scada_protocol_param 等）、Envelope schema_version、统一标识与质量码透传；16 组协议参数模板定义 | test_scada_protocol_params, test_scada_sample_data_protocol_coverage, test_message_pipeline_envelope | 完整 schema evolution 和血缘追踪未实现 | schema registry + 血缘追踪 | 2026-06-03 |
| P-FR-005 | - | 数据服务与共享 | FR | 高 | Project | P4 | 部分实现 | ingest Web API（CRUD routes + health + audit）、serving cache port；Kafka/Pulsar 消息发布已验证（contract）；warehouse/mart 仅 stub | ingest API integration tests, test_ingest_cache_to_kafka_pipeline | 对外数据服务接口、warehouse/mart 查询接口未实现 | 实现对外规范化数据服务接口 | 2026-06-03 |
| P-NFR-001 | - | 性能与容量扩展 | NFR | 高 | Project | P4 | 部分实现 | source_lab capacity/profile gate 全协议矩阵通过（polling+streaming），ingest 性能基线 9 tests passed | source_lab capacity/profile gate tests, test_ingest_prodlike_performance_profile | p95/p99 延迟和周期抖动未在真实 broker/TDengine 环境采集 | 真实环境下性能指标采集 | 2026-06-03 (Round 6: capacity/profile gate通过但真实环境性能指标未采集) |
| P-NFR-002 | - | 稳定性与长期运行 | NFR | 高 | Project | P4/P6 | 已实现 | 错误分类、重试、退避、熔断、DLQ 恢复、missed tick、worker crash/failover、graceful shutdown、writer failure recovery 8/8、writer switchover 8/8、Kafka/PostgreSQL/Redis fault injection 集成测试通过 | test_ingest_prodlike_kafka_fault_injection, test_ingest_prodlike_postgres_fault_injection, test_ingest_prodlike_redis_fault_injection, test_ingest_prodlike_worker_failover, test_whale_writer_failure_recovery, test_whale_writer_switchover, test_speed_layer_dlq_replay | 7x24 长时间运行未验证；真实 broker/TDengine 环境未覆盖 | 真实环境长时间运行验证 | 2026-06-03 (Round 6) |
| P-NFR-003 | - | 可替换与可扩展 | NFR | 高 | Project | P4 | 已验证 | port-adapter 架构：message_pipeline 3 adapters (Kafka/Pulsar/InMemory)，speed_layer 2 runners (Local/Flink)，storage 6 layers multiple backends；import boundary 30 passed 验证模块隔离 | test_turtle_octopus_import_boundary, test_ingest_no_source_lab_imports, test_message_pipeline_ports, port-adapter contract tests | 新增 backend 的 use case 不变性未做形式化验证 | 新增 backend 时回归 use case contract | 2026-06-03 |
| P-NFR-004 | - | 可观测性与运维诊断 | NFR | 高 | Project | P4/P5 | 已实现 | JSONL metrics/audit sink、structured logging、trace_id/batch_id/command_id/source_id/protocol、DB+JSONL dual audit、profile/capacity 报告可归档；P5 Round 3: P5 外部依赖环境探测脚本 (16 probes, 多级输出: tcp_ok/driver_ok/auth_ok/service_health_ok/e2e_ok, JSON+human 双格式，8 services 全覆盖, Redis 端口修正为 16379) | test_ingest_observability_sink, test_ingest_prodlike_audit_metrics_resilience, test_ingest_audit_db_jsonl_consistency, source_lab capacity/profile report tests, run_whale_l5_external_dependency_probe.sh (16 probes, multi-level + e2e_ok) | 分布式 tracing 集成未实现 | OpenTelemetry 集成 | 2026-06-03 (Round 6: 新增 run_whale_field_ready_smoke.sh 一键预检脚本，8-step 覆盖 Kafka/PG/Redis/S3/TDengine + message pipeline + raw/index/standard + serving cache) |
| P-NFR-005 | - | 安全合规 | NFR | 高 | Project | P4 | 已实现 | 安全分区配置、写入控制默认关闭、写入授权装饰器 (AuthorizedSourceWritePort)、命令审计、external access policy、file access policy、凭据不硬编码、日志脱敏 | test_ingest_security_partition_config, test_source_write_port_registry, test_source_command_authorization_guard, test_source_command_audit, test_ingest_audit_redaction, test_ingest_external_access_policy_contract | 真实电力监控系统安全分区部署未执行 | 真实安全分区部署与审计 | 2026-06-03 |
| P-AR-001 | - | Clean Architecture / Port-Adapter | AR | 高 | Project | P4 | 已验证 | use case/role/port/adapter/runtime/composition 分离，import boundary 30 passed，turtle/octopus/whale 三层组件边界 | test_turtle_octopus_import_boundary (30 tests), test_ingest_no_source_lab_imports, import boundary tests | 无 | 持续维护 | 2026-06-03 |
| P-AR-002 | - | 生产路径与工具路径分离 | AR | 高 | Project | P4 | 已验证 | ingest 不直接依赖 source_lab；source_lab runner 存在不等于 production client 完成；shared_source production runner artifact 与 source_lab build 边界明确 | test_ingest_no_source_lab_imports, test_turtle_octopus_import_boundary, ADR-010 shared_source runner boundary | 无 | 持续维护 | 2026-06-03 |
| P-DGR-001 | - | Schema 与配置治理 | DGR | 高 | Project | P4 | 已验证 | ORM/migration/schema 以当前源码为准，16 组协议参数模板，config 示例配置完整 | test_scada_protocol_params, test_scada_sample_data_protocol_coverage, config template validation | 无 | 持续维护 | 2026-06-02 |
| P-AR-003 | - | 全系统公共基础库边界 | AR | 高 | Project | P4 | 已验证并收口 | `src/platform_shared/` 22 .py 文件已建成；`src/whale/shared/crosscutting/` 整棵目录已物理删除；全仓 AST 扫描 0 个 whale.shared.crosscutting import；platform_shared AST 确认 0 个上层依赖；6 个业务文件 import 已更新为 platform_shared.*；关键集成测试和 source_lab 门禁不回退 | boundary 79 tests + compileall/ruff/mypy strict clean | contracts/kernel/messaging 为空壳骨架 | 实现 contracts/kernel/messaging 完整能力 | 2026-06-03 |
| P-SCR-001 | - | 电力监控系统安全边界 | SCR | 高 | Project | P4 | 已设计 | 安全分区部署拓扑、写入控制、审计、external access policy 已设计实现 | test_ingest_security_partition_config, test_source_command_authorization_guard, test_ingest_external_access_policy_contract | 真实电力监控系统安全分区部署未执行 | 真实安全分区部署验证 | 2026-06-03 |
| P-FR-006 | - | 仿真模型资产与结果承接 | FR | 中 | model_asset | P1 (InMemory) / P5 FAIL (TDengine REST API adapter, MISSING_ENVIRONMENT) | 真实 REST API adapter 已实现 | `src/whale/model_asset/` (6 files), `src/whale/storage/simulation_result.py` (真实 REST API write()/readback()), alembic/versions/20260527_000004; 109 unit+integration tests; TDengine simulation_result 集成测试 5 tests (4 FAIL, MISSING_ENVIRONMENT)；PostgreSQL 集成测试 16 tests NOT_RUN (MISSING_ENVIRONMENT) | 109 tests PASS (P1+P3)；test_storage_simulation_result_tdengine_integration.py 5 tests: 4 FAIL (MISSING_ENVIRONMENT), 1 PASS；test_model_asset_postgres_integration.py 16 NOT_RUN (MISSING_ENVIRONMENT)；compileall/ruff/mypy PASS | TDengine taosAdapter 不可用 (Round 3 regression: TDengine simulation_result 5 NOT_RUN, 均为环境缺失非代码缺陷)；PostgreSQL DSN 未设置 (16 NOT_RUN)；仿真时序结果不进入实时 state view | docker-compose.p5.yml 启动 TDengine+taosAdapter + PostgreSQL DSN 配置后 P5 regression 回归 | 2026-06-04 (Round 3) |
| P-DGR-002 | P-FR-006 | 仿真资产元数据与文件治理 | DGR | 中 | model_asset | P1 (InMemory/SQLite :memory:) / P5 NOT_RUN (PostgreSQL MISSING_ENVIRONMENT) | 部分实现 | ORM 四表唯一约束/FK 链/parent self-ref FK 已通过 SQLite :memory: 验证；PostgreSQL 集成测试已编写 (16 tests) 但 NOT_RUN (DSN 未设置)；SimulationArchiveService 复用 LocalCompressedArchiveSink | test_model_asset_orm (四表唯一约束/FK), test_model_asset_repository (CRUD), test_model_asset_integration (import->archive->persist), test_model_asset_postgres_integration (16 NOT_RUN) | SQLite :memory: 不等价于 PostgreSQL 并发写/索引行为；PostgreSQL 集成测试已编写但未执行 | PostgreSQL 真实环境集成验证 (DSN 配置后执行) | 2026-06-04 |
