# BlueCrystal 项目目录树

> 最后更新: 2026-06-07 (Round 20 扩展：src/starfish/protocols/iec101/link_layer.py **LinkLayerTimerService 抽象 + Default (threading.Timer) + Fake 三实现 + send/receive/on_timeout 完整状态机 + balanced FCB auto flip + retry ERROR**；src/starfish/protocols/iec101/information_elements.py **ShortFloat 兼容扩展**（int/numbers.Real/`__float__` duck typing 统一入口，**不引入 numpy 硬依赖**）；src/seahorse/strategies/curve_generation.py **Seahorse flaky 根因修复**（`daily_power_curve` 在 noise 叠加后强制 `min(values) >= floor_ratio * baseline = 0.2 * 1500.0 = 300.0`，从根因消除 `min(values)=90.952 < 100 阈值` 的统计噪声；**未使用 skip/xfail/删除测试/扩大阈值**）；src/starfish/facade/iec101_facade.py 扩展 codec_capabilities 3 个新 capabilities（`supports_link_layer_timers=true` / `supports_balanced_fcb_auto_flip=true` / `supports_retry_skeleton=true`）+ health() reason_text 7 强制要点同步；tests/unit/seahorse/test_strategies.py 新增 5 个 daily_power 稳定性测试（min_floor_enforced / cross_run_consistency / high_noise_compatible / 其它曲线无 floor 行为 / 5x 稳定性；test-validator 独立验证连续 **12 次 0 flaky**）；tests/unit/starfish/test_iec101_link_layer.py 新增 8 个 test classes（LinkLayerTimerService 抽象 + Default + Fake + balanced FCB auto flip + retry ERROR + sequence 状态机）；tests/unit/starfish/test_iec101_information_elements.py 新增 TestShortFloatRound20Compat（int / Decimal / Fraction / `__float__` duck typing 4 路输入 + NaN/Inf 仍严格拒绝）；tests/unit/starfish/test_iec101_codec.py 新增 TestIec101CodecRound20（3 新 capabilities 数字断言 + 7 强制要点 reason_text 验证）；tests/unit/starfish/test_probe_profile_capacity.py 新增 TestIec101Round20Capabilities（codec_capabilities 显式声明）；600+ IEC101 codec tests + 1215 starfish total + 15 architecture + 186 seahorse（**180 stable + 5 新 daily_power 稳定性测试 + 1 原 daily_power_preset**）= **1416 stable passed（+77 net 增量 vs Round 19 1339）**；third_party 零新增；import boundary 清洁；**LinkLayer runtime skeleton 仍不是真实 IEC101 server**（默认 `enable_timers=False` + 零 socket/pty/serial + `supports_server=false` / `supports_serial_runtime=false` 维持）；20 轮递进建设完成)

本文件维护完整文件级目录树，每个 item 附简短职责注释（不超过 40 中文字符）。
只用于导航，不替代读取当前源码。

## 根目录

```text
/ (BlueCrystal)
├── CLAUDE.md                        — Claude Code / Codex 共用执行入口
├── AGENTS.md                        — Codex 自动读取入口，指向 CLAUDE.md
├── README.md                        — 项目简介与快速开始
├── Dockerfile                       — 已迁移到 deploy/whale/ingest/Dockerfile
├── alembic.ini                      — Alembic 主配置
├── pyproject.toml                   — 项目元数据、依赖与 ruff/mypy/pytest 工具配置
├── requirements.txt                 — Python 依赖声明
├── alembic/                         — ingest 运行库迁移
│   ├── env.py                       — Alembic 环境配置
│   ├── script.py.mako               — 迁移脚本模板
│   └── versions/                    — 迁移版本（4 个）
│       ├── 20260527_000001_ingest_runtime_initial.py
│       ├── 20260527_000002_add_audit_index_and_job_stagger.py
│       ├── 20260527_000003_add_idempotency_record.py
│       └── 20260527_000004_add_model_asset_tables.py
├── .gitignore                       — Git 忽略规则
├── .vscode/settings.json            — VSCode 编辑器配置
├── .vscode/claude-wrapper.sh        — VSCode Claude CLI 包装脚本
├── .data/                           — 运行时数据（SQLite 开发/测试 DB，gitignore）
├── config/                          — 运行时配置
│   ├── ingest/                      — ingest 配置（access_policy / performance / audit / endurance / security_partition）
│   └── whale/                       — BlueCrystal 现场部署配置模板（P5 准生产依赖验证期 MISSING_ENVIRONMENT 标记）
├── src/                             — 主源码根目录
├── tests/                           — 项目级测试根目录
├── ai_shared/                       — AI 配置、规则与记忆
├── docs/                            — 项目文档
├── scripts/                         — 运维与开发脚本
├── deploy/                          — BlueCrystal / Turtle / Octopus 部署配置
├── .claude/                         — Claude Code 配置与技能
├── .agents/                         — Codex agent 配置（skills 软链至 .claude/skills）
├── .codex/                          — OpenAI Codex 适配配置
└── third_party/                     — 第三方 C 协议栈源码与预编译库
```

## 主源码 `src/`

### `src/whale/` — 数据平台核心

```text
src/whale/
├── __init__.py                      — 包入口（__version__ / __author__）
│
├── ingest/                          — 数据采集核心（六边形架构）
│   ├── __init__.py                  — 包入口（含 file_ingest 导出）
│   ├── config.py                    — 采集配置定义与加载
│   ├── composition.py               — 依赖注入组合根（采集/写入/快照发布）
│   ├── message_pipeline.py          — 消息管道编排
│   │
│   ├── entities/                    — 领域实体
│   │   ├── node_state.py            — 节点状态实体
│   │   └── source_health_state.py   — 数据源健康状态实体
│   │
│   ├── usecases/                    — 用例层（业务逻辑）
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
│   │   │   ├── state_publish_request.py  — 快照发布请求 DTO
│   │   │   └── state_publish_result.py   — 快照发布结果 DTO
│   │   └── roles/                   — 采集策略角色
│   │       ├── polling_acquisition_role.py       — 轮询采集策略
│   │       └── subscription_acquisition_role.py  — 订阅采集策略
│   │
│   ├── ports/                       — 端口层（接口抽象）
│   │   ├── audit.py                 — ingest 审计 sink 端口
│   │   ├── diagnostics.py           — 诊断接口
│   │   ├── metrics.py               — 指标端口
│   │   ├── command/                 — 命令审计端口
│   │   │   └── source_command_audit_port.py
│   │   ├── message/                 — 消息发布端口
│   │   │   └── message_publisher_port.py
│   │   ├── runtime/                 — 运行时配置端口
│   │   │   ├── access_policy_port.py           — 访问策略端口
│   │   │   ├── source_runtime_config_port.py
│   │   │   └── write_lease_port.py             — 写入租约端口
│   │   ├── source/                  — 数据源采集端口
│   │   │   ├── source_acquisition_definition_port.py
│   │   │   ├── source_acquisition_port.py
│   │   │   ├── source_acquisition_port_registry.py
│   │   │   ├── source_write_port.py
│   │   │   └── source_write_port_registry.py
│   │   └── state/                   — 状态缓存端口
│   │       ├── source_state_cache_port.py
│   │       └── source_state_snapshot_reader_port.py
│   │
│   ├── adapters/                    — 适配器层（基础设施实现）
│   │   ├── audit/                   — 审计 sink 适配器
│   │   │   ├── db_audit_sink.py     — DB 审计 sink
│   │   │   ├── http_audit_sink.py   — 外部 HTTP 审计 SIEM sink
│   │   │   └── multi_audit_sink.py  — DB + JSONL dual audit sink
│   │   ├── config/                  — 配置持久化适配器
│   │   │   ├── opcua_source_acquisition_definition_repository.py
│   │   │   └── source_runtime_config_repository.py
│   │   ├── message/                 — 消息发布适配器
│   │   │   ├── kafka_message_publisher.py
│   │   │   ├── redis_streams_message_publisher.py
│   │   │   └── relational_outbox_message_publisher.py
│   │   ├── security/                — 安全策略适配器
│   │   │   ├── external_access_policy.py
│   │   │   └── file_access_policy.py
│   │   ├── source/                  — 数据源采集适配器（13 协议）
│   │   │   ├── dispatch_source_acquisition_adapter.py  — 多协议调度采集
│   │   │   ├── http_rest_source_acquisition_adapter.py
│   │   │   ├── iec101_source_acquisition_adapter.py    — IEC101 串行采集
│   │   │   ├── iec104_source_acquisition_adapter.py    — IEC104 采集
│   │   │   ├── iec104_source_write_adapter.py          — IEC104 写入
│   │   │   ├── modbus_source_acquisition_adapter.py    — Modbus TCP 采集
│   │   │   ├── modbus_source_write_adapter.py          — Modbus TCP 写入
│   │   │   ├── modbus_rtu_source_acquisition_adapter.py — Modbus RTU 串行采集
│   │   │   ├── mqtt_source_acquisition_adapter.py      — MQTT 采集
│   │   │   ├── opcua_source_acquisition_adapter.py     — OPC UA 采集
│   │   │   ├── opcua_source_write_adapter.py           — OPC UA 写入
│   │   │   ├── iec61850_source_acquisition_adapter.py  — IEC 61850 MMS 采集
│   │   │   ├── iec61850_source_write_adapter.py        — IEC 61850 MMS 写入
│   │   │   ├── iec61850_report_source_acquisition_adapter.py — IEC 61850 Report 订阅采集
│   │   │   ├── static_source_acquisition_port_registry.py
│   │   │   └── static_source_write_port_registry.py
│   │   ├── observability/           — 观测与审计输出
│   │   │   └── file_sinks.py        — JSONL metrics / audit sink
│   │   └── state/                   — 状态缓存适配器
│   │       └── redis_source_state_cache.py
│   │
│   ├── api/                         — ingest Web API
│   │   ├── app.py                   — FastAPI app factory
│   │   ├── audit_middleware.py      — API 审计中间件
│   │   ├── errors.py                — 稳定错误模型
│   │   ├── idempotency.py           — 幂等性中间件
│   │   ├── schemas.py               — API schema
│   │   ├── readyz.py                — readyz 8 组件聚合与 degradation 脱敏
│   │   └── routes/                  — 9 路由模块
│   │       ├── acquisition_tasks.py — 采集任务 CRUD 路由
│   │       ├── audit_events.py      — audit event 查询路由
│   │       ├── bundles.py           — bundle metadata 查询路由
│   │       ├── health.py            — health / ready 路由
│   │       ├── leases.py            — lease 查询路由
│   │       ├── nodes.py             — node 查询路由
│   │       ├── runtime_config.py    — source 等配置 CRUD 路由
│   │       ├── scheduler_jobs.py    — scheduler job CRUD 路由
│   │       └── security_partitions.py — security partition CRUD 路由
│   │
│   ├── bundle/                      — 配置包导入导出
│   │   ├── checksum.py              — bundle 校验摘要
│   │   ├── model.py                 — bundle 领域模型
│   │   ├── redaction.py             — bundle 脱敏导出
│   │   └── service.py               — bundle 服务
│   │
│   ├── domain/                      — 共享领域模型
│   │   ├── audit_event.py           — ingest 结构化审计事件
│   │   └── write_security_profile.py — 写入安全配置模型
│   │
│   ├── runtime/                     — 运行时组件
│   │   ├── acquisition_mode.py      — 采集模式枚举
│   │   ├── cli.py                   — ingest 多入口 CLI
│   │   ├── entrypoint.py            — ingest 运行入口
│   │   ├── fencing.py               — fencing token 服务
│   │   ├── job_status.py            — 作业状态定义
│   │   ├── job_assignment.py        — 作业归属服务
│   │   ├── lease.py                 — 作业租约服务
│   │   ├── message_pipeline_settings.py — 管道参数设置
│   │   ├── modes.py                 — runtime 模式枚举
│   │   ├── node_runtime.py          — 节点心跳服务
│   │   ├── scheduler.py             — 调度器主逻辑
│   │   ├── scheduler_factory.py     — 调度器工厂
│   │   ├── scheduler_job.py         — 调度作业封装
│   │   ├── scheduler_settings.py    — 调度器参数
│   │   ├── write_lease.py           — 写入租约服务
│   │   ├── worker_runtime.py        — APScheduler WorkerRuntime
│   │   └── handlers.py              — WorkerRuntime 采集 job handler
│   │
│   ├── decorators/                  — 装饰器
│   │   ├── source_acquisition.py    — 采集流程装饰器
│   │   ├── source_write.py          — 写入授权装饰器
│   │   └── state_cache.py           — 状态缓存装饰器
│   │
│   ├── framework/persistence/       — 持久化框架
│   │   ├── base.py                  — ORM 声明基类
│   │   ├── init_db.py               — 数据库初始化
│   │   ├── runtime_db.py            — runtime DB 初始化与探针
│   │   ├── session.py               — 会话管理
│   │   └── orm/                     — ORM 模型包（空，模型在 shared）
│   │
│   ├── file_ingest/                 — 文件接入子系统（文件完成检测、解码、波形写入）
│   │   ├── detector.py              — FileCompletionDetector（inotify + polling）
│   │   ├── decoder.py               — FaultRecordBinaryDecoder（magic + version + header + float32 LE）
│   │   ├── repository.py            — FileIngestJobRepository（SQLite / SQLAlchemy）
│   │   ├── service.py               — FileIngestService 编排（detect → archive → decode → waveform → fault_event）
│   │   └── models.py                — FaultRecordBinary / SourceFile / FileIngestJob 领域模型
│   │
│   └── docs/                        — ingest 设计文档
│       ├── DECISIONS.md             — 架构决策记录
│       └── 设计说明书.md             — 模块设计说明书
│
├── message_pipeline/                — 消息管道抽象与适配
│   ├── model.py                     — Envelope / TopicSpec / PartitionKey / MessageOffset / ReplayRequest
│   ├── ports.py                     — Source / Sink / SchemaRegistry / DLQ / Replay 端口接口
│   └── adapters/                    — 消息管道适配器
│       ├── in_memory.py             — InMemoryMessageBus / DLQ / SchemaRegistry
│       ├── kafka.py                 — KafkaSourceAdapter (REAL consumer.poll) + KafkaSinkAdapter
│       └── pulsar.py                — PulsarSource / Sink（contract-only，environment-pending）
│
├── speed_layer/                     — 速度层消费与运行时
│   ├── light_processor.py           — SP-FR-004 实时轻处理管线
│   ├── writers.py                   — RawArchive / RawIndex / Standardized / ServingCache
│   ├── runner.py                    — SpeedLayerWiring + LocalPipelineRunner + FlinkPipelineAdapter
│   ├── metrics.py                   — MetricsCollectorPort / InMemoryMetricsCollector
│   └── preprocessing/               — Round A 固定 10 阶段预处理 Pipeline + OperatorRegistry
│       ├── models.py                — 6 运行期 DTO
│       ├── registry.py              — OperatorRegistry 加权选择
│       ├── operators.py             — 11 个基础 operator
│       └── pipeline.py              — PreprocessingPipeline 固定 10 阶段编排
│
├── storage/                         — 存储层（三层分层 + warehouse / mart / cache）
│   ├── raw_archive.py               — S3RawArchiveSink (boto3 + gzip JSONL) + LocalCompressedArchiveSink
│   ├── raw_index.py                 — TdengineRawIndexSink + MemoryRawIndexSink
│   ├── standardized.py              — TdengineStandardizedSink + MemoryStandardizedSink
│   ├── warehouse.py                 — WarehouseSinkPort + InMemoryWarehouseSink
│   ├── mart.py                      — MartSinkPort + InMemoryMartSink
│   ├── serving_cache.py             — RedisServingCache (SETEX/GET/DEL/PING/TTL) + InMemoryServingCache
│   ├── waveform.py                  — StandardizedWaveformSink + InMemory + TDengine real REST API
│   └── simulation_result.py         — SimulationResultTimeSeriesSink + InMemory + TDengine real REST API
│
├── processing/                      — 数据处理（骨架，依赖缺失无法运行）
│   ├── cleaner.py                   — 数据清洗
│   └── normalizer.py                — 数据标准化
│
├── aggregation/                     — 数据聚合（骨架，依赖缺失无法运行）
│   ├── ads.py                       — ADS 聚合
│   ├── periodic.py                  — 周期性聚合
│   └── realtime.py                  — 实时聚合
│
├── model_asset/                     — 仿真资产元数据管理与导入
│   ├── models.py                    — DTO（ModelAssetImportRequest 等）
│   ├── detector.py                  — SimulationFileTypeDetector
│   ├── archive.py                   — SimulationArchiveService（复用 storage.raw_archive）
│   ├── repository.py                — ModelAssetRepository 四表持久化（PG）
│   └── service.py                   — ModelAssetImportService 编排
│
└── shared/                          — 共享层（跨模块通用能力）
    ├── enums/
    │   └── quality.py               — 数据质量枚举
    ├── utils/
    │   └── time.py                  — 时间工具函数
    ├── persistence/                 — 共享持久化
    │   ├── base.py                  — 持久化基类
    │   ├── init_db.py               — 数据库初始化
    │   ├── session.py               — 会话管理
    │   ├── orm/                     — ORM 模型
    │   │   ├── acquisition.py       — 采集任务模型
    │   │   ├── asset.py             — 资产模型
    │   │   ├── ingest_runtime.py    — ingest 运行库模型
    │   │   ├── ingest_diagnostics.py — 采集诊断模型
    │   │   ├── model_asset.py       — 仿真资产四表 ORM
    │   │   ├── organization.py      — 组织模型
    │   │   ├── scada_ingest.py      — SCADA 采集模型
    │   │   └── scada_protocol_param.py — SCADA 协议参数模型
    │   └── template/                — 旧路径 DeprecationWarning wrapper（已迁至 seahorse.reference_data）
    │       ├── gbt_30966_fields.py
    │       ├── protocol_param_data.py
    │       ├── protocol_view_defs.py
    │       ├── sample_data.py
    │       └── OPCUA_client_connections.yaml
    └── source/                      — 数据源访问抽象
        ├── models.py                — SourceConnectionProfile / NodeValueChange / Batch
        ├── ports.py                 — Browsable / Readable / Reader / Subscribable 端口
        ├── runner_resolution.py     — shared_source production runner 路径解析
        ├── access/                  — 可复用接入适配器
        │   ├── adapter.py           — SourceAccessAdapter 基类
        │   ├── model.py             — 端点 / 点位 / Tick 数据模型
        │   └── opcua.py             — OPC UA 适配器实现
        ├── modbus/                  — Modbus TCP 读取器
        │   ├── reader.py            — ModbusSourceReader 外观
        │   └── backends/
        │       ├── base.py
        │       └── libmodbus_backend.py
        ├── opcua/                   — OPC UA 读取器
        │   ├── reader.py
        │   └── backends/
        │       ├── base.py
        │       ├── factory.py
        │       └── open62541_backend.py
        ├── iec61850/                — IEC 61850 MMS / Report 读取器
        │   ├── reader.py            — Iec61850MmsSourceReader
        │   ├── report_reader.py     — Iec61850ReportSourceReader
        │   └── backends/
        │       ├── base.py
        │       ├── libiec61850_backend.py
        │       ├── report_base.py
        │       └── libiec61850_report_backend.py
        ├── iec104/                  — IEC 104 读取器
        │   ├── reader.py
        │   └── backends/
        │       ├── base.py
        │       └── lib60870_backend.py
        ├── http_rest/               — HTTP REST 读取器
        │   └── client.py
        ├── modbus_rtu/              — Modbus RTU 串行读取器
        │   ├── reader.py
        │   └── backends/
        │       ├── base.py
        │       └── serial_backend.py
        ├── iec101/                  — IEC 101 串行读取器
        │   ├── reader.py
        │   └── backends/
        │       ├── base.py
        │       └── serial_backend.py
        ├── mqtt/                    — MQTT 读取器
        │   └── client.py
        └── scheduling/              — 调度工具
            ├── concurrency.py
            ├── fixed_rate.py
            ├── polling.py
            └── stagger.py
```

### `src/platform_shared/` — 全系统公共基础库

```text
src/platform_shared/
├── crosscutting/                    — 横切公共能力
│   ├── debug/                       — 调试与诊断
│   │   ├── diagnostics.py           — 诊断快照
│   │   ├── ring_buffer.py           — 环形缓冲区
│   │   └── trace.py                 — 链路追踪
│   ├── observability/               — 可观测性
│   │   ├── audit.py                 — 审计日志
│   │   ├── logging.py               — 结构化日志
│   │   └── metrics.py               — 指标收集
│   ├── resilience/                  — 韧性策略
│   │   ├── backoff.py               — 退避策略
│   │   ├── circuit_breaker.py       — 熔断器
│   │   ├── deadline.py              — 截止时间
│   │   ├── error_classifier.py      — 错误分类
│   │   └── retry.py                 — 重试策略
│   ├── context/                     — 请求上下文（骨架）
│   ├── contracts/                   — 通用契约（骨架）
│   ├── kernel/                      — 基础运行时（骨架）
│   └── messaging/                   — 消息基础模型（骨架）
└── security_primitives/             — 安全基础工具
    └── masking.py                   — SensitiveDataMasker
```

### `src/turtle/` — 治理控制面

```text
src/turtle/
├── auth/                            — 认证授权
│   ├── authorizer.py                — 授权器（AccessDecision）
│   ├── credential.py                — 凭证管理（CredentialRef）
│   ├── identity.py                  — 身份管理（Principal）
│   └── policy.py                    — 策略定义（AccessPolicyPort / Permission）
├── security/                        — 安全基础
│   ├── certificate.py               — 证书管理（CertificateRef）
│   ├── model.py                     — 安全模型（CredentialRef / SecretRef）
│   ├── secret_provider.py           — 密钥提供（SecretProviderPort）
│   └── tls.py                       — TLS 配置（TlsConfig）
├── compliance/                      — 合规基础
│   ├── audit_policy.py              — 审计策略（AuditEvent / AuditEventSinkPort）
│   ├── data_classification.py       — 数据分类（DataClassification）
│   └── retention.py                 — 数据保留策略（RetentionPolicy）
├── audit/                           — 审计治理（空壳）
├── policy/                          — 策略治理（空壳）
├── governance/                      — 治理框架（空壳）
├── risk/                            — 风险评估（空壳）
├── deployment_policy/               — 部署策略（空壳）
├── change_control/                  — 变更控制（空壳）
├── ports/                           — 端口定义（空壳）
├── adapters/                        — 适配器实现（空壳）
├── api/                             — API 端点（空壳）
├── runtime/                         — 运行时配置（空壳）
└── sdk/                             — 客户端 SDK（空壳）
```

### `src/octopus/` — 运维执行面

```text
src/octopus/
├── orchestration/                   — 运维流程编排（空壳）
├── deployment/                      — 部署管理（空壳）
├── monitoring/                      — 监控采集（空壳）
├── alerting/                        — 告警管理（空壳）
├── diagnostics/                     — 故障诊断（空壳）
├── automation/                      — 自动化运维（空壳）
├── rollback/                        — 回滚管理（空壳）
├── reports/                         — 运维报告（空壳）
├── adapters/                        — 外部系统适配器（空壳）
└── runtime/                         — 运行时配置（空壳）
```

### `src/seahorse/` — 样例场站生成器

```text
src/seahorse/
├── __main__.py                      — CLI 入口（4 子命令：generate-scenario / export-bundle / validate-bundle / export-server-plan）
│
├── models/                          — 核心数据模型
│   ├── scenario.py                  — ScenarioConfig / ScenarioMetadata
│   ├── plan.py                      — SeedPlan / ServerPlan 等 9 个规划型 dataclass
│   ├── generation.py                — GeneratedSignalValue / AlarmEvent / ControlResult
│   └── bundle.py                    — ScenarioBundle 16 字段场景包 + _make_serializable
│
├── ports/                           — 端口层
│   └── generation_strategy.py       — GenerationStrategy @runtime_checkable Protocol
│
├── strategies/                      — 策略实现层
│   ├── random_generation.py         — 确定性随机值生成（5 种 generation_hint）
│   ├── curve_generation.py          — 曲线生成（6 种类型 + 14 组预设模板）
│   ├── replay_generation.py         — rows / JSONL 回放 + 字段映射 + 时间偏移
│   └── registry.py                  — 策略注册 / 查找 / 实体类型覆盖
│
├── generators/                      — 生成器层
│   ├── alarm_generator.py           — 告警生成（4 种类型）
│   └── control_result_generator.py  — 控制回写生成（7 种状态）
│
├── orchestration/                   — 编排层
│   └── scenario_generator.py        — SeahorseGenerator 5 元组完整生成
│
├── exporters/                       — 导出器层
│   ├── bundle_exporter.py           — JSON bundle 导出器
│   ├── timeseries_exporter.py       — JSONL 时序导出器
│   ├── bundle_validator.py          — 场景包校验器（6 项校验）
│   ├── serialization.py             — SHA256 校验和 + dataclass JSON 序列化
│   ├── server_plan_validator.py     — ServerPlan 校验器（9 项校验）
│   └── server_plan_exporter.py      — ServerPlan handoff 导出（SHA256 payload_hash）
│
└── reference_data/                  — 参考数据层（已从 whale.shared.persistence.template 迁出）
    ├── gbt_30966_fields.py          — GB/T 30966 字段定义
    ├── protocol_param_data.py       — 16 组协议服务参数模板
    ├── protocol_view_defs.py        — 协议参数展平只读视图
    └── sample_data.py               — 13 类端点 / 16 组服务样例数据
```

### `src/starfish/` — 多协议 server simulator 工具层

```text
src/starfish/
├── __main__.py                      — CLI 入口（5 子命令：load-server-plan / smoke-server-plan / probe-server-plan / profile-server-plan / capacity-server-plan）
│
├── models/                          — Starfish 侧最小契约模型
│   └── plan.py                      — StarfishServerPlan / StarfishEndpointPlan / StarfishPointPlan / LoadResult / ValidationResult / UnsupportedOperation
│
├── loader/                          — ServerPlan JSON 加载器
│   └── server_plan_loader.py        — load_server_plan（9 项校验 + payload_hash 复算）
│
├── facade/                          — 协议 server 模拟门面
│   ├── server_simulator_facade.py   — ServerSimulatorFacade（in-memory stub fallback）
│   ├── http_rest_facade.py          — HttpRestFacade（HTTP REST 真实 server，ThreadingHTTPServer）
│   ├── modbus_tcp_facade.py         — ModbusTcpFacade（Modbus TCP 真实 server，FC03 / FC06）
│   ├── mqtt_facade.py               — MqttFacade（轻量 JSON-line TCP server）
│   ├── opcua_facade.py              — OpcUaFacade（open62541 C runner 子进程 real mode）
│   ├── iec104_facade.py             — Iec104Facade（iec104_simulator_server C runner real mode）
│   ├── iec61850_mms_facade.py       — Iec61850MmsFacade（iec61850_simulator_server C runner real mode）
│   ├── iec61850_report_facade.py    — Iec61850ReportFacade（iec61850_report_runner C runner + ReportQueue）
│   ├── iec101_facade.py             — Iec101Facade（**Round 17 一次性收口 + Round 18 扩展 14 TypeId + Round 19 扩展 17 TypeId + Round 20 LinkLayer runtime skeleton + ShortFloat 兼容 + 3 新 capabilities**：codec-enhanced-plus mode 5 级默认，回退 codec-enhanced / codec-skeleton / environment-pending / codebase-pending；TypeId / COT / ASDU / IOA / CA + SIQ / QDS / NVA / ShortFloat IEEE 754 32-bit IE / **ShortFloat 兼容 int/numbers.Real/`__float__` duck typing（Round 20 新增，不引入 numpy 硬依赖）** / **ScaledValue IE 16-bit signed（Round 18 新增）** / **17 信息对象（4 不带时标监视 M_SP_NA_1/M_DP_NA_1/M_ME_NA_1/C_SC_NA_1 + 1 不带时标标度化 M_ME_NB_1 + 1 不带时标短浮点 M_ME_NC_1 + 4 不带时标命令 C_SE_NA_1/C_SE_NB_1/C_SE_NC_1 + 3 带时标命令 C_SE_TA_1/C_SE_TB_1/C_SE_TC_1（**Round 19 新增，12/12/14 字节布局，与 IEC 60870-5-101 §7.2.6.9/10/11 对齐**） + 5 带时标监视 M_SP_TA_1/M_DP_TA_1/M_ME_TA_1/M_ME_TB_1/M_ME_TC_1 = 17；**以 capability 实际值 17 为准，严禁硬写 13/14/15/18**）** / **QOS 结构化（SetPointQualifier 枚举 + SetPointCommandQualifier 显式字段，Round 18 新增）** / **C_SC_NA_1 QU 显式化（CommandPulse + SingleCommandQualifier 子字段）** / ASDU 列表 SQ=0/SQ=1 / FT1.2 帧 / checksum / CP56Time2a 7 字节时标 IE / **5 态链路层 skeleton（IDLE/WAIT_ACK/SEND/RECEIVE/ERROR）+ LinkLayerTimers t1/t2/t3 + LinkControlHelper FCB/FCV helper + balanced/unbalanced 差异化** / **LinkLayerTimerService 抽象 + Default (threading.Timer) + Fake 三实现 + send/receive/on_timeout 完整状态机 + balanced FCB auto flip + retry ERROR（Round 20 新增；默认 `enable_timers=False` 保持 Round 17 行为完全一致）**；codec_capabilities 显式 supports_short_float=true / supports_server=false / supports_serial_runtime=false / supports_cp56time2a=true / supports_link_layer_skeleton=true / **supports_link_layer_timers=true / supports_balanced_fcb_auto_flip=true / supports_retry_skeleton=true（Round 20 新增 3 个）** / **supports_command_codec=true / supports_scaled_value=true / supports_write_runtime=false（**C_SE_* command codec 不得被高估为真实写能力，Iec101Facade.write() 仍抛 UnsupportedOperation**）** / **supported_type_ids=17 TypeId（Round 19 扩展，以 capability 实际值 17 为准）** / **supported_measurement_type_ids / supported_command_type_ids=7 / supported_time_tagged_type_ids=8 / supported_time_tagged_command_type_ids=3（Round 19 新增）** 分组 / **supports_time_tagged_command_codec=true（Round 19 新增）**；**health() reason_text 显式 codec-enhanced-plus + LinkLayer runtime skeleton 7 强制要点（Round 20 同步）+ codec_enhanced_plus_ready 诊断字段**）
│   ├── modbus_tcp_facade.py          — ModbusTcpFacade（Modbus TCP 真实 server：TCP socket, FC03/FC06 + **Round 19 扩展三个公共方法 encode_register_value / decode_register_value / register_encoding_capabilities 真实调用 register_encoding 工具，`register_encoding_runtime=false` 显式**）
│   ├── modbus_rtu_facade.py         — ModbusRtuFacade（rtu-lightweight PTY-backed 8 FCs + 4 异常码 + **Round 19 扩展三个公共方法 encode_register_value / decode_register_value / register_encoding_capabilities 真实调用 register_encoding 工具，`register_encoding_runtime=false` 显式**）
│   ├── ads_facade.py                — AdsFacade（codebase-pending stub + 增强 dotnet / TwinCAT 探针）
│   ├── goose_facade.py              — GooseFacade（environment-pending stub，L2 veth 未就绪）
│   └── sv_facade.py                 — SvFacade（environment-pending stub，L2 veth + PTP 未就绪）
│
├── native/                          — Native Runner 管理框架 + C 源码
│   ├── CMakeLists.txt               — CMake 构建脚本（lib60870 / libiec61850 / libmodbus / open62541）
│   ├── README.md                    — native runner 协议契约（READY / START / RESULT / NOTIFY / QUIT 等）
│   ├── process_handle.py            — NativeProcessHandle 子进程生命周期
│   ├── runner_probe.py              — probe_native_runner 统一 binary 探测
│   ├── runner_spec.py               — NativeRunnerSpec dataclass
│   ├── bin/                         — 预编译 native binary（20 个 runner / simulator）
│   │   ├── iec101_client_runner
│   │   ├── iec101_event_runner
│   │   ├── iec101_simulator_slave
│   │   ├── iec104_client_runner
│   │   ├── iec104_event_runner
│   │   ├── iec104_simulator_server
│   │   ├── iec61850_goose_publisher_simulator
│   │   ├── iec61850_goose_subscriber_runner
│   │   ├── iec61850_mms_client_runner
│   │   ├── iec61850_report_runner
│   │   ├── iec61850_simulator_server
│   │   ├── iec61850_sv_publisher_simulator
│   │   ├── iec61850_sv_subscriber_runner
│   │   ├── modbus_rtu_polling_runner
│   │   ├── modbus_simulator_server
│   │   ├── modbus_tcp_polling_runner
│   │   ├── open62541_client_runner
│   │   ├── open62541_source_simulator
│   │   └── open62541_subscription_runner
│   ├── build/                       — 本地 CMake 构建目录（gitignore）
│   ├── lib60870/                    — lib60870 C runner 源码（IEC 60870-5-101 / 104）
│   │   ├── iec101_client_runner.c
│   │   ├── iec101_event_runner.c
│   │   ├── iec101_simulator_slave.c
│   │   ├── iec104_client_runner.c
│   │   ├── iec104_event_runner.c
│   │   └── iec104_simulator_server.c
│   ├── libiec61850/                 — libiec61850 C runner 源码（MMS / GOOSE / SV）
│   │   ├── iec61850_goose_publisher_simulator.c
│   │   ├── iec61850_goose_subscriber_runner.c
│   │   ├── iec61850_mms_client_runner.c
│   │   ├── iec61850_report_runner.c
│   │   ├── iec61850_simulator_server.c
│   │   ├── iec61850_sv_publisher_simulator.c
│   │   └── iec61850_sv_subscriber_runner.c
│   ├── libmodbus/                   — libmodbus C runner 源码（Modbus TCP / RTU）
│   │   ├── modbus_rtu_polling_runner.c
│   │   ├── modbus_simulator_server.c
│   │   └── modbus_tcp_polling_runner.c
│   └── open62541/                   — open62541 C runner 源码（OPC UA）
│       ├── open62541_client_runner.c
│       ├── open62541_simulator_server.c
│       └── open62541_subscription_runner.c
│
├── protocols/                       — 协议层编解码器
│   ├── iec101/                      — IEC101 编解码器骨架 + 增强（Round 15 codec-enhanced + Round 16 codec-enhanced-plus 起步 + Round 17 一次性收口 + **Round 18 扩展 14 TypeId** + **Round 19 扩展 17 TypeId（3 C_SE_T* 带时标命令）**）
│   │   ├── types.py                 — TypeId 枚举（26 values）/ COT 枚举（26 values，实测）
│   │   ├── asdu.py                  — ASDUHeader 6 字节 encode / decode
│   │   ├── ioa.py                   — IOA 3 字节 encode / decode
│   │   ├── common_address.py        — CA 2 字节 encode / decode
│   │   ├── quality.py               — SIQ / QDS 质量描述符（IntFlag 位标志）encode / decode
│   │   ├── information_elements.py  — NVA 归一化值（16-bit signed）encode / decode + ShortFloat IEEE 754 32-bit IE（NaN/Inf 严格拒绝 + 0.0/-0.0/极值边界，Round 17 新增） + **ShortFloat 兼容 int/numbers.Real/`__float__` duck typing 统一入口（Round 20 新增，不引入 numpy 硬依赖）** + **ScaledValue IE（16-bit signed, range [-32768, 32767]，Round 18 新增）**
│   │   ├── information_object.py    — M_SP_NA_1 / M_DP_NA_1 / M_ME_NA_1 / C_SC_NA_1 + M_SP_TA_1 / M_DP_TA_1 / M_ME_TA_1 带时标 + M_ME_TB_1（10 字节 SVA+QDS+CP56Time2a，Round 17 新增）+ M_ME_TC_1（12 字节 ShortFloat+QDS+CP56Time2a，Round 17 新增）+ **M_ME_NB_1（5 字节 SVA+QDS，不带时标标度化，Round 18 新增）+ M_ME_NC_1（5 字节 ShortFloat+QDS，不带时标短浮点，Round 18 新增）+ C_SE_NA_1（5 字节 NVA+QOS，不带时标归一化值命令，Round 18 新增）+ C_SE_NB_1（5 字节 SVA+QOS，不带时标标度化值命令，Round 18 新增）+ C_SE_NC_1（5 字节 ShortFloat+QOS，不带时标短浮点值命令，Round 18 新增）+ C_SE_TA_1（**12 字节 NVA+QOS+CP56Time2a，带时标归一化值命令，Round 19 新增，与 IEC 60870-5-101 §7.2.6.9 对齐**）+ C_SE_TB_1（**12 字节 SVA+QOS+CP56Time2a，带时标标度化值命令，Round 19 新增，与 §7.2.6.10 对齐**）+ C_SE_TC_1（**14 字节 ShortFloat+QOS+CP56Time2a，带时标短浮点值命令，Round 19 新增，与 §7.2.6.11 对齐**）** + C_SC_NA_1_QU_QUALIFIER 枚举 + CommandPulse 枚举 + SingleCommandQualifier 显式字段（select_execute/qualifier/ql_value/persistent/pulse）+ 旧位级 roundtrip 兼容（Round 17 显式化）+ **SetPointQualifier 枚举（QOS 0-7 标准子字段，Round 18 新增）+ SetPointCommandQualifier 显式字段（select/qualifier/ql_value，Round 18 新增）** 信息对象 encode / decode = **17 TypeId 矩阵（以 capability 实际值 17 为准）**
│   │   ├── codec.py                 — ASDU 信息对象列表 SQ=0 / SQ=1 编解码 + UnknownAsduError + **5 新信息对象 dispatcher（Round 18 扩展 confirmed in `_TYPE_ID_OBJECT_SIZE`）+ 3 新 C_SE_T* dispatcher（Round 19 扩展）** = 17 TypeId
│   │   ├── frame.py                 — FT1.2 固定 / 可变帧 + checksum + 长度不一致检测
│   │   ├── time.py                  — CP56Time2a 7 字节时标 IE（milliseconds / minute / hour / day_of_month / day_of_week / month / year / IV / SU / SB 字段级 + encode / decode + to / from_datetime 转换）— Round 16 新增
│   │   └── link_layer.py            — IEC 60870-5-101 链路层最小状态机骨架（**Round 17 扩展 + Round 20 增强 LinkLayerTimerService + send/receive/on_timeout 状态机 + balanced FCB auto flip + retry ERROR** LinkLayerMode balanced/unbalanced + **LinkState 5 态 IDLE/WAIT_ACK/SEND/RECEIVE/ERROR** + **LinkLayerTimers t1/t2/t3 常量** + LinkEvent + LinkControlHelper build_ack/build_nack/build_reset/build_reset_ack/build_user_data + **fcb_bit_for_sequence/fcv_bit FCB/FCV helper** + LinkLayer feed_frame/bump_send_sequence/**flip_send_sequence/should_retry**/mark_waiting_ack/**mark_sending/mark_receiving**/reset/snapshot + **Round 20 新增 LinkLayerTimerService 抽象 + Default (threading.Timer) + Fake (无 wall-clock) 三实现 + start_timer/cancel_timer/cancel_all/on_timeout API + send_user_data / receive_ack (balanced+FCV=1 自动翻 FCB) / receive_nack (bump_retry/ERROR) / on_timeout (bump_retry；retry_count > max_retries -> ERROR)**，**balanced/unbalanced 差异化 skeleton 行为**，**仅 skeleton 非 server；默认 `enable_timers=False` 保持 Round 17 行为完全一致**）— Round 16 起步，Round 17 扩展，Round 20 增强
│   └── modbus/                      — **Modbus register_encoding 工具子包（Round 18 新增 SF-FR-030 + Round 19 facade 接入，纯 Python CPU 辅助层，非真实设备验证）**
│       ├── __init__.py             — 导出 register_encoding 模块（5 value_type × 4 byte/word 组合 = 20 组合 + NaN/Inf 拒绝 + 越界/长度错误检测）
│       └── register_encoding.py    — encode_register(value, value_type, byte_order) / decode_register(registers, value_type, byte_order)；value_type ∈ {uint16, int16, uint32, int32, float32}；byte_order ∈ {big-big, little-little, big-little, little-big}；float32 NaN/Inf 严格拒绝（ModbusFloatValueError 异常）；**Modbus facade（modbus_tcp_facade.py / modbus_rtu_facade.py）Round 19 接入** 三个公共方法 `encode_register_value` / `decode_register_value` / `register_encoding_capabilities` 真实调用 register_encoding 工具；`register_encoding_runtime=false` 显式
│
├── tools/                           — 工具层（probe / profile / capacity）
│   ├── probe.py                     — run_probe 最小启动-健康-读取探测
│   ├── profile.py                   — run_profile N 次 read 采样耗时统计
│   └── capacity.py                  — run_capacity 端点 / 点位 / 读取容量扫描
│
└── registry/                        — 运行时注册表
    └── runtime_registry.py          — RuntimeRegistry / FacadeEntry（9 模式 dispatch：real / stub / mqtt-lightweight / codec-enhanced-plus / codec-enhanced / codec-skeleton / rtu-lightweight / codebase-pending / environment-pending — Round 16 新增 codec-enhanced-plus）

状态标注：
- 13 协议 facade 全覆盖（HTTP_REST / MODBUS_TCP / MQTT / OPC_UA / IEC104 / IEC61850_MMS / IEC61850_Report / IEC101 / MODBUS_RTU / Beckhoff_ADS / GOOSE / SV）
- real mode: HTTP_REST, MODBUS_TCP, OPC_UA, IEC104, IEC61850_MMS, IEC61850_Report
- mqtt-lightweight mode: MQTT
- rtu-lightweight mode: MODBUS_RTU（PTY-backed，8 FCs + 4 异常码）
- codec-enhanced-plus mode: IEC101（**Round 17 一次性收口 + Round 18 扩展 14 TypeId + Round 19 扩展 17 TypeId + Round 20 增强 LinkLayer runtime skeleton + ShortFloat duck typing + balanced FCB auto flip + retry ERROR + Round 21 总收口**：CP56Time2a 7 字节时标 IE + **ShortFloat IEEE 754 32-bit IE** + **ShortFloat duck typing 兼容（Round 20 收口，int / float / `numbers.Real` / `__float__`，不引入 numpy 硬依赖）** + 3 带时标 TypeID M_SP_TA_1/M_DP_TA_1/M_ME_TA_1 + **2 带时标短浮点 M_ME_TB_1/M_ME_TC_1** + C_SC_NA_1 QU 显式化（CommandPulse + SingleCommandQualifier 子字段）+ **5 态链路层 skeleton（IDLE/WAIT_ACK/SEND/RECEIVE/ERROR）+ LinkLayerTimers t1/t2/t3 + LinkControlHelper FCB/FCV helper + balanced/unbalanced 差异化** + **LinkLayerTimerService 抽象 + Default (threading.Timer) + Fake 三实现 + 完整 send/receive/on_timeout 状态机 + balanced FCB auto flip（Round 20 收口）+ retry ERROR（Round 20 收口）+ 默认 enable_timers=False（Round 20 显式）** + SIQ / QDS / NVA / 4 信息对象 / ASDU 列表 SQ=0/SQ=1 / FT1.2 帧 / checksum + **ScaledValue IE（16-bit signed，Round 18 新增）+ QOS 结构化（SetPointQualifier 枚举 + SetPointCommandQualifier 显式字段，Round 18 新增）+ 5 新信息对象（M_ME_NB_1/M_ME_NC_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1，Round 18 新增）+ 3 新带时标命令（C_SE_TA_1/C_SE_TB_1/C_SE_TC_1，Round 19 收口，12/12/14 字节布局，与 IEC 60870-5-101 §7.2.6.9/10/11 对齐）**；capabilities 显式 supports_server=false / supports_serial_runtime=false / supports_cp56time2a=true / supports_short_float=true / supports_link_layer_skeleton=true / **supports_command_codec=true / supports_scaled_value=true / supports_write_runtime=false** / **supports_time_tagged_command_codec=true（Round 19 收口）** / **supports_link_layer_timers=true / supports_balanced_fcb_auto_flip=true / supports_retry_skeleton=true（Round 20 收口）** / **supported_type_ids=17 TypeId（Round 19 扩展：4 不带时标监视 + 1 不带时标标度化 + 1 不带时标短浮点 + 4 不带时标命令 + 3 带时标命令 + 5 带时标监视 = 17；以 capability 实际值 17 为准，严禁硬写 13/14/15/18）** / **supported_measurement_type_ids / supported_command_type_ids=7（Round 19 升级） / supported_time_tagged_type_ids=8（Round 19 升级） / supported_time_tagged_command_type_ids=3（Round 19 收口） 分组**；**health() reason_text 显式 codec-enhanced-plus 17 TypeId + LinkLayer runtime skeleton 7 强制要点（Round 20 同步）+ codec_enhanced_plus_ready 诊断字段**；**仅 skeleton 非 server / 非真实 write runtime**；**Round 21 总收口真实剩余项（仍 deferred，**不**得高估为已实现）**：真实 IEC101 server / 真实串口通信 / 完整 balanced/unbalanced runtime / GOOSE/SV L2 环境 / Beckhoff_ADS 真实环境 / Modbus 真实设备 / 现场部署）— Round 16 起步，Round 17 一次性收口，Round 18 扩展 14，Round 19 扩展 17，Round 20 增强，Round 21 总收口
- codec-enhanced mode: IEC101（SIQ / QDS / NVA / 4 信息对象 / ASDU 列表 SQ=0/SQ=1 / FT1.2 帧 / checksum；capabilities 显式 supports_server=false / supports_serial_runtime=false）— Round 15 升级
- codec-skeleton mode: IEC101（TypeId / COT / ASDU / IOA / CA 编解码就绪；codec-enhanced 不可用时回退）
- codebase-pending: Beckhoff_ADS（无 Python 原生 ADS 实现）
- environment-pending: GOOSE / SV（需 L2 veth + raw socket / CAP_NET_RAW / PTP）
- native runner 框架: 6 协议族 C 源码（lib60870 / libiec61850 / libmodbus / open62541）+ 20 个预编译 binary
- subscribe 语义: MqttFacade SubscriptionQueue 已实现；其他 facade subscribe 仍 NOT_IMPLEMENTED
- report 语义: IEC61850 Report facade ReportQueue 已实现，不再全 NOT_IMPLEMENTED
- 不得 import seahorse / whale.ingest / whale.shared.source
- 不等同于多协议完整 simulator
```

## 项目级测试 `tests/`

```text
tests/
├── __init__.py
├── conftest.py                      — 全局 pytest 夹具
├── TESTING.md                       — BlueCrystal 主平台测试指南（P1-P7 生命周期阶段）
│
├── unit/                            — P1 单元测试
│   ├── seahorse/                    — Seahorse 测试（8 个）
│   │   ├── test_bundle.py           — Bundle 模型 / 导出 / 校验 / CLI
│   │   ├── test_compat_wrappers.py  — 旧路径 DeprecationWarning wrapper 兼容性
│   │   ├── test_generators.py       — AlarmGenerator + ControlResultGenerator
│   │   ├── test_models.py           — 14 个核心 dataclass 构造 / 序列化
│   │   ├── test_orchestrator.py     — SeahorseGenerator 5 元组完整生成
│   │   ├── test_reference_data_imports.py — reference_data 导出完整性
│   │   ├── test_server_plan.py      — ServerPlan validator + handoff exporter + CLI
│   │   └── test_strategies.py       — Random / Curve / Replay + StrategyRegistry
│   ├── starfish/                    — Starfish 测试（15 个）
│   │   ├── test_iec101_codec.py     — IEC101 编解码器头部测试（40 tests；**Round 17 增 codec-enhanced-plus reason 文本一致性断言 + codec_enhanced_plus_ready 诊断字段断言**；**Round 18 增 supports_command_codec=true/supports_scaled_value=true/supports_write_runtime=false 显式声明断言 + 14 TypeId 矩阵分组断言**；**Round 19 增 TestIec101CodecRound19** capabilities 17/7/3 数字断言 + supported_time_tagged_command_type_ids=3 断言 + supports_time_tagged_command_codec=true 断言 + probe_iec101_codec_enhanced_plus 验证 17 TypeId 矩阵断言；**Round 20 增 TestIec101CodecRound20**：3 新 capabilities 数字断言（supports_link_layer_timers=true / supports_balanced_fcb_auto_flip=true / supports_retry_skeleton=true）+ 7 强制要点 reason_text 验证）
│   │   ├── test_iec101_information_elements.py — IEC101 信息体元素测试（**Round 17 扩展**至包含 ShortFloat IEEE 754 + M_ME_TB_1/M_ME_TC_1 元素级；NVA 24 + CP56Time2a 27；**Round 18 扩展 +ScaledValue IE 测试（16-bit signed, range [-32768, 32767]）**；**Round 20 增 TestShortFloatRound20Compat**：int 输入接受 / Decimal 输入接受 / Fraction 输入接受 / `__float__` duck typing 接受 / NaN/Inf 仍严格拒绝 / 极值 roundtrip；**不引入 numpy 硬依赖**）
│   │   ├── test_iec101_asdu_objects.py — IEC101 信息对象 + ASDU 列表测试（**Round 17 扩展**至包含带时标短浮点 M_ME_TB_1/M_ME_TC_1 + C_SC_NA_1 QU 显式化；4 不带时标 + 5 带时标 + QU 显式化；**Round 18 扩展 +5 新信息对象（M_ME_NB_1/M_ME_NC_1/C_SE_NA_1/C_SE_NB_1/C_SE_NC_1）roundtrip + QOS 结构化 SetPointQualifier 枚举 + SetPointCommandQualifier 显式字段测试**；**Round 19 扩展 +6 个 C_SE_T* test classes**：test_c_se_ta_1_roundtrip + test_c_se_tb_1_roundtrip + test_c_se_tc_1_roundtrip + test_c_se_t_a_byte_layout + test_c_se_t_b_byte_layout + test_c_se_t_c_byte_layout 验证 12/12/14 字节布局与 COT 字段）
│   │   ├── test_iec101_ft12_frame.py — IEC101 FT1.2 链路帧测试（36 tests）
│   │   ├── test_iec101_link_layer.py — IEC101 链路层最小状态机骨架测试（**Round 17 扩展**至包含 LinkLayerTimers t1/t2/t3 + FCB/FCV helper + 5 态 + balanced/unbalanced 差异化；**Round 20 增强** LinkLayerTimerService 抽象 + Default (threading.Timer) + Fake (无 wall-clock) + send/receive/on_timeout 完整状态机 + balanced FCB auto flip + retry ERROR；**Round 20 新增 8 个 test classes**：TestLinkLayerTimerService + TestDefaultLinkLayerTimerService + TestFakeLinkLayerTimerService + TestLinkLayerSendUserData + TestLinkLayerReceiveAck + TestLinkLayerReceiveNack + TestLinkLayerOnTimeout + TestLinkLayerSequenceStateMachine）— Round 16 起步，Round 17 扩展，Round 20 增强
│   │   ├── test_modbus_register_encoding.py — **Modbus register_encoding 工具子包测试（Round 18 新增 SF-FR-030，164 tests）**：5 value_type（uint16/int16/uint32/int32/float32）× 4 byte_order 组合（big-big/little-little/big-little/little-big）= 20 组合 roundtrip + 边界 + 极值 + 越界检测 + 长度错误检测 + float32 NaN/Inf 严格拒绝；**纯 Python CPU 辅助层，非 Modbus 真实设备验证**
│   │   ├── test_iec61850_facade.py  — IEC61850 MMS / Report facade
│   │   ├── test_modbus_rtu_facade.py — Modbus RTU facade（8 FCs / 4 异常码 / PTY；**Round 19 扩展 +encode_register_value/decode_register_value/register_encoding_capabilities 三方法** + 5 value_type × 4 byte/word 组合 = 20 组合 roundtrip + register_encoding 工具输出一致性 + register_encoding_runtime=false 边界）
│   │   ├── test_mqtt_facade.py      — MqttFacade 轻量 TCP server
│   │   ├── test_native_runner_framework.py — Native Runner 框架
│   │   ├── test_opcua_iec104_facade.py — OPC_UA / IEC104 facade
│   │   ├── test_probe_profile_capacity.py — probe / profile / capacity
│   │   ├── test_protocol_facade.py  — 协议专用 facade（含 RuntimeRegistry dispatch；**Round 19 扩展 +Modbus TCP/RTU facade register_encoding 集成测试** encode_register_value/decode_register_value/register_encoding_capabilities + 5 value_type × 4 byte/word 组合 + register_encoding 工具输出一致性 + register_encoding_runtime=false 边界）
│   │   ├── test_remaining_protocols.py — 3 pending facade（Beckhoff_ADS / GOOSE / SV）
│   │   ├── test_server_plan_loader.py — ServerPlan JSON loader
│   │   ├── test_server_simulator_facade.py — ServerSimulatorFacade stub
│   │   └── test_starfish_cli.py     — Starfish CLI（5 子命令 + per-endpoint mode）
│   ├── shared/
│   │   └── persistence/             — shared persistence 单测
│   │       ├── test_model_asset_orm.py
│   │       ├── test_scada_protocol_params.py
│   │       ├── test_scada_protocol_views.py
│   │       └── test_scada_sample_data_protocol_coverage.py
│   └── （根目录 80+ 个 ingest / message_pipeline / speed_layer / storage / source 单测）
│       test_acquisition_job_handler.py
│       test_config.py
│       test_dual_node_write_lease_conflict.py
│       test_http_rest_backend.py
│       test_http_rest_source_acquisition_adapter.py
│       test_iec101_backend.py
│       test_iec101_source_acquisition_adapter.py
│       test_iec104_backend.py
│       test_iec104_source_acquisition_adapter.py
│       test_iec104_source_write_adapter.py
│       test_iec61850_mms_backend.py
│       test_iec61850_report_acquisition_adapter.py
│       test_iec61850_report_backend.py
│       test_iec61850_source_acquisition_adapter.py
│       test_iec61850_source_write_adapter.py
│       test_ingest_api_app.py
│       test_ingest_audit_event_schema.py
│       test_ingest_audit_redaction.py
│       test_ingest_bundle_checksum.py
│       test_ingest_bundle_redaction.py
│       test_ingest_composition_injection.py
│       test_ingest_file_ingest_decoder.py
│       test_ingest_file_ingest_detector.py
│       test_ingest_file_ingest_models.py
│       test_ingest_file_ingest_repository.py
│       test_ingest_file_ingest_service.py
│       test_ingest_job_lease.py
│       test_ingest_metrics_events.py
│       test_ingest_no_source_lab_imports.py
│       test_ingest_observability_sink.py
│       test_ingest_readyz.py
│       test_ingest_runtime_entrypoint.py
│       test_ingest_runtime_modes.py
│       test_ingest_runtime_orm_models.py
│       test_ingest_runtime_scheduler_import.py
│       test_ingest_security_partition_config.py
│       test_ingest_source_adapter_capability_matrix.py
│       test_ingest_write_lease.py
│       test_ingest_write_lease_fencing.py
│       test_ingest_write_security_profile.py
│       test_kafka_message_publisher.py
│       test_message_pipeline_adapters.py
│       test_message_pipeline_envelope.py
│       test_message_pipeline_kafka_adapter.py
│       test_message_pipeline_ports.py
│       test_modbus_rtu_backend.py
│       test_modbus_rtu_source_acquisition_adapter.py
│       test_modbus_source_acquisition_adapter.py
│       test_modbus_source_write_adapter.py
│       test_model_asset_detector.py
│       test_model_asset_models.py
│       test_model_asset_repository.py
│       test_model_asset_service.py
│       test_mqtt_backend.py
│       test_mqtt_source_acquisition_adapter.py
│       test_opcua_adapter_resolution.py
│       test_opcua_source_acquisition_adapter.py
│       test_opcua_source_write_adapter.py
│       test_open62541_backend.py
│       test_polling_acquisition_role.py
│       test_redis_source_state_cache.py
│       test_redis_streams_message_publisher.py
│       test_relational_outbox_message_publisher.py
│       test_scheduler_job_routes.py
│       test_shared_source_runner_resolution.py
│       test_source_acquisition_port_registry.py
│       test_source_acquisition_use_case.py
│       test_source_command_audit.py
│       test_source_command_authorization_guard.py
│       test_source_command_lease_release.py
│       test_source_command_use_case.py
│       test_source_command_write_lease_guard.py
│       test_source_runtime_config_repository.py
│       test_source_scheduling.py
│       test_source_write_port_registry.py
│       test_speed_layer_light_processor.py
│       test_speed_layer_pipeline_runner.py
│       test_speed_layer_preprocessing.py
│       test_state_snapshot_publish_use_case.py
│       test_storage_raw_archive.py
│       test_storage_raw_index.py
│       test_storage_serving_cache.py
│       test_storage_simulation_result.py
│       test_storage_standardized.py
│       test_storage_waveform.py
│       test_subscription_acquisition_role.py
│       test_subscription_reconnect_baseline.py
│       test_subscription_reconnect_runtime.py
│       test_turtle_octopus_import_boundary.py
│       test_worker_runtime_do_execute.py
│
├── architecture/                    — 架构边界与 import 门禁测试
│   ├── test_seahorse_import_boundary.py — seahorse / ingest / starfish import boundary
│   └── test_starfish_import_boundary.py — starfish / seahorse / ingest import boundary（**Round 19 扩展** Round 19 3 C_SE_T* 带时标命令 + Modbus TCP/RTU facade 接入 register_encoding 工具 + 第三方代码零入侵验证）
│
├── integration/                     — P3 集成测试（80+ 个）
│   ├── test_framework_db_init.py
│   ├── test_http_rest_acquisition_chain.py
│   ├── test_iec101_acquisition_chain.py
│   ├── test_iec104_acquisition_chain.py
│   ├── test_modbus_rtu_acquisition_chain.py
│   ├── test_mqtt_acquisition_chain.py
│   ├── test_message_pipeline_inmemory_e2e.py
│   ├── test_message_pipeline_kafka_e2e.py
│   ├── test_ingest_api_*.py          — 18 个 API 集成（CRUD / 审计 / 授权 / 幂等 / dry-run / 全矩阵）
│   ├── test_ingest_audit_*.py        — 4 个审计集成（DB / JSONL 一致性 / 矩阵）
│   ├── test_ingest_bundle_*.py       — 3 个 bundle 集成（导入导出 / 单向流 / 安全分区）
│   ├── test_ingest_cache_to_kafka_pipeline.py
│   ├── test_ingest_dual_node_db_lease_e2e.py
│   ├── test_ingest_external_*.py     — 外部访问策略 / 审计 sink 合同
│   ├── test_ingest_file_ingest_integration.py
│   ├── test_ingest_*_source_write.py — 4 个协议写入集成（Modbus / OPC UA / IEC104 / IEC61850）
│   ├── test_ingest_iec61850_report_subscription.py
│   ├── test_ingest_lightweight_load_gate.py
│   ├── test_ingest_observability_sink_smoke.py
│   ├── test_ingest_polling_retry_to_redis.py
│   ├── test_ingest_prodlike_*.py     — 14 个 prodlike 集成（访问策略 / 审计 sink / Kafka / PG / Redis / 性能 / endurance / 故障注入 / 调度背压 / worker failover）
│   ├── test_ingest_runtime_*.py      — 6 个 runtime / alembic 集成
│   ├── test_ingest_scheduler_*.py    — 7 个 scheduler 集成（主备 / APScheduler / 集群分配 / 双活 / 优雅关闭 / missed tick / 错峰）
│   ├── test_ingest_security_partition_*.py — 2 个安全分区集成
│   ├── test_ingest_source_*.py       — 4 个 source 采集集成
│   ├── test_ingest_subscription_strategy.py
│   ├── test_ingest_worker_runtime_*.py — 3 个 WorkerRuntime 集成
│   ├── test_ingest_write_lease_fencing_e2e.py
│   ├── test_l5_external_dependency_verification.py — P5 准生产依赖验证期
│   ├── test_model_asset_*.py         — 3 个 model_asset 集成（含 Alembic + PG）
│   ├── test_redis_state_cache_faults.py
│   ├── test_shared_persistence_sample_data_init.py
│   ├── test_speed_layer_*.py         — 3 个 speed_layer 集成（DLQ / replay / 索引 / 原始归档）
│   ├── test_sqlite_config_init.py
│   ├── test_storage_*.py             — 2 个 TDengine 集成（waveform / simulation_result）
│   └── test_whale_writer_*.py        — 2 个 writer 故障恢复 / 主备切换
│
├── e2e/                             — P4 端到端测试
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_whale_field_minimal_smoke.py — BlueCrystal 现场最小数据链路 P4 smoke
│   ├── test_whale_l5_kafka_pipeline_e2e.py — P5 Kafka pipeline E2E
│   └── test_whale_l5_storage_e2e.py   — P5 storage E2E（S3 / TDengine / Redis）
│
├── performance/                     — 性能测试
│   ├── load/                         — 负载测试
│   │   └── conftest.py
│   ├── stress/
│   │   └── test_acquisition_pipeline_stress.py
│   └── endurance/                    — 耐久测试（待实现）
│
└── support/                         — 测试支撑模块
    ├── ingest_prodlike_runtime.py    — prodlike compose / 故障注入辅助
    ├── scada_sample_db.py            — SCADA 样例 SQLite / PG 初始化辅助
    └── shared_persistence_sample_db.py — shared persistence 样例 PG 初始化辅助
```

> 历史清理记录：
>
> - `tools/source_lab/` 与 `tests/support/source_lab_runtime.py` 已在 Round 11 物理删除（Round 12 dead path / fixture 最终清理收口）。
> - `tests/integration/test_source_lab_beckhoff_ads_runtime.py`、`test_source_lab_scada_profile.py`、`test_source_lab_scada_profile_postgres.py` 已删除。
> - `tests/unit/test_fleet_update_selection.py` 已删除。
> - `scripts/run_source_lab_l2_standalone_gate.sh`、`scripts/run_source_lab_raw_socket_dynamic_gate.sh`、`scripts/source_lab_l2_test_env.sh` 已删除。
> - 所有协议能力（13 协议 facade + probe / profile / capacity + native runner）已迁移至 `src/starfish/`。
> - 5 个 Starfish facade C binary 路径已从 `tools/source_lab/native/build/` 迁移至 `src/starfish/native/bin/`，并新增 4 族 C 源码（lib60870 / libiec61850 / libmodbus / open62541）。

## AI 配置 `ai_shared/`

```text
ai_shared/
├── agent_config/                     — AI Agent 共享配置
│   ├── hooks/                        — 共享 hook 脚本（4 个）
│   │   ├── block-dangerous-bash.py   — 危险命令拦截
│   │   ├── docstring-cn-gate.py      — 中文 docstring 门禁
│   │   ├── no-source-lab-import-gate.sh — source_lab 导入门禁
│   │   └── comment-doc-gate.py        — 注释文档门禁
│   └── skills/                       — 规范源 skill 定义（8 个）
│       ├── changed-files-gate/       — 变更范围门禁
│       ├── code-quality-gate/        — 代码质量门禁
│       ├── commit-message/           — 提交信息生成
│       ├── heavy-regression/         — 重回归测试
│       ├── project-tree-reset/       — 目录树全量重建
│       ├── project-tree-update/      — 目录树增量更新
│       ├── requirement-trace/        — 需求跟踪表更新
│       └── rule-update/              — 公共规则更新
├── templates/                        — 模板文件
│   └── coding_agent_prompt_template.txt
├── memory/                           — 长期记忆
│   ├── project_tree.md               — 本文件
│   ├── test_index.md                 — 测试资产索引与回归测试唯一索引
│   ├── 业务目标与价值愿景.md           — 项目白皮书
│   ├── 总体逻辑设计.md                — 项目白皮书
│   ├── BlueCrystal_REQ_README.md           — 需求文档规范说明
│   ├── BlueCrystal_REQ_Project.md          — 项目层面需求说明
│   ├── BlueCrystal_REQ_Ingest.md           — 采集模块需求
│   ├── BlueCrystal_REQ_SourceLab.md        — source_lab 需求
│   ├── BlueCrystal_REQ_SharedSource.md     — 共享源层需求
│   ├── BlueCrystal_REQ_Storage.md          — 存储模块需求
│   ├── BlueCrystal_REQ_MessagePipeline.md  — 消息管道需求
│   ├── BlueCrystal_REQ_BatchLayer.md       — 批处理层需求
│   ├── BlueCrystal_REQ_BatchProcessing.md  — 批处理模块需求
│   ├── BlueCrystal_REQ_SpeedLayer.md       — 速度层需求
│   ├── BlueCrystal_REQ_ServingAggregation.md — 服务聚合模块需求
│   ├── PlatformShared_REQ_Crosscutting.md — 全系统公共基础库需求
│   ├── Turtle_REQ.md                 — Turtle 治理控制面需求
│   ├── Octopus_REQ.md                — Octopus 运维执行面需求
│   ├── Seahorse_REQ.md               — Seahorse 样例场站生成器需求
│   └── Starfish_REQ.md               — Starfish 协议 server 模拟工具层需求
├── reports/                          — agent 反馈与验收归档
│   ├── testing_lifecycle_and_repo_audit_round1_closure_report.md
│   ├── testing_directory_governance_round2_closure_report.md
│   ├── testing_directory_governance_round3_closure_report.md
│   ├── code_reality_docstring_audit_round1_report.md
│   ├── code_reality_docstring_audit_round2_report.md
│   ├── model_asset_round_c_closure_report.md
│   ├── whale_l5_real_chain_round2_closure_report.md
│   ├── whale_l5_true_external_chain_round3_closure_report.md
│   ├── whale_l5_definition_req_cleanup_round4_closure_report.md
│   ├── whale_l5_external_dependency_round5_closure_report.md
│   ├── whale_field_ready_baseline_round6_closure_report.md
│   ├── p5_external_dependency_final_closure_report.md
│   ├── p5_external_dependency_regression_round1_closure_report.md
│   ├── p5_external_dependency_regression_round2_closure_report.md
│   ├── starfish_round5_serverplan_loader_cleanup_report.md
│   ├── starfish_round6_real_server_lifecycle_inventory_report.md
│   ├── starfish_round7_mqtt_probe_profile_capacity_report.md
│   ├── starfish_round8_opcua_iec104_lifecycle_report.md
│   ├── starfish_round9_iec61850_mms_report_lifecycle_report.md
│   ├── starfish_round10_final_cleanup_closure_report.md
│   ├── starfish_round11_sourcelab_tools_physical_purge_report.md
│   ├── starfish_round12_dead_path_fixture_final_purge_report.md
│   ├── starfish_round13_remaining_protocol_enhancement_report.md
│   ├── starfish_round14_modbus_rtu_iec101_codec_report.md
│   ├── starfish_round15_iec101_codec_enhanced_report.md
│   ├── starfish_round16_iec101_time_linklayer_report.md
│   ├── starfish_round17_iec101_final_codec_closure_report.md
│   ├── seahorse_round1_reference_data_models_boundary_report.md
│   ├── seahorse_round2_generation_strategy_data_report.md
│   ├── seahorse_round3_bundle_export_cli_report.md
│   └── seahorse_round4_serverplan_starfish_contract_report.md
└── rules/                            — 公共规则
    ├── routing.md                    — 规则路由
    ├── coding.md                     — 编码规范
    ├── testing.md                    — 测试规范
    ├── documentation.md              — 文档规范
    ├── reporting.md                  — 反馈规范
    ├── validation-routing.md         — 验证路由
    ├── python-docstring-cn.md        — Python 中文 docstring 规范
    └── quality-gate.md               — 代码质量门禁规则
```

## 文档 `docs/`

```text
docs/
├── GIT.md                            — Git 工作流说明
├── opcua_iec61850_guide.md           — OPC UA / IEC 61850 协议指南
├── 代码质量与注释.md                  — 代码质量规范（已过时，权威源 ai_shared/rules/）
├── 工程管理.md                        — 工程管理流程说明
└── 测试策略.md                        — 测试策略说明（已过时，权威源 ai_shared/rules/testing.md）
```

## 脚本 `scripts/`

```text
scripts/
├── cleanup_root_logs.sh              — 清理根目录日志
├── whale_test.sh                     — BlueCrystal 测试统一入口（dry-run 默认 + --execute 显式）
├── check_ads_env.py                  — Beckhoff ADS 环境预检
├── check_l2_goose_sv_env.py          — GOOSE / SV L2 环境预检
├── check_l5_field_readback_env.py    — P5 外部依赖环境预检
├── check_serial_env.py               — 串口硬件环境预检
├── run_quality_gate.py               — CI 质量门禁聚合（6 gates）
├── run_ingest_dev.sh                 — 启动 ingest 开发环境
├── run_ingest_runtime_compose_smoke.sh — ingest compose 运行态烟测
├── run_ingest_compose_readyz_e2e.sh  — compose readyz 8 组件 E2E
├── run_ingest_write_readback_smoke.sh — 三协议 simulator / native write-readback smoke
├── run_ingest_pg_lease_fault_injection.sh — PG / readyz prodlike fault injection
├── run_ingest_bundle_one_way_flow_smoke.sh — Bundle 单向流 smoke
├── run_ingest_prodlike_performance_profile.sh — 性能 profile smoke
├── run_ingest_prodlike_dependency_smoke.sh — prodlike 依赖烟测
├── run_ingest_prodlike_endurance_smoke.sh — prodlike endurance 烟测
├── run_pg_migration_matrix.sh        — PG 迁移矩阵自动化
├── ci_ingest_runtime_gate.sh         — CI 门禁脚本（7 个门禁组）
├── validate_shared_source_production_runner.sh — shared_source runner 路径解析契约验证
├── test_ingest_write_readback_smoke_contract.sh — write-readback smoke 入口 CLI 契约自检
├── run_whale_field_minimal_smoke.sh  — BlueCrystal 现场最小数据链路 smoke
├── run_whale_field_quality_gate.sh   — BlueCrystal 现场质量门禁聚合
├── run_whale_field_ready_smoke.sh    — BlueCrystal 一键预检验证（8-step）
├── run_whale_writer_switchover.sh    — BlueCrystal writer 主备切换验证
├── run_whale_l5_external_dependency_probe.sh — P5 外部依赖探测（16 probes）
├── start_whale_p5_dependencies.sh    — P5 外部依赖启动（Docker 不可用时 NOT_RUN）
├── stop_whale_p5_dependencies.sh     — P5 外部依赖停止 / 清理
├── run_whale_p5_external_dependency_regression.sh — P5 外部依赖回归
└── diagnose_whale_p5_dependencies.sh — P5 外部依赖诊断（5 依赖逐项）
```

## 部署 `deploy/`

```text
deploy/
├── whale/                            — BlueCrystal 现场部署
│   ├── README.md                     — BlueCrystal 部署总览（MISSING_ENVIRONMENT 标记）
│   ├── .env.whale.field.example      — 现场部署完整环境变量模板
│   ├── ingest/                       — BlueCrystal Ingest 部署
│   │   ├── .env.ingest.example       — ingest 环境变量模板
│   │   ├── README.md                 — Ingest 部署说明
│   │   ├── Dockerfile                — ingest 统一 runtime 镜像（build context = repo 根）
│   │   ├── docker-compose.ingest-dev.yaml      — ingest 开发栈（PG + Redis + Kafka + ingest-runtime）
│   │   └── docker-compose.ingest-prodlike.yaml — ingest 准生产栈（PG + Redis + Kafka + api + workers）
│   ├── message_pipeline/             — Kafka P5 准生产验证通过；Pulsar MISSING_ENVIRONMENT
│   │   ├── README.md                 — 消息管道部署说明
│   │   └── docker-compose.whale-l5.yaml        — L5 端到端外部依赖栈
│   ├── speed_layer/                  — InMemory 生产就绪；Flink MISSING_ENVIRONMENT
│   │   ├── README.md                 — 速度层 writers 部署说明
│   │   ├── .env.p5.example           — P5 环境变量模板（无真实密钥）
│   │   └── docker-compose.p5.yml               — P5 最小外部依赖栈
│   └── storage/README.md             — TDengine / S3 / Redis P5 准生产验证通过；HDFS MISSING_ENVIRONMENT
├── turtle/README.md                  — Turtle 部署说明
└── octopus/README.md                 — Octopus 部署说明
```

## AI 工具配置

```text
.claude/                              — Claude Code 配置
├── settings.json                     — Claude Code 全局设置
├── agents/                           — 3 个子代理定义
│   ├── code-implementer.md           — 编码实现子代理
│   ├── project-steward.md            — 文档与目录树子代理
│   └── test-validator.md             — 独立验证子代理
└── skills/                           — 9 个 Claude Code 技能（与 ai_shared/agent_config/skills 同源）

.agents/                              — Codex agent 配置
└── skills                            — 软链至 .claude/skills

.codex/                               — OpenAI Codex 适配配置
├── config.toml                       — Codex 配置
├── hooks.json                        — Codex hook 定义
└── agents/                           — 3 个子代理定义（code-implementer / project-steward / test-validator）
```

## 第三方库 `third_party/`

```text
third_party/                          — 第三方 C 协议栈源码与预编译库
├── setup_env.sh                      — 第三方库环境安装脚本
├── install/                          — 预编译头文件与库
│   ├── include/
│   │   ├── lib60870/                 — lib60870 头文件
│   │   └── libiec61850/              — libiec61850 头文件
│   ├── lib/                          — 静态 / 动态库
│   └── share/                        — cmake / pkgconfig 共享数据
├── lib60870/                         — lib60870 源码（IEC 60870-5-101 / 104）
├── libiec61850/                      — libiec61850 源码（IEC 61850 MMS / GOOSE / SV）
└── open62541/                        — open62541 源码（OPC UA 协议栈）
```

> 注：Starfish native runner 使用的 C 源码副本（仅与本项目相关的 runner / simulator 入口）已迁入 `src/starfish/native/{lib60870,libiec61850,libmodbus,open62541}/`；`third_party/` 仍保留完整上游源码与预编译库供 native runner CMake 构建使用。
