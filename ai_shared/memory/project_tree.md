# Whale 项目目录树

> 能源数据统一平台（风光储电场数据接入底座）
> 最后更新: 2026-05-31 (Round 16 — field readback L5 现场验证包固化/脚本 CLI 加固/evidence template/入口自检/需求表里程碑与 production-ready 判定)

本文件维护完整文件级目录树，每个 item 附简短职责注释（不超过 40 中文字符）。
只用于导航，不替代读取当前源码。

## 根目录

```text
/ (Whale)
├── CLAUDE.md                        — Claude Code / Codex 共用执行入口
├── AGENTS.md                        — Codex 自动读取入口，指向 CLAUDE.md
├── README.md                        — 项目简介与快速开始
├── Dockerfile                       — ingest统一runtime镜像
├── alembic.ini                      — Alembic 主配置
├── pyproject.toml                   — 项目元数据、依赖与 ruff/mypy 工具配置
├── requirements.txt                 — Python 依赖声明
├── alembic/                         — ingest运行库迁移
├── docker-compose.ingest-dev.yaml   — ingest 开发环境 Docker 编排
├── .flake8                          — flake8 代码检查配置
├── .gitignore                       — Git 忽略规则
├── .env.ingest.example              — ingest 环境变量模板
├── .vscode/settings.json            — VSCode 编辑器配置
├── config/                          — 运行时配置
│   └── ingest/                      — ingest 配置（access_policy/performance/audit/endurance/security_partition）
│
├── src/                             — 主源码根目录
├── tests/                           — 项目级测试根目录
├── tools/                           — 工具包根目录
├── ai_shared/                       — AI 配置、规则与记忆
├── docs/                            — 项目文档
├── scripts/                         — 运维与开发脚本
├── .claude/                         — Claude Code 配置与技能
├── .agents/                         — Codex agent 配置与技能（软链至 .claude/skills）
├── .codex/                          — OpenAI Codex 适配配置
└── third_party/                     — 第三方 C 协议栈源码与预编译库
```

## 主源码 `src/whale/`

```text
src/whale/
├── __init__.py                      — 包入口
│
├── ingest/                          — 数据采集核心（六边形架构）
│   ├── __init__.py
│   ├── config.py                    — 采集配置定义与加载
│   ├── composition.py               — 依赖注入组合根（采集/写入/快照发布）
│   ├── message_pipeline.py          — 消息管道编排
│   ├── whale.db                     — SQLite 开发/测试数据库
│   │
│   ├── entities/                    — 领域实体
│   │   ├── node_state.py            — 节点状态实体
│   │   └── source_health_state.py   — 数据源健康状态实体
│   │
│   ├── usecases/                    — 用例层（业务逻辑）
│   │   ├── __init__.py             — 导出 SourceAcquisitionUseCase, StateSnapshotPublishUseCase
│   │   ├── source_acquisition_use_case.py  — 采集用例入口
│   │   ├── source_command_use_case.py  — 设备写入/控制命令用例入口
│   │   ├── state_snapshot_publish_use_case.py  — 缓存快照发布到消息队列用例
│   │   ├── dtos/                    — 数据传输对象
│   │   │   ├── acquired_node_state.py
│   │   │   ├── source_acquisition_request.py
│   │   │   ├── source_acquisition_start_result.py
│   │   │   ├── source_connection_data.py
│   │   │   ├── source_write_request.py  — 写入请求 DTO
│   │   │   ├── source_write_result.py   — 写入结果 DTO
│   │   │   ├── state_publish_request.py  — 快照发布请求 DTO（过滤、dry_run、拆分）
│   │   │   └── state_publish_result.py   — 快照发布结果 DTO（状态、计数、错误）
│   │   └── roles/                   — 采集策略角色
│   │       ├── polling_acquisition_role.py       — 轮询采集策略
│   │       └── subscription_acquisition_role.py  — 订阅采集策略
│   │
│   ├── ports/                       — 端口层（接口抽象）
│   │   ├── __init__.py
│   │   ├── audit.py                 — ingest审计sink端口
│   │   ├── diagnostics.py           — 诊断接口
│   │   ├── message/                 — 消息发布端口
│   │   │   └── message_publisher_port.py
│   │   ├── runtime/                 — 运行时配置端口
│   │   │   ├── source_runtime_config_port.py
│   │   │   └── write_lease_port.py  — 写入租约端口
│   │   ├── source/                  — 数据源采集端口
│   │   │   ├── source_acquisition_definition_port.py  — 采集定义端口
│   │   │   ├── source_acquisition_port.py              — 采集端口
│   │   │   ├── source_acquisition_port_registry.py     — 端口注册表
│   │   │   ├── source_write_port.py                    — 设备写入端口
│   │   │   └── source_write_port_registry.py           — 写入端口注册表
│   │   └── state/                   — 状态缓存端口
│   │       ├── source_state_cache_port.py          — 状态缓存端口
│   │       └── source_state_snapshot_reader_port.py — 快照读取端口
│   │
│   ├── adapters/                    — 适配器层（基础设施实现）
│   │   ├── audit/                   — 审计sink适配器
│   │   │   ├── __init__.py          — 审计适配器导出
│   │   │   ├── db_audit_sink.py     — DB审计sink
│   │   │   ├── http_audit_sink.py   — 外部HTTP审计SIEM sink
│   │   │   └── multi_audit_sink.py  — DB+JSONL dual audit sink 组合器
│   │   ├── config/                  — 配置持久化适配器
│   │   │   ├── opcua_source_acquisition_definition_repository.py  — OPC UA 采集定义仓库
│   │   │   └── source_runtime_config_repository.py                — 运行时配置仓库
│   │   ├── message/                 — 消息发布适配器
│   │   │   ├── kafka_message_publisher.py           — Kafka 发布器
│   │   │   ├── redis_streams_message_publisher.py   — Redis Streams 发布器
│   │   │   └── relational_outbox_message_publisher.py  — 关系库 outbox 发布器
│   │   ├── source/                  — 数据源采集适配器
│   │   │   ├── modbus_source_acquisition_adapter.py   — Modbus TCP 采集适配器
│   │   │   ├── modbus_source_write_adapter.py         — Modbus TCP 写入适配器
│   │   │   ├── opcua_source_acquisition_adapter.py           — OPC UA 采集适配器
│   │   │   ├── opcua_source_write_adapter.py                 — OPC UA 写入适配器（含readback）
│   │   │   ├── iec61850_source_acquisition_adapter.py  — IEC 61850 MMS 采集适配器
│   │   │   ├── iec61850_source_write_adapter.py        — IEC 61850 MMS 写入适配器
    │   │   │   ├── iec61850_report_source_acquisition_adapter.py  — IEC 61850 Report 订阅采集适配器
│   │   │   ├── static_source_acquisition_port_registry.py    — 静态采集端口注册表
│   │   │   └── static_source_write_port_registry.py          — 静态写入端口注册表
│   │   ├── observability/           — 观测与审计输出
│   │   │   ├── __init__.py          — 观测sink导出
│   │   │   └── file_sinks.py        — JSONL metrics/audit sink
│   │   └── state/                   — 状态缓存适配器
│   │       └── redis_source_state_cache.py  — Redis 状态缓存
│   │
│   ├── api/                         — ingest Web API
│   │   ├── __init__.py              — API包导出
│   │   ├── app.py                   — FastAPI app factory
│   │   ├── audit_middleware.py      — API审计中间件
│   │   ├── errors.py                — 稳定错误模型
│   │   ├── schemas.py               — API schema
│   │   ├── readyz.py                — readyz 8组件聚合与degradation脱敏
│   │   └── routes/
│   │       ├── __init__.py          — API路由导出
│   │       ├── acquisition_tasks.py — 采集任务CRUD路由
│   │       ├── audit_events.py      — audit event查询路由
│   │       ├── bundles.py           — bundle metadata查询路由
│   │       ├── health.py            — health/ready 路由
│   │       ├── leases.py            — lease查询路由
│   │       ├── nodes.py             — node查询路由
│   │       ├── runtime_config.py    — source等配置CRUD路由
│   │       ├── scheduler_jobs.py    — scheduler job CRUD路由
│   │       └── security_partitions.py — security partition CRUD路由
│   │
│   ├── bundle/                      — 配置包导入导出
│   │   ├── __init__.py              — bundle包导出
│   │   ├── checksum.py              — bundle校验摘要
│   │   ├── model.py                 — bundle领域模型
│   │   ├── redaction.py             — bundle脱敏导出
│   │   └── service.py               — bundle服务
│   │
│   ├── domain/                      — 共享领域模型
│   │   ├── audit_event.py           — ingest结构化审计事件
│   │   └── write_security_profile.py — 写入安全配置模型
│   │
│   ├── runtime/                     — 运行时组件
│   │   ├── acquisition_mode.py              — 采集模式枚举
│   │   ├── cli.py                           — ingest多入口CLI
│   │   ├── entrypoint.py                    — ingest运行入口
│   │   ├── fencing.py                       — fencing token服务
│   │   ├── job_status.py                    — 作业状态定义
│   │   ├── job_assignment.py                — 作业归属服务
│   │   ├── lease.py                         — 作业租约服务
│   │   ├── message_pipeline_settings.py     — 管道参数设置
│   │   ├── modes.py                         — runtime模式枚举
│   │   ├── node_runtime.py                  — 节点心跳服务
│   │   ├── scheduler.py                     — 调度器主逻辑
│   │   ├── scheduler_factory.py             — 调度器工厂
│   │   ├── scheduler_job.py                 — 调度作业封装
│   │   ├── scheduler_settings.py            — 调度器参数
│   │   ├── write_lease.py                   — 写入租约服务
│   │   ├── worker_runtime.py                — APScheduler WorkerRuntime（含handler分发）
│   │   └── handlers.py                      — WorkerRuntime 采集 job handler
│   │
│   ├── decorators/                   — 装饰器
│   │   ├── source_acquisition.py     — 采集流程装饰器
│   │   ├── source_write.py           — 写入授权装饰器（AuthorizedSourceWritePort）
│   │   └── state_cache.py            — 状态缓存装饰器
│   │
│   ├── framework/persistence/        — 持久化框架
│   │   ├── base.py                   — ORM 声明基类
│   │   ├── init_db.py                — 数据库初始化
│   │   ├── runtime_db.py             — runtime DB初始化与探针
│   │   ├── session.py                — 会话管理
│   │   └── orm/__init__.py           — ORM 模型包（空，模型在 shared）
│   │
│   └── docs/                         — ingest 设计文档
│       ├── DECISIONS.md              — 架构决策记录
│       └── 设计说明书.md              — 模块设计说明书
│
├── processing/                       — 数据处理
│   ├── __init__.py
│   ├── cleaner.py                    — 数据清洗
│   └── normalizer.py                 — 数据标准化
│
├── aggregation/                      — 数据聚合
│   ├── __init__.py
│   ├── ads.py                        — ADS 聚合
│   ├── periodic.py                   — 周期性聚合
│   └── realtime.py                   — 实时聚合
│
├── storage/                          — 存储层（待实现）
│   └── __init__.py
│
├── shared/                           — 共享层（跨模块通用能力）
│   ├── __init__.py
│   │
│   ├── enums/                        — 共享枚举
│   │   ├── __init__.py
│   │   └── quality.py                — 数据质量枚举
│   │
│   ├── utils/                        — 工具函数
│   │   ├── __init__.py
│   │   └── time.py                   — 时间工具函数
│   │
│   ├── persistence/                  — 共享持久化
│   │   ├── __init__.py
│   │   ├── base.py                   — 持久化基类
│   │   ├── init_db.py                — 数据库初始化
│   │   ├── session.py                — 会话管理
│   │   ├── orm/                      — ORM 模型
│   │   │   ├── acquisition.py        — 采集任务模型
│   │   │   ├── asset.py              — 资产模型
│   │   │   ├── ingest_runtime.py     — ingest运行库模型
│   │   │   ├── ingest_diagnostics.py — 采集诊断模型
│   │   │   ├── organization.py       — 组织模型
│   │   │   ├── scada_ingest.py       — SCADA 采集模型
│   │   │   └── scada_protocol_param.py  — SCADA 协议参数模型
│   │   └── template/                 — 模板数据
│   │       ├── __init__.py
│   │       ├── gbt_30966_fields.py         — GB/T 30966 字段定义
│   │       ├── protocol_param_data.py      — 协议参数初始数据
│   │       ├── protocol_view_defs.py       — 协议视图定义
│   │       ├── sample_data.py              — 示例数据
│   │       └── OPCUA_client_connections.yaml  — OPC UA 连接配置
│   │
│   ├── source/                       — 数据源访问抽象
│   │   ├── __init__.py
│   │   ├── models.py                 — 数据源模型定义
│   │   ├── ports.py                  — 源访问端口接口
│   │   ├── runner_resolution.py      — shared_source production runner 路径解析与 dev fallback
│   │   ├── access/                   — 可复用接入适配器
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py            — SourceAccessAdapter 基类
│   │   │   ├── model.py              — 端点/点位/Tick 数据模型
│   │   │   └── opcua.py              — OPC UA 适配器实现
│   │   ├── modbus/                   — Modbus TCP 读取器
│   │   │   ├── __init__.py
│   │   │   ├── reader.py             — ModbusSourceReader 外观
│   │   │   └── backends/             — Modbus 后端实现
│   │   │       ├── __init__.py
│   │   │       ├── base.py           — 后端基类与数据类型
│   │   │       └── libmodbus_backend.py  — libmodbus C 子进程后端
│   │   ├── opcua/                    — OPC UA 读取器
│   │   │   ├── __init__.py
│   │   │   ├── reader.py             — OpcUaSourceReader
│   │   │   └── backends/             — OPC UA 后端实现
│   │   │       ├── base.py           — 后端基类
│   │   │       ├── factory.py        — 后端工厂
│   │   │       └── open62541_backend.py  — open62541 C 后端
│   │   ├── iec61850/                 — IEC 61850 MMS/Report 读取器
│   │   │   ├── __init__.py
│   │   │   ├── reader.py             — Iec61850MmsSourceReader 外观
│   │   │   ├── report_reader.py      — Iec61850ReportSourceReader 外观
│   │   │   └── backends/             — IEC 61850 后端实现
│   │   │       ├── __init__.py
│   │   │       ├── base.py           — 后端基类与数据类型
│   │   │       ├── libiec61850_backend.py  — libiec61850 C 子进程后端（MMS）
│   │   │       ├── report_base.py    — Report 事件数据类型
│   │   │       └── libiec61850_report_backend.py  — libiec61850 C 子进程后端（Report）
│   │   └── scheduling/               — 调度工具
│   │       ├── __init__.py
│   │       ├── concurrency.py        — 并发控制
│   │       ├── fixed_rate.py         — 固定速率执行器
│   │       ├── polling.py            — 轮询调度
│   │       └── stagger.py            — 错峰调度
│   │
│   └── crosscutting/                 — 横切关注点
│       ├── auth/                     — 认证授权
│       │   ├── authorizer.py         — 授权器
│       │   ├── credential.py         — 凭证管理
│       │   ├── identity.py           — 身份管理
│       │   └── policy.py             — 策略定义
│       ├── compliance/               — 合规
│       │   ├── audit_policy.py       — 审计策略
│       │   ├── data_classification.py — 数据分类
│       │   └── retention.py          — 数据保留策略
│       ├── debug/                    — 调试工具
│       │   ├── diagnostics.py        — 诊断
│       │   ├── ring_buffer.py        — 环形缓冲区
│       │   └── trace.py              — 链路追踪
│       ├── observability/            — 可观测性
│       │   ├── audit.py              — 审计日志
│       │   ├── logging.py            — 日志
│       │   ├── masking.py            — 数据脱敏
│       │   └── metrics.py            — 指标
│       ├── resilience/               — 韧性
│       │   ├── backoff.py            — 退避策略
│       │   ├── circuit_breaker.py    — 熔断器
│       │   ├── deadline.py           — 截止时间
│       │   ├── error_classifier.py   — 错误分类
│       │   └── retry.py              — 重试策略
│       └── security/                 — 安全
│           ├── certificate.py        — 证书管理
│           ├── model.py              — 安全模型
│           ├── secret_provider.py    — 密钥提供
│           └── tls.py                — TLS 配置
```

## 项目级测试 `tests/`

```text
tests/
├── __init__.py
├── conftest.py                       — 全局 pytest 夹具
├── conftest.py                       — 全局 pytest 夹具
├── TESTING.md                        — 测试策略说明
│
├── unit/                             — 单元测试
│   ├── __init__.py
│   ├── test_config.py                — 配置解析测试
│   ├── test_fleet_update_selection.py   — 机群更新选择测试
│   ├── test_kafka_message_publisher.py  — Kafka 发布器测试
    │   ├── test_modbus_source_acquisition_adapter.py  — Modbus TCP 采集适配器测试
    │   ├── test_modbus_source_write_adapter.py         — Modbus TCP 写入适配器测试
│   ├── test_opcua_adapter_resolution.py — OPC UA 适配器解析测试
│   ├── test_opcua_source_acquisition_adapter.py  — OPC UA 采集适配器测试
│   ├── test_iec61850_mms_backend.py         — IEC 61850 MMS 后端单元测试
│   ├── test_iec61850_source_acquisition_adapter.py  — IEC 61850 MMS 采集适配器测试
│   ├── test_iec61850_source_write_adapter.py  — IEC 61850 MMS 写入适配器测试
│   ├── test_iec61850_report_backend.py         — IEC 61850 Report 后端单元测试
│   ├── test_iec61850_report_acquisition_adapter.py  — IEC 61850 Report 订阅采集适配器测试
│   ├── test_open62541_backend.py      — open62541 后端测试
│   ├── test_polling_acquisition_role.py   — 轮询角色测试
│   ├── test_redis_source_state_cache.py   — Redis 状态缓存测试
│   ├── test_redis_streams_message_publisher.py — Redis Streams 测试
│   ├── test_relational_outbox_message_publisher.py — Outbox 发布器测试
│   ├── test_ingest_api_app.py        — FastAPI app单测
│   ├── test_ingest_audit_event_schema.py — ingest审计事件单测
│   ├── test_ingest_bundle_checksum.py — bundle摘要单测
│   ├── test_ingest_bundle_redaction.py — bundle脱敏单测
│   ├── test_ingest_composition_injection.py — 注入完整性单测
│   ├── test_ingest_job_lease.py      — 作业租约语义单测
│   ├── test_ingest_runtime_entrypoint.py — 运行入口单测
│   ├── test_ingest_runtime_modes.py  — runtime模式单测
│   ├── test_ingest_runtime_orm_models.py — runtime ORM单测
│   ├── test_ingest_runtime_scheduler_import.py — scheduler导入门禁
│   ├── test_ingest_write_lease.py    — 写入租约单测
│   ├── test_ingest_write_lease_fencing.py — 写入租约fencing单测
│   ├── test_ingest_readyz.py         — readyz 8组件聚合与degradation单测
│   ├── test_scheduler_job_routes.py  — 调度任务持久化单测
│   ├── test_worker_runtime_do_execute.py — WorkerRuntime dispatch 单测
│   ├── test_acquisition_job_handler.py — AcquisitionJobHandler L1 单测
│   ├── test_dual_node_write_lease_conflict.py — 双节点写入冲突 L2 单测
│   ├── test_source_acquisition_port_registry.py  — 端口注册表测试
│   ├── test_source_acquisition_use_case.py   — 采集用例测试
│   ├── test_source_command_write_lease_guard.py — 写入租约守卫测试
│   ├── test_source_command_use_case.py   — 命令写入用例测试
│   ├── test_source_command_lease_release.py — 写入租约释放单测
│   ├── test_shared_source_runner_resolution.py  — shared_source runner 路径解析单测
│   ├── test_state_snapshot_publish_use_case.py  — 快照发布用例测试（17 cases）
│   ├── test_source_runtime_config_repository.py  — 运行时配置仓库测试
│   ├── test_source_scheduling.py       — 调度测试
│   ├── test_source_simulation_support_sources.py  — 模拟源测试
│   ├── test_source_write_port_registry.py  — 写入端口注册表测试
│   ├── test_subscription_acquisition_role.py  — 订阅角色测试
│   ├── test_opcua_source_write_adapter.py  — OPC UA 写入适配器测试
│   └── shared/persistence/
│       └── test_scada_protocol_params.py   — SCADA 协议参数测试
│
├── integration/                       — 集成测试
│   ├── __init__.py
│   ├── test_framework_db_init.py      — 框架 DB 初始化集成测试
│   ├── test_ingest_api_acquisition_task_crud.py — acquisition task CRUD集成
│   ├── test_ingest_api_audit.py       — API审计集成测试
│   ├── test_ingest_bundle_import_export.py — bundle导入导出集成
│   ├── test_ingest_polling_retry_to_redis.py   — 轮询重试到 Redis
│   ├── test_ingest_runtime_db_init.py — runtime DB初始化集成测试
│   ├── test_ingest_runtime_entrypoint_smoke.py — entrypoint烟测
│   ├── test_ingest_source_acquisition_to_redis.py  — 采集到 Redis 集成
│   ├── test_ingest_subscription_strategy.py    — 订阅策略集成测试
│   ├── test_redis_state_cache_faults.py        — Redis 缓存容错测试
    │   ├── test_ingest_modbus_source_write.py        — Modbus TCP 写入集成测试
│   ├── test_ingest_cache_to_kafka_pipeline.py     — 缓存快照到 Kafka 发布集成测试（5 cases）
│   ├── test_ingest_opcua_source_write.py        — OPC UA 写入集成测试
│   ├── test_ingest_iec61850_mms_source_write.py  — IEC 61850 MMS 写入集成测试
│   ├── test_ingest_iec61850_report_subscription.py  — IEC 61850 Report 订阅集成测试
│   ├── test_ingest_prodlike_endurance_smoke.py — prodlike endurance 脚本烟测
│   ├── test_ingest_prodlike_postgres_fault_injection.py — PostgreSQL 故障注入恢复测试
│   ├── test_ingest_prodlike_redis_fault_injection.py — Redis 故障注入恢复测试
│   ├── test_ingest_prodlike_kafka_fault_injection.py — Kafka 故障注入恢复测试
│   ├── test_ingest_prodlike_worker_failover.py — worker crash/failover 集成测试
│   ├── test_ingest_dual_node_db_lease_e2e.py — 双节点 DB lease E2E 集成测试（L3）
│   ├── test_ingest_prodlike_scheduler_backpressure.py — 调度背压与 missed tick 测试
│   ├── test_ingest_prodlike_audit_metrics_resilience.py — 审计指标韧性测试
│   ├── test_ingest_security_partition_bundle_flow.py — Bundle单向流5 tests
│   ├── test_ingest_external_access_policy_contract.py — 外部授权合同5 tests
│   ├── test_ingest_external_audit_sink_contract.py — 外部审计sink合同5 tests
│   ├── test_ingest_prodlike_performance_profile.py — 性能基线9 tests
│   └── test_sqlite_config_init.py              — SQLite 配置初始化
│
├── e2e/                               — 端到端测试
│   ├── __init__.py
│   ├── conftest.py
│   └── helpers.py
│
├── performance/                       — 性能测试
│   ├── __init__.py
│   ├── load/
│   │   ├── __init__.py
│   │   └── conftest.py                — 负载测试夹具
│   ├── stress/
│   │   ├── __init__.py
│   │   └── test_acquisition_pipeline_stress.py  — 采集管道压力测试
│   └── endurance/
│       └── __init__.py                — 耐久测试（待实现）
│
└── support/
    ├── ingest_prodlike_runtime.py     — prodlike compose/故障注入辅助
    └── source_lab_runtime.py          — source_lab 运行时支持
```

## Source Lab 工具 `tools/source_lab/`

```text
tools/source_lab/
├── __init__.py                        — 包入口
├── README.md                          — 工具说明
├── contracts.py                       — 合约/接口定义
├── factory.py                         — 组件工厂
├── fleet.py                           — 机群管理
├── model.py                           — 数据模型
├── sources.py                         — 数据源定义
├── field_capacity.py                  — 现场容量测试 CLI
├── field_probe.py                     — 现场探测 CLI
├── field_profile.py                   — 现场性能画像 CLI
│
├── access/                            — 协议接入层引擎
│   ├── __init__.py
│   ├── README.md
│   ├── config.py                      — 接入配置加载
│   ├── capacity.py                    — 容量测试入口
│   ├── field_capacity.py              — 现场容量测试逻辑
│   ├── probe.py                       — 探测入口
│   ├── profile.py                     — 性能画像入口
│   │
│   ├── common/                        — 公共工具
│   │   ├── __init__.py
│   │   ├── access_model.py            — 接入层数据模型
│   │   ├── cpu.py                     — CPU 监控
│   │   ├── io.py                      — IO 监控
│   │   ├── progress.py                — 进度报告
│   │   ├── scheduling.py              — 调度工具
│   │   ├── table.py                   — 表格渲染
│   │   └── utils.py                   — 通用工具函数
│   │
│   ├── polling/                       — 轮询模式
│   │   ├── __init__.py
│   │   ├── capacity.py                — 轮询容量测试
│   │   ├── capacity_rows.py           — 容量结果行格式化
│   │   ├── metrics.py                 — 轮询指标收集
│   │   ├── model.py                   — 轮询数据模型
│   │   ├── profile.py                 — 轮询性能画像
│   │   ├── reporter.py                — 轮询报告生成
│   │   └── worker.py                  — 轮询 Worker
│   │
│   ├── subscribe/                     — 订阅模式
│   │   ├── __init__.py
│   │   ├── capacity.py                — 订阅容量测试
│   │   ├── capacity_model.py          — 容量测试模型
│   │   ├── capacity_plan.py           — 容量测试计划
│   │   ├── capacity_rows.py           — 容量结果行格式化
│   │   ├── capacity_scan.py           — 容量扫描
│   │   ├── metrics.py                 — 订阅指标收集
│   │   ├── model.py                   — 订阅数据模型
│   │   ├── profile.py                 — 订阅性能画像
│   │   ├── reporter.py                — 订阅报告生成
│   │   ├── scan.py                    — 订阅扫描
│   │   └── worker.py                  — 订阅 Worker
│   │
│   ├── runtime/                       — endpoint级动态运行时
│   │   ├── __init__.py
│   │   ├── endpoint_runtime.py        — endpoint运行时模型
│   │   ├── endpoint_registry.py       — endpoint动态注册表
│   │   ├── session_manager.py         — endpoint会话管理
│   │   ├── stagger_coordinator.py     — endpoint错峰协调
│   │   ├── continuity_model.py        — 连续性指标模型
│   │   ├── continuity_monitor.py      — 连续性指标监控
│   │   ├── state_store.py             — runtime文件状态存储
│   │   └── operation_journal.py       — 动态操作日志
│   │
│   ├── providers/                     — 数据提供者
│   │   ├── __init__.py
│   │   ├── base.py                    — 提供者基类
│   │   ├── expanded_field.py          — 展开字段提供者
│   │   ├── field.py                   — 字段提供者
│   │   ├── file_field.py              — 文件字段提供者
│   │   └── simulator.py               — 模拟器提供者
│   │
│   └── runners/                       — 协议运行器
│       ├── __init__.py
│       ├── base.py                    — 运行器基类
│       ├── protocol.py                — 协议枚举定义
│       ├── registry.py                — 运行器注册表
│       ├── native_runner_map.py       — Native 运行器映射
│       ├── native_process.py          — Native 进程管理
│       ├── native_cmd.py              — Native 命令封装
│       ├── generic_polling.py         — 通用轮询运行器
│       ├── generic_streaming.py       — 通用流式运行器
│       ├── http_rest_polling.py       — HTTP REST 轮询
│       ├── iec101_polling.py          — IEC 101 轮询
│       ├── iec101_event.py            — IEC 101 事件
│       ├── iec104_polling.py          — IEC 104 轮询
│       ├── iec104_event.py            — IEC 104 事件
│       ├── iec61850_l2_streaming.py   — GOOSE/SV L2 订阅运行器
│       ├── iec61850_mms_polling.py    — IEC 61850 MMS 轮询
│       ├── iec61850_report.py         — IEC 61850 报告
│       ├── modbus_rtu_polling.py      — Modbus RTU 轮询
│       ├── modbus_tcp_polling.py      — Modbus TCP 轮询
│       ├── mqtt_subscription.py       — MQTT 订阅
│       ├── open62541_serial_polling.py    — open62541 串行轮询
│       └── open62541_subscription.py      — open62541 订阅
│
├── protocols/                         — 协议仿真（含 ServerSimulatorFacade）
│   ├── __init__.py
│   ├── registry.py                    — 协议注册表（含 ServerSimulatorFacade 工厂）
│   ├── common/                        — 协议公共
│   │   ├── __init__.py
│   │   ├── point_mapping.py           — 测点映射
│   │   ├── simulators.py              — 通用模拟器
│   │   ├── simulator_models.py        — ServerSimulatorFacade 数据模型
│   │   ├── simulator_facade.py        — ServerSimulatorFacade Protocol
│   │   └── _base_facade.py            — 默认 NOT_IMPLEMENTED 基类
│   ├── http_rest/__init__.py          — HTTP REST 协议
│   ├── iec101/__init__.py             — IEC 101 协议
│   ├── iec104/__init__.py             — IEC 104 协议
│   ├── iec61850/__init__.py           — IEC 61850 协议
│   ├── modbus/
│   │   ├── __init__.py
│   │   └── simulator.py               — Modbus TCP/RTU facades
│   ├── mqtt/
│   │   ├── __init__.py
│   │   └── simulator.py               — MQTT facade
│   └── opcua/                         — OPC UA 模拟器
│       ├── __init__.py
│       ├── simulator.py               — OPC UA facade
│       ├── address_space.py           — OPC UA 地址空间生成
│       ├── open62541_source_simulator.py  — open62541 仿真数据源
│       ├── docs/GBT_30966.2-2022-信息模型.pdf  — 新能源信息模型标准
│       ├── templates/OPCUANodeSet.xml     — OPC UA 节点集模板
│       └── templates/OPCUA_client_connections.yaml  — 客户端连接模板
│
├── native/                            — C 原生运行器源码
│   ├── CMakeLists.txt                 — CMake 构建配置
│   ├── README.md
│   ├── open62541/                     — OPC UA 原生运行器
│   │   ├── open62541_client_runner.c  — OPC UA 客户端运行器
│   │   ├── open62541_simulator_server.c   — OPC UA 模拟器服务端
│   │   └── open62541_subscription_runner.c  — OPC UA 订阅运行器
│   ├── lib60870/                      — IEC 60870 原生运行器
│   │   ├── iec101_client_runner.c     — IEC 101 客户端
│   │   ├── iec101_event_runner.c      — IEC 101 事件运行器
│   │   ├── iec101_simulator_slave.c   — IEC 101 模拟从站
│   │   ├── iec104_client_runner.c     — IEC 104 客户端
│   │   ├── iec104_event_runner.c      — IEC 104 事件运行器
│   │   └── iec104_simulator_server.c  — IEC 104 模拟服务端
│   ├── libiec61850/                   — IEC 61850 原生运行器
│   │   ├── iec61850_goose_publisher_simulator.c  — GOOSE 发布模拟器
│   │   ├── iec61850_goose_subscriber_runner.c    — GOOSE 订阅运行器
│   │   ├── iec61850_mms_client_runner.c          — MMS 客户端运行器
│   │   ├── iec61850_report_runner.c              — 报告运行器
│   │   ├── iec61850_simulator_server.c           — 61850 模拟服务端
│   │   ├── iec61850_sv_publisher_simulator.c     — SV 发布模拟器
│   │   └── iec61850_sv_subscriber_runner.c       — SV 订阅运行器
│   └── libmodbus/                     — Modbus 原生运行器
│       ├── modbus_rtu_polling_runner.c    — Modbus RTU 轮询
│       ├── modbus_tcp_polling_runner.c    — Modbus TCP 轮询
│       └── modbus_simulator_server.c      — Modbus 模拟服务端
│
└── tests/                             — Source Lab 测试
    ├── __init__.py
    ├── README.md
    ├── TEST_AUDIT.md                   — 测试审计记录
    ├── conftest.py                     — 测试夹具（含 load 测试自动跳过）
    ├── support/
    │   ├── __init__.py
    │   └── sources.py                  — 测试数据源定义
    ├── test_factory.py                 — 工厂测试
    ├── test_fleet_partial_lifecycle.py — fleet局部生命周期测试
    ├── test_fleet_startup_controls.py  — 机群启动控制测试
    ├── test_open62541_source_simulation_single_server_smoke.py  — 单服务器冒烟
    ├── test_source_simulation_multi_server_polling_capacity.py  — 多服务器轮询容量
    ├── test_source_simulation_multi_server_polling_profile.py   — 多服务器轮询画像
    ├── test_source_simulation_multi_server_subscribe_capacity.py  — 多服务器订阅容量
    ├── test_source_simulation_multi_server_subscribe_profile.py   — 多服务器订阅画像
    ├── fixtures/
    │   ├── db_export/
    │   │   ├── field_servers.tsv       — 场站服务器 TSV 导出
    │   │   └── signal_profile_items.tsv  — 信号配置文件 TSV 导出
    │   └── simulator/
    │       ├── field_servers.tsv       — 模拟器场站服务器输入
    │       └── signal_profile_items.tsv  — 模拟器信号输入
    │
    └── access/                         — 接入层专项测试
        ├── __init__.py
        ├── test_access_config.py       — 接入配置测试
        ├── test_access_facades.py      — 接入外观测试
        ├── test_access_metrics.py      — 接入指标测试
        ├── test_access_probe.py        — 接入探测测试
        ├── test_access_probe_protocol_handshake.py  — 协议握手探测
        ├── test_access_probe_protocol_semantics.py  — 协议语义探测
        ├── test_access_progress_reporting.py  — 进度报告测试
        ├── test_access_reporter.py     — 报告器测试
        ├── test_access_scheduling.py   — 调度测试
        ├── test_access_structure.py    — 结构测试
        ├── test_access_worker.py       — Worker 测试
        ├── test_all_protocols_polling_capacity.py   — 全协议轮询容量
        ├── test_all_protocols_polling_profile.py    — 全协议轮询画像
        ├── test_all_protocols_probe.py — 全协议探测
        ├── test_all_protocols_streaming_capacity.py  — 全协议流式容量
        ├── test_all_protocols_streaming_profile.py   — 全协议流式画像
        ├── test_capacity_progress.py   — 容量进度测试
	        ├── test_capacity_reporter.py   — 容量报告器测试
        ├── test_capacity_rows.py       — 容量行格式化测试
        ├── test_capacity_service.py    — 容量服务测试
        ├── _dynamic_runtime_test_utils.py — 动态runtime测试辅助
        ├── test_dynamic_cli.py         — 动态CLI测试
        ├── test_dynamic_cli_accepted_state.py — accepted-state CLI测试
        ├── test_dynamic_endpoint_patch_matrix.py — 动态patch矩阵测试
        ├── test_dynamic_goose_sv_streaming_endpoint_adjustment.py — GOOSE/SV动态隔离测试
        ├── test_dynamic_goose_sv_permission_gate.py — GOOSE/SV权限门禁测试
        ├── test_dynamic_iec61850_report_endpoint_adjustment.py — IEC61850 Report隔离测试
        ├── test_dynamic_native_interactive_control_boundary.py — native交互边界测试
        ├── test_dynamic_native_runner_isolation.py — native runner隔离测试
        ├── test_dynamic_opcua_polling_endpoint_adjustment.py — OPC UA polling隔离测试
        ├── test_dynamic_opcua_subscription_endpoint_adjustment.py — OPC UA订阅隔离测试
        ├── test_dynamic_operation_journal_audit.py — 动态审计日志测试
        ├── test_dynamic_polling_endpoint_adjustment.py — 动态polling局部调整测试
        ├── test_dynamic_runtime_state_store_resilience.py — runtime状态存储韧性测试
        ├── test_dynamic_runtime_state_store_integrity.py — runtime状态完整性测试
        ├── test_dynamic_runtime_state_store_retention.py — runtime状态备份保留测试
        ├── test_dynamic_runtime_state_store_repair_cli.py — runtime状态修复CLI测试
        ├── test_dynamic_subscription_endpoint_adjustment.py — 动态订阅局部调整测试
        ├── test_dynamic_runtime_state_recovery.py — 动态runtime恢复测试
        ├── test_field_capacity_cli.py  — 现场容量 CLI 测试
        ├── test_field_probe_cli.py     — 现场探测 CLI 测试
        ├── test_field_profile_cli.py   — 现场画像 CLI 测试
        ├── test_field_provider.py      — 字段提供者测试
        ├── test_iec61850_lightweight_semantics.py  — IEC 61850 轻量语义
        ├── test_native_cmd_runner_preflight.py  — NativeCmdCapacityRunner 预检测试（7 tests）
        ├── test_native_cmd_timeout.py  — Native 命令超时单测（3 tests）
        ├── test_native_process_protocol.py  — Native 进程协议测试
        ├── test_native_runners_availability.py  — Native 运行器可用性
        ├── test_opcua_access_adapter.py  — OPC UA 接入适配器测试
    │   ├── test_modbus_client_runner_write_protocol.py  — Modbus TCP 写入协议测试
        ├── test_iec61850_mms_client_runner_write_protocol.py  — IEC 61850 MMS 写入协议测试
        ├── test_iec61850_goose_sv_streaming_e2e.py  — GOOSE/SV 流式 E2E 条件测试
        ├── test_iec61850_l2_native_runner_failure_modes.py  — L2 native失败模式测试
        ├── test_iec61850_production_capacity_profile_gate.py  — IEC 61850 capacity/profile 门禁测试
        ├── test_iec61850_report_runner_protocol.py  — IEC 61850 Report 运行器协议测试
        ├── test_iec61850_report_capacity_profile_gate.py  — IEC 61850 Report 生产门禁验收测试
        ├── test_open62541_client_runner_write_protocol.py  — OPC UA 写入协议测试
        ├── test_open62541_serial_polling_runner.py  — OPC UA 串行轮询测试
        ├── test_open62541_subscription_runner.py    — OPC UA 订阅测试
        ├── test_polling_metrics.py     — 轮询指标测试
        ├── test_port_allocator.py      — 端口分配器测试
        ├── test_profile_service.py     — 画像服务测试
        ├── test_protocol_matrix.py     — 协议矩阵测试
        ├── test_protocol_registry.py   — 协议注册表测试
        ├── test_protocol_service_capabilities.py  — 协议服务能力
        ├── test_source_lab_final_protocol_matrix.py  — 最终协议矩阵门禁
        ├── test_protocol_production_readiness_gate.py  — 协议生产准入门禁测试
        ├── test_modbus_tcp_production_capacity_profile_gate.py  — Modbus TCP capacity/profile 门禁测试
        ├── test_protocol_simulator_factory.py  — 协议模拟器工厂
	        ├── test_server_simulator_facade_contract.py  — ServerSimulatorFacade 契约测试
	        ├── test_server_simulator_facade_real_protocol_smoke.py  — 真实协议 smoke 测试
	        ├── test_server_simulator_facade_capacity_profile_e2e.py  — capacity/profile E2E CI 验收
	        ├── test_server_simulator_factory.py  — ServerSimulatorFacade 工厂测试
        ├── test_subscribe_capacity_entrypoint.py  — 订阅容量入口
        ├── test_subscribe_capacity_reporter.py    — 订阅容量报告
        ├── test_subscribe_scan.py      — 订阅扫描测试
        ├── test_subscribe_update_policy.py  — 订阅更新策略
        └── test_subscription_metrics.py     — 订阅指标测试
```

## AI 配置 `ai_shared/`

```text
ai_shared/
├── adr/                               — 架构决策记录
│   ├── ADR索引.md                                 — ADR 索引
│   ├── 0000-template.md                           — ADR 模板
│   ├── ADR-20260523-001-source-lab-server-client-ingest-boundary.md  — source_lab/shared/source/ingest 三层边界
│   ├── ADR-20260523-002-source-lab-task-facade-boundary.md           — source_lab 是 Task Facade 不是 Protocol Client Facade
│   ├── ADR-20260523-003-source-production-client-and-write-port-boundary.md — production client 与 write port 边界
│   ├── ADR-20260524-004-source-protocol-production-readiness-gate.md       — 生产协议准入与 capacity/profile 门禁
│   ├── ADR-20260524-005-cache-to-message-queue-publish-use-case.md         — 缓存快照发布用例边界
│   ├── ADR-20260524-006-source-lab-protocol-directory-consolidation.md     — source_lab 协议目录统一治理
│   ├── ADR-20260524-007-iec61850-mms-production-read-write-round1.md      — IEC 61850 MMS 生产读写第一闭环
│   ├── ADR-20260524-008-iec61850-report-subscription-boundary.md          — IEC 61850 Report 订阅采集第一闭环
│   └── ADR-20260524-009-source-lab-server-simulator-facade.md             — source_lab 统一模拟器 facade 契约
├── agent_config/                      — AI Agent 共享配置规范与 hook
│   ├── hooks/                         — 共享 hook 脚本
│   │   ├── block-dangerous-bash.py   — 危险命令拦截 hook
│   │   ├── docstring-cn-gate.py      — 中文 docstring 门禁 hook
│   │   └── no-source-lab-import-gate.sh — source_lab 导入门禁
│   │   ├── comment-doc-gate.py        — 注释文档门禁 hook
│   ├── skills/                        — 规范源 skill 定义（10 个 skill 规范，SKILL.md 子目录格式）
├── templates/                         — 模板文件
│   └── coding_agent_prompt_template.txt — Coding Agent prompt 模板
├── memory/                            — 长期记忆
│   ├── project_tree.md                — 本文件（目录树）
│   ├── Whale项目说明.md                — 项目背景、长期边界、工程原则
│   ├── Whale_REQ_README.md           — 需求文档规范说明（按模块拆分原则）
│   ├── Whale_REQ_Project.md          — 项目层面需求说明
│   ├── Whale_REQ_Ingest.md           — 采集模块需求说明
│   ├── Whale_REQ_SourceLab.md        — source_lab 需求说明
│   ├── Whale_REQ_SharedSource.md     — 共享源层需求说明
│   ├── Whale_REQ_Processing.md       — 数据处理模块需求说明
│   ├── Whale_REQ_Aggregation.md      — 聚合模块需求说明
│   ├── Whale_REQ_Storage.md          — 存储模块需求说明
│   ├── Whale_REQ_MessagePipeline.md  — 消息管道需求说明
│   ├── Whale_REQ_BatchLayer.md       — 批处理层需求说明
│   ├── Whale_REQ_SpeedLayer.md       — 速度层需求说明
│   └── Whale_REQ_Crosscutting.md     — 横切关注点需求说明
├── prompts/                           — prompt 模板（当前空）
├── reports/                           — agent 反馈与验收归档
│   ├── ingest_source_lab_arch_security_audit_review_round1.md — 架构安全审计审查报告 Round 1
│   ├── ingest_source_lab_arch_security_audit_review_round2_fix_closure.md — 架构安全审计修复收口报告 Round 2
│   ├── four_rounds_engineering_baseline_closure_report.md — 四轮收口自查与工程基线固化报告
│   ├── cache_to_message_queue_use_case_round4_report.md   — 缓存快照发布用例报告（Round 4）
│   ├── source_protocol_readiness_gate_round3_report.md    — 协议准入矩阵治理报告（Round 3）
│   ├── source_modbus_tcp_production_read_write_report.md  — Modbus TCP 生产读写报告（Round 2）
│   ├── source_write_opcua_round1_of_4_validation_report.md — OPC UA 写闭环验证报告（Round 1）
│   ├── source_write_opcua_first_slice_report.md           — OPC UA 写首切片报告
│   ├── source_lab_and_cache_to_kafka_reading_report.md    — source_lab 与 Kafka 预读报告
│   ├── source_lab_facade_pattern_probe_report.md          — source_lab Facade 模式探查报告
│   ├── source_lab_server_client_ingest_boundary_report.md — 三层边界探查报告
│   ├── iec61850_mms_production_read_write_round1_report.md — IEC 61850 MMS 生产读写第一闭环报告
│   ├── iec61850_report_subscription_round1_report.md — IEC 61850 Report 订阅第一闭环报告
│   ├── iec61850_report_subscription_round2_report.md — IEC 61850 Report 订阅采集 Round 2 实施报告
│   ├── iec61850_report_subscription_stage_closure_report.md — IEC 61850 Report 订阅采集阶段收口报告
│   ├── source_lab_server_simulator_facade_round1_report.md — source_lab ServerSimulatorFacade Round 1
│   ├── source_lab_server_simulator_facade_round2_report.md — source_lab ServerSimulatorFacade Round 2
│   ├── source_lab_server_simulator_facade_round4_ci_e2e_validation_report.md — source_lab ServerSimulatorFacade Round 4 CI E2E 验收
│   ├── source_lab_server_simulator_facade_capacity_profile_multi_protocol_closure_report.md — capacity/profile 多协议运行闭环
│   ├── source_lab_server_simulator_facade_round5_3_mqtt_http_rest_opcua_subscribe_and_template_governance_report.md — Round 5-3 协议闭环与模板治理
│   ├── source_lab_round5_3_followup_adr_index_and_template_governance_closure_report.md — Round 5-3 治理收口补丁报告
│   ├── source_lab_round5_4_iec61850_goose_sv_event_sample_closure_report.md — Round 5-4 GOOSE/SV 收口报告
│   ├── source_lab_round5_5_final_protocol_gate_and_goose_sv_ci_validation_report.md — Round 5-5 最终门禁报告
│   ├── source_lab_dynamic_endpoint_adjustment_probe_report.md — source_lab 动态局部调整探查报告
│   ├── source_lab_dynamic_endpoint_runtime_round1_report.md — source_lab动态runtime第1轮报告
│   ├── source_lab_dynamic_endpoint_runtime_round2_report.md — source_lab动态runtime第2轮报告
│   ├── source_lab_dynamic_endpoint_runtime_round3_final_closure_report.md — source_lab动态runtime第3轮最终收口报告
│   ├── source_lab_dynamic_endpoint_runtime_permission_and_state_store_closure_report.md — source_lab动态runtime第4轮归档
│   ├── source_lab_goose_sv_dynamic_raw_socket_gate_report.md — GOOSE/SV raw-socket门禁报告
│   ├── source_lab_goose_sv_dynamic_raw_socket_gate_20260526.log — GOOSE/SV raw-socket门禁日志
│   ├── source_lab_goose_sv_dynamic_raw_socket_gate_after_setcap_report.md — GOOSE/SV setcap后门禁报告
│   ├── ingest_runtime_scheduler_crud_multinode_round1_report.md — ingest第1轮骨架实施报告
│   ├── source_lab_goose_sv_dynamic_raw_socket_gate_after_setcap_20260526.log — GOOSE/SV setcap后lo门禁日志
│   ├── source_lab_goose_sv_dynamic_raw_socket_gate_after_setcap_20260526_eth0.log — GOOSE/SV setcap后eth0门禁日志
	│   ├── ingest_source_lab_arch_security_audit_review_round1.md — 架构安全审计审查报告 Round 1
	│   ├── ingest_source_lab_arch_security_audit_review_round2_fix_closure.md — 架构安全审计修复收口报告 Round 2
	│   ├── ingest_source_lab_remaining_risks_quality_gate_round3.md — 剩余风险与质量门禁报告 Round 3
	│   ├── ingest_source_lab_docstring_violation_inventory_round4.md — docstring 违规清单 Round 4
	│   ├── ingest_source_lab_real_chain_docstring_quality_round4.md — 真实链路/docstring/质量门禁报告 Round 4
	│   ├── ingest_source_lab_docstring_violation_inventory_round5.md — docstring 违规清单 Round 5
	│   ├── ingest_source_lab_round5_docstring_and_remaining_risks.md — Round 5 docstring 治理与剩余风险收口报告
	│   ├── ingest_source_lab_docstring_violation_inventory_round6.md — docstring 违规清单 Round 6
	│   ├── ingest_source_lab_docstring_true_closure_round6.md — Round 6 docstring 治理与 remaining inventory 报告
	│   ├── ingest_source_lab_type_docstring_lint_inventory_round7.md — Round 7 类型/docstring/lint 治理清单
	│   ├── ingest_source_lab_mypy_inventory_round8.md — Round 8 mypy 基线与剩余类型债清单
	│   ├── ingest_source_lab_mypy_closure_round8.md — Round 8 mypy 治理验证与未收口归档
	│   ├── ingest_source_lab_module_ready_requirements_and_status_round10.md — Round 10 模块准入与需求边界核验报告
	│   ├── ingest_external_dependency_readiness_matrix_round11.md — Round 11 ingest 外部依赖准入矩阵
	│   ├── ingest_module_deployment_topology_port_matrix_round11.md — Round 11 ingest 部署拓扑/端口/通信矩阵
	│   ├── ingest_source_lab_module_ready_blocker_closure_round11.md — Round 11 ingest/source_lab 阻塞项修复与状态同步
	│   ├── ingest_write_readback_field_validation_plan_round11.md — Round 11 ingest 写入 readback 现场验证计划
	│   ├── source_lab_mypy_debt_plan_round12.md — Round 12 source_lab mypy 分阶段治理计划
	│   ├── shared_source_production_runner_artifact_validation_round12.md — Round 12 shared_source runner artifact 契约验证报告
	│   ├── ingest_source_lab_production_ready_blocker_closure_round12.md — Round 12 ingest/source_lab 阻塞项收口与 production-ready 判定
	│   ├── source_lab_mypy_phase1_closure_round13.md — Round 13 source_lab mypy 第一阶段治理收口报告
	│   ├── ingest_crosscutting_integration_matrix_round13.md — Round 13 ingest 横切能力接入矩阵报告
	│   ├── ingest_source_lab_round13_production_evidence_closure.md — Round 13 生产准入剩余证据闭环报告
	│   ├── source_lab_mypy_phase2_closure_round14.md — Round 14 source_lab mypy 第二阶段治理收口报告
	│   ├── ingest_source_lab_round14_pg_readyz_mypy_closure.md — Round 14 PG E2E/readyz/mypy 阻塞项收口报告
	│   ├── ingest_source_lab_round15_pg_fencing_and_tests_mypy_closure.md — Round 15 PG fencing 修复与全量 mypy 收口报告
	│   ├── ingest_source_lab_round16_field_readback_l5_readiness.md — Round 16 field readback L5 现场验证包固化与生产准入判定
	│   ├── ingest_field_readback_l5_evidence_template.md — L5 现场验证证据收集模板（全字段）
	│   ├── source_lab_tests_mypy_closure_round15.md — Round 15 source_lab tests mypy 0 errors 治理终点报告
	│   └── requirements_trace_update_20260525_source_lab_ingest_round1.md — 需求核验 Round 1 报告
├── rules/                             — 公共规则
    ├── routing.md                     — 规则路由
    ├── coding.md                      — 编码规范
    ├── testing.md                     — 测试规范
    ├── documentation.md               — 文档规范
    ├── reporting.md                   — 反馈规范
    ├── validation-routing.md          — 验证路由
    ├── python-docstring-cn.md         — Python 中文 docstring 规范
    └── quality-gate.md                — 代码质量门禁规则
```

## 文档 `docs/`

```text
docs/
├── GIT.md                             — Git 工作流说明
├── opcua_iec61850_guide.md            — OPC UA / IEC 61850 协议指南
├── 代码质量与注释.md                   — 代码质量规范与注释要求
├── 工程管理.md                         — 工程管理流程说明
└── 测试策略.md                         — 测试策略说明
```

## 脚本 `scripts/`

```text
scripts/
├── cleanup_root_logs.sh               — 清理根目录日志文件
├── run_ingest_dev.sh                  — 启动 ingest 开发环境
├── run_ingest_runtime_compose_smoke.sh — ingest compose运行态烟测
├── run_ingest_compose_readyz_e2e.sh   — compose readyz 8组件聚合 E2E 脚本
├── run_ingest_write_readback_smoke.sh — 三协议 simulator/native write-readback smoke（L3，CLI 加固含--dry-run/--protocol/--confirm）
├── run_ingest_pg_lease_fault_injection.sh — PostgreSQL/readyz prodlike fault injection 入口
├── run_pg_migration_matrix.sh        — PostgreSQL迁移矩阵自动化脚本
├── ci_ingest_runtime_gate.sh         — CI门禁脚本（7个门禁组）
├── run_ingest_bundle_one_way_flow_smoke.sh — Bundle单向流smoke
├── run_ingest_prodlike_performance_profile.sh — 性能profile smoke
├── run_source_lab_raw_socket_dynamic_gate.sh — raw socket动态门禁回归
├── run_source_lab_l2_standalone_gate.sh — GOOSE/SV standalone门禁
├── validate_shared_source_production_runner.sh — shared_source runner 路径解析契约验证
├── test_ingest_write_readback_smoke_contract.sh — write-readback smoke 入口 CLI 契约自检（L2）
└── source_lab_l2_test_env.sh          — 可控L2 veth环境搭建
```

## AI 工具配置

```text
.claude/                               — Claude Code 配置
├── settings.json                      — Claude Code 全局设置
├── settings.local.json                — 本地覆盖设置
├── agents/                            — Claude Code 子代理定义
│   ├── code-implementer.md           — 编码实现子代理
│   ├── project-steward.md            — 文档与目录树子代理
│   └── test-validator.md             — 独立验证子代理
└── skills/                            — Claude Code 技能
    ├── adr-upsert/SKILL.md            — 架构决策记录管理
    ├── changed-files-gate/SKILL.md    — 变更范围门禁
    ├── code-quality-gate/SKILL.md     — 代码质量门禁
    ├── commit-message/SKILL.md        — 提交信息生成
    ├── heavy-regression/SKILL.md      — 重回归测试
    ├── project-tree-reset/SKILL.md    — 目录树全量重建
    ├── project-tree-update/SKILL.md   — 目录树增量更新
    ├── requirement-trace/SKILL.md     — 需求跟踪表更新
    └── rule-update/SKILL.md           — 公共规则更新

.agents/                               — Codex agent 配置（指向 .claude/skills）
└── skills                             — Codex 技能路径指向 .claude/skills
```

## ADR `ai_shared/adr/`

```text
ai_shared/adr/
├── ADR-20260523-001-source-lab-server-client-ingest-boundary.md — SourceLab / shared_source / ingest 边界
├── ADR-20260523-002-source-lab-task-facade-boundary.md — tool task facade 边界
├── ADR-20260523-003-source-production-client-and-write-port-boundary.md — production client / write port 边界
├── ADR-20260524-004-source-protocol-production-readiness-gate.md — 协议 production readiness 门禁
├── ADR-20260524-005-cache-to-message-queue-publish-use-case.md — cache->message 发布职责
├── ADR-20260524-006-source-lab-protocol-directory-consolidation.md — source_lab 目录整理
├── ADR-20260524-007-iec61850-mms-production-read-write-round1.md — IEC 61850 MMS 生产读写
├── ADR-20260524-008-iec61850-report-subscription-boundary.md — IEC 61850 Report 订阅边界
├── ADR-20260524-009-source-lab-server-simulator-facade.md — simulator facade 架构
└── ADR-20260530-010-shared-source-production-runner-artifact-boundary.md — shared_source production runner artifact 与 source_lab build 边界
```

## 第三方库 `third_party/`

```text
third_party/                           — 第三方 C 协议栈源码与预编译库
├── setup_env.sh                       — 第三方库环境安装脚本
├── install/                           — 预编译头文件和库
│   ├── include/
│   │   ├── lib60870/                  — lib60870 头文件
│   │   └── libiec61850/               — libiec61850 头文件
│   ├── lib/                           — 静态/动态库
│   └── share/                         — cmake/pkgconfig 共享数据
├── lib60870/                          — lib60870 源码（IEC 60870-5-101/104）
├── libiec61850/                       — libiec61850 源码（IEC 61850 MMS/GOOSE/SV）
└── open62541/                         — open62541 源码（OPC UA 协议栈）
```
