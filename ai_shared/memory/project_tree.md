# BlueCrystal 项目目录树

> 最后更新: 2026-06-09
> 重建方式: `project-tree-reset`
> 扫描边界: 基于当前仓库真实纳管文件重建，并纳入本轮未跟踪源码文档 `src/starfish/README.md`
> 默认排除: `.git`、`.conda`、`__pycache__`、`.mypy_cache`、`.pytest_cache`、`.ruff_cache`、`node_modules`、`dist`、`build`、`third_party`、日志与其他生成产物

本文件用于导航当前仓库的稳定结构，只记录主要源码、测试、配置、部署与规则文件。
对超大静态资源或构建产物仅保留目录级说明，不把运行环境垃圾和第三方库写入目录树。

## 根目录

```text
/ (BlueCrystal)
├── AGENTS.md                        — Codex 自动读取入口，转向公共规则
├── CLAUDE.md                        — Claude / Codex 共用执行入口
├── README.md                        — 项目概述与开发快速开始
├── pyproject.toml                   — Python 项目元数据与 ruff/mypy/pytest 配置
├── requirements.txt                 — 依赖清单
├── alembic.ini                      — Alembic 配置
├── .gitignore                       — Git 忽略规则
├── alembic/                         — ingest 运行库迁移
├── config/                          — 运行配置模板
├── deploy/                          — 部署与基础设施编排
├── docs/                            — 通用补充文档
├── scripts/                         — 质量门禁、环境探测与运行脚本
├── src/                             — 主源码根目录
├── tests/                           — 架构 / 单元 / 集成 / e2e / 性能测试
├── ai_shared/                       — 共享规则、技能、记忆与模板
├── .claude/                         — Claude 侧 agent 配置
├── .codex/                          — Codex 侧 agent 与 hook 配置
└── .agents/                         — agent 适配层（技能软链入口）
```

## 迁移与配置

```text
alembic/
├── env.py                           — Alembic 环境入口
├── script.py.mako                   — 迁移模板
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
    ├── message_pipeline.kafka.example.yaml — Kafka 管道示例
    ├── message_pipeline.pulsar.example.yaml — Pulsar 管道示例
    ├── speed_layer.writers.example.yaml — speed layer writer 示例
    ├── storage.raw_archive.example.yaml — 原始归档存储示例
    ├── storage.serving_cache.example.yaml — serving cache 示例
    └── storage.tdengine.example.yaml — TDengine 存储示例
```

## 部署与运维脚本

```text
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

scripts/
├── run_quality_gate.py              — 本地质量门禁入口
├── whale_test.sh                    — 测试总入口脚本
├── run_ingest_dev.sh                — 本地启动 ingest 开发栈
├── run_ingest_runtime_compose_smoke.sh — ingest compose smoke
├── run_ingest_bundle_one_way_flow_smoke.sh — bundle 单向流 smoke
├── run_ingest_compose_readyz_e2e.sh — readyz 端到端脚本
├── run_ingest_pg_lease_fault_injection.sh — PG lease 故障注入脚本
├── run_ingest_prodlike_dependency_smoke.sh — 准生产依赖 smoke
├── run_ingest_prodlike_endurance_smoke.sh — 准生产 endurance smoke
├── run_ingest_prodlike_performance_profile.sh — 准生产性能画像脚本
├── run_ingest_write_readback_smoke.sh — 写入读回 smoke
├── run_pg_migration_matrix.sh       — PG/SQLite 迁移矩阵脚本
├── run_whale_field_minimal_smoke.sh — 现场最小 smoke
├── run_whale_field_quality_gate.sh  — 现场质量门禁脚本
├── run_whale_field_ready_smoke.sh   — 现场 ready 检查
├── run_whale_l5_external_dependency_probe.sh — L5 依赖探针
├── run_whale_p5_external_dependency_regression.sh — P5 外部依赖回归
├── run_whale_writer_switchover.sh   — writer 切换脚本
├── start_whale_p5_dependencies.sh   — 启动 P5 外部依赖
├── stop_whale_p5_dependencies.sh    — 停止 P5 外部依赖
├── validate_shared_source_production_runner.sh — shared source 生产 runner 校验
├── check_ads_env.py                 — ADS 运行环境探针
├── check_l2_goose_sv_env.py         — GOOSE / SV L2 环境探针
├── check_l5_field_readback_env.py   — L5 读回环境探针
├── check_serial_env.py              — 串口环境探针
├── diagnose_whale_p5_dependencies.sh — P5 依赖诊断
├── ci_ingest_runtime_gate.sh        — ingest CI 运行时门禁
├── cleanup_root_logs.sh             — 根目录日志清理
└── test_ingest_write_readback_smoke_contract.sh — 写入读回 smoke 合约脚本
```

## 主源码 `src/`

### `src/manta/` — 前端控制台

```text
src/manta/
├── package.json                     — 前端依赖与脚本入口
├── pnpm-lock.yaml                   — PNPM 锁文件
├── babel.config.js                  — Babel 配置
├── eslint.config.cjs                — ESLint 配置
├── prettier.config.cjs              — Prettier 配置
├── commitlint.config.js             — commitlint 配置
├── tsconfig.json                    — TypeScript 配置
├── index.html                       — Vite HTML 入口
├── components.d.ts                  — 组件类型声明
├── .env.development                 — 开发环境变量
├── .env.production                  — 生产环境变量
├── .husky/
│   ├── commit-msg                   — commit-msg hook
│   └── pre-commit                   — pre-commit hook
├── config/
│   ├── vite.config.base.ts          — Vite 基础配置
│   ├── vite.config.dev.ts           — Vite 开发配置
│   ├── vite.config.prod.ts          — Vite 生产配置
│   ├── plugin/                      — Vite 插件装配
│   └── utils/index.ts               — 前端构建工具函数
├── docs/openapi/                    — OpenAPI 路径与 schema 定义
├── public/imagery/                  — 静态地图切片资源（大量 JPG，reset 中仅保留目录说明）
└── src/
    ├── main.ts                      — 前端应用启动入口
    ├── App.vue                      — Vue 根组件
    └── env.d.ts                     — 前端环境类型声明
```

### `src/whale/` — 数据平台核心

```text
src/whale/
├── __init__.py                      — Whale 包元信息
├── aggregation/
│   ├── __init__.py                  — 聚合包入口
│   ├── ads.py                       — ADS 聚合骨架
│   ├── periodic.py                  — 周期聚合骨架
│   └── realtime.py                  — 实时聚合骨架
├── ingest/
│   ├── __init__.py                  — ingest 包入口
│   ├── config.py                    — ingest 配置模型与加载
│   ├── composition.py               — 依赖装配根
│   ├── message_pipeline.py          — ingest 消息管道编排
│   ├── api/                         — FastAPI API 层
│   ├── adapters/                    — 审计 / 配置 / 消息 / source / state 适配器
│   ├── bundle/                      — bundle 导入导出服务
│   ├── decorators/                  — 采集 / 写入 / 状态装饰器
│   ├── domain/                      — 共享领域模型
│   ├── entities/                    — ingest 领域实体
│   ├── file_ingest/                 — 文件接入子系统
│   ├── framework/persistence/       — ORM 与数据库初始化
│   ├── ports/                       — 采集 / 写入 / 状态 / 消息端口
│   ├── runtime/                     — scheduler / lease / runtime 入口
│   ├── usecases/                    — 采集 / 写入 / 状态发布用例
│   └── docs/
│       ├── DECISIONS.md             — ingest 架构决策记录
│       └── 设计说明书.md             — ingest 模块设计说明
├── message_pipeline/
│   ├── __init__.py                  — 消息管道包入口
│   ├── model.py                     — Envelope / TopicSpec 等模型
│   ├── ports.py                     — Source / Sink / DLQ / Replay 端口
│   └── adapters/
│       ├── in_memory.py             — 内存消息总线
│       ├── kafka.py                 — Kafka 适配器
│       └── pulsar.py                — Pulsar 合约适配器
├── model_asset/
│   ├── __init__.py                  — 模型资产包入口
│   ├── archive.py                   — 仿真资产归档服务
│   ├── detector.py                  — 仿真文件类型探测
│   ├── models.py                    — 模型资产 DTO
│   ├── repository.py                — 模型资产持久化仓储
│   └── service.py                   — 模型资产导入编排
├── processing/
│   ├── __init__.py                  — 处理层包入口
│   ├── cleaner.py                   — 数据清洗骨架
│   └── normalizer.py                — 数据标准化骨架
├── shared/
│   └── __init__.py                  — shared 包入口
├── speed_layer/
│   ├── __init__.py                  — 速度层包入口
│   ├── light_processor.py           — 实时轻处理主流程
│   ├── metrics.py                   — 速度层指标抽象
│   ├── runner.py                    — 速度层本地 / Flink 运行器
│   ├── writers.py                   — 各目标写入器
│   └── preprocessing/               — 固定 10 阶段预处理 pipeline
├── storage/
│   ├── __init__.py                  — 存储层包入口
│   ├── mart.py                      — mart sink 抽象
│   ├── raw_archive.py               — 原始归档 sink
│   ├── raw_index.py                 — 原始索引 sink
│   ├── serving_cache.py             — serving cache sink
│   ├── simulation_result.py         — 仿真结果时序 sink
│   ├── standardized.py              — 标准化存储 sink
│   ├── warehouse.py                 — warehouse sink
│   └── waveform.py                  — 波形存储 sink
```

### `src/platform_shared/` — 跨模块公共基础库

```text
src/platform_shared/
├── __init__.py                      — 平台共享库入口
├── contracts/__init__.py            — 公共契约命名空间
├── crosscutting/__init__.py         — 横切能力命名空间
├── kernel/__init__.py               — 核心基础命名空间
├── messaging/__init__.py            — 消息基础命名空间
└── security_primitives/
    ├── __init__.py                  — 安全原语包入口
    └── masking.py                   — 脱敏工具
```

### `src/turtle/` — 治理与安全控制面

```text
src/turtle/
├── __init__.py                      — Turtle 包入口
├── adapters/__init__.py             — 适配层命名空间
├── api/__init__.py                  — API 命名空间
├── audit/__init__.py                — 审计命名空间
├── auth/
│   ├── __init__.py                  — 认证鉴权包入口
│   ├── authorizer.py                — 鉴权器
│   ├── credential.py                — 凭据模型
│   ├── identity.py                  — 身份模型
│   └── policy.py                    — 策略模型
├── change_control/__init__.py       — 变更控制命名空间
├── compliance/
│   ├── __init__.py                  — 合规包入口
│   ├── audit_policy.py              — 审计策略
│   ├── data_classification.py       — 数据分级
│   └── retention.py                 — 保留策略
├── deployment_policy/__init__.py    — 部署策略命名空间
├── governance/__init__.py           — 治理命名空间
├── policy/__init__.py               — 策略命名空间
├── ports/__init__.py                — 端口命名空间
├── risk/__init__.py                 — 风险命名空间
├── runtime/__init__.py              — 运行时命名空间
├── sdk/__init__.py                  — SDK 命名空间
└── security/
    ├── __init__.py                  — 安全包入口
    ├── certificate.py               — 证书模型
    ├── model.py                     — 安全模型
    ├── secret_provider.py           — 密钥提供器抽象
    └── tls.py                       — TLS 配置模型
```

### `src/octopus/` — 运维执行面骨架

```text
src/octopus/
├── __init__.py                      — Octopus 包入口
├── adapters/__init__.py             — 适配层命名空间
├── alerting/__init__.py             — 告警命名空间
├── automation/__init__.py           — 自动化命名空间
├── deployment/__init__.py           — 部署命名空间
├── diagnostics/__init__.py          — 诊断命名空间
├── monitoring/__init__.py           — 监控命名空间
├── orchestration/__init__.py        — 编排命名空间
├── reports/__init__.py              — 报告命名空间
├── rollback/__init__.py             — 回滚命名空间
└── runtime/__init__.py              — 运行时命名空间
```

### `src/seahorse/` — 场景与样站生成器

```text
src/seahorse/
├── __init__.py                      — Seahorse 包说明
├── __main__.py                      — CLI 入口
├── exporters/
│   ├── __init__.py                  — exporter 包入口
│   ├── bundle_exporter.py           — bundle 导出
│   ├── bundle_validator.py          — bundle 校验
│   ├── serialization.py             — 序列化工具
│   ├── server_plan_exporter.py      — Starfish ServerPlan 导出
│   ├── server_plan_validator.py     — ServerPlan 校验
│   └── timeseries_exporter.py       — 时序导出
├── generators/
│   ├── __init__.py                  — generator 包入口
│   ├── alarm_generator.py           — 告警序列生成
│   └── control_result_generator.py  — 控制结果生成
├── models/
│   ├── __init__.py                  — 模型包入口
│   ├── bundle.py                    — bundle 模型
│   ├── generation.py                — 生成配置模型
│   ├── plan.py                      — 计划模型
│   └── scenario.py                  — 场景模型
├── orchestration/
│   ├── __init__.py                  — 编排包入口
│   └── scenario_generator.py        — 场景编排入口
├── ports/
│   ├── __init__.py                  — 端口包入口
│   └── generation_strategy.py       — 生成策略端口
├── reference_data/
│   ├── __init__.py                  — 参考数据包入口
│   ├── gbt_30966_fields.py          — 国标字段定义
│   ├── protocol_param_data.py       — 协议参数样本
│   ├── protocol_view_defs.py        — 协议视图定义
│   └── sample_data.py               — 样本数据
└── strategies/
    ├── __init__.py                  — 策略包入口
    ├── curve_generation.py          — 曲线生成策略
    ├── random_generation.py         — 随机生成策略
    ├── registry.py                  — 策略注册表
    └── replay_generation.py         — 回放生成策略
```

### `src/starfish/` — 多协议 server simulator 工具层

```text
src/starfish/
├── README.md                        — Starfish 模块总览、分层职责与 CLI 用法
├── __init__.py                      — 包级定位与能力边界说明
├── __main__.py                      — CLI 入口（load / smoke / probe / profile / capacity）
├── facade/
│   ├── __init__.py                  — facade 包入口
│   ├── ads_facade.py                — ADS facade 占位实现
│   ├── goose_facade.py              — GOOSE facade 占位实现
│   ├── http_rest_facade.py          — HTTP REST 真实 facade
│   ├── iec101_facade.py             — IEC101 facade 与编解码运行时骨架
│   ├── iec104_facade.py             — IEC104 native facade
│   ├── iec61850_mms_facade.py       — IEC61850 MMS native facade
│   ├── iec61850_report_facade.py    — IEC61850 Report facade
│   ├── modbus_rtu_facade.py         — Modbus RTU facade
│   ├── modbus_tcp_facade.py         — Modbus TCP facade
│   ├── mqtt_facade.py               — 轻量 MQTT facade
│   ├── opcua_facade.py              — OPC UA native facade
│   ├── server_simulator_facade.py   — 通用 in-memory stub facade
│   └── sv_facade.py                 — SV facade 占位实现
├── loader/
│   ├── __init__.py                  — loader 包入口
│   └── server_plan_loader.py        — ServerPlan JSON 加载与 9 项校验
├── models/
│   ├── __init__.py                  — 模型包入口
│   └── plan.py                      — ServerPlan / Endpoint / Point / Validation 模型
├── native/
│   ├── __init__.py                  — native 支撑包入口
│   ├── CMakeLists.txt               — native runner 构建脚本
│   ├── README.md                    — native runner 协议与构建说明
│   ├── process_handle.py            — native 子进程生命周期管理
│   ├── runner_probe.py              — native binary 探针
│   ├── runner_spec.py               — native runner 元数据模型
│   ├── bin/                         — 预编译 runner / simulator 二进制
│   ├── lib60870/                    — IEC101 / IEC104 C runner 源码
│   ├── libiec61850/                 — IEC61850 C runner 源码
│   ├── libmodbus/                   — Modbus C runner 源码
│   └── open62541/                   — OPC UA C runner 源码
├── protocols/
│   ├── __init__.py                  — 协议工具包入口
│   ├── iec101/
│   │   ├── __init__.py              — IEC101 编解码包入口
│   │   ├── asdu.py                  — ASDU 结构
│   │   ├── codec.py                 — IEC101 编解码器
│   │   ├── common_address.py        — 公共地址模型
│   │   ├── frame.py                 — FT1.2 帧结构
│   │   ├── information_elements.py  — 信息元素定义
│   │   ├── information_object.py    — 信息对象模型
│   │   ├── ioa.py                   — 信息对象地址模型
│   │   ├── link_layer.py            — 链路层状态机骨架
│   │   ├── quality.py               — 质量位定义
│   │   ├── time.py                  — CP56Time2a 等时间模型
│   │   └── types.py                 — TypeId / COT 类型定义
│   └── modbus/
│       ├── __init__.py              — Modbus 协议工具包入口
│       └── register_encoding.py     — Modbus 寄存器编解码工具
├── registry/
│   ├── __init__.py                  — registry 包入口
│   └── runtime_registry.py          — protocol -> facade 分发注册表
└── tools/
    ├── __init__.py                  — probe / profile / capacity 导出入口
    ├── capacity.py                  — 轻量容量扫描
    ├── probe.py                     — 最小可用性探测
    └── profile.py                   — read 耗时采样
```

## 共享规则与记忆 `ai_shared/`

```text
ai_shared/
├── agent_config/
│   ├── hooks/
│   │   ├── block-dangerous-bash.py  — 危险 bash 阻断 hook
│   │   ├── comment-doc-gate.py      — 注释 / 文档门禁 hook
│   │   ├── docstring-cn-gate.py     — 中文 docstring 门禁 hook
│   │   └── no-source-lab-import-gate.sh — source_lab import 边界门禁
│   └── skills/
│       ├── changed-files-gate/SKILL.md
│       ├── code-quality-gate/SKILL.md
│       ├── commit-message/SKILL.md
│       ├── heavy-regression/SKILL.md
│       ├── project-tree-reset/SKILL.md
│       ├── project-tree-update/SKILL.md
│       ├── requirement-trace/SKILL.md
│       └── rule-update/SKILL.md
├── memory/
│   ├── BlueCrystal_REQ_README.md    — 项目需求索引
│   ├── BlueCrystal_REQ_Project.md   — 项目级需求
│   ├── BlueCrystal_REQ_Ingest.md    — ingest 需求
│   ├── BlueCrystal_REQ_MessagePipeline.md — 消息管道需求
│   ├── BlueCrystal_REQ_Storage.md   — 存储层需求
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
│   ├── test_index.md                — 测试索引
│   ├── project_tree.md              — 当前目录树
│   ├── 总体逻辑设计.md               — 系统总体逻辑设计
│   └── 业务目标与价值愿景.md          — 业务目标与价值愿景
├── rules/
│   ├── coding.md                    — 编码规则
│   ├── documentation.md             — 文档维护规则
│   ├── python-docstring-cn.md       — 文档注释规则
│   ├── quality-gate.md              — 质量门禁规则
│   ├── reporting.md                 — 报告与反馈规则
│   ├── routing.md                   — 规则路由入口
│   ├── testing.md                   — 测试规则
│   └── validation-routing.md        — 验证路由规则
└── templates/
    └── coding_agent_prompt_template.txt — coding agent prompt 模板
```

## 测试 `tests/`

```text
tests/
├── TESTING.md                       — 测试约定说明
├── __init__.py                      — 测试包入口
├── conftest.py                      — 全局测试夹具
├── architecture/
│   ├── __init__.py                  — 架构测试包入口
│   ├── test_seahorse_import_boundary.py — Seahorse import 边界测试
│   └── test_starfish_import_boundary.py — Starfish import 边界测试
├── e2e/
│   ├── __init__.py                  — e2e 包入口
│   ├── conftest.py                  — e2e 夹具
│   ├── helpers.py                   — e2e 辅助函数
│   ├── test_whale_field_minimal_smoke.py — 现场最小 smoke
│   ├── test_whale_l5_kafka_pipeline_e2e.py — L5 Kafka pipeline e2e
│   └── test_whale_l5_storage_e2e.py — L5 storage e2e
├── integration/
│   ├── __init__.py                  — integration 包入口
│   ├── test_framework_db_init.py    — DB 初始化集成测试
│   ├── test_http_rest_acquisition_chain.py — HTTP REST 采集链集成测试
│   ├── test_iec101_acquisition_chain.py — IEC101 采集链集成测试
│   ├── test_iec104_acquisition_chain.py — IEC104 采集链集成测试
│   ├── test_mqtt_acquisition_chain.py — MQTT 采集链集成测试
│   ├── test_modbus_rtu_acquisition_chain.py — Modbus RTU 采集链集成测试
│   ├── test_ingest_api_*.py         — ingest API CRUD / audit / idempotency / auth 系列测试
│   ├── test_ingest_runtime_*.py     — ingest runtime / migration / entrypoint 系列测试
│   ├── test_ingest_scheduler_*.py   — scheduler / active-standby / failover 系列测试
│   ├── test_ingest_*_source_write.py — OPC UA / IEC104 / IEC61850 / Modbus 写入链测试
│   ├── test_ingest_*_subscription.py — Report / subscription 系列测试
│   ├── test_message_pipeline_*.py   — 消息管道集成测试
│   ├── test_model_asset_*.py        — 模型资产集成测试
│   ├── test_speed_layer_*.py        — 速度层集成测试
│   └── test_storage_*_integration.py — 波形 / 仿真结果存储集成测试
├── performance/
│   ├── __init__.py                  — performance 包入口
│   ├── endurance/__init__.py        — endurance 分类入口
│   ├── load/
│   │   ├── __init__.py              — load 分类入口
│   │   └── conftest.py              — load 夹具
│   └── stress/
│       ├── __init__.py              — stress 分类入口
│       └── test_acquisition_pipeline_stress.py — 采集管线压力测试
├── support/
│   ├── ingest_prodlike_runtime.py   — 准生产运行时辅助
│   ├── scada_sample_db.py           — SCADA 样本数据库辅助
│   └── shared_persistence_sample_db.py — shared persistence 样本库辅助
└── unit/
    ├── __init__.py                  — unit 包入口
    ├── seahorse/                    — Seahorse 单元测试
    ├── starfish/                    — Starfish 单元测试
    ├── shared/persistence/          — shared persistence 单元测试
    ├── test_acquisition_job_handler.py — 采集作业 handler 单测
    ├── test_config.py               — 配置单测
    ├── test_http_rest_backend.py    — HTTP REST backend 单测
    ├── test_iec101_backend.py       — IEC101 backend 单测
    ├── test_iec104_backend.py       — IEC104 backend 单测
    ├── test_iec61850_mms_backend.py — IEC61850 MMS backend 单测
    ├── test_iec61850_report_backend.py — IEC61850 Report backend 单测
    ├── test_ingest_api_app.py       — ingest API app 单测
    └── 其余 `test_*.py`             — adapter / lease / audit / source / write 等细分单测
```

## Agent 适配层

```text
.claude/
├── settings.json                    — Claude 配置
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

.agents/
└── skills                           — skills 入口软链
```

## 说明

```text
1. 本次 reset 已剔除 `.conda/`、cache、pyc、`src/manta/node_modules/`、`src/manta/dist/`、`src/starfish/native/build/`、`third_party/` 等非项目源码边界内容。
2. `src/manta/public/imagery/` 为超大静态切片资源，保留目录职责说明，不逐 JPG 枚举。
3. 若后续新增、删除、重命名或职责变化文件，回到 `project-tree-update` 做增量维护；不要再把历史 round 结果堆回顶部摘要。
```
