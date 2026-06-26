# BlueCrystal 项目目录树

> 最后更新: 2026-06-26
> 重建方式: `project-tree-reset`
> 扫描边界: 基于当前工作区真实文件系统重建，包含未提交新增文件，不包含已删除旧路径
> 默认排除: `.git`、`.conda`、`__pycache__`、`.pytest_cache`、`.mypy_cache`、`.ruff_cache`、`node_modules`、`dist`、`build`、`tmp`、日志、`.pyc` 和第三方库

本文件只用于导航，不替代读取真实源码、测试、配置、schema 或报告。
`src/manta/public/imagery/` 等大体量静态瓦片资源以目录级说明记录，不逐个展开图片文件。

## 根目录

```text
/ (BlueCrystal)
├── AGENTS.md                        — Codex 自动读取入口
├── CLAUDE.md                        — Claude / Codex 共用执行规则入口
├── README.md                        — 项目概览与开发入口
├── pyproject.toml                   — Python 项目、pytest、ruff、mypy 配置
├── alembic.ini                      — Alembic 迁移配置
├── .gitignore                       — Git 忽略规则
├── .mcp.json                        — MCP 工具配置
├── .vscode/settings.json            — VS Code 工作区设置
├── .claude/                         — Claude agent 与本地设置
├── .codex/                          — Codex agent、hook 与配置
├── .agents/                         — agent 适配层入口
├── ai_shared/                       — 共享规则、技能、记忆、模板与报告
├── alembic/                         — 数据库迁移脚本
├── config/                          — 运行配置模板
├── deploy/                          — 部署与环境编排资产
├── docs/                            — 项目工程与测试文档
├── scripts/                         — 本地质量门禁、环境探针和运维脚本
├── src/                             — 主源码根
└── tests/                           — 单元、集成、e2e、部署和性能测试
```

## Agent 配置

```text
.claude/
├── settings.json                    — Claude 默认设置
├── settings.local.json              — Claude 本地设置
└── agents/
    ├── code-implementer.md          — 实现 agent 说明
    ├── project-steward.md           — 文档 / 目录树 agent 说明
    └── test-validator.md            — 验证 agent 说明

.codex/
├── config.toml                      — Codex 配置
├── hooks.json                       — Codex hook 配置
└── agents/
    ├── code-implementer.toml        — 实现 agent 配置
    ├── project-steward.toml         — 文档 agent 配置
    └── test-validator.toml          — 验证 agent 配置
```

## 共享规则、记忆与报告

```text
ai_shared/
├── agent_config/
│   ├── hooks/
│   │   ├── block-dangerous-bash.py  — 危险 bash 命令阻断
│   │   ├── block-git-write-ops.py   — Git 写操作阻断
│   │   ├── comment-doc-gate.py      — 注释与文档门禁
│   │   ├── docstring-cn-gate.py     — 中文 docstring 门禁
│   │   └── no-source-lab-import-gate.sh — source_lab import 边界门禁
│   └── skills/
│       ├── changed-files-gate/SKILL.md — 真实变更范围门禁
│       ├── code-quality-gate/SKILL.md — 代码质量门禁
│       ├── commit-message/SKILL.md  — staged diff commit message 生成
│       ├── heavy-regression/SKILL.md — 重回归矩阵说明
│       ├── project-tree-reset/SKILL.md — 全量重建目录树
│       ├── project-tree-update/SKILL.md — 增量更新目录树
│       ├── requirement-trace/SKILL.md — 需求证据追踪
│       └── rule-update/SKILL.md     — 共享规则更新
├── memory/
│   ├── BlueCrystal_REQ_README.md    — 需求索引
│   ├── BlueCrystal_REQ_Project.md   — 项目级需求
│   ├── BlueCrystal_REQ_Ingest.md    — ingest 需求
│   ├── BlueCrystal_REQ_MessagePipeline.md — 消息管道需求
│   ├── BlueCrystal_REQ_Storage.md   — 存储需求
│   ├── BlueCrystal_REQ_SpeedLayer.md — 速度层需求
│   ├── BlueCrystal_REQ_BatchLayer.md — batch layer 需求
│   ├── BlueCrystal_REQ_BatchProcessing.md — batch processing 需求
│   ├── BlueCrystal_REQ_ServingAggregation.md — serving / aggregation 需求
│   ├── BlueCrystal_REQ_SharedSource.md — shared source 需求
│   ├── BlueCrystal_REQ_SourceLab.md — source lab 历史需求
│   ├── Octopus_REQ.md               — Octopus 需求
│   ├── PlatformShared_REQ_Crosscutting.md — 平台共享横切需求
│   ├── Seahorse_REQ.md              — Seahorse 需求
│   ├── Starfish_REQ.md              — Starfish 需求
│   ├── Turtle_REQ.md                — Turtle 需求
│   ├── project_tree.md              — 当前目录树
│   ├── test_index.md                — 测试资产索引
│   ├── 总体逻辑设计.md               — 总体逻辑设计
│   └── 业务目标与价值愿景.md          — 业务目标与价值愿景
├── report/
│   ├── dependency_scan_report.md    — Starfish import 边界报告
│   ├── runtime_v2_refactor_report.md — Starfish Runtime v2 重构事实报告
│   ├── drivers_removal_report.md    — Starfish drivers 删除报告
│   ├── observability_v1_report.md   — Starfish runtime 可观测报告
│   ├── registry_purification_report.md — ServerRegistry 纯化报告
│   ├── semantic_reorg_report.md    — Starfish 语义分层重组报告
│   ├── dependency_after_reorg.md    — 重组后依赖扫描报告
│   ├── module_boundary_report.md    — 模块边界验证报告
│   ├── usecase_mapping_report.md    — runtime lifecycle 到 usecase 映射
│   ├── snapshot_example.json        — RuntimeSnapshot 示例
│   ├── event_sample.log             — RuntimeEvent 示例流
│   └── test_report.md               — Starfish 测试报告
├── rules/
│   ├── coding.md                    — 编码、接口、类型与注释规则
│   ├── documentation.md             — 文档、目录树与规则维护
│   ├── python-docstring-cn.md       — 中文注释与 docstring 规则
│   ├── quality-gate.md              — 质量门禁规则
│   ├── reporting.md                 — 反馈与报告归档规则
│   ├── routing.md                   — 规则读取路由
│   ├── testing.md                   — 测试规则
│   └── validation-routing.md        — 验证路由规则
└── templates/
    └── coding_agent_prompt_template.txt — coding agent prompt 模板
```

## 迁移、配置、部署与脚本

```text
alembic/
├── env.py                           — Alembic 环境入口
├── script.py.mako                   — Alembic 迁移模板
└── versions/
    ├── 20260527_000001_ingest_runtime_initial.py
    ├── 20260527_000002_add_audit_index_and_job_stagger.py
    ├── 20260527_000003_add_idempotency_record.py
    └── 20260527_000004_add_model_asset_tables.py

config/
├── ingest/
│   ├── access_policy.external.example.yaml — 外部访问策略示例
│   ├── access_policy.prodlike.yaml  — 准生产访问策略
│   ├── audit_sink.external.example.yaml — 外部审计 sink 示例
│   ├── endurance.prodlike.yaml      — endurance 示例配置
│   ├── performance.prodlike.yaml    — performance 示例配置
│   └── security_partition.example.yaml — 安全分区示例
└── whale/
    ├── message_pipeline.kafka.example.yaml — Kafka 管道配置示例
    ├── message_pipeline.pulsar.example.yaml — Pulsar 管道配置示例
    ├── speed_layer.writers.example.yaml — speed layer writer 示例
    ├── storage.raw_archive.example.yaml — 原始归档存储示例
    ├── storage.serving_cache.example.yaml — serving cache 示例
    └── storage.tdengine.example.yaml — TDengine 存储示例

deploy/
├── octopus/README.md                — Octopus 部署说明
├── turtle/README.md                 — Turtle 部署说明
└── whale/
    ├── README.md                    — Whale 部署总览
    ├── .env.whale.field.example     — 现场环境变量模板
    ├── ingest/
    │   ├── .env.ingest.example      — ingest 环境变量模板
    │   ├── Dockerfile               — ingest 镜像构建文件
    │   ├── README.md                — ingest 部署说明
    │   ├── docker-compose.ingest-dev.yaml — ingest 开发编排
    │   └── docker-compose.ingest-prodlike.yaml — ingest 准生产编排
    ├── message_pipeline/
    │   ├── README.md                — L5 消息管道部署说明
    │   └── docker-compose.whale-l5.yaml — L5 消息管道编排
    ├── speed_layer/
    │   ├── .env.p5.example          — P5 速度层环境模板
    │   ├── README.md                — 速度层部署说明
    │   └── docker-compose.p5.yml    — 速度层编排
    └── storage/README.md            — 存储层部署说明

docs/
├── 4+1视图.md                       — 架构视图文档
├── GIT.md                           — Git 使用说明
├── clean_architecture.md            — Clean Architecture 说明
├── opcua_iec61850_guide.md          — OPC UA / IEC61850 指南
├── 代码质量与注释.md                 — 代码质量说明
├── 工程管理.md                      — 工程管理说明
└── 测试策略.md                      — 测试策略说明

scripts/
├── check_ads_env.py                 — ADS 环境探针
├── check_l2_goose_sv_env.py         — GOOSE / SV L2 环境探针
├── check_l5_field_readback_env.py   — L5 读回环境探针
├── check_serial_env.py              — 串口环境探针
├── ci_ingest_runtime_gate.sh        — ingest CI 运行时门禁
├── cleanup_root_logs.sh             — 根目录日志清理
├── diagnose_whale_p5_dependencies.sh — P5 依赖诊断
├── run_quality_gate.py              — 本地质量门禁入口
├── run_ingest_*.sh                  — ingest smoke / compose / fault / performance 脚本
├── run_pg_migration_matrix.sh       — PG / SQLite 迁移矩阵
├── run_whale_*.sh                   — Whale 现场、L5、P5、writer 脚本
├── start_whale_p5_dependencies.sh   — 启动 P5 外部依赖
├── stop_whale_p5_dependencies.sh    — 停止 P5 外部依赖
├── test_ingest_write_readback_smoke_contract.sh — 写入读回合约脚本
├── validate_shared_source_production_runner.sh — shared source runner 校验
└── whale_test.sh                    — Whale 测试总入口
```

## 主源码 `src/`

### 包元数据

```text
src/
├── bluecrystal.egg-info/            — BlueCrystal 本地包元数据
└── whale.egg-info/                  — Whale 本地包元数据
```

### `src/platform_shared/` — 平台共享基础能力

```text
src/platform_shared/
├── __init__.py                      — 平台共享包入口
├── contracts/__init__.py            — 公共契约命名空间
├── kernel/__init__.py               — kernel 命名空间
├── messaging/__init__.py            — messaging 命名空间
├── security_primitives/
│   ├── __init__.py                  — 安全原语入口
│   └── masking.py                   — 脱敏工具
└── crosscutting/
    ├── __init__.py                  — 横切能力入口
    ├── context/__init__.py          — 上下文命名空间
    ├── debug/
    │   ├── __init__.py              — debug 入口
    │   ├── diagnostics.py           — 诊断辅助
    │   ├── ring_buffer.py           — 环形缓冲
    │   └── trace.py                 — trace 辅助
    ├── observability/
    │   ├── __init__.py              — 可观测性入口
    │   ├── audit.py                 — 审计抽象
    │   ├── logging.py               — 日志辅助
    │   └── metrics.py               — 指标抽象
    └── resilience/
        ├── __init__.py              — 韧性能力入口
        ├── backoff.py               — backoff 策略
        ├── circuit_breaker.py       — 熔断器
        ├── deadline.py              — deadline 工具
        ├── error_classifier.py      — 错误分类
        └── retry.py                 — retry 策略
```

### `src/seahorse/` — 场景与配置生成

```text
src/seahorse/
├── __init__.py                      — Seahorse 包入口
├── __main__.py                      — Seahorse CLI 入口
├── exporters/
│   ├── __init__.py                  — exporter 入口
│   ├── bundle_exporter.py           — bundle 导出
│   ├── bundle_validator.py          — bundle 校验
│   ├── serialization.py             — 序列化工具
│   ├── server_config_exporter.py    — server config 导出
│   ├── server_config_validator.py   — server config 校验
│   ├── server_plan_exporter.py      — server plan 导出兼容
│   ├── server_plan_validator.py     — server plan 校验兼容
│   └── timeseries_exporter.py       — 时序数据导出
├── generators/
│   ├── __init__.py                  — generator 入口
│   ├── alarm_generator.py           — 告警生成
│   └── control_result_generator.py  — 控制结果生成
├── models/
│   ├── __init__.py                  — 模型入口
│   ├── bundle.py                    — bundle 模型
│   ├── generation.py                — 生成参数模型
│   ├── plan.py                      — plan 模型
│   └── scenario.py                  — scenario 模型
├── orchestration/
│   ├── __init__.py                  — 编排入口
│   └── scenario_generator.py        — 场景生成编排
├── ports/
│   ├── __init__.py                  — port 入口
│   └── generation_strategy.py       — 生成策略 port
├── reference_data/
│   ├── __init__.py                  — 参考数据入口
│   ├── gbt_30966_fields.py          — GBT 30966 字段
│   ├── protocol_param_data.py       — 协议参数数据
│   ├── protocol_view_defs.py        — 协议视图定义
│   └── sample_data.py               — 样本数据
└── strategies/
    ├── __init__.py                  — 策略入口
    ├── curve_generation.py          — 曲线生成策略
    ├── random_generation.py         — 随机生成策略
    ├── registry.py                  — 策略注册表
    └── replay_generation.py         — 回放生成策略
```

### `src/starfish/` — 多协议 server simulator runtime

```text
src/starfish/
├── README.md                        — Starfish 模块总览与 CLI 用法
├── __init__.py                      — Starfish 包入口
├── __main__.py                      — CLI 入口
├── api/
│   ├── __init__.py                  — API 导出入口
│   └── server_manager_api.py        — 高层运行时 API / composition root
├── application/
│   ├── __init__.py                  — application 导出入口
│   ├── orchestration/
│   │   ├── __init__.py              — orchestration 导出入口
│   │   ├── service.py               — config 加载与 manager 装配用例
│   │   └── registry.py              — RuntimeGraph 构建与 binding 解析
│   ├── ports/
│   │   ├── __init__.py              — port 导出入口
│   │   ├── config_loader.py         — server config 加载 port
│   │   ├── driver_factory.py        — driver factory port
│   │   ├── driver_port.py           — Runtime v2 driver port
│   │   └── registry.py              — RuntimeGraph 构建 port
│   ├── runtime/
│   │   ├── __init__.py              — application runtime 导出入口
│   │   ├── event.py                 — RuntimeEvent 事件模型
│   │   ├── event_bus.py             — RuntimeEventBus 进程内事件缓冲
│   │   ├── graph.py                 — RuntimeGraph / DriverInstance 模型
│   │   ├── snapshot.py              — RuntimeSnapshot 快照模型
│   │   └── state.py                 — RuntimeState 状态模型
│   └── use_cases/
│       ├── __init__.py              — runtime usecase 导出入口
│       └── runtime_control.py       — start/stop/read/write/hot-swap 编排
├── adapters/
│   ├── __init__.py                  — adapters 层入口
│   ├── config/
│   │   ├── __init__.py              — config adapter 入口
│   │   └── server_config_loader.py  — JSON config 加载与校验
│   └── drivers/
│       ├── __init__.py              — driver adapter 导出入口
│       ├── factory/__init__.py      — 协议 dispatch 与 facade factory
│       ├── ads/ads_facade.py        — ADS driver 占位
│       ├── iec/iec101_facade.py     — IEC101 driver 与 codec 探测
│       ├── iec/goose_facade.py      — GOOSE driver 占位
│       ├── iec/sv_facade.py         — SV driver 占位
│       ├── modbus/modbus_tcp_facade.py — Modbus TCP driver
│       ├── modbus/modbus_rtu_facade.py — Modbus RTU driver
│       ├── native/iec/iec104_facade.py — IEC104 native driver facade
│       ├── native/iec/iec61850_mms_facade.py — IEC61850 MMS driver facade
│       ├── native/iec/iec61850_report_facade.py — IEC61850 Report driver facade
│       ├── native/opcua/opcua_facade.py — OPC UA native driver facade
│       ├── protocol/http/http_rest_facade.py — HTTP REST driver
│       ├── protocol/mqtt/mqtt_facade.py — 轻量 MQTT driver
│       └── simulator/server_simulator_facade.py — 通用 in-memory stub driver
├── domain/
│   ├── __init__.py                  — domain 导出入口
│   ├── driver.py                    — DriverEntry 值对象
│   ├── server_config.py             — server config 契约模型
│   └── protocols/
│       ├── __init__.py              — domain protocol 入口
│       ├── iec101/
│       │   ├── __init__.py          — IEC101 编解码入口
│       │   ├── asdu.py              — ASDU 结构
│       │   ├── codec.py             — IEC101 codec
│       │   ├── common_address.py    — 公共地址
│       │   ├── frame.py             — FT1.2 帧
│       │   ├── information_elements.py — 信息元素
│       │   ├── information_object.py — 信息对象
│       │   ├── ioa.py               — IOA 模型
│       │   ├── link_layer.py        — 链路层状态机骨架
│       │   ├── quality.py           — 质量位
│       │   ├── time.py              — CP56Time2a 时间模型
│       │   └── types.py             — TypeId / COT 类型
│       └── modbus/
│           ├── __init__.py          — Modbus protocol 入口
│           └── register_encoding.py — Modbus 寄存器编码
└── infrastructure/
    ├── __init__.py                  — infrastructure 入口
    └── native/
        ├── __init__.py              — native 支撑入口
        ├── CMakeLists.txt           — native runner 构建脚本
        ├── README.md                — native runner 说明
        ├── runtime.py               — native runner 环境定位
        ├── process_handle.py        — 子进程句柄管理
        ├── runner_probe.py          — binary 探针
        ├── runner_spec.py           — runner 元数据模型
        ├── bin/                     — 预编译 runner / simulator 二进制
        ├── lib60870/                — IEC101 / IEC104 C runner 源码
        ├── libiec61850/             — IEC61850 C runner 源码
        ├── libmodbus/               — Modbus C runner 源码
        └── open62541/               — OPC UA C runner 源码
```

### `src/whale/` — 数据采集、消息、存储与速度层

```text
src/whale/
├── __init__.py                      — Whale 包入口
├── aggregation/
│   ├── __init__.py                  — 聚合入口
│   ├── ads.py                       — ADS 聚合骨架
│   ├── periodic.py                  — 周期聚合骨架
│   └── realtime.py                  — 实时聚合骨架
├── ingest/
│   ├── __init__.py                  — ingest 入口
│   ├── composition.py               — 依赖装配根
│   ├── config.py                    — ingest 配置
│   ├── message_pipeline.py          — ingest 消息管道编排
│   ├── adapters/                    — audit/config/message/observability/security/source/state 适配器
│   ├── api/                         — FastAPI app、middleware、routes、schemas
│   ├── bundle/                      — bundle checksum/model/redaction/service
│   ├── decorators/                  — source acquisition/write/state cache 装饰器
│   ├── diagnostics/                 — capacity/probe/profile 诊断
│   ├── docs/                        — ingest 决策与设计说明
│   ├── domain/                      — audit event 与 write security profile
│   ├── entities/                    — node/source health state
│   ├── file_ingest/                 — 文件接入 decoder/detector/model/repository/service
│   ├── framework/persistence/       — ORM base、init_db、runtime_db、session
│   ├── ports/                       — audit、diagnostics、message、metrics、runtime、source、state ports
│   ├── runtime/                     — CLI、entrypoint、scheduler、lease、worker runtime
│   └── usecases/                    — acquisition、command、state publish use cases
├── message_pipeline/
│   ├── __init__.py                  — 消息管道入口
│   ├── model.py                     — envelope / topic 模型
│   ├── ports.py                     — pipeline ports
│   └── adapters/
│       ├── __init__.py              — adapter 入口
│       ├── in_memory.py             — 内存消息总线
│       ├── kafka.py                 — Kafka adapter
│       └── pulsar.py                — Pulsar adapter
├── model_asset/
│   ├── __init__.py                  — 模型资产入口
│   ├── archive.py                   — 资产归档
│   ├── detector.py                  — 文件类型探测
│   ├── models.py                    — DTO / 模型
│   ├── repository.py                — 仓储
│   └── service.py                   — 导入服务
├── processing/
│   ├── __init__.py                  — processing 入口
│   ├── cleaner.py                   — 清洗骨架
│   └── normalizer.py                — 标准化骨架
├── shared/
│   ├── __init__.py                  — shared 入口
│   ├── enums/quality.py             — 质量枚举
│   ├── persistence/                 — shared ORM、session、模板数据
│   ├── source/                      — HTTP/IEC/Modbus/MQTT/OPC UA source reader 与 backend
│   └── utils/time.py                — 时间工具
├── speed_layer/
│   ├── __init__.py                  — 速度层入口
│   ├── light_processor.py           — 轻处理流程
│   ├── metrics.py                   — 指标抽象
│   ├── runner.py                    — 本地 / Flink runner
│   ├── writers.py                   — 写入器
│   └── preprocessing/
│       ├── __init__.py              — 预处理入口
│       ├── models.py                — 预处理模型
│       ├── operators.py             — 预处理算子
│       ├── pipeline.py              — 预处理 pipeline
│       └── registry.py              — 算子注册
└── storage/
    ├── __init__.py                  — 存储入口
    ├── mart.py                      — mart sink
    ├── raw_archive.py               — 原始归档
    ├── raw_index.py                 — 原始索引
    ├── serving_cache.py             — serving cache
    ├── simulation_result.py         — 仿真结果存储
    ├── standardized.py              — 标准化存储
    ├── warehouse.py                 — warehouse sink
    └── waveform.py                  — 波形存储
```

### `src/turtle/` — 治理、安全与控制面

```text
src/turtle/
├── __init__.py                      — Turtle 包入口
├── adapters/__init__.py             — adapter 命名空间
├── api/__init__.py                  — API 命名空间
├── audit/__init__.py                — audit 命名空间
├── auth/
│   ├── __init__.py                  — auth 入口
│   ├── authorizer.py                — 鉴权器
│   ├── credential.py                — 凭据模型
│   ├── identity.py                  — 身份模型
│   └── policy.py                    — 策略模型
├── change_control/__init__.py       — 变更控制命名空间
├── compliance/
│   ├── __init__.py                  — compliance 入口
│   ├── audit_policy.py              — 审计策略
│   ├── data_classification.py       — 数据分级
│   └── retention.py                 — 保留策略
├── deployment_policy/__init__.py    — 部署策略命名空间
├── governance/__init__.py           — 治理命名空间
├── policy/__init__.py               — policy 命名空间
├── ports/__init__.py                — port 命名空间
├── risk/__init__.py                 — risk 命名空间
├── runtime/__init__.py              — runtime 命名空间
├── sdk/__init__.py                  — SDK 命名空间
└── security/
    ├── __init__.py                  — security 入口
    ├── certificate.py               — 证书模型
    ├── model.py                     — 安全模型
    ├── secret_provider.py           — secret provider
    └── tls.py                       — TLS 配置
```

### `src/octopus/` — 运维、部署与自动化命名空间

```text
src/octopus/
├── __init__.py                      — Octopus 包入口
├── adapters/__init__.py             — adapter 命名空间
├── alerting/__init__.py             — 告警命名空间
├── automation/__init__.py           — 自动化命名空间
├── deployment/__init__.py           — 部署命名空间
├── diagnostics/__init__.py          — 诊断命名空间
├── monitoring/__init__.py           — 监控命名空间
├── orchestration/__init__.py        — 编排命名空间
├── reports/__init__.py              — 报告命名空间
├── rollback/__init__.py             — 回滚命名空间
└── runtime/__init__.py              — runtime 命名空间
```

### `src/manta/` — 前端控制台

```text
src/manta/
├── package.json                     — 前端依赖与脚本
├── pnpm-lock.yaml                   — PNPM 锁文件
├── babel.config.js                  — Babel 配置
├── commitlint.config.js             — commitlint 配置
├── eslint.config.cjs                — ESLint 配置
├── prettier.config.cjs              — Prettier 配置
├── tsconfig.json                    — TypeScript 配置
├── index.html                       — Vite HTML 入口
├── echarts-gl-debug.html            — ECharts GL 调试页
├── components.d.ts                  — 组件类型声明
├── .env.development                 — 开发环境变量
├── .env.production                  — 生产环境变量
├── .prettierignore                  — Prettier 忽略规则
├── .husky/
│   ├── commit-msg                   — commit-msg hook
│   └── pre-commit                   — pre-commit hook
├── config/
│   ├── vite.config.base.ts          — Vite 基础配置
│   ├── vite.config.dev.ts           — Vite 开发配置
│   ├── vite.config.prod.ts          — Vite 生产配置
│   ├── plugin/                      — Vite 插件配置
│   └── utils/index.ts               — Vite 工具函数
├── docs/openapi/
│   ├── showtime.openapi.yaml        — OpenAPI 汇总文件
│   ├── paths/                       — data/lidar/load/message/power/user/windfarm 路径
│   └── schemas/                     — common/data/lidar/load/message/power/user/windfarm schema
├── public/
│   ├── imagery/                     — 地图影像瓦片，静态资源按目录级记录
│   ├── models/WT_10MW.glb           — 风机 3D 模型
│   └── terrain/layer.json           — 地形 layer 配置
└── src/
    ├── main.ts                      — 前端应用启动入口
    ├── App.vue                      — Vue 根组件
    ├── env.d.ts                     — 前端环境类型
    ├── api/                         — generated OpenAPI client、interceptor、本地数据
    ├── assets/                      — banner、logo、全局样式
    ├── bootstrap/cesium.ts          — Cesium 初始化
    ├── components/                  — 面包屑、图表、菜单、导航、指标卡等组件
    ├── config/                      — chart theme 与前端设置
    ├── directive/                   — 权限指令
    ├── hooks/                       — loading、locale、permission、request、theme 等 hooks
    ├── layout/                      — 默认布局与页面布局
    ├── locale/                      — en-US / zh-CN 语言包
    ├── mock/                        — 各业务域 mock 数据与规则
    ├── router/                      — 菜单、guard、routes、类型
    ├── store/                       — app、tab-bar、user store
    ├── types/                       — 全局、mock、lidar、power 类型
    ├── utils/                       — auth、env、event、mock、route 工具
    └── views/                       — dashboard、采集、激光雷达、降载、功率、登录、异常、用户视图
```

## 测试 `tests/`

```text
tests/
├── TESTING.md                       — 测试约定
├── __init__.py                      — 测试包入口
├── conftest.py                      — 全局测试夹具
├── issue_trace.md                   — 问题追踪索引
├── deployment/README.md             — 部署测试说明
├── architecture/                    — 架构边界测试
├── e2e/
│   ├── __init__.py                  — e2e 入口
│   ├── conftest.py                  — e2e 夹具
│   ├── helpers.py                   — e2e 辅助
│   ├── test_whale_field_minimal_smoke.py
│   ├── test_whale_l5_kafka_pipeline_e2e.py
│   └── test_whale_l5_storage_e2e.py
├── integration/
│   ├── __init__.py                  — integration 入口
│   ├── test_http_rest_acquisition_chain.py
│   ├── test_iec101_acquisition_chain.py
│   ├── test_iec104_acquisition_chain.py
│   ├── test_modbus_rtu_acquisition_chain.py
│   ├── test_mqtt_acquisition_chain.py
│   ├── test_ingest_api_*.py         — ingest API CRUD、审计、鉴权、幂等、dry-run 集成测试
│   ├── test_ingest_runtime_*.py     — runtime DB、entrypoint、migration 集成测试
│   ├── test_ingest_scheduler_*.py   — scheduler / failover / graceful shutdown 集成测试
│   ├── test_ingest_prodlike_*.py    — prodlike 依赖、故障、性能、worker 集成测试
│   ├── test_ingest_*source_write.py — OPC UA / IEC104 / IEC61850 / Modbus 写入链测试
│   ├── test_message_pipeline_*.py   — message pipeline e2e / adapter 测试
│   ├── test_model_asset_*.py        — model asset 迁移与集成测试
│   ├── test_speed_layer_*.py        — speed layer 集成测试
│   ├── test_storage_*_integration.py — TDengine 存储集成测试
│   ├── test_whale_writer_*.py       — writer failure / switchover 测试
│   └── 其余 `test_*.py`             — Redis、SQLite、L5、bundle、observability 集成测试
├── performance/
│   ├── __init__.py                  — performance 入口
│   ├── endurance/__init__.py        — endurance 分类
│   ├── load/
│   │   ├── __init__.py              — load 分类
│   │   └── conftest.py              — load 夹具
│   └── stress/
│       ├── __init__.py              — stress 分类
│       └── test_acquisition_pipeline_stress.py
├── support/
│   ├── ingest_prodlike_runtime.py   — 准生产 runtime 测试辅助
│   ├── scada_sample_db.py           — SCADA 样本库辅助
│   └── shared_persistence_sample_db.py — shared persistence 样本库辅助
└── unit/
    ├── __init__.py                  — unit 入口
    ├── architecture/
    │   ├── __init__.py
    │   ├── test_seahorse_import_boundary.py
    │   └── test_starfish_import_boundary.py
    ├── seahorse/
    │   ├── __init__.py
    │   ├── test_bundle.py
    │   ├── test_compat_wrappers.py
    │   ├── test_generators.py
    │   ├── test_models.py
    │   ├── test_orchestrator.py
    │   ├── test_reference_data_imports.py
    │   ├── test_server_plan.py
    │   └── test_strategies.py
    ├── starfish/
    │   ├── __init__.py
    │   ├── conftest.py
    │   ├── test_runtime_observability.py
    │   ├── test_runtime_api.py
    │   ├── test_runtime_v2.py
    │   ├── test_starfish_cli.py
    │   ├── test_server_plan_loader.py
    │   ├── test_protocol_facade.py
    │   ├── test_native_runner_framework.py
    │   ├── test_probe_profile_capacity.py
    │   ├── test_iec101_*.py
    │   ├── test_iec61850_facade.py
    │   ├── test_modbus_*.py
    │   ├── test_mqtt_facade.py
    │   ├── test_opcua_iec104_facade.py
    │   ├── test_remaining_protocols.py
    │   └── test_server_simulator_facade.py
    └── test_*.py                    — Whale ingest、source、storage、speed、message、Turtle/Octopus 单测
```

## Reset 说明

```text
扫描文件总数:
  - find 原始文件数: 3336
  - 排除 cache / build / dist / tmp / 生成物 / `*:Zone.Identifier` 后的候选文件数: 2917
  - `rg --files` 可导航文件数: 2885

主要省略:
  - `src/manta/public/imagery/` 大量 JPG 瓦片
  - cache / pyc / build / dist / node_modules / third_party / 日志 / `*:Zone.Identifier`

主要差异:
  - 根目录已不存在 `requirements.txt`，本次从导航树移除。
  - `docs/clean_architecture.md` 已纳入；`docs/clean_architecture.md:Zone.Identifier` 作为系统元数据省略。
  - Starfish 旧 `src/starfish/drivers/`、`src/starfish/native/`、`src/starfish/protocols/` 不再作为真实源码路径记录。
  - Starfish 新 `adapters/`、`domain/protocols/`、`infrastructure/native/`、`application/ports/` 和 `application/runtime/graph.py` 已纳入。
  - Starfish 新 `application/use_cases/` 已纳入，runtime 执行职责从 registry 移至 usecase。
  - Starfish 新 `application/orchestration/`、`adapters/drivers/protocol/`、`adapters/drivers/native/` 和 `adapters/drivers/factory/` 已纳入。
  - `ai_shared/report/` Runtime v2、drivers removal 与 observability v1 报告已纳入。
  - `src/platform_shared/crosscutting/`、`src/octopus/`、`src/manta/src/` 当前结构已纳入。
```
