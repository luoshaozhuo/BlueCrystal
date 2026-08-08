# BlueCrystal 项目目录树

> 全量重建日期: 2026-07-13
> 数据来源: 当前工作区真实文件扫描
> 用途: 文件定位与职责导航；不能替代读取真实源码、测试、配置和 schema
> 维护方式: 普通文件变化使用 `project-tree-update`；用户明确要求全量重建时使用 `project-tree-reset`

## 1. 扫描口径

本次扫描当前磁盘中的 4788 个文件，纳入文件级导航 1047 个，省略 3741 个。纳入范围包括未提交和未跟踪文件，因此目录树反映当前工作区，而不是仅反映 Git HEAD。

### 1.1 纳入文件分布

| 顶层路径 | 文件数 |
|---|---:|
| `.claude` | 5 |
| `.codex` | 5 |
| `.dockerignore` | 1 |
| `.gitignore` | 1 |
| `.mcp.json` | 1 |
| `.vscode` | 1 |
| `AGENTS.md` | 1 |
| `CLAUDE.md` | 1 |
| `README.md` | 1 |
| `ai_shared` | 58 |
| `alembic.ini` | 1 |
| `alembic_multidb` | 5 |
| `config` | 12 |
| `deploy` | 15 |
| `docs` | 16 |
| `pyproject.toml` | 1 |
| `scripts` | 29 |
| `src` | 660 |
| `tests` | 233 |

主要文件类型：

| 类型 | 文件数 |
|---|---:|
| `.py` | 645 |
| `.ts` | 131 |
| `.md` | 90 |
| `.vue` | 73 |
| `.yaml` | 36 |
| `.sh` | 25 |
| `.json` | 9 |
| `[无扩展名]` | 7 |
| `.toml` | 5 |
| `.sql` | 4 |
| `.example` | 3 |
| `.cjs` | 3 |
| `.js` | 2 |
| `.html` | 2 |
| `.svg` | 2 |
| `.less` | 2 |
| `.txt` | 1 |
| `.ini` | 1 |
| `.mako` | 1 |
| `.yml` | 1 |
| `.development` | 1 |
| `.production` | 1 |
| `.png` | 1 |
| `.c` | 1 |

### 1.2 省略文件

| 类别 | 文件数 | 说明 |
|---|---:|---|
| Git 元数据 | 1636 | `.git/` 内部对象、引用与日志 |
| 下载来源元数据 | 5 | Windows `Zone.Identifier` 附属数据流导出文件 |
| 运行时数据库 | 1 | `data/shared/whale.db` 运行时数据文件 |
| 前端地图、影像或模型资产 | 1602 | Cesium terrain、影像切片和 GLB 模型；保留 `layer.json` 元数据 |
| 构建或打包产物 | 6 | `build/`、`dist/`、`*.egg-info/` |
| 第三方库 | 225 | `third_party/` vendor 源码与安装产物 |
| 缓存 | 265 | `__pycache__/`、`.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/`、字节码 |
| 编译二进制 | 1 | ELF 等本地编译产物；保留对应源码与构建定义 |

## 2. 完整文件级目录树

行尾注释来自真实文件的模块 docstring、Markdown 标题、脚本说明或文件类型与命名；用于快速定位，不构成接口或行为证据。

```text
BlueCrystal/
├── .claude/  # Claude Code 薄适配配置
│   ├── agents/
│   │   ├── code-implementer.md  # code-implementer
│   │   ├── project-steward.md  # project-steward
│   │   └── test-validator.md  # test-validator
│   ├── settings.json  # 配置：settings.json
│   └── settings.local.json  # 配置：settings.local.json
├── .codex/  # Codex 薄适配配置
│   ├── agents/
│   │   ├── code-implementer.toml  # 配置：code-implementer.toml
│   │   ├── project-steward.toml  # 配置：project-steward.toml
│   │   └── test-validator.toml  # 配置：test-validator.toml
│   ├── config.toml  # 配置：config.toml
│   └── hooks.json  # 配置：hooks.json
├── .dockerignore  # Docker 构建上下文缓存与字节码忽略规则
├── .vscode/  # VS Code 工作区配置
│   └── settings.json  # 配置：settings.json
├── ai_shared/  # 共享规则、技能、记忆、报告与模板
│   ├── agent_config/
│   │   ├── hooks/
│   │   │   ├── block-dangerous-bash.py  # 阻断明显危险的 shell 命令
│   │   │   ├── block-git-write-ops.py  # 阻断默认不允许的 Git/GitHub 写操作
│   │   │   ├── comment-doc-gate.py  # 轻量检查 changed files 的文档注释、类型抑制和危险异常模式
│   │   │   ├── docstring-cn-gate.py  # 兼容旧 hook 名称；实际规则已升级为通用注释与文档注释检查
│   │   │   └── no-source-lab-import-gate.sh  # Shell 脚本：no-source-lab-import-gate.sh
│   │   └── skills/
│   │       ├── changed-files-gate/
│   │       │   └── SKILL.md  # changed-files-gate
│   │       ├── code-quality-gate/
│   │       │   └── SKILL.md  # code-quality-gate
│   │       ├── commit-message/
│   │       │   └── SKILL.md  # commit-message
│   │       ├── heavy-regression/
│   │       │   └── SKILL.md  # heavy-regression
│   │       ├── project-tree-reset/
│   │       │   └── SKILL.md  # project-tree-reset
│   │       ├── project-tree-update/
│   │       │   └── SKILL.md  # project-tree-update
│   │       ├── requirement-trace/
│   │       │   └── SKILL.md  # requirement-trace
│   │       └── rule-update/
│   │           └── SKILL.md  # rule-update
│   ├── memory/
│   │   ├── BlueCrystal_REQ_BatchLayer.md  # BlueCrystal_REQ_BatchLayer
│   │   ├── BlueCrystal_REQ_BatchProcessing.md  # BlueCrystal_REQ_BatchProcessing
│   │   ├── BlueCrystal_REQ_Ingest.md  # BlueCrystal_REQ_Ingest
│   │   ├── BlueCrystal_REQ_MessagePipeline.md  # BlueCrystal_REQ_MessagePipeline
│   │   ├── BlueCrystal_REQ_Project.md  # BlueCrystal_REQ_Project
│   │   ├── BlueCrystal_REQ_README.md  # BlueCrystal Requirements
│   │   ├── BlueCrystal_REQ_ServingAggregation.md  # BlueCrystal_REQ_ServingAggregation
│   │   ├── BlueCrystal_REQ_SharedSource.md  # BlueCrystal_REQ_SharedSource
│   │   ├── BlueCrystal_REQ_SourceLab.md  # BlueCrystal_REQ_SourceLab
│   │   ├── BlueCrystal_REQ_SpeedLayer.md  # BlueCrystal_REQ_SpeedLayer
│   │   ├── BlueCrystal_REQ_Storage.md  # BlueCrystal_REQ_Storage
│   │   ├── Octopus_REQ.md  # Octopus_REQ
│   │   ├── PlatformShared_REQ_Crosscutting.md  # PlatformShared_REQ_Crosscutting
│   │   ├── project_tree.md  # BlueCrystal 项目目录树
│   │   ├── Seahorse_REQ.md  # Seahorse Requirements
│   │   ├── Starfish_REQ.md  # Starfish Requirements
│   │   ├── test_index.md  # BlueCrystal 测试索引
│   │   ├── Turtle_REQ.md  # Turtle_REQ
│   │   ├── 业务目标与价值愿景.md  # 项目白皮书：业务目标与价值愿景
│   │   └── 总体逻辑设计.md  # 项目白皮书-总体逻辑设计
│   ├── reports/
│   │   ├── seahorse_clean_architecture_v4_1_alignment.md  # Seahorse Clean Architecture v4.1 对齐
│   │   ├── seahorse_clean_architecture_v4_2_typer_cli.md  # Seahorse Clean Architecture v4.2 Typer CLI 收敛报告
│   │   ├── seahorse_round1_architecture_reorg.md  # Seahorse Round 1 Architecture Reorg
│   │   ├── seahorse_round2_runtime_contract.md  # Seahorse Round 2 Runtime Contract
│   │   ├── seahorse_round3_whale_writeplan.md  # Seahorse Round 3 Whale Metadata 到 WritePlan 读取链路报告
│   │   ├── seahorse_round4_datasource_runtime.md  # Seahorse Round 4 DataSource Runtime 最小实现
│   │   ├── seahorse_round5_scheduler_executor.md  # Seahorse Round 5 Scheduler Executor 最小实现
│   │   ├── seahorse_round6_starfish_writer_dispatch.md  # Seahorse Round 6 StarfishWriter Batch Dispatch
│   │   ├── seahorse_round7_runtime_smoke_cleanup.md  # Seahorse Round 7 内存 Runtime Smoke Workflow 与残留清理
│   │   ├── seahorse_round7b_legacy_no_compat_cleanup.md  # Seahorse Round 7B 旧顶层目录硬清理 — 无兼容尾巴
│   │   ├── seahorse_round7c_repo_import_closure.md  # Seahorse Round 7C 仓库范围 broken import 收口
│   │   ├── starfish_architecture_doc_finalize.md  # Starfish Clean Architecture v3.3 文档封板收尾
│   │   ├── starfish_clean_boundary_refactor.md  # Starfish Clean Boundary Refactor
│   │   ├── starfish_strict_di_refactor.md  # Starfish Strict DI 收敛重构报告
│   │   ├── tools_sqlalchemy_session_extraction.md  # session.py 迁出至 tools.sqlalchemy_session：横切工具下沉
│   │   └── whale_session_url_minimalization.md  # session.py 极简化：多 env 收敛到单一 WHALE_DB_URL
│   ├── rules/
│   │   ├── coding.md  # 通用编码、接口、类型与注释规则
│   │   ├── documentation.md  # 文档、目录树与规则维护
│   │   ├── python-docstring-cn.md  # Python 中文注释与 Google-style Docstring 规则
│   │   ├── quality-gate.md  # 质量门禁规则
│   │   ├── reporting.md  # Agent 反馈与报告归档规则
│   │   ├── routing.md  # 规则读取路由
│   │   ├── testing.md  # 测试规则
│   │   └── validation-routing.md  # 验证路由规则
│   └── templates/
│       └── coding_agent_prompt_template.txt  # Coding Agent Prompt 模板生成说明
├── alembic_multidb/  # Whale 数据库迁移
│   ├── versions/
│   │   ├── 3c0b0e1fecc4_add_whale_views.py  # add whale views
│   │   └── eb5d458b81c8_init_whale_schema.py  # init whale schema
│   ├── env.py  # BlueCrystal Alembic environment
│   ├── README  # alembic_multidb — Whale 多库 Alembic 工作流
│   └── script.py.mako  # Alembic 迁移脚本模板
├── config/  # 样例与环境配置
│   ├── ingest/
│   │   ├── access_policy.external.example.yaml  # 配置：access_policy.external.example.yaml
│   │   ├── access_policy.prodlike.yaml  # 配置：access_policy.prodlike.yaml
│   │   ├── audit_sink.external.example.yaml  # 配置：audit_sink.external.example.yaml
│   │   ├── endurance.prodlike.yaml  # 配置：endurance.prodlike.yaml
│   │   ├── performance.prodlike.yaml  # 配置：performance.prodlike.yaml
│   │   └── security_partition.example.yaml  # 配置：security_partition.example.yaml
│   └── whale/
│       ├── message_pipeline.kafka.example.yaml  # 配置：message_pipeline.kafka.example.yaml
│       ├── message_pipeline.pulsar.example.yaml  # 配置：message_pipeline.pulsar.example.yaml
│       ├── speed_layer.writers.example.yaml  # 配置：speed_layer.writers.example.yaml
│       ├── storage.raw_archive.example.yaml  # 配置：storage.raw_archive.example.yaml
│       ├── storage.serving_cache.example.yaml  # 配置：storage.serving_cache.example.yaml
│       └── storage.tdengine.example.yaml  # 配置：storage.tdengine.example.yaml
├── deploy/  # 部署交付资产
│   ├── octopus/
│   │   └── README.md  # Octopus 运维编排基础能力部署
│   ├── turtle/
│   │   └── README.md  # Turtle 治理基础能力部署
│   └── whale/
│       ├── ingest/
│       │   ├── .env.ingest.example  # 配置：.env.ingest.example
│       │   ├── docker-compose.ingest-dev.yaml  # 配置：docker-compose.ingest-dev.yaml
│       │   ├── docker-compose.ingest-prodlike.yaml  # 配置：docker-compose.ingest-prodlike.yaml
│       │   ├── Dockerfile  # 容器镜像构建定义
│       │   └── README.md  # Whale Ingest 现场部署说明
│       ├── message_pipeline/
│       │   ├── docker-compose.whale-l5.yaml  # 配置：docker-compose.whale-l5.yaml
│       │   └── README.md  # Whale Message Pipeline 现场部署说明
│       ├── speed_layer/
│       │   ├── .env.p5.example  # 配置：.env.p5.example
│       │   ├── docker-compose.p5.yml  # 配置：docker-compose.p5.yml
│       │   └── README.md  # Whale Speed Layer 现场部署说明
│       ├── storage/
│       │   └── README.md  # Whale Storage 现场部署说明
│       ├── .env.whale.field.example  # 配置：.env.whale.field.example
│       └── README.md  # Whale 现场部署
├── docs/  # 架构、工程与协议文档
│   ├── 架构/
│   │   └── clean_architecture.md  # Clean Architecture Blueprint & Codex Constraint Specification
│   ├── 通信协议/
│   │   ├── ADS.md  # 第一部分：ADS（Automation Device Specification）
│   │   ├── IEC_60870-5-101.md  # IEC 60870-5-101 工程说明文档（子站侧重点版）
│   │   ├── IEC_60870-5-104.md  # IEC 60870-5-104 工程说明文档（子站侧重点版）
│   │   ├── IEC_61850.md  # 1. 标准概述
│   │   ├── ISA_95.md  # ISA-95（IEC 62264）介绍文档
│   │   ├── Modbus.md  # 第一部分：Modbus（RTU / TCP）
│   │   ├── OPC_UA.md  # 第一部分：OPC UA（Open Platform Communications Unified Architecture）
│   │   └── PROFINET.md  # PROFINET 工程说明文档 v2
│   ├── 4+1视图.md  # 4+1 视图关注点与常用 UML 图形
│   ├── GIT.md  # Git Commit 信息前缀规范
│   ├── install.md  # 安装whale
│   ├── opcua_iec61850_guide.md  # OPC UA × IEC 61850 通信与建模指南（扩展版）
│   ├── 代码质量与注释.md  # Python 工程工具与代码文档规范说明
│   ├── 工程管理.md  # 工程管理方法论：低成本自动化驱动的演化型增量迭代开发模型
│   └── 测试策略.md  # Python 项目测试规范与目录组织建议（Codex 使用版）
├── scripts/  # 质量、部署与环境验证脚本
│   ├── check_ads_env.py  # Beckhoff ADS 环境预检脚本
│   ├── check_l2_goose_sv_env.py  # GOOSE/SV L2 网络环境预检脚本
│   ├── check_l5_field_readback_env.py  # L5 Field Readback 环境预检脚本
│   ├── check_serial_env.py  # 串口 (Serial) 环境预检脚本
│   ├── ci_ingest_runtime_gate.sh  # CI gate script for ingest runtime — run all non-source_lab validation tests
│   ├── cleanup_root_logs.sh  # Root-only artifacts that should never be kept in repository root
│   ├── diagnose_whale_p5_dependencies.sh  # diagnose_whale_p5_dependencies.sh
│   ├── run_ingest_bundle_one_way_flow_smoke.sh  # ── Ingest One-Way Bundle Flow Smoke ──────────────────────────────────
│   ├── run_ingest_compose_readyz_e2e.sh  # ============================================================================
│   ├── run_ingest_dev.sh  # run_ingest_dev.sh — 本地开发环境下的 Ingest 服务一键启动脚本
│   ├── run_ingest_pg_lease_fault_injection.sh  # ============================================================================
│   ├── run_ingest_prodlike_dependency_smoke.sh  # Production-like dependency smoke script
│   ├── run_ingest_prodlike_endurance_smoke.sh  # Shell 脚本：run_ingest_prodlike_endurance_smoke.sh
│   ├── run_ingest_prodlike_performance_profile.sh  # ── Ingest Production-like Performance Profile ──────────────────────────
│   ├── run_ingest_runtime_compose_smoke.sh  # Unset proxy to avoid interference with localhost container requests
│   ├── run_ingest_write_readback_smoke.sh  # ============================================================================
│   ├── run_pg_migration_matrix.sh  # Run PostgreSQL migration matrix tests via docker compose PG
│   ├── run_quality_gate.py  # CI/本地质量门禁聚合脚本
│   ├── run_whale_field_minimal_smoke.sh  # =============================================================================
│   ├── run_whale_field_quality_gate.sh  # =============================================================================
│   ├── run_whale_field_ready_smoke.sh  # =============================================================================
│   ├── run_whale_l5_external_dependency_probe.sh  # =============================================================================
│   ├── run_whale_p5_external_dependency_regression.sh  # run_whale_p5_external_dependency_regression.sh
│   ├── run_whale_writer_switchover.sh  # =============================================================================
│   ├── start_whale_p5_dependencies.sh  # start_whale_p5_dependencies.sh
│   ├── stop_whale_p5_dependencies.sh  # stop_whale_p5_dependencies.sh
│   ├── test_ingest_write_readback_smoke_contract.sh  # ============================================================================
│   ├── validate_shared_source_production_runner.sh  # ============================================================================
│   └── whale_test.sh  # =============================================================================
├── src/  # 运行时代码
│   ├── manta/
│   │   ├── .husky/
│   │   │   ├── commit-msg  # Shell 脚本：commit-msg
│   │   │   └── pre-commit  # Shell 脚本：pre-commit
│   │   ├── config/
│   │   │   ├── plugin/
│   │   │   │   ├── arcoResolver.ts  # TypeScript 模块：arcoResolver
│   │   │   │   ├── arcoStyleImport.ts  # TypeScript 模块：arcoStyleImport
│   │   │   │   ├── compress.ts  # TypeScript 模块：compress
│   │   │   │   ├── imagemin.ts  # TypeScript 模块：imagemin
│   │   │   │   └── visualizer.ts  # TypeScript 模块：visualizer
│   │   │   ├── utils/
│   │   │   │   └── index.ts  # TypeScript 模块：index
│   │   │   ├── vite.config.base.ts  # TypeScript 模块：vite.config.base
│   │   │   ├── vite.config.dev.ts  # TypeScript 模块：vite.config.dev
│   │   │   └── vite.config.prod.ts  # TypeScript 模块：vite.config.prod
│   │   ├── docs/
│   │   │   └── openapi/
│   │   │       ├── paths/
│   │   │       │   ├── data-acquisition.yaml  # 配置：data-acquisition.yaml
│   │   │       │   ├── lidar.yaml  # 配置：lidar.yaml
│   │   │       │   ├── load-mitigation.yaml  # 配置：load-mitigation.yaml
│   │   │       │   ├── message.yaml  # 配置：message.yaml
│   │   │       │   ├── power-analysis.yaml  # 配置：power-analysis.yaml
│   │   │       │   ├── turbine.yaml  # 配置：turbine.yaml
│   │   │       │   ├── user-center.yaml  # 配置：user-center.yaml
│   │   │       │   ├── user.yaml  # 配置：user.yaml
│   │   │       │   └── windfarm.yaml  # 配置：windfarm.yaml
│   │   │       ├── schemas/
│   │   │       │   ├── common.yaml  # 配置：common.yaml
│   │   │       │   ├── data-acquisition.yaml  # 配置：data-acquisition.yaml
│   │   │       │   ├── lidar.yaml  # 配置：lidar.yaml
│   │   │       │   ├── load-mitigation.yaml  # 配置：load-mitigation.yaml
│   │   │       │   ├── message.yaml  # 配置：message.yaml
│   │   │       │   ├── power-analysis.yaml  # 配置：power-analysis.yaml
│   │   │       │   ├── turbine.yaml  # 配置：turbine.yaml
│   │   │       │   ├── user-center.yaml  # 配置：user-center.yaml
│   │   │       │   ├── user.yaml  # 配置：user.yaml
│   │   │       │   └── windfarm.yaml  # 配置：windfarm.yaml
│   │   │       └── showtime.openapi.yaml  # 配置：showtime.openapi.yaml
│   │   ├── public/
│   │   │   └── terrain/
│   │   │       └── layer.json  # 配置：layer.json
│   │   ├── src/
│   │   │   ├── api/
│   │   │   │   ├── generated/
│   │   │   │   │   └── openapi/
│   │   │   │   │       ├── client/
│   │   │   │   │       │   ├── client.gen.ts  # TypeScript 模块：client.gen
│   │   │   │   │       │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   │       │   ├── types.gen.ts  # TypeScript 模块：types.gen
│   │   │   │   │       │   └── utils.gen.ts  # TypeScript 模块：utils.gen
│   │   │   │   │       ├── core/
│   │   │   │   │       │   ├── auth.gen.ts  # TypeScript 模块：auth.gen
│   │   │   │   │       │   ├── bodySerializer.gen.ts  # TypeScript 模块：bodySerializer.gen
│   │   │   │   │       │   ├── params.gen.ts  # TypeScript 模块：params.gen
│   │   │   │   │       │   ├── pathSerializer.gen.ts  # TypeScript 模块：pathSerializer.gen
│   │   │   │   │       │   ├── queryKeySerializer.gen.ts  # TypeScript 模块：queryKeySerializer.gen
│   │   │   │   │       │   ├── serverSentEvents.gen.ts  # TypeScript 模块：serverSentEvents.gen
│   │   │   │   │       │   ├── types.gen.ts  # TypeScript 模块：types.gen
│   │   │   │   │       │   └── utils.gen.ts  # TypeScript 模块：utils.gen
│   │   │   │   │       ├── client.gen.ts  # TypeScript 模块：client.gen
│   │   │   │   │       ├── index.ts  # TypeScript 模块：index
│   │   │   │   │       ├── sdk.gen.ts  # TypeScript 模块：sdk.gen
│   │   │   │   │       └── types.gen.ts  # TypeScript 模块：types.gen
│   │   │   │   ├── local-data/
│   │   │   │   │   ├── data-acquisition.ts  # TypeScript 模块：data-acquisition
│   │   │   │   │   ├── lidar.ts  # TypeScript 模块：lidar
│   │   │   │   │   ├── load-mitigation.ts  # TypeScript 模块：load-mitigation
│   │   │   │   │   └── power-analysis.ts  # TypeScript 模块：power-analysis
│   │   │   │   ├── interceptor.ts  # TypeScript 模块：interceptor
│   │   │   │   └── lidar-page.ts  # TypeScript 模块：lidar-page
│   │   │   ├── assets/
│   │   │   │   ├── images/
│   │   │   │   │   ├── default-avatar.svg  # 前端资源：default-avatar.svg
│   │   │   │   │   └── login-banner.png  # 前端资源：login-banner.png
│   │   │   │   ├── style/
│   │   │   │   │   ├── breakpoint.less  # 前端资源：breakpoint.less
│   │   │   │   │   └── global.less  # 前端资源：global.less
│   │   │   │   └── logo.svg  # 前端资源：logo.svg
│   │   │   ├── bootstrap/
│   │   │   │   └── cesium.ts  # TypeScript 模块：cesium
│   │   │   ├── components/
│   │   │   │   ├── breadcrumb/
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── chart/
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── footer/
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── global-setting/
│   │   │   │   │   ├── block.vue  # Vue 组件：block
│   │   │   │   │   ├── form-wrapper.vue  # Vue 组件：form-wrapper
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── menu/
│   │   │   │   │   ├── index.vue  # Vue 组件：index
│   │   │   │   │   └── use-menu-tree.ts  # TypeScript 模块：use-menu-tree
│   │   │   │   ├── navbar/
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── overview-metric-card/
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── overview-turbine-info-card/
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── overview-turbine-select-card/
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── tab-bar/
│   │   │   │   │   ├── index.vue  # Vue 组件：index
│   │   │   │   │   ├── readme.md  # 组件说明
│   │   │   │   │   └── tab-item.vue  # Vue 组件：tab-item
│   │   │   │   ├── top-metric-card/
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   └── index.ts  # TypeScript 模块：index
│   │   │   ├── config/
│   │   │   │   ├── chart-theme.ts  # TypeScript 模块：chart-theme
│   │   │   │   └── settings.json  # 配置：settings.json
│   │   │   ├── directive/
│   │   │   │   ├── permission/
│   │   │   │   │   └── index.ts  # TypeScript 模块：index
│   │   │   │   └── index.ts  # TypeScript 模块：index
│   │   │   ├── hooks/
│   │   │   │   ├── chart-option.ts  # TypeScript 模块：chart-option
│   │   │   │   ├── loading.ts  # TypeScript 模块：loading
│   │   │   │   ├── locale.ts  # TypeScript 模块：locale
│   │   │   │   ├── permission.ts  # TypeScript 模块：permission
│   │   │   │   ├── request.ts  # TypeScript 模块：request
│   │   │   │   ├── responsive.ts  # TypeScript 模块：responsive
│   │   │   │   ├── themes.ts  # TypeScript 模块：themes
│   │   │   │   ├── user.ts  # TypeScript 模块：user
│   │   │   │   └── visible.ts  # TypeScript 模块：visible
│   │   │   ├── layout/
│   │   │   │   ├── default-layout.vue  # Vue 组件：default-layout
│   │   │   │   └── page-layout.vue  # Vue 组件：page-layout
│   │   │   ├── locale/
│   │   │   │   ├── en-US/
│   │   │   │   │   └── settings.ts  # TypeScript 模块：settings
│   │   │   │   ├── zh-CN/
│   │   │   │   │   └── settings.ts  # TypeScript 模块：settings
│   │   │   │   ├── en-US.ts  # TypeScript 模块：en-US
│   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   └── zh-CN.ts  # TypeScript 模块：zh-CN
│   │   │   ├── mock/
│   │   │   │   ├── data-acquisition/
│   │   │   │   │   ├── fixtures.ts  # TypeScript 模块：fixtures
│   │   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   │   └── rules.ts  # TypeScript 模块：rules
│   │   │   │   ├── lidar/
│   │   │   │   │   ├── fixtures.ts  # TypeScript 模块：fixtures
│   │   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   │   └── rules.ts  # TypeScript 模块：rules
│   │   │   │   ├── load-mitigation/
│   │   │   │   │   ├── amplitude-structure.ts  # TypeScript 模块：amplitude-structure
│   │   │   │   │   ├── fixtures.ts  # TypeScript 模块：fixtures
│   │   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   │   ├── markov-matrix.ts  # TypeScript 模块：markov-matrix
│   │   │   │   │   ├── optimization-evidence.ts  # TypeScript 模块：optimization-evidence
│   │   │   │   │   └── rules.ts  # TypeScript 模块：rules
│   │   │   │   ├── message/
│   │   │   │   │   ├── data.ts  # TypeScript 模块：data
│   │   │   │   │   └── index.ts  # TypeScript 模块：index
│   │   │   │   ├── power-analysis/
│   │   │   │   │   ├── fixtures.ts  # TypeScript 模块：fixtures
│   │   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   │   └── rules.ts  # TypeScript 模块：rules
│   │   │   │   ├── user/
│   │   │   │   │   ├── data.ts  # TypeScript 模块：data
│   │   │   │   │   └── index.ts  # TypeScript 模块：index
│   │   │   │   ├── user-center/
│   │   │   │   │   ├── data.ts  # TypeScript 模块：data
│   │   │   │   │   └── index.ts  # TypeScript 模块：index
│   │   │   │   ├── windfarm/
│   │   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   │   ├── turbine-data.ts  # TypeScript 模块：turbine-data
│   │   │   │   │   └── windfarm-data.ts  # TypeScript 模块：windfarm-data
│   │   │   │   └── index.ts  # TypeScript 模块：index
│   │   │   ├── router/
│   │   │   │   ├── app-menus/
│   │   │   │   │   └── index.ts  # TypeScript 模块：index
│   │   │   │   ├── guard/
│   │   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   │   ├── permission.ts  # TypeScript 模块：permission
│   │   │   │   │   └── userLoginInfo.ts  # TypeScript 模块：userLoginInfo
│   │   │   │   ├── routes/
│   │   │   │   │   ├── modules/
│   │   │   │   │   │   ├── dashboard.ts  # TypeScript 模块：dashboard
│   │   │   │   │   │   ├── data-acquisition.ts  # TypeScript 模块：data-acquisition
│   │   │   │   │   │   ├── lidar-wind-field.ts  # TypeScript 模块：lidar-wind-field
│   │   │   │   │   │   ├── load-mitigation.ts  # TypeScript 模块：load-mitigation
│   │   │   │   │   │   ├── power-optimization.ts  # TypeScript 模块：power-optimization
│   │   │   │   │   │   └── user.ts  # TypeScript 模块：user
│   │   │   │   │   ├── base.ts  # TypeScript 模块：base
│   │   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   │   └── types.ts  # TypeScript 模块：types
│   │   │   │   ├── constants.ts  # TypeScript 模块：constants
│   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   └── typings.d.ts  # TypeScript 模块：typings.d
│   │   │   ├── store/
│   │   │   │   ├── modules/
│   │   │   │   │   ├── app/
│   │   │   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   │   │   └── types.ts  # TypeScript 模块：types
│   │   │   │   │   ├── tab-bar/
│   │   │   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   │   │   └── types.ts  # TypeScript 模块：types
│   │   │   │   │   └── user/
│   │   │   │   │       ├── index.ts  # TypeScript 模块：index
│   │   │   │   │       └── types.ts  # TypeScript 模块：types
│   │   │   │   └── index.ts  # TypeScript 模块：index
│   │   │   ├── types/
│   │   │   │   ├── global.ts  # TypeScript 模块：global
│   │   │   │   ├── lidar.ts  # TypeScript 模块：lidar
│   │   │   │   ├── mock.ts  # TypeScript 模块：mock
│   │   │   │   └── power-analysis.ts  # TypeScript 模块：power-analysis
│   │   │   ├── utils/
│   │   │   │   ├── auth.ts  # TypeScript 模块：auth
│   │   │   │   ├── env.ts  # TypeScript 模块：env
│   │   │   │   ├── event.ts  # TypeScript 模块：event
│   │   │   │   ├── index.ts  # TypeScript 模块：index
│   │   │   │   ├── is.ts  # TypeScript 模块：is
│   │   │   │   ├── route-listener.ts  # TypeScript 模块：route-listener
│   │   │   │   └── setup-mock.ts  # TypeScript 模块：setup-mock
│   │   │   ├── views/
│   │   │   │   ├── dashboard/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── GeoSceneViewer.locale.ts  # TypeScript 模块：GeoSceneViewer.locale
│   │   │   │   │   │   └── GeoSceneViewer.vue  # Vue 组件：GeoSceneViewer
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── data-acquisition/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── ChannelResourceCard.vue  # Vue 组件：ChannelResourceCard
│   │   │   │   │   │   ├── ComputeResourceCard.vue  # Vue 组件：ComputeResourceCard
│   │   │   │   │   │   ├── DataQualityAnalysisCard.vue  # Vue 组件：DataQualityAnalysisCard
│   │   │   │   │   │   ├── DeviceCommStatusCard.vue  # Vue 组件：DeviceCommStatusCard
│   │   │   │   │   │   └── StorageResourceCard.vue  # Vue 组件：StorageResourceCard
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── exception/
│   │   │   │   │   ├── 403/
│   │   │   │   │   │   ├── locale/
│   │   │   │   │   │   │   ├── en-US.ts  # TypeScript 模块：en-US
│   │   │   │   │   │   │   └── zh-CN.ts  # TypeScript 模块：zh-CN
│   │   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   │   ├── 404/
│   │   │   │   │   │   ├── locale/
│   │   │   │   │   │   │   ├── en-US.ts  # TypeScript 模块：en-US
│   │   │   │   │   │   │   └── zh-CN.ts  # TypeScript 模块：zh-CN
│   │   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   │   └── 500/
│   │   │   │   │       ├── locale/
│   │   │   │   │       │   ├── en-US.ts  # TypeScript 模块：en-US
│   │   │   │   │       │   └── zh-CN.ts  # TypeScript 模块：zh-CN
│   │   │   │   │       └── index.vue  # Vue 组件：index
│   │   │   │   ├── lidar-wind-filed/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── ConsistencyAlignmentChart.vue  # Vue 组件：ConsistencyAlignmentChart
│   │   │   │   │   │   ├── DataQualityPanel.vue  # Vue 组件：DataQualityPanel
│   │   │   │   │   │   ├── DeviceInfoCard.vue  # Vue 组件：DeviceInfoCard
│   │   │   │   │   │   ├── LidarInflowProfilePanel.vue  # Vue 组件：LidarInflowProfilePanel
│   │   │   │   │   │   ├── LidarVolumeView.vue  # Vue 组件：LidarVolumeView
│   │   │   │   │   │   ├── TopRealtimeWindWave.vue  # Vue 组件：TopRealtimeWindWave
│   │   │   │   │   │   ├── TransferFunctionChart.vue  # Vue 组件：TransferFunctionChart
│   │   │   │   │   │   └── WindRoseTiStats.vue  # Vue 组件：WindRoseTiStats
│   │   │   │   │   ├── echarts-gl.d.ts  # TypeScript 模块：echarts-gl.d
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── load-mitigation/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── AmplitudeStructureComparison.vue  # Vue 组件：AmplitudeStructureComparison
│   │   │   │   │   │   ├── EnergySpectrumComparison.vue  # Vue 组件：EnergySpectrumComparison
│   │   │   │   │   │   ├── HighAmplitudeRiskComparison.vue  # Vue 组件：HighAmplitudeRiskComparison
│   │   │   │   │   │   ├── ImprovementStabilityStats.vue  # Vue 组件：ImprovementStabilityStats
│   │   │   │   │   │   ├── LoadCycleMigrationHeatmap.vue  # Vue 组件：LoadCycleMigrationHeatmap
│   │   │   │   │   │   ├── PeakQuantileEvidence.vue  # Vue 组件：PeakQuantileEvidence
│   │   │   │   │   │   └── RmsImprovementOverview.vue  # Vue 组件：RmsImprovementOverview
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── login/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── banner.vue  # Vue 组件：banner
│   │   │   │   │   │   └── login-form.vue  # Vue 组件：login-form
│   │   │   │   │   ├── locale/
│   │   │   │   │   │   ├── en-US.ts  # TypeScript 模块：en-US
│   │   │   │   │   │   └── zh-CN.ts  # TypeScript 模块：zh-CN
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── not-found/
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── power-analysis/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── BootstrapStabilityChart.vue  # Vue 组件：BootstrapStabilityChart
│   │   │   │   │   │   ├── DistributionShiftChart.vue  # Vue 组件：DistributionShiftChart
│   │   │   │   │   │   ├── GustResponse.vue  # Vue 组件：GustResponse
│   │   │   │   │   │   ├── PowerCurveComparisonChart.vue  # Vue 组件：PowerCurveComparisonChart
│   │   │   │   │   │   ├── StatSummaryCard.vue  # Vue 组件：StatSummaryCard
│   │   │   │   │   │   ├── TailCcdfChart.vue  # Vue 组件：TailCcdfChart
│   │   │   │   │   │   └── VolatilitySummary.vue  # Vue 组件：VolatilitySummary
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── redirect/
│   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   ├── result/
│   │   │   │   │   ├── error/
│   │   │   │   │   │   ├── locale/
│   │   │   │   │   │   │   ├── en-US.ts  # TypeScript 模块：en-US
│   │   │   │   │   │   │   └── zh-CN.ts  # TypeScript 模块：zh-CN
│   │   │   │   │   │   └── index.vue  # Vue 组件：index
│   │   │   │   │   └── success/
│   │   │   │   │       ├── locale/
│   │   │   │   │       │   ├── en-US.ts  # TypeScript 模块：en-US
│   │   │   │   │       │   └── zh-CN.ts  # TypeScript 模块：zh-CN
│   │   │   │   │       └── index.vue  # Vue 组件：index
│   │   │   │   └── user/
│   │   │   │       ├── info/
│   │   │   │       │   ├── components/
│   │   │   │       │   │   ├── latest-activity.vue  # Vue 组件：latest-activity
│   │   │   │       │   │   ├── latest-notification.vue  # Vue 组件：latest-notification
│   │   │   │       │   │   ├── my-project.vue  # Vue 组件：my-project
│   │   │   │       │   │   ├── my-team.vue  # Vue 组件：my-team
│   │   │   │       │   │   └── user-info-header.vue  # Vue 组件：user-info-header
│   │   │   │       │   ├── locale/
│   │   │   │       │   │   ├── en-US.ts  # TypeScript 模块：en-US
│   │   │   │       │   │   └── zh-CN.ts  # TypeScript 模块：zh-CN
│   │   │   │       │   └── index.vue  # Vue 组件：index
│   │   │   │       └── setting/
│   │   │   │           ├── components/
│   │   │   │           │   ├── basic-information.vue  # Vue 组件：basic-information
│   │   │   │           │   ├── certification-records.vue  # Vue 组件：certification-records
│   │   │   │           │   ├── certification.vue  # Vue 组件：certification
│   │   │   │           │   ├── enterprise-certification.vue  # Vue 组件：enterprise-certification
│   │   │   │           │   ├── security-settings.vue  # Vue 组件：security-settings
│   │   │   │           │   └── user-panel.vue  # Vue 组件：user-panel
│   │   │   │           ├── locale/
│   │   │   │           │   ├── en-US.ts  # TypeScript 模块：en-US
│   │   │   │           │   └── zh-CN.ts  # TypeScript 模块：zh-CN
│   │   │   │           └── index.vue  # Vue 组件：index
│   │   │   ├── App.vue  # Vue 组件：App
│   │   │   ├── env.d.ts  # TypeScript 模块：env.d
│   │   │   └── main.ts  # TypeScript 模块：main
│   │   ├── .env.development  # 配置：.env.development
│   │   ├── .env.production  # 配置：.env.production
│   │   ├── .prettierignore  # 项目文件：.prettierignore
│   │   ├── babel.config.js  # JavaScript 模块：babel.config
│   │   ├── commitlint.config.js  # JavaScript 模块：commitlint.config
│   │   ├── components.d.ts  # TypeScript 模块：components.d
│   │   ├── echarts-gl-debug.html  # 前端资源：echarts-gl-debug.html
│   │   ├── eslint.config.cjs  # JavaScript 模块：eslint.config
│   │   ├── index.html  # 前端资源：index.html
│   │   ├── package.json  # 配置：package.json
│   │   ├── pnpm-lock.yaml  # 配置：pnpm-lock.yaml
│   │   ├── prettier.config.cjs  # JavaScript 模块：prettier.config
│   │   ├── stylelint.config.cjs  # JavaScript 模块：stylelint.config
│   │   └── tsconfig.json  # 配置：tsconfig.json
│   ├── octopus/
│   │   ├── adapters/
│   │   │   └── __init__.py  # Octopus 适配器层
│   │   ├── alerting/
│   │   │   └── __init__.py  # Octopus 告警管理
│   │   ├── automation/
│   │   │   └── __init__.py  # Octopus 自动化引擎
│   │   ├── deployment/
│   │   │   └── __init__.py  # Octopus 部署管理
│   │   ├── diagnostics/
│   │   │   └── __init__.py  # Octopus 诊断工具
│   │   ├── monitoring/
│   │   │   └── __init__.py  # Octopus 监控采集
│   │   ├── orchestration/
│   │   │   └── __init__.py  # Octopus 编排引擎
│   │   ├── reports/
│   │   │   └── __init__.py  # Octopus 运维报告
│   │   ├── rollback/
│   │   │   └── __init__.py  # Octopus 回滚管理
│   │   ├── runtime/
│   │   │   └── __init__.py  # Octopus 运行时层
│   │   └── __init__.py  # Octopus 运维编排基础能力包
│   ├── platform_shared/
│   │   ├── contracts/
│   │   │   └── __init__.py  # 跨组件通用契约模型（骨架）
│   │   ├── crosscutting/
│   │   │   ├── context/
│   │   │   │   └── __init__.py  # Tracing 和 correlation context 基础模型（骨架）
│   │   │   ├── debug/
│   │   │   │   ├── __init__.py  # Debug trace and diagnostics helpers
│   │   │   │   ├── diagnostics.py  # Debug snapshot models for external runner diagnostics
│   │   │   │   ├── ring_buffer.py  # Small recent-failure buffer used by debug tooling
│   │   │   │   └── trace.py  # Debug trace context and sink abstractions
│   │   │   ├── observability/
│   │   │   │   ├── __init__.py  # Observability primitives for logging, metrics, and audit bridging
│   │   │   │   ├── audit.py  # Helpers that bridge audit concepts into observability pipelines
│   │   │   │   ├── logging.py  # Structured logging data models
│   │   │   │   └── metrics.py  # Metrics sink protocol shared by adapters and wrappers
│   │   │   ├── resilience/
│   │   │   │   ├── __init__.py  # Reusable resilience policies and classifications
│   │   │   │   ├── backoff.py  # Backoff policy helpers
│   │   │   │   ├── circuit_breaker.py  # Minimal circuit-breaker model primitives
│   │   │   │   ├── deadline.py  # Deadline models for bounded operations
│   │   │   │   ├── error_classifier.py  # Stable error classification models
│   │   │   │   └── retry.py  # Retry-policy models shared by wrappers and adapters
│   │   │   └── __init__.py  # 全系统横切基础能力
│   │   ├── kernel/
│   │   │   └── __init__.py  # 基础 kernel 工具（骨架）
│   │   ├── messaging/
│   │   │   └── __init__.py  # 跨组件消息基础模型（骨架）
│   │   ├── security_primitives/
│   │   │   ├── __init__.py  # 无策略的安全基础工具
│   │   │   └── masking.py  # Helpers for masking sensitive values before they reach logs or traces
│   │   └── __init__.py  # PlatformShared 全系统公共基础库
│   ├── seahorse/
│   │   ├── adapters/
│   │   │   ├── drivers/
│   │   │   │   ├── factory/
│   │   │   │   │   └── __init__.py  # Seahorse driver adapter factory 占位包
│   │   │   │   ├── __init__.py  # Seahorse driver adapter 层
│   │   │   │   └── backend_ports.py  # driver adapter 局部 backend 契约
│   │   │   ├── gateways/
│   │   │   │   ├── __init__.py  # Seahorse 外部 handoff gateway
│   │   │   │   ├── server_config_handoff_gateway.py  # seahorse ServerConfig handoff 导出入口
│   │   │   │   ├── server_config_validator.py  # seahorse ServerConfig 契约校验入口
│   │   │   │   ├── server_plan_handoff_gateway.py  # seahorse ServerConfig handoff 导出器
│   │   │   │   ├── server_plan_validator.py  # seahorse ServerConfig 契约校验器
│   │   │   │   └── starfish_writer_gateway.py  # Starfish writer gateway
│   │   │   ├── presenters/
│   │   │   │   └── __init__.py  # Seahorse presenter 适配器占位包
│   │   │   ├── serializers/
│   │   │   │   ├── __init__.py  # Seahorse JSON/JSONL 序列化适配器
│   │   │   │   ├── bundle_json_serializer.py  # seahorse JSON 包导出器
│   │   │   │   ├── bundle_serialization.py  # seahorse 序列化辅助 —— 校验和计算与规范化 JSON 导出
│   │   │   │   └── timeseries_jsonl_serializer.py  # seahorse JSONL 时序导出器
│   │   │   └── __init__.py  # Seahorse 适配器层
│   │   ├── api/
│   │   │   ├── __init__.py  # Seahorse API facade 层
│   │   │   └── seahorse_facade.py  # Seahorse facade
│   │   ├── application/
│   │   │   ├── ports/
│   │   │   │   ├── __init__.py  # Seahorse 应用端口契约
│   │   │   │   ├── clock_port.py  # Seahorse 时钟端口
│   │   │   │   ├── data_source_port.py  # Seahorse 数据源端口
│   │   │   │   ├── generation_strategy_port.py  # seahorse 生成策略端口 —— GenerationStrategy Protocol
│   │   │   │   ├── scheduler_port.py  # Seahorse scheduler 端口
│   │   │   │   ├── starfish_writer_port.py  # Starfish writer 应用端口
│   │   │   │   ├── telemetry_port.py  # Seahorse telemetry 端口
│   │   │   │   └── whale_metadata_port.py  # Whale 元数据运行计划读取端口
│   │   │   ├── runtime/
│   │   │   │   ├── __init__.py  # Seahorse runtime 最小骨架
│   │   │   │   ├── context.py  # Seahorse runtime 上下文骨架
│   │   │   │   ├── event_bus.py  # Seahorse runtime 事件总线骨架
│   │   │   │   ├── executor.py  # Seahorse 最小 tick 驱动 runtime executor
│   │   │   │   ├── graph.py  # Seahorse runtime 图契约
│   │   │   │   ├── snapshot.py  # Seahorse runtime 快照契约
│   │   │   │   └── state.py  # Seahorse runtime 状态契约
│   │   │   ├── use_cases/
│   │   │   │   ├── atomic/
│   │   │   │   │   ├── __init__.py  # Seahorse atomic use cases
│   │   │   │   │   ├── build_write_batch.py  # 从 WritePlan 与数据源端口构建 WriteBatch
│   │   │   │   │   ├── build_write_plan.py  # 构建 WritePlan 的最小用例
│   │   │   │   │   ├── dispatch_write_batch.py  # WriteBatch 分发用例
│   │   │   │   │   ├── runtime_smoke_workflow.py  # Seahorse 内存 runtime smoke workflow
│   │   │   │   │   ├── update_runtime_period.py  # 更新 runtime 周期配置的纯用例
│   │   │   │   │   └── validate_write_plan.py  # 校验 WritePlan 的最小用例
│   │   │   │   ├── __init__.py  # Seahorse 应用层入口
│   │   │   │   ├── alarm_generator.py  # seahorse 告警事件生成器
│   │   │   │   ├── bundle_validator.py  # seahorse 场景包校验器
│   │   │   │   ├── control_result_generator.py  # seahorse 控制回写响应生成器
│   │   │   │   ├── curve_generation.py  # seahorse 曲线生成策略
│   │   │   │   ├── random_generation.py  # seahorse 确定性随机值生成策略
│   │   │   │   ├── replay_generation.py  # seahorse 回放生成策略
│   │   │   │   ├── scenario_generator.py  # seahorse 场景生成编排器 —— SeahorseGenerator
│   │   │   │   ├── seed_whale_metadata.py  # Whale 元数据样例 seed 用例
│   │   │   │   └── strategy_registry.py  # seahorse 生成策略注册表
│   │   │   ├── __init__.py  # Seahorse 应用层
│   │   │   └── exceptions.py  # Seahorse 应用层稳定异常
│   │   ├── domain/
│   │   │   ├── __init__.py  # Seahorse 领域模型层
│   │   │   ├── bundle.py  # seahorse 核心模型 —— 场景包（ScenarioBundle）
│   │   │   ├── bundle_checksum.py  # seahorse 序列化辅助 —— 校验和计算与规范化 JSON 导出
│   │   │   ├── generation.py  # seahorse 核心模型 —— 生成结果值
│   │   │   ├── plan.py  # seahorse 核心模型 —— 种子计划与端点规划
│   │   │   ├── runtime_contract.py  # Seahorse runtime contract 领域模型
│   │   │   └── scenario.py  # seahorse 核心模型 —— 场景配置、元数据与种子计划
│   │   ├── infrastructure/
│   │   │   ├── data_sources/
│   │   │   │   ├── __init__.py  # Seahorse 数据源基础设施
│   │   │   │   └── runtime.py  # Seahorse 内存 DataSource runtime adapter
│   │   │   ├── drivers/
│   │   │   │   ├── __init__.py  # Seahorse driver backend 基础设施包
│   │   │   │   ├── backend_factory.py  # Seahorse driver backend 工厂
│   │   │   │   └── starfish_writer_backend.py  # Starfish writer 内存 backend
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py  # Seahorse repository 基础设施
│   │   │   │   └── whale_metadata_repository.py  # Seahorse repository —— Whale 元数据只读映射与样例种子薄入口
│   │   │   ├── schedulers/
│   │   │   │   ├── __init__.py  # Seahorse scheduler 基础设施
│   │   │   │   └── clock.py  # Seahorse scheduler 基础设施时钟
│   │   │   ├── telemetry/
│   │   │   │   └── __init__.py  # Seahorse telemetry 基础设施占位包
│   │   │   └── __init__.py  # Seahorse 基础设施层
│   │   ├── __init__.py  # seahorse — 样例场站生成器
│   │   ├── __main__.py  # Seahorse CLI 薄输入入口（Typer）
│   │   └── container.py  # Seahorse composition root
│   ├── starfish/
│   │   ├── adapters/
│   │   │   ├── db_views/
│   │   │   │   ├── iec104/
│   │   │   │   │   ├── __init__.py  # IEC104 DB view adapter
│   │   │   │   │   └── loader.py  # IEC104 connection/task/member/point view loader
│   │   │   │   ├── __init__.py  # DB view outbound adapters
│   │   │   │   ├── connections.py  # Whale connection 执行视图的通用索引 loader
│   │   │   │   └── errors.py  # DB view adapter 错误边界
│   │   │   ├── protocols/
│   │   │   │   ├── iec104/
│   │   │   │   │   ├── native/
│   │   │   │   │   │   ├── lib60870/
│   │   │   │   │   │   │   └── iec104_simulator_server.c  # C 源码：iec104 simulator server
│   │   │   │   │   │   ├── __init__.py  # IEC104 native runner 资源与启动辅助
│   │   │   │   │   │   └── runtime.py  # starfish native runner 启动辅助
│   │   │   │   │   ├── __init__.py  # IEC104 c104 adapter 对外入口
│   │   │   │   │   ├── backend.py  # iec104-python 双角色 runtime 与 point/task API
│   │   │   │   │   └── server.py  # IEC104 connection worker 与稳定委托接口
│   │   │   │   ├── __init__.py  # Protocol server outbound adapters
│   │   │   │   └── factory.py  # Protocol server factory adapter
│   │   │   └── __init__.py  # Starfish adapters 层入口
│   │   ├── core/
│   │   │   ├── ports/
│   │   │   │   ├── __init__.py  # Starfish core ports
│   │   │   │   ├── protocol_server.py  # Protocol server worker port
│   │   │   │   ├── server_factory.py  # Server factory port
│   │   │   │   └── server_loader.py  # Server definition loader port
│   │   │   ├── __init__.py  # Starfish 核心运行时模型
│   │   │   ├── definitions.py  # Starfish core 使用的 simulator definition
│   │   │   └── manager.py  # Starfish core server manager
│   │   ├── __init__.py  # starfish 对外包入口
│   │   ├── __main__.py  # starfish CLI 入口 —— 通过 Whale DB view 启动 Starfish simulator
│   │   ├── ARCHITECTURE.md  # Starfish 架构说明
│   │   ├── composition.py  # Starfish 依赖装配与协议分派入口
│   │   └── README.md  # Starfish
│   ├── tools/
│   │   ├── __init__.py  # 跨模块通用工具集
│   │   └── sqlalchemy_session.py  # 跨模块 SQLAlchemy engine 与 session 工具
│   ├── turtle/
│   │   ├── adapters/
│   │   │   └── __init__.py  # Turtle 适配器层
│   │   ├── api/
│   │   │   └── __init__.py  # Turtle API 层
│   │   ├── audit/
│   │   │   └── __init__.py  # Turtle 审计治理基础能力
│   │   ├── auth/
│   │   │   ├── __init__.py  # Turtle 认证授权基础能力
│   │   │   ├── authorizer.py  # 授权决策模型
│   │   │   ├── credential.py  # 凭证引用重导出
│   │   │   ├── identity.py  # 身份模型
│   │   │   └── policy.py  # 访问策略端口抽象
│   │   ├── change_control/
│   │   │   └── __init__.py  # Turtle 变更控制基础能力
│   │   ├── compliance/
│   │   │   ├── __init__.py  # Turtle 合规基础能力
│   │   │   ├── audit_policy.py  # 审计事件模型和 sink 端口
│   │   │   ├── data_classification.py  # 数据分类标记
│   │   │   └── retention.py  # 数据保留策略模型
│   │   ├── deployment_policy/
│   │   │   └── __init__.py  # Turtle 部署策略基础能力
│   │   ├── governance/
│   │   │   └── __init__.py  # Turtle 治理框架基础能力
│   │   ├── policy/
│   │   │   └── __init__.py  # Turtle 策略治理基础能力
│   │   ├── ports/
│   │   │   └── __init__.py  # Turtle 端口层
│   │   ├── risk/
│   │   │   └── __init__.py  # Turtle 风险评估基础能力
│   │   ├── runtime/
│   │   │   └── __init__.py  # Turtle 运行时层
│   │   ├── sdk/
│   │   │   └── __init__.py  # Turtle SDK 层
│   │   ├── security/
│   │   │   ├── __init__.py  # Turtle 安全基础能力
│   │   │   ├── certificate.py  # 证书引用重导出
│   │   │   ├── model.py  # 安全引用模型
│   │   │   ├── secret_provider.py  # 密钥提供方端口
│   │   │   └── tls.py  # TLS 配置模型
│   │   └── __init__.py  # Turtle 治理基础能力包
│   └── whale/
│       ├── aggregation/
│       │   ├── __init__.py  # 数据聚合层（aggregation）—— 当前为骨架模块
│       │   ├── ads.py  # ADS business aggregations for scenario1
│       │   ├── periodic.py  # Periodic 1-minute DWS aggregation
│       │   └── realtime.py  # Realtime 5-second DWS aggregation
│       ├── ingest/
│       │   ├── adapters/
│       │   │   ├── audit/
│       │   │   │   ├── __init__.py  # 审计 sink 适配器。提供审计事件的持久化和转发实现（数据库、HTTP、多路）
│       │   │   │   ├── db_audit_sink.py  # 审计日志适配器
│       │   │   │   ├── http_audit_sink.py  # 审计日志适配器
│       │   │   │   └── multi_audit_sink.py  # 可组合的审计 sink 适配器。提供多路审计事件转发和聚合错误处理
│       │   │   ├── config/
│       │   │   │   ├── __init__.py  # 配置适配器
│       │   │   │   ├── opcua_source_acquisition_definition_repository.py  # 配置适配器
│       │   │   │   └── source_runtime_config_repository.py  # 配置适配器
│       │   │   ├── message/
│       │   │   │   ├── __init__.py  # 消息发布适配器
│       │   │   │   ├── kafka_message_publisher.py  # 消息发布适配器
│       │   │   │   ├── redis_streams_message_publisher.py  # 消息发布适配器
│       │   │   │   └── relational_outbox_message_publisher.py  # 消息发布适配器
│       │   │   ├── observability/
│       │   │   │   ├── __init__.py  # 可观测性适配器
│       │   │   │   └── file_sinks.py  # 可观测性适配器
│       │   │   ├── security/
│       │   │   │   ├── __init__.py  # 安全策略适配器
│       │   │   │   ├── external_access_policy.py  # 基于外部 HTTP 的 ingest 运行时访问策略适配器。将权限决策委托给远程授权服务
│       │   │   │   └── file_access_policy.py  # 安全策略适配器
│       │   │   ├── source/
│       │   │   │   ├── __init__.py  # 协议采集适配器
│       │   │   │   ├── dispatch_source_acquisition_adapter.py  # 多协议采集端口调度适配器
│       │   │   │   ├── http_rest_source_acquisition_adapter.py  # HTTP REST source 采集适配器
│       │   │   │   ├── iec101_source_acquisition_adapter.py  # IEC 101 source 采集适配器
│       │   │   │   ├── iec104_source_acquisition_adapter.py  # 协议采集适配器
│       │   │   │   ├── iec104_source_write_adapter.py  # 协议采集适配器
│       │   │   │   ├── iec61850_report_source_acquisition_adapter.py  # IEC 61850 Report source 采集适配器
│       │   │   │   ├── iec61850_source_acquisition_adapter.py  # 协议采集适配器
│       │   │   │   ├── iec61850_source_write_adapter.py  # 协议采集适配器
│       │   │   │   ├── modbus_rtu_source_acquisition_adapter.py  # Modbus RTU source 采集适配器
│       │   │   │   ├── modbus_source_acquisition_adapter.py  # 协议采集适配器
│       │   │   │   ├── modbus_source_write_adapter.py  # 协议采集适配器
│       │   │   │   ├── mqtt_source_acquisition_adapter.py  # MQTT source 采集适配器
│       │   │   │   ├── opcua_source_acquisition_adapter.py  # OPC UA source 采集适配器
│       │   │   │   ├── opcua_source_write_adapter.py  # OPC UA source write adapter
│       │   │   │   ├── static_source_acquisition_port_registry.py  # 静态 source acquisition port registry
│       │   │   │   └── static_source_write_port_registry.py  # Static source write port registry
│       │   │   ├── state/
│       │   │   │   ├── __init__.py  # 状态缓存适配器
│       │   │   │   └── redis_source_state_cache.py  # Redis-backed latest-state cache for ingest
│       │   │   └── __init__.py  # 适配器实现
│       │   ├── api/
│       │   │   ├── routes/
│       │   │   │   ├── __init__.py  # API 路由包。导出 ingest API 的各路由子模块
│       │   │   │   ├── acquisition_tasks.py  # 采集任务 CRUD 路由
│       │   │   │   ├── audit_events.py  # 审计事件查询路由
│       │   │   │   ├── bundles.py  # Bundle 元数据查询路由
│       │   │   │   ├── health.py  # 管理 健康检查 资源的 API 路由
│       │   │   │   ├── leases.py  # 管理 租约 资源的 API 路由
│       │   │   │   ├── nodes.py  # 管理 节点 资源的 API 路由
│       │   │   │   ├── runtime_config.py  # 管理 运行时配置 资源的 API 路由
│       │   │   │   ├── scheduler_jobs.py  # 管理 调度任务 资源的 API 路由
│       │   │   │   └── security_partitions.py  # 管理 安全分区 资源的 API 路由
│       │   │   ├── __init__.py  # Ingest API init
│       │   │   ├── app.py  # Ingest FastAPI 应用工厂
│       │   │   ├── audit_middleware.py  # 审计中间件
│       │   │   ├── errors.py  # API 错误定义
│       │   │   ├── idempotency.py  # 幂等键支持模块。为 ingest 运行时 CRUD API 提供防重复请求的中间件和服务
│       │   │   ├── readyz.py  # ingest 运行时模块级就绪探针聚合
│       │   │   └── schemas.py  # Ingest 运行时 CRUD API 的 Pydantic schema 定义
│       │   ├── bundle/
│       │   │   ├── __init__.py  # Bundle 服务包。提供 bundle 的导入、导出、签名、脱敏等核心能力
│       │   │   ├── checksum.py  # Bundle 校验和
│       │   │   ├── model.py  # Bundle 数据模型
│       │   │   ├── redaction.py  # Bundle 脱敏辅助函数。对 bundle 中的敏感字段按可配置规则做脱敏处理
│       │   │   └── service.py  # Bundle 服务
│       │   ├── decorators/
│       │   │   ├── __init__.py  # 装饰器模块
│       │   │   ├── source_acquisition.py  # 装饰器模块
│       │   │   ├── source_write.py  # 装饰器模块
│       │   │   └── state_cache.py  # 装饰器模块
│       │   ├── diagnostics/
│       │   │   ├── __init__.py  # Ingest 侧 runtime 诊断工具
│       │   │   ├── capacity.py  # Ingest runtime capacity —— 轻量端点/点位/读取容量扫描
│       │   │   ├── probe.py  # Ingest runtime probe —— 最小启动-健康-读取探测
│       │   │   └── profile.py  # Ingest runtime profile —— 对 read 执行 N 次采样并统计耗时
│       │   ├── docs/
│       │   │   ├── DECISIONS.md  # Ingest 模块决策
│       │   │   └── 设计说明书.md  # ingest 模块设计说明书
│       │   ├── domain/
│       │   │   ├── audit_event.py  # 审计事件领域模型
│       │   │   └── write_security_profile.py  # 写入安全配置文件
│       │   ├── entities/
│       │   │   ├── __init__.py  # 可复用实体定义。包含 node_state、source_health_state 等 ingest 领域实体
│       │   │   ├── node_state.py  # 节点状态实体
│       │   │   └── source_health_state.py  # 数据源健康状态实体
│       │   ├── file_ingest/
│       │   │   ├── __init__.py  # 文件接入子包
│       │   │   ├── decoder.py  # 文件接入专用解码器
│       │   │   ├── detector.py  # 文件落地完成检测器
│       │   │   ├── models.py  # 文件接入运行期数据模型与 DTO
│       │   │   ├── repository.py  # 文件接入仓储层
│       │   │   └── service.py  # 文件接入服务
│       │   ├── framework/
│       │   │   └── persistence/
│       │   │       ├── orm/
│       │   │       │   └── __init__.py  # 框架基础设施
│       │   │       ├── __init__.py  # 框架基础设施
│       │   │       ├── base.py  # SQLAlchemy 基础模型。定义 ingest 持久化层共用的 declarative base
│       │   │       ├── init_db.py  # 框架基础设施
│       │   │       ├── runtime_db.py  # 框架基础设施
│       │   │       └── session.py  # 框架基础设施
│       │   ├── ports/
│       │   │   ├── command/
│       │   │   │   ├── __init__.py  # 端口接口定义
│       │   │   │   └── source_command_audit_port.py  # 端口接口定义
│       │   │   ├── message/
│       │   │   │   ├── __init__.py  # 端口接口定义
│       │   │   │   └── message_publisher_port.py  # 端口接口定义
│       │   │   ├── runtime/
│       │   │   │   ├── __init__.py  # ingest 运行时 init
│       │   │   │   ├── access_policy_port.py  # ingest 运行时 access policy port
│       │   │   │   ├── source_runtime_config_port.py  # ingest 运行时 source runtime config port
│       │   │   │   └── write_lease_port.py  # ingest 运行时 write lease port
│       │   │   ├── source/
│       │   │   │   ├── __init__.py  # 端口接口定义
│       │   │   │   ├── source_acquisition_definition_port.py  # 端口接口定义
│       │   │   │   ├── source_acquisition_port.py  # source 采集端口定义
│       │   │   │   ├── source_acquisition_port_registry.py  # 端口接口定义
│       │   │   │   ├── source_write_port.py  # Source write/control port for ingest
│       │   │   │   └── source_write_port_registry.py  # 端口接口定义
│       │   │   ├── state/
│       │   │   │   ├── __init__.py  # 端口接口定义
│       │   │   │   ├── source_state_cache_port.py  # source latest-state cache 端口定义
│       │   │   │   └── source_state_snapshot_reader_port.py  # 端口接口定义
│       │   │   ├── __init__.py  # 端口接口定义
│       │   │   ├── audit.py  # 端口接口定义
│       │   │   ├── diagnostics.py  # IngestRuntimeDiagnosticsPort — 采集运行时诊断端口
│       │   │   └── metrics.py  # Ingest 指标 port 接口。声明计数器、直方图等指标契约，由具体 sink 实现
│       │   ├── runtime/
│       │   │   ├── __init__.py  # ingest 运行时 init
│       │   │   ├── acquisition_mode.py  # 采集模式定义
│       │   │   ├── cli.py  # ingest CLI 入口
│       │   │   ├── entrypoint.py  # ingest 启动入口
│       │   │   ├── fencing.py  # Fencing token 辅助模块。提供防脑裂的 fencing token 生成和验证能力
│       │   │   ├── handlers.py  # WorkerRuntime job handlers for ingest
│       │   │   ├── job_assignment.py  # 任务分配逻辑
│       │   │   ├── job_status.py  # 任务状态管理
│       │   │   ├── lease.py  # 分布式租约管理
│       │   │   ├── message_pipeline_settings.py  # 消息管道配置
│       │   │   ├── modes.py  # 运行模式定义
│       │   │   ├── node_runtime.py  # 节点运行时管理
│       │   │   ├── scheduler.py  # 采集调度器
│       │   │   ├── scheduler_factory.py  # 调度器工厂
│       │   │   ├── scheduler_job.py  # 调度任务定义
│       │   │   ├── scheduler_settings.py  # 调度器配置
│       │   │   ├── worker_runtime.py  # 基于 APScheduler 的 ingest worker 运行时。管理作业调度、心跳和指标
│       │   │   └── write_lease.py  # Write-control specific lease guard
│       │   ├── usecases/
│       │   │   ├── dtos/
│       │   │   │   ├── __init__.py  # 数据传输对象
│       │   │   │   ├── acquired_node_state.py  # 采集状态 DTO
│       │   │   │   ├── source_acquisition_request.py  # 采集请求 DTO
│       │   │   │   ├── source_acquisition_start_result.py  # SourceAcquisitionStartResult DTO — source 采集启动结果
│       │   │   │   ├── source_connection_data.py  # 采集连接 DTO
│       │   │   │   ├── source_write_request.py  # Source write request DTOs for the write/control use case
│       │   │   │   ├── source_write_result.py  # 数据传输对象
│       │   │   │   ├── state_publish_request.py  # 状态快照发布请求 DTO。承载一次发布操作所需的源标识、时间戳等参数
│       │   │   │   └── state_publish_result.py  # 数据传输对象
│       │   │   ├── roles/
│       │   │   │   ├── __init__.py  # 采集角色实现
│       │   │   │   ├── polling_acquisition_role.py  # Polling 采集 role
│       │   │   │   └── subscription_acquisition_role.py  # SubscriptionAcquisitionRole — 启动订阅采集 session
│       │   │   ├── __init__.py  # ingest usecase 导出
│       │   │   ├── source_acquisition_use_case.py  # 统一 source 采集 usecase
│       │   │   ├── source_command_use_case.py  # Source command/write use case
│       │   │   └── state_snapshot_publish_use_case.py  # 用例：将全量状态快照从缓存发布到消息队列。包含过滤、组装和发布全流程编排
│       │   ├── __init__.py  # Ingest 模块入口
│       │   ├── composition.py  # 依赖注入装配（composition root）
│       │   ├── config.py  # ingest 配置管理
│       │   └── message_pipeline.py  # 消息管线抽象。定义采集数据输出的发布接口和内存实现
│       ├── message_pipeline/
│       │   ├── adapters/
│       │   │   ├── __init__.py  # 消息管道适配器包
│       │   │   ├── in_memory.py  # 消息管道内存测试适配器
│       │   │   ├── kafka.py  # Kafka 消息管道适配器
│       │   │   └── pulsar.py  # Pulsar 消息管道适配器（contract adapter）
│       │   ├── __init__.py  # 消息管道模块
│       │   ├── model.py  # 消息管道领域模型
│       │   └── ports.py  # 消息管道端口接口
│       ├── model_asset/
│       │   ├── __init__.py  # 模型资产子包 — 仿真模型资产的导入、检测、归档与服务
│       │   ├── archive.py  # 仿真归档服务
│       │   ├── detector.py  # 仿真文件类型检测器
│       │   ├── models.py  # 模型资产 DTO 和数据模型
│       │   ├── repository.py  # 模型资产持久化仓库
│       │   └── service.py  # 模型资产导入编排服务
│       ├── processing/
│       │   ├── __init__.py  # 数据处理层（processing）—— 当前为骨架模块
│       │   ├── cleaner.py  # Cleaning rules for scenario1 normalized points
│       │   └── normalizer.py  # Raw batch normalization for scenario1
│       ├── shared/
│       │   ├── enums/
│       │   │   ├── __init__.py  # Shared enumerations
│       │   │   └── quality.py  # Stable enums shared across scenario pipelines
│       │   ├── persistence/
│       │   │   ├── orm/
│       │   │   │   ├── __init__.py  # Python 包入口与公开导出
│       │   │   │   └── models.py  # Python 模块：models
│       │   │   ├── template/
│       │   │   │   ├── 01_bluecrystal_create_database_v1_5_6.sql  # SQL 定义：01 bluecrystal create database v1 5 6
│       │   │   │   ├── 02_bluecrystal_schema_ddl_v1_5_6.sql  # SQL 定义：02 bluecrystal schema ddl v1 5 6
│       │   │   │   ├── 03_bluecrystal_basic_data_v1_5_6.sql  # SQL 定义：03 bluecrystal basic data v1 5 6
│       │   │   │   ├── 04_bluecrystal_site_sample_v1_5_6.sql  # SQL 定义：04 bluecrystal site sample v1 5 6
│       │   │   │   └── bluecrystal_model_v1_5_6.md  # BlueCrystal 数据模型正式版 v1.5.6
│       │   │   ├── views/
│       │   │   │   ├── __init__.py  # 共享持久化层数据库视图定义导出边界
│       │   │   │   ├── definition.py  # 数据库 view 定义的通用数据结构
│       │   │   │   ├── registry.py  # shared persistence 数据库 view 注册表
│       │   │   │   ├── scada_protocol_views.py  # SCADA 协议端点参数展平 view 的 SQLAlchemy Core 定义
│       │   │   │   └── scada_server_view.py  # SCADA server 汇总 view 的 SQLAlchemy Core 定义
│       │   │   ├── __init__.py  # Shared persistence layer for Whale
│       │   │   ├── base.py  # SQLAlchemy declarative base for all Whale ORM models
│       │   │   └── sample_data.py  # 共享持久化层 SCADA 协议样例数据生成器 —— whale 元数据库种子写入
│       │   ├── source/
│       │   │   ├── access/
│       │   │   │   ├── __init__.py  # Reusable source access models and adapters
│       │   │   │   ├── adapter.py  # Reusable source access adapter interfaces
│       │   │   │   ├── model.py  # Reusable runtime models for source access adapters
│       │   │   │   └── opcua.py  # Reusable OPC UA source access adapter
│       │   │   ├── http_rest/
│       │   │   │   ├── __init__.py  # HTTP REST shared source 模块
│       │   │   │   └── client.py  # HTTP REST 生产级 shared source backend
│       │   │   ├── iec101/
│       │   │   │   ├── backends/
│       │   │   │   │   ├── __init__.py  # IEC 101 backend 抽象与实现
│       │   │   │   │   ├── base.py  # IEC 101 backend 基础类型定义
│       │   │   │   │   └── serial_backend.py  # IEC 101 串行通信 backend
│       │   │   │   ├── __init__.py  # IEC 101 source read shared library
│       │   │   │   └── reader.py  # IEC 101 source reader facade
│       │   │   ├── iec104/
│       │   │   │   ├── backends/
│       │   │   │   │   ├── __init__.py  # IEC 104 backend abstractions for raw read/write
│       │   │   │   │   ├── base.py  # IEC 104 backend base types
│       │   │   │   │   └── lib60870_backend.py  # IEC 104 client backend backed by native C runner subprocess
│       │   │   │   ├── __init__.py  # IEC 104 source read/write shared library
│       │   │   │   └── reader.py  # IEC 104 source reader/writer facade
│       │   │   ├── iec61850/
│       │   │   │   ├── backends/
│       │   │   │   │   ├── __init__.py  # IEC 61850 backend implementations
│       │   │   │   │   ├── base.py  # IEC 61850 MMS backend base types
│       │   │   │   │   ├── libiec61850_backend.py  # libiec61850-based IEC 61850 MMS client backend (subprocess runner)
│       │   │   │   │   ├── libiec61850_report_backend.py  # libiec61850-based IEC 61850 Report backend (subprocess runner)
│       │   │   │   │   └── report_base.py  # IEC 61850 Report backend base types
│       │   │   │   ├── __init__.py  # IEC 61850 MMS source implementations
│       │   │   │   ├── reader.py  # IEC 61850 MMS source reader facade
│       │   │   │   └── report_reader.py  # IEC 61850 Report source reader facade
│       │   │   ├── modbus/
│       │   │   │   ├── backends/
│       │   │   │   │   ├── __init__.py  # Modbus backend abstractions for raw read/write
│       │   │   │   │   ├── base.py  # Modbus TCP backend base types
│       │   │   │   │   └── libmodbus_backend.py  # Modbus TCP client backend backed by native C runner subprocess
│       │   │   │   ├── __init__.py  # Modbus TCP source read/write shared library
│       │   │   │   └── reader.py  # Modbus TCP source reader/writer facade
│       │   │   ├── modbus_rtu/
│       │   │   │   ├── backends/
│       │   │   │   │   ├── __init__.py  # Modbus RTU backend 抽象与实现
│       │   │   │   │   ├── base.py  # Modbus RTU backend 基础类型定义
│       │   │   │   │   └── serial_backend.py  # Modbus RTU 串行通信 backend
│       │   │   │   ├── __init__.py  # Modbus RTU source read shared library
│       │   │   │   └── reader.py  # Modbus RTU source reader facade
│       │   │   ├── mqtt/
│       │   │   │   ├── __init__.py  # MQTT shared source 模块
│       │   │   │   └── client.py  # MQTT 生产级 shared source backend
│       │   │   ├── opcua/
│       │   │   │   ├── backends/
│       │   │   │   │   ├── __init__.py  # OPC UA client backend abstractions for raw polling
│       │   │   │   │   ├── base.py  # OPC UA 客户端后端抽象基类
│       │   │   │   │   ├── factory.py  # OPC UA 客户端后端工厂
│       │   │   │   │   └── open62541_backend.py  # open62541 OPC UA 客户端后端实现
│       │   │   │   ├── __init__.py  # OPC UA source implementations
│       │   │   │   └── reader.py  # Open62541-backed OPC UA raw polling facade
│       │   │   ├── scheduling/
│       │   │   │   ├── __init__.py  # Public exports for the worker-local source polling kernel
│       │   │   │   ├── concurrency.py  # Worker-local read concurrency control for high-frequency source polling
│       │   │   │   ├── fixed_rate.py  # Diagnostic-only high-frequency fixed-rate scheduler
│       │   │   │   ├── polling.py  # Worker-local fixed-rate polling primitives for source acquisition
│       │   │   │   └── stagger.py  # Deterministic stagger-offset helpers for worker-local source polling
│       │   │   ├── __init__.py  # 统一对外暴露 source 层接口和 OPC UA reader
│       │   │   ├── models.py  # 统一的 source 层数据模型，用于 read / subscription batch 处理
│       │   │   ├── ports.py  # 优化后的 ports.py
│       │   │   └── runner_resolution.py  # Shared native runner path resolution for production source clients
│       │   ├── utils/
│       │   │   └── time.py  # Time utilities for deterministic scenario processing
│       │   └── __init__.py  # Shared helpers for Whale
│       ├── speed_layer/
│       │   ├── preprocessing/
│       │   │   ├── __init__.py  # speed layer 预处理 Pipeline — Round A
│       │   │   ├── models.py  # speed layer 预处理 Pipeline 运行期 DTO 与 dataclass
│       │   │   ├── operators.py  # speed layer 预处理 Operator 实现
│       │   │   ├── pipeline.py  # speed layer 预处理 Pipeline — 固定 10 阶段编排
│       │   │   └── registry.py  # speed layer 预处理 Operator / Strategy Registry
│       │   ├── __init__.py  # speed layer 模块
│       │   ├── light_processor.py  # speed layer 实时轻处理管线（SP-FR-004）
│       │   ├── metrics.py  # speed layer 指标收集
│       │   ├── runner.py  # speed layer pipeline runner
│       │   └── writers.py  # speed layer 消息消费者与写入者
│       ├── storage/
│       │   ├── __init__.py  # Whale 数据底座存储层
│       │   ├── mart.py  # 数据集市层（mart）——面向业务服务的预聚合数据
│       │   ├── raw_archive.py  # 原始归档层（raw_archive）——不可变原始事实层
│       │   ├── raw_index.py  # 原始时序索引层（raw_index）——TDengine 快速查询入口
│       │   ├── serving_cache.py  # 业务侧近实时 serving cache 层
│       │   ├── simulation_result.py  # 仿真结果时序存储端口与适配器
│       │   ├── standardized.py  # 标准时序层（standardized）——TDengine 清洗后数据存储
│       │   ├── warehouse.py  # 数据仓库层（warehouse）——面向主题分析的数据存储
│       │   └── waveform.py  # 标准化波形存储端口与适配器
│       └── __init__.py  # Whale - 能源数据统一平台
├── tests/  # 测试代码与测试支持
│   ├── deployment/
│   │   └── README.md  # Deployment Tests
│   ├── e2e/
│   │   ├── __init__.py  # Whale 主平台 E2E 测试包
│   │   ├── conftest.py  # E2E test fixtures: PostgreSQL + Redis + Kafka infrastructure
│   │   ├── helpers.py  # Shared helpers for e2e tests — importable utilities and constants
│   │   ├── test_whale_field_minimal_smoke.py  # Whale 现场最小链路 E2E smoke 测试
│   │   ├── test_whale_l5_kafka_pipeline_e2e.py  # Whale L5 端到端验证测试 — Kafka pipeline
│   │   └── test_whale_l5_storage_e2e.py  # Whale L5 端到端验证测试 — 存储层（S3/MinIO + TDengine + Redis）
│   ├── integration/
│   │   ├── __init__.py  # Whale 主平台 integration 测试包
│   │   ├── starfish/
│   │   │   └── test_iec104_c104_runtime.py  # 真实 View 与 c104 双角色网络闭环测试
│   │   ├── test_framework_db_init.py  # Integration tests for framework database initialization
│   │   ├── test_http_rest_acquisition_chain.py  # HTTP REST 全链路采集集成测试
│   │   ├── test_iec101_acquisition_chain.py  # IEC 101 全链路采集集成测试
│   │   ├── test_iec104_acquisition_chain.py  # IEC104 全链路采集集成测试
│   │   ├── test_ingest_api_acquisition_task_crud.py  # Acquisition-task CRUD integration tests
│   │   ├── test_ingest_api_audit.py  # API audit integration tests
│   │   ├── test_ingest_api_authorization_deny.py  # Authorization deny E2E tests for ingest runtime API
│   │   ├── test_ingest_api_bundle_metadata_crud.py  # Bundle-metadata query API integration tests
│   │   ├── test_ingest_api_dry_run_all_mutating_routes.py  # Dry-run coverage across all mutating CRUD routes
│   │   ├── test_ingest_api_full_audit_matrix.py  # Full audit matrix integration tests — verify every API action emits audit
│   │   ├── test_ingest_api_idempotency_all_mutating_routes.py  # Idempotency-Key coverage across all mutating CRUD route groups
│   │   ├── test_ingest_api_idempotency_dry_run.py  # Integration tests for API idempotency key and dry-run support
│   │   ├── test_ingest_api_idempotency_dry_run_interaction.py  # Idempotency-Key + dry_run=true interaction tests
│   │   ├── test_ingest_api_node_lease_audit_query.py  # Node / Lease / Audit-event query API integration tests
│   │   ├── test_ingest_api_runtime_config_audit.py  # Runtime-config API audit tests
│   │   ├── test_ingest_api_runtime_config_crud.py  # Runtime-config CRUD integration tests
│   │   ├── test_ingest_api_scheduler_job_crud.py  # Scheduler-job CRUD integration tests
│   │   ├── test_ingest_api_security_partition_crud.py  # Security-partition CRUD integration tests
│   │   ├── test_ingest_audit_db_jsonl_consistency.py  # Audit DB/JSONL sink consistency tests
│   │   ├── test_ingest_audit_matrix_api_bundle_scheduler_write.py  # Audit matrix tests covering API, bundle, scheduler, and write events
│   │   ├── test_ingest_bundle_import_export.py  # Bundle import/export integration tests
│   │   ├── test_ingest_bundle_offline_one_way_flow.py  # Offline one-way bundle flow tests
│   │   ├── test_ingest_cache_to_kafka_pipeline.py  # Integration test: cache snapshot → StateSnapshotPublishUseCase → Kafka publisher
│   │   ├── test_ingest_dual_node_db_lease_e2e.py  # 双节点实时数据库 lease 冲突 E2E 测试
│   │   ├── test_ingest_external_access_policy_contract.py  # External access policy contract tests with a local HTTP stub server
│   │   ├── test_ingest_external_audit_sink_contract.py  # External audit/SIEM sink contract tests with a local HTTP stub server
│   │   ├── test_ingest_file_ingest_integration.py  # 文件接入模块集成测试
│   │   ├── test_ingest_iec104_source_write.py  # Integration test for IEC 104 source write via SourceCommandUseCase
│   │   ├── test_ingest_iec61850_mms_source_write.py  # Integration test for IEC 61850 MMS source write via SourceCommandUseCase
│   │   ├── test_ingest_iec61850_report_subscription.py  # IEC 61850 Report subscription integration tests
│   │   ├── test_ingest_lightweight_load_gate.py  # Lightweight ingest load gate with in-memory/test sinks
│   │   ├── test_ingest_modbus_source_write.py  # Integration test for Modbus TCP source write via SourceCommandUseCase
│   │   ├── test_ingest_observability_sink_smoke.py  # Smoke test for deployment-ready JSONL observability sinks
│   │   ├── test_ingest_opcua_source_write.py  # Integration test for OPC UA source write via SourceCommandUseCase
│   │   ├── test_ingest_polling_retry_to_redis.py  # Integration tests for polling retry semantics against Redis latest-state cache
│   │   ├── test_ingest_prodlike_access_policy.py  # Production-like access policy integration tests
│   │   ├── test_ingest_prodlike_audit_metrics_resilience.py  # Audit and metrics resilience tests under prodlike dependency failures
│   │   ├── test_ingest_prodlike_audit_sink.py  # Production-like audit sink integration tests
│   │   ├── test_ingest_prodlike_endurance_smoke.py  # Short-duration endurance smoke for the prodlike ingest compose profile
│   │   ├── test_ingest_prodlike_kafka_fault_injection.py  # Kafka fault injection and recovery tests for prodlike ingest runtime
│   │   ├── test_ingest_prodlike_kafka_publish.py  # Production-like Kafka publish integration tests
│   │   ├── test_ingest_prodlike_performance_profile.py  # Performance profile conformance tests for ingest runtime
│   │   ├── test_ingest_prodlike_postgres_fault_injection.py  # PostgreSQL fault injection and recovery tests for prodlike ingest runtime
│   │   ├── test_ingest_prodlike_postgres_runtime_db.py  # Production-like PostgreSQL runtime DB integration tests
│   │   ├── test_ingest_prodlike_redis_cache.py  # Production-like Redis cache integration tests
│   │   ├── test_ingest_prodlike_redis_fault_injection.py  # Redis fault injection and recovery tests for prodlike ingest runtime
│   │   ├── test_ingest_prodlike_scheduler_backpressure.py  # Scheduler backpressure, missed-tick, and assignment-lag tests
│   │   ├── test_ingest_prodlike_worker_failover.py  # Worker crash, restart, fencing, and failover tests
│   │   ├── test_ingest_runtime_alembic_migration.py  # Alembic migration integration tests
│   │   ├── test_ingest_runtime_alembic_postgres_matrix.py  # Alembic PostgreSQL migration matrix — upgrade head & verify schema
│   │   ├── test_ingest_runtime_alembic_sqlite_matrix.py  # Alembic SQLite migration matrix — upgrade head & downgrade base
│   │   ├── test_ingest_runtime_db_init.py  # Runtime DB initialization smoke
│   │   ├── test_ingest_runtime_entrypoint_smoke.py  # CLI smoke tests for ingest runtime entrypoints
│   │   ├── test_ingest_runtime_migrate_entrypoint.py  # Integration tests for the migrate CLI entrypoint
│   │   ├── test_ingest_scheduler_active_standby_failover.py  # Active-standby scheduler failover tests
│   │   ├── test_ingest_scheduler_apscheduler_runtime.py  # Integration tests for WorkerRuntime / APScheduler-driven ingestion
│   │   ├── test_ingest_scheduler_cluster_assignment.py  # Cluster scheduler assignment tests
│   │   ├── test_ingest_scheduler_dual_active_partitioned.py  # Dual-active partitioned scheduler tests
│   │   ├── test_ingest_scheduler_graceful_shutdown.py  # Integration tests for WorkerRuntime graceful shutdown
│   │   ├── test_ingest_scheduler_missed_tick_and_stagger.py  # Integration tests for missed_tick and stagger_offset behavior
│   │   ├── test_ingest_security_partition_bundle_flow.py  # Security partition one-way bundle flow tests for ingest
│   │   ├── test_ingest_security_partition_smoke.py  # Security partition sample-config smoke
│   │   ├── test_ingest_source_acquisition_to_redis.py  # Integration test for source server -> Redis latest-state cache
│   │   ├── test_ingest_source_cache_message_e2e.py  # Integration test for source -> cache -> message chain
│   │   ├── test_ingest_source_cache_message_kafka_e2e.py  # Kafka container E2E for source -> cache -> message
│   │   ├── test_ingest_subscription_strategy.py  # Integration tests for current subscription strategy boundaries
│   │   ├── test_ingest_worker_runtime_executes_usecase_handlers.py  # Integration tests for WorkerRuntime job-type handler dispatch
│   │   ├── test_ingest_worker_runtime_handler_failure.py  # Integration tests for WorkerRuntime handler failure and missing handler
│   │   ├── test_ingest_worker_runtime_shutdown_inflight.py  # Integration tests for WorkerRuntime shutdown with inflight jobs
│   │   ├── test_ingest_write_lease_fencing_e2e.py  # Write lease / fencing / readback integration tests
│   │   ├── test_l5_external_dependency_verification.py  # P5 准生产依赖验证期 — 外部依赖接入验证测试
│   │   ├── test_message_pipeline_inmemory_e2e.py  # message_pipeline InMemory 全链路集成测试
│   │   ├── test_message_pipeline_kafka_e2e.py  # message_pipeline Kafka 集成测试（contract-only）
│   │   ├── test_modbus_rtu_acquisition_chain.py  # Modbus RTU 全链路采集集成测试
│   │   ├── test_model_asset_alembic_migration.py  # model_asset Alembic migration 集成测试
│   │   ├── test_model_asset_integration.py  # model_asset 模块集成测试
│   │   ├── test_model_asset_postgres_integration.py  # model_asset PostgreSQL 真实集成测试
│   │   ├── test_mqtt_acquisition_chain.py  # MQTT 全链路采集集成测试
│   │   ├── test_redis_state_cache_faults.py  # Integration tests for live Redis latest-state cache fault handling
│   │   ├── test_shared_persistence_sample_data_init.py  # 共享持久化样例初始化 PostgreSQL 集成测试
│   │   ├── test_speed_layer_dlq_replay.py  # speed layer DLQ 与 replay 语义集成测试
│   │   ├── test_speed_layer_index_standardized_pipeline.py  # speed layer index 和 standardized 管道集成测试
│   │   ├── test_speed_layer_raw_archive_pipeline.py  # speed layer raw_archive 管道集成测试
│   │   ├── test_sqlite_config_init.py  # Integration tests for the SQLite config initialization script
│   │   ├── test_storage_simulation_result_tdengine_integration.py  # TDengine simulation_result 真实写入/读回集成测试
│   │   ├── test_storage_waveform_tdengine_integration.py  # TDengine waveform 真实写入/读回集成测试
│   │   ├── test_whale_writer_failure_recovery.py  # Whale writer 故障恢复集成测试
│   │   └── test_whale_writer_switchover.py  # Whale writer 无缝切换集成测试
│   ├── performance/
│   │   ├── endurance/
│   │   │   └── __init__.py  # 续航测试包
│   │   ├── load/
│   │   │   ├── __init__.py  # 负载测试包
│   │   │   └── conftest.py  # Load test fixtures: PostgreSQL + Redis + Kafka, large NodeSets
│   │   ├── stress/
│   │   │   ├── __init__.py  # 压力测试包
│   │   │   └── test_acquisition_pipeline_stress.py  # Current-architecture stress smoke for ingest acquisition -> Redis latest-state cache
│   │   └── __init__.py  # 性能测试包
│   ├── support/
│   │   ├── ingest_prodlike_runtime.py  # Shared helpers for prodlike ingest compose, endurance, and fault tests
│   │   ├── scada_sample_db.py  # shared persistence SCADA sample DB 测试辅助函数
│   │   └── shared_persistence_sample_db.py  # Helpers for creating isolated shared persistence sample databases in tests
│   ├── unit/
│   │   ├── architecture/
│   │   │   ├── __init__.py  # 构建期门禁测试包
│   │   │   ├── test_seahorse_import_boundary.py  # seahorse / ingest / starfish import boundary 门禁测试
│   │   │   └── test_starfish_import_boundary.py  # starfish import boundary 门禁测试
│   │   ├── seahorse/
│   │   │   ├── __init__.py  # seahorse 单元测试
│   │   │   ├── test_bundle.py  # seahorse 场景包导出与校验测试
│   │   │   ├── test_compat_wrappers.py  # seahorse 旧路径硬清理验证
│   │   │   ├── test_datasource_runtime.py  # Seahorse DataSource runtime 最小实现单元测试
│   │   │   ├── test_generators.py  # seahorse 生成器测试 —— 告警与控制回写
│   │   │   ├── test_main_typer_cli.py  # Seahorse ''__main__.py'' Typer CLI 行为测试
│   │   │   ├── test_models.py  # seahorse 核心模型序列化与确定性种子测试
│   │   │   ├── test_orchestrator.py  # seahorse 最小编排器测试
│   │   │   ├── test_reference_data_imports.py  # seahorse reference_data 硬清理验证
│   │   │   ├── test_runtime_contract.py  # Seahorse runtime contract 单元测试
│   │   │   ├── test_runtime_smoke_workflow.py  # Seahorse 内存 runtime smoke workflow 单元测试
│   │   │   ├── test_scheduler_executor.py  # Seahorse scheduler executor 最小实现单元测试
│   │   │   ├── test_server_plan.py  # seahorse ServerConfig 契约校验、handoff 导出与 CLI 测试
│   │   │   ├── test_starfish_writer_dispatch.py  # Seahorse StarfishWriter batch dispatch 最小实现测试
│   │   │   ├── test_strategies.py  # seahorse 生成策略测试
│   │   │   └── test_whale_write_plan_read_chain.py  # Seahorse Whale metadata 到 WritePlan 读取链路单元测试
│   │   ├── shared/
│   │   │   └── persistence/
│   │   │       ├── test_model_asset_orm.py  # model_asset ORM 表定义与约束单元测试
│   │   │       ├── test_scada_protocol_params.py  # SCADA 协议参数模板与 ORM 单测
│   │   │       ├── test_scada_protocol_views.py  # SCADA 协议视图定义单测
│   │   │       └── test_scada_sample_data_protocol_coverage.py  # SCADA 多协议样例数据覆盖单测
│   │   ├── starfish/
│   │   │   ├── __init__.py  # starfish unit 测试包
│   │   │   ├── conftest.py  # Starfish unit 测试子树的通用 marker 约束
│   │   │   ├── test_connection_db_view_loader.py  # 通用 connection view loader 与 composition protocol 分派测试
│   │   │   ├── test_iec104_backend.py  # Starfish c104 双角色 backend 行为测试
│   │   │   ├── test_iec104_db_view_loader.py  # IEC104 当前四类 view 契约测试
│   │   │   ├── test_iec104_server.py  # IEC104 worker API 与 protocol factory 测试
│   │   │   ├── test_import_boundary.py  # Starfish 与其他业务 Python 包的 AST 隔离门禁
│   │   │   ├── test_runtime_api.py  # Starfish manager 与 IEC104 worker 生命周期测试
│   │   │   └── test_starfish_cli.py  # Starfish CLI 的 DB selector 与生命周期测试
│   │   ├── __init__.py  # Whale 主平台 unit 测试包
│   │   ├── test_acquisition_job_handler.py  # AcquisitionJobHandler 单元测试
│   │   ├── test_config.py  # Unit tests for ingest configuration resolution
│   │   ├── test_dual_node_write_lease_conflict.py  # 双节点写入冲突与 lease/fencing 并发语义测试
│   │   ├── test_http_rest_backend.py  # HTTP REST client backend 单元测试
│   │   ├── test_http_rest_source_acquisition_adapter.py  # HTTP REST 采集适配器单元测试
│   │   ├── test_iec101_backend.py  # IEC 101 backend 单元测试
│   │   ├── test_iec101_source_acquisition_adapter.py  # IEC 101 source 采集适配器单元测试
│   │   ├── test_iec104_backend.py  # Unit tests for IEC 104 backend (stdout protocol parsing)
│   │   ├── test_iec104_source_acquisition_adapter.py  # Unit tests for IEC 104 source acquisition adapter
│   │   ├── test_iec104_source_write_adapter.py  # Unit tests for IEC 104 source write adapter
│   │   ├── test_iec61850_mms_backend.py  # libiec61850 backend 单元测试
│   │   ├── test_iec61850_report_acquisition_adapter.py  # Tests for Iec61850ReportSourceAcquisitionAdapter
│   │   ├── test_iec61850_report_backend.py  # Tests for LibIec61850ReportBackend — report event parsing & subprocess protocol
│   │   ├── test_iec61850_source_acquisition_adapter.py  # Iec61850MmsSourceAcquisitionAdapter 单元测试
│   │   ├── test_iec61850_source_write_adapter.py  # Iec61850MmsSourceWriteAdapter 单元测试
│   │   ├── test_ingest_api_app.py  # FastAPI app factory tests
│   │   ├── test_ingest_audit_event_schema.py  # Structured ingest audit event tests
│   │   ├── test_ingest_audit_redaction.py  # Unit tests for audit event redaction
│   │   ├── test_ingest_bundle_checksum.py  # Bundle checksum tests
│   │   ├── test_ingest_bundle_redaction.py  # Bundle redaction tests
│   │   ├── test_ingest_composition_injection.py  # QA-1: composition.py 注入完整性测试
│   │   ├── test_ingest_file_ingest_decoder.py  # 文件接入解码器单元测试
│   │   ├── test_ingest_file_ingest_detector.py  # 文件落地完成检测器单元测试
│   │   ├── test_ingest_file_ingest_models.py  # 文件接入 DTO 模型单元测试
│   │   ├── test_ingest_file_ingest_repository.py  # 文件接入仓储层单元测试
│   │   ├── test_ingest_file_ingest_service.py  # 文件接入服务单元测试
│   │   ├── test_ingest_job_lease.py  # DB-backed lease semantics tests
│   │   ├── test_ingest_metrics_events.py  # Metrics event emission tests for ingest core chains
│   │   ├── test_ingest_no_source_lab_imports.py  # 确保 ingest 生产代码不引入 tools.source_lab（目录已物理删除，此检查为历史门禁保留）
│   │   ├── test_ingest_observability_sink.py  # Unit tests for lightweight ingest observability sinks
│   │   ├── test_ingest_readyz.py  # ingest readyz 模块级就绪聚合单元测试
│   │   ├── test_ingest_runtime_entrypoint.py  # CLI entrypoint tests for ingest runtime
│   │   ├── test_ingest_runtime_modes.py  # Runtime mode parsing tests
│   │   ├── test_ingest_runtime_orm_models.py  # Runtime ORM model registration tests
│   │   ├── test_ingest_runtime_scheduler_import.py  # Import smoke for the ingest runtime scheduler package
│   │   ├── test_ingest_security_partition_config.py  # Security partition config guard tests
│   │   ├── test_ingest_source_adapter_capability_matrix.py  # Ingest adapter capability matrix guard
│   │   ├── test_ingest_write_lease.py  # Write lease service tests
│   │   ├── test_ingest_write_lease_fencing.py  # Write lease fencing tests
│   │   ├── test_ingest_write_security_profile.py  # Unit tests for WriteSecurityProfile domain model
│   │   ├── test_kafka_message_publisher.py  # Unit tests for the Kafka snapshot publisher
│   │   ├── test_message_pipeline_adapters.py  # message_pipeline InMemory 适配器单元测试
│   │   ├── test_message_pipeline_envelope.py  # message_pipeline 领域模型单元测试
│   │   ├── test_message_pipeline_kafka_adapter.py  # Kafka message_pipeline 适配器契约与配置测试
│   │   ├── test_message_pipeline_ports.py  # message_pipeline 端口接口契约测试
│   │   ├── test_modbus_rtu_backend.py  # Modbus RTU backend 单元测试
│   │   ├── test_modbus_rtu_source_acquisition_adapter.py  # Modbus RTU source 采集适配器单元测试
│   │   ├── test_modbus_source_acquisition_adapter.py  # ModbusSourceAcquisitionAdapter 单元测试
│   │   ├── test_modbus_source_write_adapter.py  # ModbusSourceWriteAdapter 单元测试
│   │   ├── test_model_asset_detector.py  # model_asset detector 单元测试
│   │   ├── test_model_asset_models.py  # model_asset DTO 模型单元测试
│   │   ├── test_model_asset_repository.py  # model_asset repository 单元测试
│   │   ├── test_model_asset_service.py  # model_asset service 单元测试
│   │   ├── test_mqtt_backend.py  # MQTT client backend 单元测试
│   │   ├── test_mqtt_source_acquisition_adapter.py  # MQTT 采集适配器单元测试
│   │   ├── test_opcua_adapter_resolution.py  # OPC UA adapter 地址解析单元测试
│   │   ├── test_opcua_source_acquisition_adapter.py  # OPC UA source acquisition adapter 单元测试
│   │   ├── test_opcua_source_write_adapter.py  # OpcUaSourceWriteAdapter 单元测试
│   │   ├── test_open62541_backend.py  # open62541 backend 单元测试
│   │   ├── test_polling_acquisition_role.py  # PollingAcquisitionRole 单元测试
│   │   ├── test_redis_source_state_cache.py  # Unit tests for the Redis latest-state cache adapter
│   │   ├── test_redis_streams_message_publisher.py  # Unit tests for the Redis Streams snapshot publisher
│   │   ├── test_relational_outbox_message_publisher.py  # Unit tests for the relational outbox snapshot publisher
│   │   ├── test_scheduler_job_routes.py  # QA-5: scheduler_job stagger_offset_ms 持久化端到端测试
│   │   ├── test_shared_source_runner_resolution.py  # shared_source native runner path resolution boundary tests
│   │   ├── test_source_acquisition_port_registry.py  # StaticSourceAcquisitionPortRegistry 单元测试
│   │   ├── test_source_acquisition_use_case.py  # SourceAcquisitionUseCase 单元测试
│   │   ├── test_source_command_audit.py  # SourceCommandUseCase audit tests
│   │   ├── test_source_command_authorization_guard.py  # Unit tests for AuthorizedSourceWritePort
│   │   ├── test_source_command_lease_release.py  # QA-2: SourceCommandUseCase 异常路径 lease release 测试
│   │   ├── test_source_command_use_case.py  # SourceCommandUseCase 单元测试
│   │   ├── test_source_command_write_lease_guard.py  # Source command write lease guard tests
│   │   ├── test_source_runtime_config_repository.py  # Unit tests for the runtime-config repository
│   │   ├── test_source_scheduling.py  # Unit tests for the worker-local source polling kernel
│   │   ├── test_source_write_port_registry.py  # Source write port registry 单元测试
│   │   ├── test_speed_layer_light_processor.py  # speed layer 轻处理管线单元测试（SP-FR-004）
│   │   ├── test_speed_layer_pipeline_runner.py  # speed layer pipeline runner 单元测试
│   │   ├── test_speed_layer_preprocessing.py  # speed layer 预处理 Pipeline Round A 测试
│   │   ├── test_state_snapshot_publish_use_case.py  # StateSnapshotPublishUseCase 单元测试
│   │   ├── test_storage_raw_archive.py  # storage raw_archive 层单元测试
│   │   ├── test_storage_raw_index.py  # storage raw_index 层单元测试
│   │   ├── test_storage_serving_cache.py  # storage serving_cache Redis 适配器单元测试
│   │   ├── test_storage_simulation_result.py  # storage simulation_result 单元测试
│   │   ├── test_storage_standardized.py  # storage standardized 层单元测试
│   │   ├── test_storage_waveform.py  # storage waveform 层单元测试
│   │   ├── test_subscription_acquisition_role.py  # SubscriptionAcquisitionRole unit tests
│   │   ├── test_subscription_reconnect_baseline.py  # Reconnect baseline read strategy tests for SubscriptionAcquisitionRole
│   │   ├── test_subscription_reconnect_runtime.py  # Subscription runtime reconnect/backoff/max-retry tests
│   │   ├── test_turtle_octopus_import_boundary.py  # turtle/octopus 与 platform_shared 的 import boundary 门禁测试
│   │   └── test_worker_runtime_do_execute.py  # WorkerRuntime._do_execute handler dispatch 单元测试
│   ├── __init__.py  # 测试包初始化
│   ├── conftest.py  # Shared pytest fixtures for ingest integration tests
│   ├── issue_trace.md  # 测试问题追踪
│   └── TESTING.md  # Whale 主平台测试指南
├── .gitignore  # Git 忽略规则
├── .mcp.json  # MCP 工具配置
├── AGENTS.md  # Codex / Agent 执行入口
├── alembic.ini  # Alembic 主配置
├── CLAUDE.md  # 共享执行入口与编排规则
├── pyproject.toml  # Python 项目元数据、依赖与工具配置
└── README.md  # BlueCrystal 项目说明与快速开始
```

## 3. 关键入口与边界

- `CLAUDE.md` 与 `ai_shared/rules/routing.md`：Agent 执行、规则路由与固定流程入口。
- `pyproject.toml`：Python 包、依赖和 Ruff / Black / mypy / pytest 配置入口。
- `src/whale/`：能源数据平台的采集、消息管道、速度层、共享持久化与存储实现。
- `src/seahorse/`：按 Clean Architecture 组织的样例场站、场景和时序数据生成组件。
- `src/starfish/`：按 Hexagonal Architecture 组织的 IEC104 simulator 生命周期管理；`composition.py` 是装配根，`core/` 是内核，`adapters/` 是 DB view 与协议适配器。
- `src/platform_shared/`：不归属具体业务域的公共契约、内核和横切能力。
- `src/turtle/`：安全、合规、审计和治理基础能力。
- `src/octopus/`：部署、监控、告警、诊断和自动化运维基础能力。
- `src/manta/`：Vue / TypeScript 前端及 Cesium 可视化资源。
- `src/tools/`：跨业务模块的通用工具，当前包含 SQLAlchemy session 工具。
- `tests/`：deployment、e2e、integration、performance、support 与 unit 分层测试。

## 4. 与旧目录树的主要差异

- 删除旧文件中的多轮开发过程、历史验证结果和重复架构叙述，使本文件恢复为当前状态导航索引。
- 按当前工作区重列 Starfish：保留 `core/`、`composition.py`、`adapters/db_views/` 与 `adapters/protocols/iec104/`，不再列出当前已删除的旧 `application/`、`domain/`、`infrastructure/`、`api/` 和多协议 driver 路径。
- 将 `.claude/`、`.codex/` 和 `.vscode/settings.json` 纳入文件级导航；它们是仓库内实际配置，但共享规则语义仍以 `ai_shared/` 为准。
- 扫描数量、文件类型分布和省略数量改为本次实际计算值，不沿用旧树的估算值。
- 前端海量 terrain / imagery / GLB 资产按类别计数省略，保留 `src/manta/public/terrain/layer.json` 作为图层元数据入口。

## 5. 风险与使用限制

- 当前工作区包含大量未提交的 Starfish 重构；本树准确反映扫描时磁盘状态，但在这些变更提交、撤销或继续调整后可能立即过期。
- 自动提取的行尾职责注释适合定位；判断真实依赖、接口、schema、测试覆盖或运行状态时，必须再次读取目标文件并执行相应验证。
- 本次只重建导航文档，没有运行源码测试，也不把文件存在或扫描成功视为功能通过。
