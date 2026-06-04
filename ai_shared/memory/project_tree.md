# Whale 项目目录树

> 能源数据统一平台（风光储电场数据接入底座）
> 最后更新: 2026-06-04 (Round 3 P5 外部依赖环境拉起收口: docker-compose.p5.yml 最小 P5 编排; start/stop/diagnose 脚本覆盖 PostgreSQL/Redis/Kafka/MinIO/TDengine 5 依赖; .env.p5.example 环境变量模板; regression 脚本 5 测试组逐项输出 + SUMMARY 行; ADR-015 v5 补录)

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
├── pyproject.toml                   — 项目元数据、依赖与 ruff/mypy/pytest 工具配置（含 unit/smoke/integration/e2e/l5/external/prodlike/environment_pending/load/stress/slow/requires_raw_socket/requires_cap_net_raw/requires_root_or_cap_net_raw 共 14 个 markers）
├── requirements.txt                 — Python 依赖声明
├── alembic/                         — ingest运行库迁移
│   ├── env.py                       — Alembic 环境配置
│   ├── script.py.mako               — 迁移脚本模板
│   └── versions/                    — 迁移版本
│       ├── 20260527_000001_ingest_runtime_initial.py
│       ├── 20260527_000002_add_audit_index_and_job_stagger.py
│       ├── 20260527_000003_add_idempotency_record.py
│       └── 20260527_000004_add_model_asset_tables.py
├── docker-compose.ingest-dev.yaml   — ingest 开发环境 Docker 编排
├── docker-compose.ingest-prodlike.yaml — ingest prodlike 环境 Docker 编排（PostgreSQL + Redis + Kafka）
├── docker-compose.whale-l5.yaml     — P5 外部依赖 5-service Docker 环境（Kafka/PG/Redis/MinIO/TDengine）
├── docker-compose.p5.yml            — 最小 P5 本地编排（PG+Redis+Kafka/MinIO+TDengine+taosAdapter）
├── .flake8                          — flake8 代码检查配置
├── .gitignore                       — Git 忽略规则
├── .env.ingest.example              — ingest 环境变量模板
├── .env.whale.field.example         — Whale 现场部署完整环境变量模板
├── .env.p5.example                   — P5 环境变量模板（无真实密钥）
├── .vscode/settings.json            — VSCode 编辑器配置
├── .vscode/claude-wrapper.sh        — VSCode Claude CLI 包装脚本
├── .data/                            — 运行时数据（SQLite 开发/测试 DB，gitignore）
├── config/                          — 运行时配置
│   ├── ingest/                      — ingest 配置（access_policy/performance/audit/endurance/security_partition）
│   │   ├── access_policy.external.example.yaml
│   │   ├── access_policy.prodlike.yaml
│   │   ├── audit_sink.external.example.yaml
│   │   ├── endurance.prodlike.yaml
│   │   ├── performance.prodlike.yaml
│   │   └── security_partition.example.yaml
│   └── whale/                       — Whale 现场部署配置模板（P5 准生产依赖验证期状态注释，MISSING_ENVIRONMENT 标记）
│       ├── message_pipeline.kafka.example.yaml
│       ├── message_pipeline.pulsar.example.yaml
│       ├── speed_layer.writers.example.yaml
│       ├── storage.raw_archive.example.yaml
│       ├── storage.serving_cache.example.yaml
│       └── storage.tdengine.example.yaml
│
├── src/                             — 主源码根目录
├── tests/                           — 项目级测试根目录
├── tools/                           — 工具包根目录
├── ai_shared/                       — AI 配置、规则与记忆
├── docs/                            — 项目文档
├── scripts/                         — 运维与开发脚本
├── deploy/                          — Whale/Turtle/Octopus 部署配置
│   ├── whale/README.md              — Whale 现场部署说明（含环境准备/配置/一键预检/各层启动/故障恢复/安全分区，MISSING_ENVIRONMENT 标记）
│   ├── whale/ingest/README.md       — Whale Ingest 现场部署说明
│   ├── whale/message_pipeline/README.md — Whale Message Pipeline 现场部署说明（Kafka P5 准生产依赖验证期验证通过，Pulsar MISSING_ENVIRONMENT）
│   ├── whale/speed_layer/README.md  — Whale Speed Layer 现场部署说明（InMemory 生产就绪，Flink MISSING_ENVIRONMENT）
│   ├── whale/storage/README.md      — Whale Storage 现场部署说明（TDengine/S3/Redis P5 准生产依赖验证期验证通过，HDFS MISSING_ENVIRONMENT）
│   ├── turtle/README.md             — Turtle 部署说明
│   └── octopus/README.md            — Octopus 部署说明
├── .claude/                         — Claude Code 配置与技能
├── .agents/                         — Codex agent 配置与技能（软链至 .claude/skills）
├── .codex/                          — OpenAI Codex 适配配置
└── third_party/                     — 第三方 C 协议栈源码与预编译库
```

## 主源码 `src/`

### `src/whale/` — 数据平台核心

```text
src/whale/
├── __init__.py                      — 包入口
│
├── ingest/                          — 数据采集核心（六边形架构）
│   ├── __init__.py                  — 包入口（含 file_ingest 导出）
│   ├── config.py                    — 采集配置定义与加载
│   ├── composition.py               — 依赖注入组合根（采集/写入/快照发布）
│   ├── message_pipeline.py          — 消息管道编排
│   ├── whale.db                     — SQLite 开发/测试数据库
│   │
│   ├── entities/                    — 领域实体
│   │   ├── __init__.py
│   │   ├── node_state.py            — 节点状态实体
│   │   └── source_health_state.py   — 数据源健康状态实体
│   │
│   ├── usecases/                    — 用例层（业务逻辑）
│   │   ├── __init__.py              — 导出 SourceAcquisitionUseCase, StateSnapshotPublishUseCase
│   │   ├── source_acquisition_use_case.py  — 采集用例入口
│   │   ├── source_command_use_case.py  — 设备写入/控制命令用例入口
│   │   ├── state_snapshot_publish_use_case.py  — 缓存快照发布到消息队列用例
│   │   ├── dtos/                    — 数据传输对象
│   │   │   ├── __init__.py
│   │   │   ├── acquired_node_state.py
│   │   │   ├── source_acquisition_request.py
│   │   │   ├── source_acquisition_start_result.py
│   │   │   ├── source_connection_data.py
│   │   │   ├── source_write_request.py  — 写入请求 DTO
│   │   │   ├── source_write_result.py   — 写入结果 DTO
│   │   │   ├── state_publish_request.py  — 快照发布请求 DTO
│   │   │   └── state_publish_result.py   — 快照发布结果 DTO
│   │   └── roles/                   — 采集策略角色
│   │       ├── __init__.py
│   │       ├── polling_acquisition_role.py       — 轮询采集策略
│   │       └── subscription_acquisition_role.py  — 订阅采集策略
│   │
│   ├── ports/                       — 端口层（接口抽象）
│   │   ├── __init__.py
│   │   ├── audit.py                 — ingest审计sink端口
│   │   ├── diagnostics.py           — 诊断接口
│   │   ├── metrics.py               — 指标端口
│   │   ├── command/                 — 命令审计端口
│   │   │   ├── __init__.py
│   │   │   └── source_command_audit_port.py  — 写入命令审计端口
│   │   ├── message/                 — 消息发布端口
│   │   │   ├── __init__.py
│   │   │   └── message_publisher_port.py
│   │   ├── runtime/                 — 运行时配置端口
│   │   │   ├── __init__.py
│   │   │   ├── access_policy_port.py           — 访问策略端口
│   │   │   ├── source_runtime_config_port.py
│   │   │   └── write_lease_port.py  — 写入租约端口
│   │   ├── source/                  — 数据源采集端口
│   │   │   ├── __init__.py
│   │   │   ├── source_acquisition_definition_port.py  — 采集定义端口
│   │   │   ├── source_acquisition_port.py              — 采集端口
│   │   │   ├── source_acquisition_port_registry.py     — 端口注册表
│   │   │   ├── source_write_port.py                    — 设备写入端口
│   │   │   └── source_write_port_registry.py           — 写入端口注册表
│   │   └── state/                   — 状态缓存端口
│   │       ├── __init__.py
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
│   │   │   ├── __init__.py
│   │   │   ├── opcua_source_acquisition_definition_repository.py  — OPC UA 采集定义仓库
│   │   │   └── source_runtime_config_repository.py                — 运行时配置仓库
│   │   ├── message/                 — 消息发布适配器
│   │   │   ├── __init__.py
│   │   │   ├── kafka_message_publisher.py           — Kafka 发布器
│   │   │   ├── redis_streams_message_publisher.py   — Redis Streams 发布器
│   │   │   └── relational_outbox_message_publisher.py  — 关系库 outbox 发布器
│   │   ├── security/                — 安全策略适配器
│   │   │   ├── __init__.py          — 安全适配器导出
│   │   │   ├── external_access_policy.py  — 外部访问策略适配器
│   │   │   └── file_access_policy.py      — 文件访问策略适配器
│   │   ├── source/                  — 数据源采集适配器
│   │   │   ├── __init__.py
│   │   │   ├── dispatch_source_acquisition_adapter.py  — 多协议调度采集适配器
│   │   │   ├── http_rest_source_acquisition_adapter.py  — HTTP REST 采集适配器
│   │   │   ├── iec101_source_acquisition_adapter.py     — IEC101 串行采集适配器
│   │   │   ├── iec104_source_acquisition_adapter.py   — IEC104 采集适配器
│   │   │   ├── iec104_source_write_adapter.py          — IEC104 写入适配器
│   │   │   ├── modbus_source_acquisition_adapter.py   — Modbus TCP 采集适配器
│   │   │   ├── modbus_source_write_adapter.py         — Modbus TCP 写入适配器
│   │   │   ├── modbus_rtu_source_acquisition_adapter.py — Modbus RTU 串行采集适配器
│   │   │   ├── mqtt_source_acquisition_adapter.py     — MQTT 采集适配器
│   │   │   ├── opcua_source_acquisition_adapter.py           — OPC UA 采集适配器
│   │   │   ├── opcua_source_write_adapter.py                 — OPC UA 写入适配器
│   │   │   ├── iec61850_source_acquisition_adapter.py  — IEC 61850 MMS 采集适配器
│   │   │   ├── iec61850_source_write_adapter.py        — IEC 61850 MMS 写入适配器
│   │   │   ├── iec61850_report_source_acquisition_adapter.py  — IEC 61850 Report 订阅采集适配器
│   │   │   ├── static_source_acquisition_port_registry.py    — 静态采集端口注册表
│   │   │   └── static_source_write_port_registry.py          — 静态写入端口注册表
│   │   ├── observability/           — 观测与审计输出
│   │   │   ├── __init__.py          — 观测sink导出
│   │   │   └── file_sinks.py        — JSONL metrics/audit sink
│   │   └── state/                   — 状态缓存适配器
│   │       ├── __init__.py
│   │       └── redis_source_state_cache.py  — Redis 状态缓存
│   │
│   ├── api/                         — ingest Web API
│   │   ├── __init__.py              — API包导出
│   │   ├── app.py                   — FastAPI app factory
│   │   ├── audit_middleware.py      — API审计中间件
│   │   ├── errors.py                — 稳定错误模型
│   │   ├── idempotency.py           — 幂等性中间件
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
│   │   ├── acquisition_mode.py      — 采集模式枚举
│   │   ├── cli.py                   — ingest多入口CLI
│   │   ├── entrypoint.py            — ingest运行入口
│   │   ├── fencing.py               — fencing token服务
│   │   ├── job_status.py            — 作业状态定义
│   │   ├── job_assignment.py        — 作业归属服务
│   │   ├── lease.py                 — 作业租约服务
│   │   ├── message_pipeline_settings.py — 管道参数设置
│   │   ├── modes.py                 — runtime模式枚举
│   │   ├── node_runtime.py          — 节点心跳服务
│   │   ├── scheduler.py             — 调度器主逻辑
│   │   ├── scheduler_factory.py     — 调度器工厂
│   │   ├── scheduler_job.py         — 调度作业封装
│   │   ├── scheduler_settings.py    — 调度器参数
│   │   ├── write_lease.py           — 写入租约服务
│   │   ├── worker_runtime.py        — APScheduler WorkerRuntime
│   │   └── handlers.py              — WorkerRuntime 采集 job handler
│   │
│   ├── decorators/                   — 装饰器
│   │   ├── __init__.py
│   │   ├── source_acquisition.py     — 采集流程装饰器
│   │   ├── source_write.py           — 写入授权装饰器
│   │   └── state_cache.py            — 状态缓存装饰器
│   │
│   ├── framework/persistence/        — 持久化框架
│   │   ├── __init__.py
│   │   ├── base.py                   — ORM 声明基类
│   │   ├── init_db.py                — 数据库初始化
│   │   ├── runtime_db.py             — runtime DB初始化与探针
│   │   ├── session.py                — 会话管理
│   │   └── orm/__init__.py           — ORM 模型包（空，模型在 shared）
│   │
│   ├── file_ingest/                  — 文件接入子系统（文件完成检测、解码、波形写入）
│   │   ├── __init__.py               — 包入口，导出 FileIngestService/FaultRecordBinary 等
│   │   ├── models.py                 — FaultRecordBinary/SourceFile/FileIngestJob 领域模型
│   │   ├── detector.py               — FileCompletionDetector 文件完成检测（inotify+polling）
│   │   ├── decoder.py                — FaultRecordBinaryDecoder 二进制解码（magic+version+header+values float32 LE）
│   │   ├── repository.py             — FileIngestJobRepository 任务持久化（SQLite/SQLAlchemy）
│   │   └── service.py                — FileIngestService 编排：detect->raw_archive->decode->waveform sink->fault_event
│   │
│   └── docs/                         — ingest 设计文档
│       ├── DECISIONS.md              — 架构决策记录
│       └── 设计说明书.md              — 模块设计说明书
│
├── message_pipeline/                 — 消息管道抽象与适配
│   ├── __init__.py                   — 包入口
│   ├── model.py                      — Envelope/TopicSpec/PartitionKey/MessageOffset/ReplayRequest
│   ├── ports.py                      — Source/Sink/SchemaRegistry/DLQ/Replay 端口接口
│   └── adapters/                     — 消息管道适配器
│       ├── __init__.py               — 适配器导出
│       ├── in_memory.py              — InMemoryMessageBus/InMemoryDeadLetterSink/InMemorySchemaRegistry
│       ├── kafka.py                  — KafkaSourceAdapter (REAL consumer.poll()) + KafkaSinkAdapter (REAL producer)
│       └── pulsar.py                 — PulsarSourceAdapter/PulsarSinkAdapter (contract-only, environment-pending)
│
├── speed_layer/                      — 速度层消费与运行时
│   ├── __init__.py                   — 包入口（含 Round A preprocessing 导出）
│   ├── light_processor.py            — SP-FR-004 实时轻处理管线（EnvelopeValidator/MessageDeduplicator/QualityCodePassThrough/OutOfOrderGuard/LightProcessingPipeline）
│   ├── writers.py                    — RawArchiveWriter/RawIndexWriter/StandardizedWriter/ServingCacheUpdater
│   ├── runner.py                     — SpeedLayerWiring (with_* builders, with_light_processor, build) + _LightFilteredSource + LocalPipelineRunner + FlinkPipelineAdapter
│   ├── metrics.py                    — MetricsCollectorPort/InMemoryMetricsCollector
│   └── preprocessing/                — Round A 固定 10 阶段预处理 Pipeline + OperatorRegistry
│       ├── __init__.py               — 预处理包入口，导出 6 DTO、11 operator、PreprocessingPipeline、OperatorRegistry
│       ├── models.py                 — 6 运行期 DTO（DecodedSignal/ResolvedSignal/StandardizedPointValue/StateViewRecord 等）
│       ├── registry.py               — OperatorRegistry 按 payload_type/protocol/vendor/descriptor_key/default 条件加权选择
│       ├── operators.py              — 11 个基础 operator（PayloadClassifier/Decoder/Resolver/Normalizer/Evaluator/Dedup/Writer/StateViewUpdater）
│       └── pipeline.py               — PreprocessingPipeline 固定 10 阶段编排（STAGE_ORDER 1-10），decode-before-resolve
│
├── storage/                          — 存储层（三层分层 + warehouse/mart/cache）
│   ├── __init__.py                   — 包入口（含 waveform 导出）
│   ├── raw_archive.py                — 压缩文件归档（S3RawArchiveSink boto3 +gzip JSONL + WHALE_S3_* env var + LocalCompressedArchiveSink + S3ManifestRepository）
│   ├── raw_index.py                  — TdengineRawIndexSink (INSERT STABLE TAGS SQL + REST API) + MemoryRawIndexSink
│   ├── standardized.py               — TdengineStandardizedSink (全量 10 required fields + readback + REST API) + MemoryStandardizedSink
│   ├── warehouse.py                  — WarehouseSinkPort/InMemoryWarehouseSink（端口+stub）
│   ├── mart.py                       — MartSinkPort/InMemoryMartSink（端口+stub）
│   ├── serving_cache.py              — RedisServingCache (redis-py SETEX/GET/DEL/PING/TTL) + InMemoryServingCache
│   ├── waveform.py                   — StandardizedWaveformSinkPort / InMemory / Tdengine real REST API adapter + WHALE_TDENGINE_REST_PATH + _check_rest_api_alive()
│   └── simulation_result.py          — SimulationResultTimeSeriesSinkPort / InMemory / TDengine real REST API adapter + WHALE_TDENGINE_REST_PATH + _check_rest_api_alive()
│
├── processing/                       — 数据处理（骨架，依赖缺失无法运行）
│   ├── __init__.py
│   ├── cleaner.py                    — 数据清洗（骨架，whale.models 不存在）
│   └── normalizer.py                 — 数据标准化（骨架，whale.models 不存在）
│
├── aggregation/                      — 数据聚合（骨架，依赖缺失无法运行）
│   ├── __init__.py
│   ├── ads.py                        — ADS 聚合（骨架，whale.models 不存在）
│   ├── periodic.py                   — 周期性聚合（骨架，whale.models 不存在）
│   └── realtime.py                   — 实时聚合（骨架，whale.models 不存在）
│
├── model_asset/                       — 仿真资产元数据管理与导入
│   ├── __init__.py                    — 包入口，导出 DTO/detector/archive/repository/service
│   ├── models.py                      — DTO（ModelAssetImportRequest/SimulationFileType/SimulationImportManifest 等）
│   ├── detector.py                    — SimulationFileTypeDetector 仿真文件类型检测
│   ├── archive.py                     — SimulationArchiveService 文件归档（复用 storage.raw_archive）
│   ├── repository.py                  — ModelAssetRepository 四表持久化（PostgreSQL）
│   └── service.py                     — ModelAssetImportService 导入编排（detect->archive->repository）
│
└── shared/                           — 共享层（跨模块通用能力）
    ├── __init__.py                   — 包入口，Shared helpers for Whale
    │
    ├── enums/                        — 共享枚举
    │   ├── __init__.py
    │   └── quality.py                — 数据质量枚举
    │
    ├── utils/                        — 工具函数
    │   └── time.py                   — 时间工具函数（ensure_utc 等）
    │
    ├── persistence/                  — 共享持久化
    │   ├── __init__.py
    │   ├── base.py                   — 持久化基类
    │   ├── init_db.py                — 数据库初始化
    │   ├── session.py                — 会话管理
    │   ├── orm/                      — ORM 模型
    │   │   ├── __init__.py
    │   │   ├── acquisition.py        — 采集任务模型
    │   │   ├── asset.py              — 资产模型
    │   │   ├── ingest_runtime.py     — ingest运行库模型
    │   │   ├── ingest_diagnostics.py — 采集诊断模型
    │   │   ├── model_asset.py       — 仿真资产四表ORM（ModelAsset/SimulationCase/SimulationResult/SimulationArtifact）
    │   │   ├── organization.py       — 组织模型
    │   │   ├── scada_ingest.py       — SCADA 采集模型
    │   │   └── scada_protocol_param.py  — SCADA 协议参数模型
    │   └── template/                 — 模板数据
    │       ├── __init__.py
    │       ├── gbt_30966_fields.py         — GB/T 30966 字段定义
    │       ├── protocol_param_data.py      — 16 组协议服务参数模板定义
    │       ├── protocol_view_defs.py       — 协议参数展平只读视图定义
    │       ├── sample_data.py              — 13 类端点/16组服务样例初始化
    │       └── OPCUA_client_connections.yaml  — OPC UA 连接配置
    │
    ├── source/                       — 数据源访问抽象
    │   ├── __init__.py               — 统一对外暴露 source 层接口和 reader
    │   ├── models.py                 — SourceConnectionProfile/NodeValueChange/Batch/SourceNodeInfo 等
    │   ├── ports.py                  — BrowsableSourcePort/ReadableSourcePort/SourceReaderPort/SubscribableSourcePort
    │   ├── runner_resolution.py      — shared_source production runner 路径解析与 dev fallback
    │   ├── access/                   — 可复用接入适配器
    │   │   ├── __init__.py
    │   │   ├── adapter.py            — SourceAccessAdapter 基类
    │   │   ├── model.py              — 端点/点位/Tick 数据模型
    │   │   └── opcua.py              — OPC UA 适配器实现
    │   ├── modbus/                   — Modbus TCP 读取器
    │   │   ├── __init__.py
    │   │   ├── reader.py             — ModbusSourceReader 外观
    │   │   └── backends/
    │   │       ├── __init__.py
    │   │       ├── base.py           — 后端基类与数据类型
    │   │       └── libmodbus_backend.py  — libmodbus C 子进程后端
    │   ├── opcua/                    — OPC UA 读取器
    │   │   ├── __init__.py
    │   │   ├── reader.py             — OpcUaSourceReader
    │   │   └── backends/
    │   │       ├── __init__.py
    │   │       ├── base.py           — 后端基类
    │   │       ├── factory.py        — 后端工厂
    │   │       └── open62541_backend.py  — open62541 C 后端
    │   ├── iec61850/                 — IEC 61850 MMS/Report 读取器
    │   │   ├── __init__.py
    │   │   ├── reader.py             — Iec61850MmsSourceReader 外观
    │   │   ├── report_reader.py      — Iec61850ReportSourceReader 外观
    │   │   └── backends/
    │   │       ├── __init__.py
    │   │       ├── base.py           — 后端基类与数据类型
    │   │       ├── libiec61850_backend.py  — libiec61850 C 子进程后端（MMS）
    │   │       ├── report_base.py    — Report 事件数据类型
    │   │       └── libiec61850_report_backend.py  — libiec61850 C 子进程后端（Report）
    │   ├── iec104/                   — IEC 104 读取器
    │   │   ├── __init__.py
    │   │   ├── reader.py             — Iec104SourceReader 外观
    │   │   └── backends/
    │   │       ├── __init__.py
    │   │       ├── base.py           — 后端基类与数据类型
    │   │       └── lib60870_backend.py — lib60870 C 子进程后端
    │   ├── http_rest/                — HTTP REST 读取器
    │   │   ├── __init__.py
    │   │   └── client.py             — HttpRestClientBackend（asyncio HTTP/1.1）
    │   ├── modbus_rtu/               — Modbus RTU 串行读取器
    │   │   ├── __init__.py           — 模块入口（python_lightweight_runner）
    │   │   ├── reader.py             — ModbusRtuSourceReader 外观
    │   │   └── backends/
    │   │       ├── __init__.py
    │   │       ├── base.py           — 后端基类与数据类型
    │   │       └── serial_backend.py — 真实串口后端（CRC16）
    │   ├── iec101/                   — IEC 101 串行读取器
    │   │   ├── __init__.py           — 模块入口（python_lightweight_runner）
    │   │   ├── reader.py             — Iec101SourceReader 外观
    │   │   └── backends/
    │   │       ├── __init__.py
    │   │       ├── base.py           — 后端基类与数据类型
    │   │       └── serial_backend.py — 真实串口后端（FT1.2+ASDU）
    │   ├── mqtt/                     — MQTT 读取器
    │   │   ├── __init__.py
    │   │   └── client.py             — MqttClientBackend（asyncio MQTT v3.1.1）
    │   └── scheduling/               — 调度工具
    │       ├── __init__.py
    │       ├── concurrency.py        — 并发控制
    │       ├── fixed_rate.py         — 固定速率执行器
    │       ├── polling.py            — 轮询调度
    │       └── stagger.py            — 错峰调度
```

### `src/platform_shared/` — 全系统公共基础库

```text
src/platform_shared/
├── __init__.py                                     — 包入口（无业务归属、无运行状态的基础能力）
│
├── crosscutting/                                   — 横切公共能力
│   ├── __init__.py                                 — 包入口
│   ├── debug/                                      — 调试与诊断
│   │   ├── __init__.py
│   │   ├── diagnostics.py                          — 诊断快照
│   │   ├── ring_buffer.py                          — 环形缓冲区
│   │   └── trace.py                                — 链路追踪
│   ├── observability/                              — 可观测性
│   │   ├── __init__.py
│   │   ├── audit.py                                — 审计日志
│   │   ├── logging.py                              — 结构化日志
│   │   └── metrics.py                              — 指标收集
│   ├── resilience/                                 — 韧性策略
│   │   ├── __init__.py
│   │   ├── backoff.py                              — 退避策略
│   │   ├── circuit_breaker.py                      — 熔断器
│   │   ├── deadline.py                             — 截止时间
│   │   ├── error_classifier.py                     — 错误分类
│   │   └── retry.py                                — 重试策略
│   └── context/                                    — 请求上下文（骨架）
│       └── __init__.py
├── contracts/                                      — 通用契约（骨架）
│   └── __init__.py
├── kernel/                                         — 基础运行时（骨架）
│   └── __init__.py
├── messaging/                                      — 消息基础模型（骨架）
│   └── __init__.py
└── security_primitives/                            — 安全基础工具
    ├── __init__.py
    └── masking.py                                  — SensitiveDataMasker 数据脱敏
```

### `src/turtle/` — 治理控制面

```text
src/turtle/
├── __init__.py                      — 包入口（全局治理、安全、合规、审计基础能力）
│
├── auth/                            — 认证授权
│   ├── __init__.py
│   ├── authorizer.py                — 授权器（AccessDecision）
│   ├── credential.py                — 凭证管理（CredentialRef）
│   ├── identity.py                  — 身份管理（Principal）
│   └── policy.py                    — 策略定义（AccessPolicyPort、Permission）
│
├── security/                        — 安全基础
│   ├── __init__.py
│   ├── certificate.py               — 证书管理（CertificateRef）
│   ├── model.py                     — 安全模型（CredentialRef、SecretRef）
│   ├── secret_provider.py           — 密钥提供（SecretProviderPort）
│   └── tls.py                       — TLS 配置（TlsConfig）
│
├── compliance/                      — 合规基础
│   ├── __init__.py
│   ├── audit_policy.py              — 审计策略（AuditEvent、AuditEventSinkPort）
│   ├── data_classification.py       — 数据分类（DataClassification）
│   └── retention.py                 — 数据保留策略（RetentionPolicy）
│
├── audit/                           — 审计治理（空壳）
│   └── __init__.py
├── policy/                          — 策略治理（空壳）
│   └── __init__.py
├── governance/                      — 治理框架（空壳）
│   └── __init__.py
├── risk/                            — 风险评估（空壳）
│   └── __init__.py
├── deployment_policy/               — 部署策略（空壳）
│   └── __init__.py
├── change_control/                  — 变更控制（空壳）
│   └── __init__.py
├── ports/                           — 端口定义（空壳）
│   └── __init__.py
├── adapters/                        — 适配器实现（空壳）
│   └── __init__.py
├── api/                             — API 端点（空壳）
│   └── __init__.py
├── runtime/                         — 运行时配置（空壳）
│   └── __init__.py
└── sdk/                             — 客户端 SDK（空壳）
    └── __init__.py
```

### `src/octopus/` — 运维执行面

```text
src/octopus/
├── __init__.py                      — 包入口（部署、监控、告警、诊断、自动化运维基础能力）
├── orchestration/                   — 运维流程编排（空壳）
│   └── __init__.py
├── deployment/                      — 部署管理（空壳）
│   └── __init__.py
├── monitoring/                      — 监控采集（空壳）
│   └── __init__.py
├── alerting/                        — 告警管理（空壳）
│   └── __init__.py
├── diagnostics/                     — 故障诊断（空壳）
│   └── __init__.py
├── automation/                      — 自动化运维（空壳）
│   └── __init__.py
├── rollback/                        — 回滚管理（空壳）
│   └── __init__.py
├── reports/                         — 运维报告（空壳）
│   └── __init__.py
├── adapters/                        — 外部系统适配器（空壳）
│   └── __init__.py
└── runtime/                         — 运行时配置（空壳）
    └── __init__.py
```

## 项目级测试 `tests/`

```text
tests/
├── __init__.py
├── conftest.py                       — 全局 pytest 夹具
├── TESTING.md                        — Whale 主平台测试指南（P1-P7 生命周期阶段、PASS/FAIL/NOT_RUN、边界说明）
│
├── unit/                             — P1 单元测试
│   ├── __init__.py
│   ├── test_config.py                — 配置解析测试
│   ├── test_fleet_update_selection.py   — 机群更新选择测试
│   ├── test_kafka_message_publisher.py  — Kafka 发布器测试
│   ├── test_message_pipeline_adapters.py  — message_pipeline 适配器单测（InMemory/DLQ/SchemaRegistry）
│   ├── test_message_pipeline_envelope.py  — message_pipeline Envelope/schema/model 单测
│   ├── test_message_pipeline_kafka_adapter.py — message_pipeline Kafka 适配器单测
│   ├── test_message_pipeline_ports.py     — message_pipeline 端口契约单测
│   ├── test_modbus_source_acquisition_adapter.py  — Modbus TCP 采集适配器测试
│   ├── test_modbus_source_write_adapter.py         — Modbus TCP 写入适配器测试
│   ├── test_mqtt_backend.py            — MQTT client backend 单测（P1 unit/mock，asyncio MQTT v3.1.1）
│   ├── test_mqtt_source_acquisition_adapter.py — MQTT 采集适配器单测（P1 unit/mock）
│   ├── test_http_rest_backend.py       — HTTP REST client backend 单测（P1 unit/mock）
│   ├── test_http_rest_source_acquisition_adapter.py — HTTP REST 采集适配器单测（P1 unit/mock）
│   ├── test_iec104_backend.py           — IEC104 lib60870 backend 单测
│   ├── test_iec104_source_acquisition_adapter.py   — IEC104 采集适配器单测（P1 unit/mock）
│   ├── test_iec104_source_write_adapter.py          — IEC104 写入适配器单测
│   ├── test_modbus_rtu_backend.py       — Modbus RTU serial backend 单测（P1 unit/mock，CRC16）
│   ├── test_modbus_rtu_source_acquisition_adapter.py — Modbus RTU 采集适配器单测（P1 unit/mock）
│   ├── test_iec101_backend.py           — IEC101 serial backend 单测（P1 unit/mock，FT1.2+ASDU）
│   ├── test_iec101_source_acquisition_adapter.py   — IEC101 采集适配器单测（P1 unit/mock）
│   ├── test_opcua_adapter_resolution.py — OPC UA 适配器解析测试
│   ├── test_opcua_source_acquisition_adapter.py  — OPC UA 采集适配器测试
│   ├── test_opcua_source_write_adapter.py  — OPC UA 写入适配器测试
│   ├── test_iec61850_mms_backend.py         — IEC 61850 MMS 后端单元测试
│   ├── test_iec61850_source_acquisition_adapter.py  — IEC 61850 MMS 采集适配器测试
│   ├── test_iec61850_source_write_adapter.py  — IEC 61850 MMS 写入适配器测试
│   ├── test_iec61850_report_backend.py         — IEC 61850 Report 后端单元测试
│   ├── test_iec61850_report_acquisition_adapter.py  — IEC 61850 Report 订阅采集适配器测试
│   ├── test_open62541_backend.py      — open62541 后端测试
│   ├── test_polling_acquisition_role.py   — 轮询角色测试
│   ├── test_subscription_acquisition_role.py  — 订阅角色测试
│   ├── test_subscription_reconnect_baseline.py  — 订阅重连基线单测
│   ├── test_subscription_reconnect_runtime.py   — 订阅重连运行时单测
│   ├── test_redis_source_state_cache.py   — Redis 状态缓存测试
│   ├── test_redis_streams_message_publisher.py — Redis Streams 测试
│   ├── test_relational_outbox_message_publisher.py — Outbox 发布器测试
│   ├── test_ingest_api_app.py        — FastAPI app单测
│   ├── test_ingest_audit_event_schema.py — ingest审计事件单测
│   ├── test_ingest_audit_redaction.py — ingest审计脱敏单测
│   ├── test_ingest_metrics_events.py  — ingest metrics事件单测
│   ├── test_ingest_no_source_lab_imports.py — import边界门禁单测
│   ├── test_turtle_octopus_import_boundary.py — turtle/octopus import边界门禁
│   ├── test_ingest_observability_sink.py  — 观测sink单测
│   ├── test_ingest_source_adapter_capability_matrix.py — 适配器能力矩阵单测
│   ├── test_ingest_security_partition_config.py — 安全分区配置单测
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
│   ├── test_ingest_write_security_profile.py — 写入安全配置单测
│   ├── test_ingest_readyz.py         — readyz 8组件聚合与degradation单测
│   ├── test_scheduler_job_routes.py  — 调度任务持久化单测
│   ├── test_worker_runtime_do_execute.py — WorkerRuntime dispatch 单测
│   ├── test_acquisition_job_handler.py — AcquisitionJobHandler P1 单测
│   ├── test_dual_node_write_lease_conflict.py — 双节点写入冲突 P2 单测
│   ├── test_source_acquisition_port_registry.py  — 端口注册表测试
│   ├── test_source_acquisition_use_case.py   — 采集用例测试
│   ├── test_source_command_write_lease_guard.py — 写入租约守卫测试
│   ├── test_source_command_use_case.py   — 命令写入用例测试
│   ├── test_source_command_lease_release.py — 写入租约释放单测
│   ├── test_source_command_audit.py   — 命令审计单测
│   ├── test_source_command_authorization_guard.py — 命令授权守卫单测
│   ├── test_shared_source_runner_resolution.py  — shared_source runner 路径解析单测
│   ├── test_state_snapshot_publish_use_case.py  — 快照发布用例测试
│   ├── test_source_runtime_config_repository.py  — 运行时配置仓库测试
│   ├── test_source_scheduling.py       — 调度测试
│   ├── test_source_simulation_support_sources.py  — 模拟源测试
│   ├── test_source_write_port_registry.py  — 写入端口注册表测试
│   ├── test_speed_layer_light_processor.py  — SP-FR-004 light_processor 单测（26 tests）
│   ├── test_speed_layer_pipeline_runner.py  — speed_layer pipeline runner 单测
│   ├── test_speed_layer_preprocessing.py      — speed_layer preprocessing Round A 单测（83 tests：10 阶段 pipeline/registry/operator/DTO）
│   ├── test_storage_raw_archive.py          — storage raw_archive 单测
│   ├── test_storage_raw_index.py            — storage raw_index 单测
│   ├── test_storage_standardized.py         — storage standardized 单测
│   ├── test_storage_serving_cache.py        — storage serving_cache 单测（9 tests）
│   ├── test_storage_waveform.py              — storage waveform 单测（12 tests：port/InMemory/Tdengine real REST API）
│   ├── test_storage_simulation_result.py    — storage simulation_result 单测（InMemory/TDengine real REST API）
│   ├── test_ingest_file_ingest_models.py     — file_ingest models 单测（FaultRecordBinary/SourceFile）
│   ├── test_ingest_file_ingest_detector.py   — file_ingest detector 单测（FileCompletionDetector）
│   ├── test_ingest_file_ingest_decoder.py    — file_ingest decoder 单测（FaultRecordBinaryDecoder）
│   ├── test_ingest_file_ingest_repository.py — file_ingest repository 单测（FileIngestJobRepository）
│   ├── test_ingest_file_ingest_service.py    — file_ingest service 单测（FileIngestService 编排）
│   ├── test_model_asset_models.py         — model_asset models DTO/枚举单测（SimulationFileType 等）
│   ├── test_model_asset_detector.py       — SimulationFileTypeDetector 文件类型检测单测
│   ├── test_model_asset_repository.py     — ModelAssetRepository 四表 CRUD 单测
│   ├── test_model_asset_service.py        — ModelAssetImportService 导入编排单测
│   └── shared/persistence/
│       ├── test_model_asset_orm.py       — model_asset ORM 四表唯一约束/FK 单测
│       ├── test_scada_protocol_params.py   — SCADA 协议参数模板与注释测试
│       ├── test_scada_sample_data_protocol_coverage.py — SCADA 样例数据协议覆盖测试
│       └── test_scada_protocol_views.py    — SCADA 协议视图测试
│
├── integration/                       — P3 集成测试
│   ├── __init__.py
│   ├── test_framework_db_init.py      — 框架 DB 初始化集成测试
│   ├── test_ingest_file_ingest_integration.py — file_ingest 模块集成测试（detect->archive->decode->waveform，6 tests，临时文件）
│   ├── test_model_asset_integration.py    — model_asset 模块集成测试（import->detect->archive->persist，12 tests）
│   ├── test_model_asset_alembic_migration.py — model_asset Alembic 迁移集成测试（upgrade/downgrade 4 表）
│   ├── test_http_rest_acquisition_chain.py — HTTP REST 全链路采集集成测试（P3 simulator）
│   ├── test_iec104_acquisition_chain.py    — IEC104 全链路采集集成测试（P3 simulator）
│   ├── test_modbus_rtu_acquisition_chain.py — Modbus RTU 全链路采集集成测试（P3 simulator）
│   ├── test_iec101_acquisition_chain.py    — IEC101 全链路采集集成测试（P3 simulator）
│   ├── test_mqtt_acquisition_chain.py      — MQTT 全链路采集集成测试（P3 simulator）
│   ├── test_ingest_api_acquisition_task_crud.py — acquisition task CRUD集成
│   ├── test_ingest_api_audit.py       — API审计集成测试
│   ├── test_ingest_api_authorization_deny.py — API授权拒绝集成测试
│   ├── test_ingest_api_bundle_metadata_crud.py — bundle metadata CRUD集成
│   ├── test_ingest_api_dry_run_all_mutating_routes.py — API dry-run全mutating路由集成
│   ├── test_ingest_api_full_audit_matrix.py — API全审计矩阵集成
│   ├── test_ingest_api_idempotency_all_mutating_routes.py — 幂等性全mutating路由集成
│   ├── test_ingest_api_idempotency_dry_run.py — 幂等性dry-run集成
│   ├── test_ingest_api_idempotency_dry_run_interaction.py — 幂等性dry-run交互集成
│   ├── test_ingest_api_node_lease_audit_query.py — node/lease审计查询集成
│   ├── test_ingest_api_runtime_config_audit.py — runtime config审计集成
│   ├── test_ingest_api_runtime_config_crud.py — runtime config CRUD集成
│   ├── test_ingest_api_scheduler_job_crud.py — scheduler job CRUD集成
│   ├── test_ingest_api_security_partition_crud.py — security partition CRUD集成
│   ├── test_ingest_audit_db_jsonl_consistency.py — DB/JSONL审计一致性集成
│   ├── test_ingest_audit_matrix_api_bundle_scheduler_write.py — 审计矩阵API/bundle/scheduler集成
│   ├── test_ingest_bundle_import_export.py — bundle导入导出集成
│   ├── test_ingest_bundle_offline_one_way_flow.py — bundle单向流离线集成
│   ├── test_ingest_iec104_source_write.py  — IEC104 写入集成测试
│   ├── test_ingest_lightweight_load_gate.py — 轻量加载门禁集成
│   ├── test_ingest_observability_sink_smoke.py — 观测sink烟测集成
│   ├── test_ingest_polling_retry_to_redis.py   — 轮询重试到 Redis
│   ├── test_ingest_prodlike_access_policy.py — prodlike访问策略集成
│   ├── test_ingest_prodlike_audit_sink.py — prodlike审计sink集成
│   ├── test_ingest_prodlike_audit_metrics_resilience.py — 审计指标韧性测试
│   ├── test_ingest_prodlike_endurance_smoke.py — prodlike endurance 脚本烟测
│   ├── test_ingest_prodlike_kafka_publish.py — prodlike Kafka发布集成
│   ├── test_ingest_prodlike_kafka_fault_injection.py — Kafka 故障注入恢复测试
│   ├── test_ingest_prodlike_performance_profile.py — 性能基线测试
│   ├── test_ingest_prodlike_postgres_fault_injection.py — PostgreSQL 故障注入恢复测试
│   ├── test_ingest_prodlike_postgres_runtime_db.py — prodlike PostgreSQL runtime DB集成
│   ├── test_ingest_prodlike_redis_cache.py — prodlike Redis缓存集成
│   ├── test_ingest_prodlike_redis_fault_injection.py — Redis 故障注入恢复测试
│   ├── test_ingest_prodlike_scheduler_backpressure.py — 调度背压与 missed tick 测试
│   ├── test_ingest_prodlike_worker_failover.py — worker crash/failover 集成测试
│   ├── test_ingest_runtime_alembic_migration.py — Alembic迁移集成测试
│   ├── test_ingest_runtime_alembic_postgres_matrix.py — Alembic PostgreSQL矩阵集成
│   ├── test_ingest_runtime_alembic_sqlite_matrix.py — Alembic SQLite矩阵集成
│   ├── test_ingest_runtime_db_init.py — runtime DB初始化集成测试
│   ├── test_ingest_runtime_entrypoint_smoke.py — entrypoint烟测
│   ├── test_ingest_runtime_migrate_entrypoint.py — migrate入口集成测试
│   ├── test_ingest_scheduler_active_standby_failover.py — 调度器主备故障转移集成
│   ├── test_ingest_scheduler_apscheduler_runtime.py — APScheduler运行时集成
│   ├── test_ingest_scheduler_cluster_assignment.py — 调度器集群分配集成
│   ├── test_ingest_scheduler_dual_active_partitioned.py — 调度器双活分区集成
│   ├── test_ingest_scheduler_graceful_shutdown.py — 调度器优雅关闭集成
│   ├── test_ingest_scheduler_missed_tick_and_stagger.py — missed tick与错峰集成
│   ├── test_ingest_source_acquisition_to_redis.py  — 采集到 Redis 集成
│   ├── test_ingest_source_cache_message_e2e.py — 源缓存消息E2E集成
│   ├── test_ingest_source_cache_message_kafka_e2e.py — 源缓存Kafka消息E2E集成
│   ├── test_ingest_subscription_strategy.py    — 订阅策略集成测试
│   ├── test_ingest_security_partition_bundle_flow.py — Bundle单向流测试
│   ├── test_ingest_security_partition_smoke.py — 安全分区烟测集成
│   ├── test_ingest_worker_runtime_executes_usecase_handlers.py — WorkerRuntime usecase handler执行集成
│   ├── test_ingest_worker_runtime_handler_failure.py — WorkerRuntime handler失败集成
│   ├── test_ingest_worker_runtime_shutdown_inflight.py — WorkerRuntime shutdown inflight集成
│   ├── test_ingest_write_lease_fencing_e2e.py — 写入租约fencing E2E集成
│   ├── test_ingest_external_access_policy_contract.py — 外部授权合同测试
│   ├── test_ingest_external_audit_sink_contract.py — 外部审计sink合同测试
│   ├── test_message_pipeline_inmemory_e2e.py      — message_pipeline InMemory E2E 集成测试
│   ├── test_message_pipeline_kafka_e2e.py         — message_pipeline Kafka E2E 集成测试
│   ├── test_ingest_modbus_source_write.py        — Modbus TCP 写入集成测试
│   ├── test_ingest_opcua_source_write.py        — OPC UA 写入集成测试
│   ├── test_ingest_iec61850_mms_source_write.py  — IEC 61850 MMS 写入集成测试
│   ├── test_ingest_iec61850_report_subscription.py  — IEC 61850 Report 订阅集成测试
│   ├── test_ingest_cache_to_kafka_pipeline.py     — 缓存快照到 Kafka 发布集成测试
│   ├── test_shared_persistence_sample_data_init.py — 样例初始化 PostgreSQL 集成测试
│   ├── test_source_lab_scada_profile.py — source_lab 消费 SCADA sample DB 集成测试
│   ├── test_source_lab_scada_profile_postgres.py — source_lab 消费 PostgreSQL SCADA sample DB
│   ├── test_speed_layer_dlq_replay.py            — speed_layer DLQ/replay 集成测试
│   ├── test_speed_layer_index_standardized_pipeline.py — speed_layer index/standardized/serving_cache 集成测试
│   ├── test_speed_layer_raw_archive_pipeline.py  — speed_layer raw_archive pipeline 集成测试
│   ├── test_source_lab_beckhoff_ads_runtime.py — Beckhoff ADS in_process+dotnet统一输入集成测试
│   ├── test_whale_writer_failure_recovery.py    — Whale writer 故障恢复集成测试
│   ├── test_whale_writer_switchover.py          — Whale writer 主备切换集成测试
│   ├── test_l5_external_dependency_verification.py — P5 准生产依赖验证期 外部依赖验证（Kafka/PG/Redis/S3/TDengine 验证通过，Pulsar/HDFS/Flink MISSING_ENVIRONMENT）
│   ├── test_model_asset_postgres_integration.py — model_asset PostgreSQL 集成（16 tests, NOT_RUN: DSN 未设置; DSN 已设置但连接失败时 FAIL）
│   ├── test_storage_waveform_tdengine_integration.py — waveform TDengine REST API P5 集成（4 tests, NOT_RUN: TCP+REST 两阶段探测 skipif）
│   ├── test_storage_simulation_result_tdengine_integration.py — simulation_result TDengine REST API P5 集成（5 tests, NOT_RUN: TCP+REST 两阶段探测 skipif）
│   ├── test_redis_state_cache_faults.py        — Redis 缓存容错测试
│   ├── test_ingest_dual_node_db_lease_e2e.py — 双节点 DB lease E2E 集成测试（P3）
│   └── test_sqlite_config_init.py              — SQLite 配置初始化
│
├── e2e/                               — P4 端到端测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_whale_field_minimal_smoke.py — Whale 现场最小数据链路 P4 smoke（7 tests）
│   ├── test_whale_l5_kafka_pipeline_e2e.py — P5 Kafka pipeline E2E（4 tests）
│   └── test_whale_l5_storage_e2e.py        — P5 storage E2E（10 tests：S3/TDengine/Redis）
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
    ├── scada_sample_db.py             — SCADA 样例 SQLite/PG 初始化辅助
    ├── shared_persistence_sample_db.py — shared persistence 样例 PG 初始化辅助
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
├── beckhoff_ads_virtual_server_setup.md — Windows TwinCAT ADS virtual server 指引
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
│   │   ├── dynamic_cli.py             — 动态CLI入口
│   │   ├── session_manager.py         — endpoint会话管理
│   │   ├── stagger_coordinator.py     — endpoint错峰协调
│   │   ├── continuity_model.py        — 连续性指标模型
│   │   ├── continuity_monitor.py      — 连续性指标监控
│   │   ├── state_store.py             — runtime文件状态存储
│   │   ├── operation_journal.py       — 动态操作日志
│   │   └── native_interactive_control.py — native交互控制
│   │
│   ├── providers/                     — 数据提供者
│   │   ├── __init__.py
│   │   ├── base.py                    — 提供者基类
│   │   ├── expanded_field.py          — 展开字段提供者
│   │   ├── field.py                   — 字段提供者
│   │   ├── file_field.py              — 文件字段提供者
│   │   ├── scada_profile.py           — shared persistence SCADA 样例 provider
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
│       ├── beckhoff_ads_polling.py    — Beckhoff ADS 轮询运行器
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
│   │   ├── _base_facade.py            — 默认 NOT_IMPLEMENTED 基类
│   │   └── _interactive_runner.py     — 交互式运行器基类
│   ├── beckhoff_ads/                  — Beckhoff ADS 协议
│   │   ├── __init__.py
│   │   ├── ads_client.py              — ADS Python pyads 子进程客户端
│   │   ├── dotnet_virtual_server.py   — Beckhoff .NET virtual ADS server 管理
│   │   ├── runtime.py                 — ADS in_process tool runtime
│   │   └── simulator.py               — ADS facade/read-write-readback
│   ├── http_rest/
│   │   ├── __init__.py                — HTTP REST 协议
│   │   └── simulator.py               — HTTP REST facade
│   ├── iec101/
│   │   ├── __init__.py                — IEC 101 协议
│   │   └── simulator.py               — IEC 101 facade
│   ├── iec104/
│   │   ├── __init__.py                — IEC 104 协议
│   │   └── simulator.py               — IEC 104 facade
│   ├── iec61850/
│   │   ├── __init__.py                — IEC 61850 协议
│   │   └── simulator.py               — IEC 61850 facade
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
    ├── README.md                       — 测试边界、工具名与验证等级区别、NOT_RUN 条件
    ├── TEST_AUDIT.md                   — 测试审计记录（含 P1-P7 生命周期术语对齐说明）
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
        ├── _dynamic_runtime_test_utils.py — 动态runtime测试辅助
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
        ├── test_ai_shared_report_template_references.py — AI报告模板引用测试
        ├── test_all_protocols_polling_capacity.py   — 全协议轮询容量
        ├── test_all_protocols_polling_profile.py    — 全协议轮询画像
        ├── test_all_protocols_probe.py — 全协议探测
        ├── test_all_protocols_streaming_capacity.py  — 全协议流式容量
        ├── test_all_protocols_streaming_profile.py   — 全协议流式画像
        ├── test_beckhoff_ads_capacity_profile_gate.py — ADS capacity/profile 门禁测试
        ├── test_beckhoff_ads_client_runner_protocol.py — ADS client/preflight 测试
        ├── test_beckhoff_ads_dotnet_virtual_server.py — ADS .NET virtual server 测试（env-pending）
        ├── test_beckhoff_ads_environment_probe.py — ADS 环境探测测试（env-pending）
        ├── test_beckhoff_ads_native_preflight.py — ADS AdsLib native 预检测试（env-pending）
        ├── test_beckhoff_ads_real_protocol_readback.py — ADS 真实协议 readback 测试（env-pending）
        ├── test_beckhoff_ads_simulator_contract.py — ADS facade 合同测试
        ├── test_capacity_progress.py   — 容量进度测试
        ├── test_capacity_reporter.py   — 容量报告器测试
        ├── test_capacity_rows.py       — 容量行格式化测试
        ├── test_capacity_service.py    — 容量服务测试
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
        ├── test_dynamic_runtime_state_recovery.py — 动态runtime恢复测试
        ├── test_dynamic_subscription_endpoint_adjustment.py — 动态订阅局部调整测试
        ├── test_field_capacity_cli.py  — 现场容量 CLI 测试
        ├── test_field_probe_cli.py     — 现场探测 CLI 测试
        ├── test_field_profile_cli.py   — 现场画像 CLI 测试
        ├── test_field_provider.py      — 字段提供者测试
        ├── test_iec104_client_runner_write_protocol.py — IEC104 写入协议测试
        ├── test_iec104_production_capacity_profile_gate.py — IEC104 capacity/profile门禁测试
        ├── test_iec61850_lightweight_semantics.py  — IEC 61850 轻量语义
        ├── test_iec61850_goose_sv_streaming_e2e.py  — GOOSE/SV 流式 E2E 条件测试
        ├── test_iec61850_l2_native_runner_failure_modes.py  — L2 native失败模式测试
        ├── test_iec61850_production_capacity_profile_gate.py  — IEC 61850 capacity/profile 门禁测试
        ├── test_iec61850_report_runner_protocol.py  — IEC 61850 Report 运行器协议测试
        ├── test_iec61850_report_capacity_profile_gate.py  — IEC 61850 Report 生产门禁验收测试
        ├── test_iec61850_mms_client_runner_write_protocol.py  — IEC 61850 MMS 写入协议测试
        ├── test_modbus_client_runner_write_protocol.py  — Modbus TCP 写入协议测试
        ├── test_modbus_tcp_production_capacity_profile_gate.py  — Modbus TCP capacity/profile 门禁测试
        ├── test_native_cmd_runner_preflight.py  — NativeCmdCapacityRunner 预检测试
        ├── test_native_cmd_timeout.py  — Native 命令超时单测
        ├── test_native_process_protocol.py  — Native 进程协议测试
        ├── test_native_runners_availability.py  — Native 运行器可用性
        ├── test_opcua_access_adapter.py  — OPC UA 接入适配器测试
        ├── test_open62541_client_runner_write_protocol.py  — OPC UA 写入协议测试
        ├── test_open62541_serial_polling_runner.py  — OPC UA 串行轮询测试
        ├── test_open62541_subscription_runner.py    — OPC UA 订阅测试
        ├── test_polling_metrics.py     — 轮询指标测试
        ├── test_port_allocator.py      — 端口分配器测试
        ├── test_profile_service.py     — 画像服务测试
        ├── test_protocol_directory_structure.py — 协议目录结构测试
        ├── test_protocol_matrix.py     — 协议矩阵测试
        ├── test_protocol_registry.py   — 协议注册表测试
        ├── test_protocol_service_capabilities.py  — 协议服务能力
        ├── test_source_lab_final_protocol_matrix.py  — 最终协议矩阵门禁
        ├── test_protocol_production_readiness_gate.py  — 协议生产准入门禁测试
        ├── test_protocol_simulator_factory.py  — 协议模拟器工厂
        ├── test_scada_profile_provider.py — SCADA sample DB provider 测试
        ├── test_scada_profile_runtime_coverage.py — SCADA runtime 覆盖矩阵测试
        ├── test_scada_profile_facade_smoke.py — SCADA runtime facade smoke
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
│   ├── ADR索引.md                     — ADR 索引
│   ├── 0000-template.md               — ADR 模板
│   ├── ADR-20260523-001-source-lab-server-client-ingest-boundary.md
│   ├── ADR-20260523-002-source-lab-task-facade-boundary.md
│   ├── ADR-20260523-003-source-production-client-and-write-port-boundary.md
│   ├── ADR-20260524-004-source-protocol-production-readiness-gate.md
│   ├── ADR-20260524-005-cache-to-message-queue-publish-use-case.md
│   ├── ADR-20260524-006-source-lab-protocol-directory-consolidation.md
│   ├── ADR-20260524-007-iec61850-mms-production-read-write-round1.md
│   ├── ADR-20260524-008-iec61850-report-subscription-boundary.md
│   ├── ADR-20260524-009-source-lab-server-simulator-facade.md
│   ├── ADR-20260530-010-shared-source-production-runner-artifact-boundary.md
│   ├── ADR-20260602-011-system-component-peer-boundary.md
│   ├── ADR-20260602-012-crosscutting-shrink-auth-security-compliance-to-turtle.md
│   ├── ADR-20260602-013-message-pipeline-abstraction-adaptation-only.md
│   ├── ADR-20260602-014-speed-layer-flink-pipeline-runtime-local-dev.md
│   ├── ADR-20260602-015-storage-three-layer-raw-archive-index-standardized.md
│   ├── ADR-20260604-016-ingest-file-ingest-waveform-boundary.md
│   └── ADR-20260604-017-model-asset-simulation-metadata-boundary.md
├── agent_config/                      — AI Agent 共享配置规范与 hook
│   ├── hooks/                         — 共享 hook 脚本
│   │   ├── block-dangerous-bash.py   — 危险命令拦截 hook
│   │   ├── docstring-cn-gate.py      — 中文 docstring 门禁 hook
│   │   ├── no-source-lab-import-gate.sh — source_lab 导入门禁
│   │   └── comment-doc-gate.py        — 注释文档门禁 hook
│   └── skills/                        — 规范源 skill 定义（10 个 skill）
├── templates/                         — 模板文件
│   └── coding_agent_prompt_template.txt — Coding Agent prompt 模板
├── memory/                            — 长期记忆
│   ├── project_tree.md                — 本文件（目录树）
│   ├── test_index.md                  — 测试资产索引与回归测试唯一索引（含 2.1"不能证明什么"表）
│   ├── 业务目标与价值愿景.md            — 项目白皮书：业务目标与价值愿景
│   ├── 总体逻辑设计.md                  — 项目白皮书：总体逻辑设计
│   ├── Whale_REQ_README.md           — 需求文档规范说明
│   ├── Whale_REQ_Project.md          — 项目层面需求说明
│   ├── Whale_REQ_Ingest.md           — 采集模块需求说明
│   ├── Whale_REQ_SourceLab.md        — source_lab 需求说明
│   ├── Whale_REQ_SharedSource.md     — 共享源层需求说明
│   ├── Whale_REQ_Storage.md          — 存储模块需求说明
│   ├── Whale_REQ_MessagePipeline.md  — 消息管道需求说明
│   ├── Whale_REQ_BatchLayer.md       — 批处理层需求说明
│   ├── Whale_REQ_BatchProcessing.md  — 批处理模块需求说明
│   ├── Whale_REQ_SpeedLayer.md       — 速度层需求说明
│   ├── Whale_REQ_ServingAggregation.md — 服务聚合模块需求说明
│   ├── PlatformShared_REQ_Crosscutting.md — 全系统公共基础库需求说明
│   ├── Turtle_REQ.md                 — Turtle 治理控制面需求说明
│   └── Octopus_REQ.md                — Octopus 运维执行面需求说明
├── reports/                           — agent 反馈与验收归档
│   ├── whale_field_ready_baseline_round6_closure_report.md — Round 6 现场部署前可交付基线收口报告
│   ├── whale_l5_definition_req_cleanup_round4_closure_report.md — Round 4 L5 定义纠偏、field_readback 清理与 SpeedLayer 证据收口报告
│   ├── whale_l5_external_dependency_round5_closure_report.md — Round 5 准生产外部依赖 P5 E2E 扩展验证报告
│   ├── whale_l5_real_chain_round2_closure_report.md — Round 2 真实链路缺口复核与 P0 最小生产链路补齐报告
│   ├── whale_l5_true_external_chain_round3_closure_report.md — Round 3 P5 真实外部依赖链路收口与 REQ 状态纠偏报告
│   ├── testing_lifecycle_and_repo_audit_round1_closure_report.md — Round 1 测试生命周期化重构与全仓规则审核收口报告
│   ├── testing_directory_governance_round2_closure_report.md — Round 2 测试目录治理与索引校准收口报告
│   ├── testing_directory_governance_round3_closure_report.md — Round 3 docs/scripts/reports 残留治理最终收口报告
│   ├── code_reality_docstring_audit_round1_report.md — Round 1 全仓空实现误判与注释规则合规审计报告
│   ├── code_reality_docstring_audit_round2_report.md — Round 2 补审与残留清理报告（deploy/config 术语迁移、test_l5 P4 修正、test_index"不能证明什么"表）
│   └── model_asset_round_c_closure_report.md — Round C model_asset 仿真资产元数据管理收口报告
└── rules/                             — 公共规则
    ├── routing.md                     — 规则路由
    ├── coding.md                      — 编码规范（架构边界/接口类型/测试同步/文档注释）
    ├── testing.md                     — 测试规范（P1-P7 七个生命周期阶段/回归测试/NOT_RUN 枚举）
    ├── documentation.md               — 文档规范
    ├── reporting.md                   — 反馈规范（Agent result 格式/报告命名/NOT_RUN 枚举）
    ├── validation-routing.md          — 验证路由（变更类型->阶段->优先级路由规则）
    ├── python-docstring-cn.md         — Python 中文 docstring 规范（P1-P7 生命周期阶段/测试文件头）
    └── quality-gate.md                — 代码质量门禁规则
```

## 文档 `docs/`

```text
docs/
├── GIT.md                             — Git 工作流说明
├── opcua_iec61850_guide.md            — OPC UA / IEC 61850 协议指南
├── 代码质量与注释.md                   — 代码质量规范与注释要求（已过时/历史参考，权威规则源：ai_shared/rules/）
├── 工程管理.md                         — 工程管理流程说明
└── 测试策略.md                         — 测试策略说明（已过时/历史参考，权威规则源：ai_shared/rules/testing.md）
```

## 脚本 `scripts/`

```text
scripts/
├── cleanup_root_logs.sh               — 清理根目录日志文件
├── whale_test.sh                      — Whale 测试统一入口（dry-run 默认安全模式 + --execute 显式执行，PASS/FAIL/NOT_RUN 输出）
├── run_ingest_dev.sh                  — 启动 ingest 开发环境
├── run_ingest_runtime_compose_smoke.sh — ingest compose运行态烟测
├── run_ingest_compose_readyz_e2e.sh   — compose readyz 8组件聚合 E2E 脚本
├── run_ingest_write_readback_smoke.sh — 三协议 simulator/native write-readback smoke
├── run_ingest_pg_lease_fault_injection.sh — PostgreSQL/readyz prodlike fault injection 入口
├── run_pg_migration_matrix.sh         — PostgreSQL迁移矩阵自动化脚本
├── ci_ingest_runtime_gate.sh          — CI门禁脚本（7个门禁组）
├── run_ingest_bundle_one_way_flow_smoke.sh — Bundle单向流smoke
├── run_ingest_prodlike_performance_profile.sh — 性能profile smoke
├── run_ingest_prodlike_dependency_smoke.sh — prodlike依赖烟测
├── run_ingest_prodlike_endurance_smoke.sh — prodlike endurance烟测
├── run_source_lab_raw_socket_dynamic_gate.sh — raw socket动态门禁回归
├── run_source_lab_l2_standalone_gate.sh — GOOSE/SV standalone门禁
├── validate_shared_source_production_runner.sh — shared_source runner 路径解析契约验证
├── test_ingest_write_readback_smoke_contract.sh — write-readback smoke 入口 CLI 契约自检
├── run_whale_field_minimal_smoke.sh — Whale 现场最小数据链路 smoke
├── run_whale_field_quality_gate.sh  — Whale 现场质量门禁聚合脚本
├── run_whale_field_ready_smoke.sh   — Whale 一键预检验证脚本（8-step）
├── run_whale_writer_switchover.sh   — Whale writer 主备切换验证脚本
├── run_whale_l5_external_dependency_probe.sh — P5 外部依赖环境探测（16 probes）（历史命名，功能不变）
├── source_lab_l2_test_env.sh          — 可控L2 veth环境搭建
├── check_l5_field_readback_env.py      — P5 外部依赖环境预检脚本（历史命名，功能不变）
├── check_serial_env.py                 — 串口硬件环境预检脚本（dry-run PENDING）
├── check_ads_env.py                    — Beckhoff ADS 环境预检脚本（dry-run PENDING）
├── check_l2_goose_sv_env.py            — GOOSE/SV L2 环境预检脚本（dry-run PENDING）
├── start_whale_p5_dependencies.sh   — P5 外部依赖启动脚本（Docker 不可用时 NOT_RUN: MISSING_ENVIRONMENT）
├── stop_whale_p5_dependencies.sh    — P5 外部依赖停止/清理脚本
├── run_whale_p5_external_dependency_regression.sh — P5 外部依赖回归脚本（5 测试组逐项输出/SUMMARY 行/PASS 计数/FAIL 时 exit 1；无 FAIL 但有 NOT_RUN 时 exit 0）
├── diagnose_whale_p5_dependencies.sh  — P5 外部依赖诊断脚本（5 依赖逐项 TCP+auth+minimal operation+脱敏+PASS/FAIL/NOT_RUN+reason）
└── run_quality_gate.py                 — CI 质量门禁聚合脚本（6 gates，JSON+human输出）
```

## AI 工具配置

```text
.claude/                               — Claude Code 配置
├── settings.json                      — Claude Code 全局设置
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

.codex/                                — OpenAI Codex 适配配置
├── config.toml                        — Codex 配置
├── hooks.json                         — Codex hook 定义
└── agents/                            — Codex 子代理定义
    ├── code-implementer.toml          — 编码实现子代理
    ├── project-steward.toml           — 文档与目录树子代理
    └── test-validator.toml            — 独立验证子代理
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
