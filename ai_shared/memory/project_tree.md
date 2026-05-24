# Whale 项目目录树

> 能源数据统一平台（风光储电场数据接入底座）
> 最后更新: 2026-05-24

本文件维护完整文件级目录树，每个 item 附简短职责注释（不超过 40 中文字符）。
只用于导航，不替代读取当前源码。

## 根目录

```text
/ (Whale)
├── CLAUDE.md                        — Claude Code / Codex 共用执行入口
├── AGENTS.md                        — Codex 自动读取入口，指向 CLAUDE.md
├── README.md                        — 项目简介与快速开始
├── pyproject.toml                   — 项目元数据、依赖与工具配置
├── requirements.txt                 — Python 依赖声明
├── docker-compose.ingest-dev.yaml   — ingest 开发环境 Docker 编排
├── .flake8                          — flake8 代码检查配置
├── .gitignore                       — Git 忽略规则
├── .env.ingest.example              — ingest 环境变量模板
├── .vscode/settings.json            — VSCode 编辑器配置
├── config/                          — 运行时配置（当前为空目录）
│
├── src/                             — 主源码根目录
├── tests/                           — 项目级测试根目录
├── tools/                           — 工具包根目录
├── ai_shared/                       — AI 配置、规则与记忆
├── docs/                            — 项目文档
├── scripts/                         — 运维与开发脚本
├── .claude/                         — Claude Code 配置与技能
├── .agents/                         — Codex agent 配置与技能
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
│   │   ├── diagnostics.py           — 诊断接口
│   │   ├── message/                 — 消息发布端口
│   │   │   └── message_publisher_port.py
│   │   ├── runtime/                 — 运行时配置端口
│   │   │   └── source_runtime_config_port.py
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
│   │   │   ├── opcua_source_write_adapter.py                 — OPC UA 写入适配器
│   │   │   ├── static_source_acquisition_port_registry.py    — 静态采集端口注册表
│   │   │   └── static_source_write_port_registry.py          — 静态写入端口注册表
│   │   └── state/                   — 状态缓存适配器
│   │       └── redis_source_state_cache.py  — Redis 状态缓存
│   │
│   ├── runtime/                     — 运行时组件
│   │   ├── acquisition_mode.py              — 采集模式枚举
│   │   ├── job_status.py                    — 作业状态定义
│   │   ├── message_pipeline_settings.py     — 管道参数设置
│   │   ├── scheduler.py                     — 调度器主逻辑
│   │   ├── scheduler_factory.py             — 调度器工厂
│   │   ├── scheduler_job.py                 — 调度作业封装
│   │   └── scheduler_settings.py            — 调度器参数
│   │
│   ├── decorators/                   — 装饰器
│   │   ├── source_acquisition.py     — 采集流程装饰器
│   │   └── state_cache.py            — 状态缓存装饰器
│   │
│   ├── framework/persistence/        — 持久化框架
│   │   ├── base.py                   — ORM 声明基类
│   │   ├── init_db.py                — 数据库初始化
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
│   ├── test_open62541_backend.py      — open62541 后端测试
│   ├── test_polling_acquisition_role.py   — 轮询角色测试
│   ├── test_redis_source_state_cache.py   — Redis 状态缓存测试
│   ├── test_redis_streams_message_publisher.py — Redis Streams 测试
│   ├── test_relational_outbox_message_publisher.py — Outbox 发布器测试
│   ├── test_source_acquisition_port_registry.py  — 端口注册表测试
│   ├── test_source_acquisition_use_case.py   — 采集用例测试
│   ├── test_source_command_use_case.py   — 命令写入用例测试
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
│   ├── test_ingest_polling_retry_to_redis.py   — 轮询重试到 Redis
│   ├── test_ingest_source_acquisition_to_redis.py  — 采集到 Redis 集成
│   ├── test_ingest_subscription_strategy.py    — 订阅策略集成测试
│   ├── test_redis_state_cache_faults.py        — Redis 缓存容错测试
    │   ├── test_ingest_modbus_source_write.py        — Modbus TCP 写入集成测试
│   ├── test_ingest_cache_to_kafka_pipeline.py     — 缓存快照到 Kafka 发布集成测试（5 cases）
│   ├── test_ingest_opcua_source_write.py        — OPC UA 写入集成测试
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
│       ├── iec61850_mms_polling.py    — IEC 61850 MMS 轮询
│       ├── iec61850_report.py         — IEC 61850 报告
│       ├── modbus_rtu_polling.py      — Modbus RTU 轮询
│       ├── modbus_tcp_polling.py      — Modbus TCP 轮询
│       ├── mqtt_subscription.py       — MQTT 订阅
│       ├── open62541_serial_polling.py    — open62541 串行轮询
│       └── open62541_subscription.py      — open62541 订阅
│
├── protocols/                         — 协议仿真
│   ├── __init__.py
│   ├── registry.py                    — 协议注册表
│   ├── common/                        — 协议公共
│   │   ├── __init__.py
│   │   ├── point_mapping.py           — 测点映射
│   │   └── simulators.py              — 通用模拟器
│   ├── http_rest/__init__.py          — HTTP REST 协议
│   ├── iec101/__init__.py             — IEC 101 协议
│   ├── iec104/__init__.py             — IEC 104 协议
│   ├── iec61850/__init__.py           — IEC 61850 协议
│   ├── modbus/__init__.py             — Modbus 协议
│   └── mqtt/__init__.py               — MQTT 协议
│
├── opcua/                             — OPC UA 模拟器
│   ├── __init__.py
│   ├── address_space.py               — OPC UA 地址空间生成
│   ├── open62541_source_simulator.py  — open62541 仿真数据源
│   ├── docs/GBT_30966.2-2022-信息模型.pdf  — 新能源信息模型标准
│   ├── templates/OPCUANodeSet.xml     — OPC UA 节点集模板
│   └── templates/OPCUA_client_connections.yaml  — 客户端连接模板
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
    ├── conftest.py                     — 测试夹具
    ├── support/
    │   ├── __init__.py
    │   └── sources.py                  — 测试数据源定义
    ├── test_factory.py                 — 工厂测试
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
        ├── test_field_capacity_cli.py  — 现场容量 CLI 测试
        ├── test_field_probe_cli.py     — 现场探测 CLI 测试
        ├── test_field_profile_cli.py   — 现场画像 CLI 测试
        ├── test_field_provider.py      — 字段提供者测试
        ├── test_iec61850_lightweight_semantics.py  — IEC 61850 轻量语义
        ├── test_native_process_protocol.py  — Native 进程协议测试
        ├── test_native_runners_availability.py  — Native 运行器可用性
        ├── test_opcua_access_adapter.py  — OPC UA 接入适配器测试
    │   ├── test_modbus_client_runner_write_protocol.py  — Modbus TCP 写入协议测试
        ├── test_open62541_client_runner_write_protocol.py  — OPC UA 写入协议测试
        ├── test_open62541_serial_polling_runner.py  — OPC UA 串行轮询测试
        ├── test_open62541_subscription_runner.py    — OPC UA 订阅测试
        ├── test_polling_metrics.py     — 轮询指标测试
        ├── test_port_allocator.py      — 端口分配器测试
        ├── test_profile_service.py     — 画像服务测试
        ├── test_protocol_matrix.py     — 协议矩阵测试
        ├── test_protocol_registry.py   — 协议注册表测试
        ├── test_protocol_service_capabilities.py  — 协议服务能力
        ├── test_protocol_production_readiness_gate.py  — 协议生产准入门禁测试
        ├── test_modbus_tcp_production_capacity_profile_gate.py  — Modbus TCP capacity/profile 门禁测试
        ├── test_protocol_simulator_factory.py  — 协议模拟器工厂
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
│   └── ADR-20260524-005-cache-to-message-queue-publish-use-case.md         — 缓存快照发布用例边界
├── memory/                            — 长期记忆
│   ├── project_tree.md                — 本文件（目录树）
│   └── 项目说明.md                    — 项目背景说明
├── prompts/                           — prompt 模板
│   └── 外部AI生成CodingAgent执行Prompt模板.md  — 供外部 AI 使用的 prompt 模板
├── reports/                           — agent 反馈与验收归档
│   ├── _template.md                   — 归档模板
│   ├── four_rounds_engineering_baseline_closure_report.md — 四轮收口自查与工程基线固化报告
│   ├── cache_to_message_queue_use_case_round4_report.md   — 缓存快照发布用例报告（Round 4）
│   ├── source_protocol_readiness_gate_round3_report.md    — 协议准入矩阵治理报告（Round 3）
│   ├── source_modbus_tcp_production_read_write_report.md  — Modbus TCP 生产读写报告（Round 2）
│   ├── source_write_opcua_round1_of_4_validation_report.md — OPC UA 写闭环验证报告（Round 1）
│   ├── source_write_opcua_first_slice_report.md           — OPC UA 写首切片报告
│   ├── source_lab_and_cache_to_kafka_reading_report.md    — source_lab 与 Kafka 预读报告
│   ├── source_lab_facade_pattern_probe_report.md          — source_lab Facade 模式探查报告
│   └── source_lab_server_client_ingest_boundary_report.md — 三层边界探查报告
└── rules/                             — 公共规则
    ├── routing.md                     — 规则路由
    ├── coding.md                      — 编码规范
    ├── testing.md                     — 测试规范
    ├── documentation.md               — 文档规范
    ├── reporting.md                   — 反馈规范
    └── validation-routing.md          — 验证路由
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
└── run_ingest_dev.sh                  — 启动 ingest 开发环境
```

## AI 工具配置

```text
.claude/                               — Claude Code 配置
├── project-memory.md                  — 项目级记忆
├── settings.json                      — Claude Code 全局设置
├── settings.local.json                — 本地覆盖设置
└── skills/                            — Claude Code 技能
    ├── adr-upsert/SKILL.md            — 架构决策记录管理
    ├── commit-message/SKILL.md        — 提交信息生成
    ├── feedback-archive/SKILL.md      — 反馈归档
    ├── heavy-regression/SKILL.md      — 重回归测试
    ├── project-tree-read/SKILL.md     — 目录树读取
    ├── project-tree-reset/SKILL.md    — 目录树全量重建
    ├── project-tree-update/SKILL.md   — 目录树增量更新
    └── rule-update/SKILL.md           — 公共规则更新

.agents/                               — Codex agent 配置
└── skills/                            — Codex 技能（与 .claude/skills 同步）
    ├── adr-upsert/SKILL.md
    ├── commit-message/SKILL.md
    ├── feedback-archive/SKILL.md
    ├── heavy-regression/SKILL.md
    ├── project-tree-read/SKILL.md
    ├── project-tree-reset/SKILL.md
    ├── project-tree-update/SKILL.md
    └── rule-update/SKILL.md
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
