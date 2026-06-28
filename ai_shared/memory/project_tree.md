# BlueCrystal Project Tree

> 全量重建日期: 2026-06-28
> 来源: 仓库真实文件扫描。
> 用途: 导航索引；不能替代读取真实源码、测试、配置和 schema。

## 扫描口径

- 原始文件数: 3718
- 纳入导航文件数: 1936
- 省略文件数: 1782
- 省略范围: `.git`、虚拟环境、cache、build/dist/tmp、日志、字节码、egg-info、third_party、系统元数据、锁文件、二进制/图片/字体/压缩包等生成或第三方资产。

## 目录树

```text
.
├── .claude/ — Claude agent 配置
│   ├── agents/
│   │   ├── code-implementer.md                 — code-implementer
│   │   ├── project-steward.md                  — project-steward
│   │   ├── test-validator.md                   — test-validator
│   ├── settings.json                       — JSON 配置
│   ├── settings.local.json                 — JSON 配置
├── .codex/ — Codex agent 配置
│   ├── agents/
│   │   ├── code-implementer.toml               — TOML 配置
│   │   ├── project-steward.toml                — TOML 配置
│   │   ├── test-validator.toml                 — TOML 配置
│   ├── config.toml                         — TOML 配置
│   ├── hooks.json                          — JSON 配置
├── .vscode/ — VS Code 工作区配置
│   ├── settings.json                       — JSON 配置
├── ai_shared/ — 共享规则、记忆与 agent 配置
│   ├── agent_config/ — 共享 agent 配置
│   │   ├── hooks/ — 安全与质量 hook
│   │   │   ├── block-dangerous-bash.py             — 阻断明显危险的 shell 命令。
│   │   │   ├── block-git-write-ops.py              — 阻断默认不允许的 Git/GitHub 写操作。
│   │   │   ├── comment-doc-gate.py                 — 轻量检查 changed files 的文档注释、类型抑制和危险异常模式。
│   │   │   ├── docstring-cn-gate.py                — 兼容旧 hook 名称；实际规则已升级为通用注释与文档注释检查。
│   │   │   ├── no-source-lab-import-gate.sh        — Shell 脚本
│   │   ├── skills/ — Codex/Claude skills
│   │   │   ├── changed-files-gate/
│   │   │   │   ├── SKILL.md                            — Skill 使用说明
│   │   │   ├── code-quality-gate/
│   │   │   │   ├── SKILL.md                            — Skill 使用说明
│   │   │   ├── commit-message/
│   │   │   │   ├── SKILL.md                            — Skill 使用说明
│   │   │   ├── heavy-regression/
│   │   │   │   ├── SKILL.md                            — Skill 使用说明
│   │   │   ├── project-tree-reset/
│   │   │   │   ├── SKILL.md                            — Skill 使用说明
│   │   │   ├── project-tree-update/
│   │   │   │   ├── SKILL.md                            — Skill 使用说明
│   │   │   ├── requirement-trace/
│   │   │   │   ├── SKILL.md                            — Skill 使用说明
│   │   │   ├── rule-update/
│   │   │   │   ├── SKILL.md                            — Skill 使用说明
│   ├── memory/ — 长期记忆与需求索引
│   │   ├── BlueCrystal_REQ_BatchLayer.md       — BlueCrystal_REQ_BatchLayer
│   │   ├── BlueCrystal_REQ_BatchProcessing.md  — BlueCrystal_REQ_BatchProcessing
│   │   ├── BlueCrystal_REQ_Ingest.md           — BlueCrystal_REQ_Ingest
│   │   ├── BlueCrystal_REQ_MessagePipeline.md  — BlueCrystal_REQ_MessagePipeline
│   │   ├── BlueCrystal_REQ_Project.md          — BlueCrystal_REQ_Project
│   │   ├── BlueCrystal_REQ_README.md           — BlueCrystal Requirements
│   │   ├── BlueCrystal_REQ_ServingAggregation.md — BlueCrystal_REQ_ServingAggregation
│   │   ├── BlueCrystal_REQ_SharedSource.md     — BlueCrystal_REQ_SharedSource
│   │   ├── BlueCrystal_REQ_SourceLab.md        — BlueCrystal_REQ_SourceLab
│   │   ├── BlueCrystal_REQ_SpeedLayer.md       — BlueCrystal_REQ_SpeedLayer
│   │   ├── BlueCrystal_REQ_Storage.md          — BlueCrystal_REQ_Storage
│   │   ├── Octopus_REQ.md                      — Octopus_REQ
│   │   ├── PlatformShared_REQ_Crosscutting.md  — PlatformShared_REQ_Crosscutting
│   │   ├── Seahorse_REQ.md                     — Seahorse Requirements
│   │   ├── Starfish_REQ.md                     — Starfish Requirements
│   │   ├── Turtle_REQ.md                       — Turtle_REQ
│   │   ├── project_tree.md                     — BlueCrystal Project Tree
│   │   ├── test_index.md                       — BlueCrystal 测试索引
│   │   ├── 业务目标与价值愿景.md                        — 项目白皮书：业务目标与价值愿景
│   │   ├── 总体逻辑设计.md                           — 项目白皮书-总体逻辑设计
│   ├── reports/ — 任务报告归档
│   │   ├── starfish_architecture_doc_finalize.md — Starfish Clean Architecture v3.3 文档封板收尾
│   │   ├── starfish_clean_boundary_refactor.md — Starfish Clean Boundary Refactor
│   │   ├── starfish_strict_di_refactor.md      — Starfish Strict DI 收敛重构报告
│   ├── rules/ — 共享执行规则
│   │   ├── coding.md                           — 通用编码、接口、类型与注释规则
│   │   ├── documentation.md                    — 文档、目录树与规则维护
│   │   ├── python-docstring-cn.md              — Python 中文注释与 Google-style Docstring 规则
│   │   ├── quality-gate.md                     — 质量门禁规则
│   │   ├── reporting.md                        — Agent 反馈与报告归档规则
│   │   ├── routing.md                          — 规则读取路由
│   │   ├── testing.md                          — 测试规则
│   │   ├── validation-routing.md               — 验证路由规则
│   ├── templates/ — 提示模板
│   │   ├── coding_agent_prompt_template.txt    — 文本模板
├── alembic/ — 数据库迁移配置与版本
│   ├── versions/ — Alembic migration 版本
│   │   ├── 20260527_000001_ingest_runtime_initial.py — ingest runtime initial revision
│   │   ├── 20260527_000002_add_audit_index_and_job_stagger.py — Add audit_event action/timestamp index and scheduler job stagger colum
│   │   ├── 20260527_000003_add_idempotency_record.py — Add ingest_idempotency_record table
│   │   ├── 20260527_000004_add_model_asset_tables.py — Add model_asset, simulation_case, simulation_result, simulation_artifa
│   ├── env.py                              — Alembic 运行环境
│   ├── script.py.mako                      — Alembic 模板
├── config/ — 运行配置样例
│   ├── ingest/
│   │   ├── access_policy.external.example.yaml — YAML 配置
│   │   ├── access_policy.prodlike.yaml         — YAML 配置
│   │   ├── audit_sink.external.example.yaml    — YAML 配置
│   │   ├── endurance.prodlike.yaml             — YAML 配置
│   │   ├── performance.prodlike.yaml           — YAML 配置
│   │   ├── security_partition.example.yaml     — YAML 配置
│   ├── whale/ — Whale 模块资产
│   │   ├── message_pipeline.kafka.example.yaml — YAML 配置
│   │   ├── message_pipeline.pulsar.example.yaml — YAML 配置
│   │   ├── speed_layer.writers.example.yaml    — YAML 配置
│   │   ├── storage.raw_archive.example.yaml    — YAML 配置
│   │   ├── storage.serving_cache.example.yaml  — YAML 配置
│   │   ├── storage.tdengine.example.yaml       — YAML 配置
├── deploy/ — 部署资产与 runbook
│   ├── octopus/ — Octopus 模块资产
│   │   ├── README.md                           — Octopus 运维编排基础能力部署
│   ├── turtle/ — Turtle 模块资产
│   │   ├── README.md                           — Turtle 治理基础能力部署
│   ├── whale/ — Whale 模块资产
│   │   ├── ingest/
│   │   │   ├── .env.ingest.example                 — 项目文件
│   │   │   ├── Dockerfile                          — 容器镜像构建文件
│   │   │   ├── README.md                           — Whale Ingest 现场部署说明
│   │   │   ├── docker-compose.ingest-dev.yaml      — YAML 配置
│   │   │   ├── docker-compose.ingest-prodlike.yaml — YAML 配置
│   │   ├── message_pipeline/
│   │   │   ├── README.md                           — Whale Message Pipeline 现场部署说明
│   │   │   ├── docker-compose.whale-l5.yaml        — YAML 配置
│   │   ├── speed_layer/
│   │   │   ├── .env.p5.example                     — 项目文件
│   │   │   ├── README.md                           — Whale Speed Layer 现场部署说明
│   │   │   ├── docker-compose.p5.yml               — YAML 配置
│   │   ├── storage/
│   │   │   ├── README.md                           — Whale Storage 现场部署说明
│   │   ├── .env.whale.field.example            — 项目文件
│   │   ├── README.md                           — Whale 现场部署
├── docs/ — 项目长期文档
│   ├── 4+1视图.md                            — 4+1 视图关注点与常用 UML 图形
│   ├── GIT.md                              — Git Commit 信息前缀规范
│   ├── clean_architecture.md               — Clean Architecture Blueprint & Standard Specification
│   ├── opcua_iec61850_guide.md             — OPC UA × IEC 61850 通信与建模指南（扩展版）
│   ├── 代码质量与注释.md                          — Python 工程工具与代码文档规范说明
│   ├── 工程管理.md                             — 工程管理方法论：低成本自动化驱动的演化型增量迭代开发模型
│   ├── 测试策略.md                             — Python 项目测试规范与目录组织建议（Codex 使用版）
├── scripts/ — 质量门禁与运维脚本
│   ├── check_ads_env.py                    — Beckhoff ADS 环境预检脚本。
│   ├── check_l2_goose_sv_env.py            — Python 模块
│   ├── check_l5_field_readback_env.py      — L5 Field Readback 环境预检脚本。
│   ├── check_serial_env.py                 — 串口 (Serial) 环境预检脚本。
│   ├── ci_ingest_runtime_gate.sh           — Shell 脚本
│   ├── cleanup_root_logs.sh                — Shell 脚本
│   ├── diagnose_whale_p5_dependencies.sh   — Shell 脚本
│   ├── run_ingest_bundle_one_way_flow_smoke.sh — Shell 脚本
│   ├── run_ingest_compose_readyz_e2e.sh    — Shell 脚本
│   ├── run_ingest_dev.sh                   — Shell 脚本
│   ├── run_ingest_pg_lease_fault_injection.sh — Shell 脚本
│   ├── run_ingest_prodlike_dependency_smoke.sh — Shell 脚本
│   ├── run_ingest_prodlike_endurance_smoke.sh — Shell 脚本
│   ├── run_ingest_prodlike_performance_profile.sh — Shell 脚本
│   ├── run_ingest_runtime_compose_smoke.sh — Shell 脚本
│   ├── run_ingest_write_readback_smoke.sh  — Shell 脚本
│   ├── run_pg_migration_matrix.sh          — Shell 脚本
│   ├── run_quality_gate.py                 — CI/本地质量门禁聚合脚本。
│   ├── run_whale_field_minimal_smoke.sh    — Shell 脚本
│   ├── run_whale_field_quality_gate.sh     — Shell 脚本
│   ├── run_whale_field_ready_smoke.sh      — Shell 脚本
│   ├── run_whale_l5_external_dependency_probe.sh — Shell 脚本
│   ├── run_whale_p5_external_dependency_regression.sh — Shell 脚本
│   ├── run_whale_writer_switchover.sh      — Shell 脚本
│   ├── start_whale_p5_dependencies.sh      — Shell 脚本
│   ├── stop_whale_p5_dependencies.sh       — Shell 脚本
│   ├── test_ingest_write_readback_smoke_contract.sh — Shell 脚本
│   ├── validate_shared_source_production_runner.sh — Shell 脚本
│   ├── whale_test.sh                       — Shell 脚本
├── src/ — 产品源码
│   ├── manta/ — Manta 前端资产
│   │   ├── .husky/
│   │   │   ├── commit-msg                          — 项目文件
│   │   │   ├── pre-commit                          — 项目文件
│   │   ├── config/ — 运行配置样例
│   │   │   ├── plugin/
│   │   │   │   ├── arcoResolver.ts                     — TypeScript 模块
│   │   │   │   ├── arcoStyleImport.ts                  — TypeScript 模块
│   │   │   │   ├── compress.ts                         — TypeScript 模块
│   │   │   │   ├── imagemin.ts                         — TypeScript 模块
│   │   │   │   ├── visualizer.ts                       — TypeScript 模块
│   │   │   ├── utils/
│   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   ├── vite.config.base.ts                 — TypeScript 模块
│   │   │   ├── vite.config.dev.ts                  — TypeScript 模块
│   │   │   ├── vite.config.prod.ts                 — TypeScript 模块
│   │   ├── docs/ — 项目长期文档
│   │   │   ├── openapi/ — OpenAPI 文档
│   │   │   │   ├── paths/
│   │   │   │   │   ├── data-acquisition.yaml               — YAML 配置
│   │   │   │   │   ├── lidar.yaml                          — YAML 配置
│   │   │   │   │   ├── load-mitigation.yaml                — YAML 配置
│   │   │   │   │   ├── message.yaml                        — YAML 配置
│   │   │   │   │   ├── power-analysis.yaml                 — YAML 配置
│   │   │   │   │   ├── turbine.yaml                        — YAML 配置
│   │   │   │   │   ├── user-center.yaml                    — YAML 配置
│   │   │   │   │   ├── user.yaml                           — YAML 配置
│   │   │   │   │   ├── windfarm.yaml                       — YAML 配置
│   │   │   │   ├── schemas/ — schema 定义
│   │   │   │   │   ├── common.yaml                         — YAML 配置
│   │   │   │   │   ├── data-acquisition.yaml               — YAML 配置
│   │   │   │   │   ├── lidar.yaml                          — YAML 配置
│   │   │   │   │   ├── load-mitigation.yaml                — YAML 配置
│   │   │   │   │   ├── message.yaml                        — YAML 配置
│   │   │   │   │   ├── power-analysis.yaml                 — YAML 配置
│   │   │   │   │   ├── turbine.yaml                        — YAML 配置
│   │   │   │   │   ├── user-center.yaml                    — YAML 配置
│   │   │   │   │   ├── user.yaml                           — YAML 配置
│   │   │   │   │   ├── windfarm.yaml                       — YAML 配置
│   │   │   │   ├── showtime.openapi.yaml               — YAML 配置
│   │   ├── public/
│   │   │   ├── models/
│   │   │   │   ├── WT_10MW.glb                         — 项目文件
│   │   │   ├── terrain/
│   │   │   │   ├── 0/
│   │   │   │   │   ├── 0/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   ├── 1/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   ├── 1/
│   │   │   │   │   ├── 0/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   ├── 1/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   ├── 2/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   ├── 3/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   ├── 10/
│   │   │   │   │   ├── 1662/
│   │   │   │   │   │   ├── 727.terrain                         — 项目文件
│   │   │   │   │   │   ├── 728.terrain                         — 项目文件
│   │   │   │   │   ├── 1663/
│   │   │   │   │   │   ├── 727.terrain                         — 项目文件
│   │   │   │   │   │   ├── 728.terrain                         — 项目文件
│   │   │   │   ├── 11/
│   │   │   │   │   ├── 3325/
│   │   │   │   │   │   ├── 1454.terrain                        — 项目文件
│   │   │   │   │   │   ├── 1455.terrain                        — 项目文件
│   │   │   │   │   │   ├── 1456.terrain                        — 项目文件
│   │   │   │   │   ├── 3326/
│   │   │   │   │   │   ├── 1454.terrain                        — 项目文件
│   │   │   │   │   │   ├── 1455.terrain                        — 项目文件
│   │   │   │   │   │   ├── 1456.terrain                        — 项目文件
│   │   │   │   │   ├── 3327/
│   │   │   │   │   │   ├── 1454.terrain                        — 项目文件
│   │   │   │   │   │   ├── 1455.terrain                        — 项目文件
│   │   │   │   │   │   ├── 1456.terrain                        — 项目文件
│   │   │   │   ├── 12/
│   │   │   │   │   ├── 6650/
│   │   │   │   │   │   ├── 2908.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2909.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2910.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2911.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2912.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2913.terrain                        — 项目文件
│   │   │   │   │   ├── 6651/
│   │   │   │   │   │   ├── 2908.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2909.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2910.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2911.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2912.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2913.terrain                        — 项目文件
│   │   │   │   │   ├── 6652/
│   │   │   │   │   │   ├── 2908.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2909.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2910.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2911.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2912.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2913.terrain                        — 项目文件
│   │   │   │   │   ├── 6653/
│   │   │   │   │   │   ├── 2908.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2909.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2910.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2911.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2912.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2913.terrain                        — 项目文件
│   │   │   │   │   ├── 6654/
│   │   │   │   │   │   ├── 2908.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2909.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2910.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2911.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2912.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2913.terrain                        — 项目文件
│   │   │   │   │   ├── 6655/
│   │   │   │   │   │   ├── 2908.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2909.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2910.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2911.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2912.terrain                        — 项目文件
│   │   │   │   │   │   ├── 2913.terrain                        — 项目文件
│   │   │   │   ├── 13/
│   │   │   │   │   ├── 13301/
│   │   │   │   │   │   ├── 5817.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5818.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5819.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5820.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5821.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5822.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5823.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5824.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5825.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5826.terrain                        — 项目文件
│   │   │   │   │   ├── 13302/
│   │   │   │   │   │   ├── 5817.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5818.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5819.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5820.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5821.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5822.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5823.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5824.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5825.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5826.terrain                        — 项目文件
│   │   │   │   │   ├── 13303/
│   │   │   │   │   │   ├── 5817.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5818.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5819.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5820.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5821.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5822.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5823.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5824.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5825.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5826.terrain                        — 项目文件
│   │   │   │   │   ├── 13304/
│   │   │   │   │   │   ├── 5817.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5818.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5819.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5820.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5821.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5822.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5823.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5824.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5825.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5826.terrain                        — 项目文件
│   │   │   │   │   ├── 13305/
│   │   │   │   │   │   ├── 5817.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5818.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5819.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5820.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5821.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5822.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5823.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5824.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5825.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5826.terrain                        — 项目文件
│   │   │   │   │   ├── 13306/
│   │   │   │   │   │   ├── 5817.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5818.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5819.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5820.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5821.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5822.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5823.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5824.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5825.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5826.terrain                        — 项目文件
│   │   │   │   │   ├── 13307/
│   │   │   │   │   │   ├── 5817.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5818.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5819.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5820.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5821.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5822.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5823.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5824.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5825.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5826.terrain                        — 项目文件
│   │   │   │   │   ├── 13308/
│   │   │   │   │   │   ├── 5817.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5818.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5819.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5820.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5821.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5822.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5823.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5824.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5825.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5826.terrain                        — 项目文件
│   │   │   │   │   ├── 13309/
│   │   │   │   │   │   ├── 5817.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5818.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5819.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5820.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5821.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5822.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5823.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5824.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5825.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5826.terrain                        — 项目文件
│   │   │   │   │   ├── 13310/
│   │   │   │   │   │   ├── 5817.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5818.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5819.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5820.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5821.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5822.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5823.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5824.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5825.terrain                        — 项目文件
│   │   │   │   │   │   ├── 5826.terrain                        — 项目文件
│   │   │   │   ├── 2/
│   │   │   │   │   ├── 0/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   ├── 1/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   ├── 2/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   ├── 3/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   ├── 4/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   ├── 5/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   ├── 6/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   ├── 7/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   ├── 3/
│   │   │   │   │   ├── 0/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 1/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 10/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 11/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 12/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 13/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 14/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 15/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 2/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 3/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 4/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 5/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 6/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 7/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 8/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   ├── 9/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   ├── 4/
│   │   │   │   │   ├── 0/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 1/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 10/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 11/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 12/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 13/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 14/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 15/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 16/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 17/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 18/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 19/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 2/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 20/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 21/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 22/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 23/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 24/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 25/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 26/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 27/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 28/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 29/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 3/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 30/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 31/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 4/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 5/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 6/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 7/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 8/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   │   ├── 9/
│   │   │   │   │   │   ├── 0.terrain                           — 项目文件
│   │   │   │   │   │   ├── 1.terrain                           — 项目文件
│   │   │   │   │   │   ├── 10.terrain                          — 项目文件
│   │   │   │   │   │   ├── 11.terrain                          — 项目文件
│   │   │   │   │   │   ├── 12.terrain                          — 项目文件
│   │   │   │   │   │   ├── 13.terrain                          — 项目文件
│   │   │   │   │   │   ├── 14.terrain                          — 项目文件
│   │   │   │   │   │   ├── 15.terrain                          — 项目文件
│   │   │   │   │   │   ├── 2.terrain                           — 项目文件
│   │   │   │   │   │   ├── 3.terrain                           — 项目文件
│   │   │   │   │   │   ├── 4.terrain                           — 项目文件
│   │   │   │   │   │   ├── 5.terrain                           — 项目文件
│   │   │   │   │   │   ├── 6.terrain                           — 项目文件
│   │   │   │   │   │   ├── 7.terrain                           — 项目文件
│   │   │   │   │   │   ├── 8.terrain                           — 项目文件
│   │   │   │   │   │   ├── 9.terrain                           — 项目文件
│   │   │   │   ├── 5/
│   │   │   │   │   ├── 51/
│   │   │   │   │   │   ├── 22.terrain                          — 项目文件
│   │   │   │   ├── 6/
│   │   │   │   │   ├── 103/
│   │   │   │   │   │   ├── 45.terrain                          — 项目文件
│   │   │   │   ├── 7/
│   │   │   │   │   ├── 207/
│   │   │   │   │   │   ├── 90.terrain                          — 项目文件
│   │   │   │   │   │   ├── 91.terrain                          — 项目文件
│   │   │   │   ├── 8/
│   │   │   │   │   ├── 415/
│   │   │   │   │   │   ├── 181.terrain                         — 项目文件
│   │   │   │   │   │   ├── 182.terrain                         — 项目文件
│   │   │   │   ├── 9/
│   │   │   │   │   ├── 831/
│   │   │   │   │   │   ├── 363.terrain                         — 项目文件
│   │   │   │   │   │   ├── 364.terrain                         — 项目文件
│   │   │   │   ├── layer.json                          — JSON 配置
│   │   ├── src/ — 产品源码
│   │   │   ├── api/
│   │   │   │   ├── generated/
│   │   │   │   │   ├── openapi/ — OpenAPI 文档
│   │   │   │   │   │   ├── client/
│   │   │   │   │   │   │   ├── client.gen.ts                       — TypeScript 模块
│   │   │   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   │   │   ├── types.gen.ts                        — TypeScript 模块
│   │   │   │   │   │   │   ├── utils.gen.ts                        — TypeScript 模块
│   │   │   │   │   │   ├── core/
│   │   │   │   │   │   │   ├── auth.gen.ts                         — TypeScript 模块
│   │   │   │   │   │   │   ├── bodySerializer.gen.ts               — TypeScript 模块
│   │   │   │   │   │   │   ├── params.gen.ts                       — TypeScript 模块
│   │   │   │   │   │   │   ├── pathSerializer.gen.ts               — TypeScript 模块
│   │   │   │   │   │   │   ├── queryKeySerializer.gen.ts           — TypeScript 模块
│   │   │   │   │   │   │   ├── serverSentEvents.gen.ts             — TypeScript 模块
│   │   │   │   │   │   │   ├── types.gen.ts                        — TypeScript 模块
│   │   │   │   │   │   │   ├── utils.gen.ts                        — TypeScript 模块
│   │   │   │   │   │   ├── client.gen.ts                       — TypeScript 模块
│   │   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── sdk.gen.ts                          — TypeScript 模块
│   │   │   │   │   │   ├── types.gen.ts                        — TypeScript 模块
│   │   │   │   ├── local-data/
│   │   │   │   │   ├── data-acquisition.ts                 — TypeScript 模块
│   │   │   │   │   ├── lidar.ts                            — TypeScript 模块
│   │   │   │   │   ├── load-mitigation.ts                  — TypeScript 模块
│   │   │   │   │   ├── power-analysis.ts                   — TypeScript 模块
│   │   │   │   ├── interceptor.ts                      — TypeScript 模块
│   │   │   │   ├── lidar-page.ts                       — TypeScript 模块
│   │   │   ├── assets/ — 静态资产
│   │   │   │   ├── images/
│   │   │   │   │   ├── default-avatar.svg                  — 项目文件
│   │   │   │   ├── style/
│   │   │   │   │   ├── breakpoint.less                     — 项目文件
│   │   │   │   │   ├── global.less                         — 项目文件
│   │   │   │   ├── logo.svg                            — 项目文件
│   │   │   ├── bootstrap/
│   │   │   │   ├── cesium.ts                           — TypeScript 模块
│   │   │   ├── components/
│   │   │   │   ├── breadcrumb/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── chart/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── footer/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── global-setting/
│   │   │   │   │   ├── block.vue                           — Vue 组件
│   │   │   │   │   ├── form-wrapper.vue                    — Vue 组件
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── menu/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   │   ├── use-menu-tree.ts                    — TypeScript 模块
│   │   │   │   ├── navbar/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── overview-metric-card/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── overview-turbine-info-card/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── overview-turbine-select-card/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── tab-bar/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   │   ├── readme.md                           — 组件说明
│   │   │   │   │   ├── tab-item.vue                        — Vue 组件
│   │   │   │   ├── top-metric-card/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   ├── config/ — 运行配置样例
│   │   │   │   ├── chart-theme.ts                      — TypeScript 模块
│   │   │   │   ├── settings.json                       — JSON 配置
│   │   │   ├── directive/
│   │   │   │   ├── permission/
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   ├── hooks/ — 安全与质量 hook
│   │   │   │   ├── chart-option.ts                     — TypeScript 模块
│   │   │   │   ├── loading.ts                          — TypeScript 模块
│   │   │   │   ├── locale.ts                           — TypeScript 模块
│   │   │   │   ├── permission.ts                       — TypeScript 模块
│   │   │   │   ├── request.ts                          — TypeScript 模块
│   │   │   │   ├── responsive.ts                       — TypeScript 模块
│   │   │   │   ├── themes.ts                           — TypeScript 模块
│   │   │   │   ├── user.ts                             — TypeScript 模块
│   │   │   │   ├── visible.ts                          — TypeScript 模块
│   │   │   ├── layout/
│   │   │   │   ├── default-layout.vue                  — Vue 组件
│   │   │   │   ├── page-layout.vue                     — Vue 组件
│   │   │   ├── locale/
│   │   │   │   ├── en-US/
│   │   │   │   │   ├── settings.ts                         — TypeScript 模块
│   │   │   │   ├── zh-CN/
│   │   │   │   │   ├── settings.ts                         — TypeScript 模块
│   │   │   │   ├── en-US.ts                            — TypeScript 模块
│   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   ├── zh-CN.ts                            — TypeScript 模块
│   │   │   ├── mock/
│   │   │   │   ├── data-acquisition/
│   │   │   │   │   ├── fixtures.ts                         — TypeScript 模块
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   ├── rules.ts                            — TypeScript 模块
│   │   │   │   ├── lidar/
│   │   │   │   │   ├── fixtures.ts                         — TypeScript 模块
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   ├── rules.ts                            — TypeScript 模块
│   │   │   │   ├── load-mitigation/
│   │   │   │   │   ├── amplitude-structure.ts              — TypeScript 模块
│   │   │   │   │   ├── fixtures.ts                         — TypeScript 模块
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   ├── markov-matrix.ts                    — TypeScript 模块
│   │   │   │   │   ├── optimization-evidence.ts            — TypeScript 模块
│   │   │   │   │   ├── rules.ts                            — TypeScript 模块
│   │   │   │   ├── message/
│   │   │   │   │   ├── data.ts                             — TypeScript 模块
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   ├── power-analysis/
│   │   │   │   │   ├── fixtures.ts                         — TypeScript 模块
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   ├── rules.ts                            — TypeScript 模块
│   │   │   │   ├── user/
│   │   │   │   │   ├── data.ts                             — TypeScript 模块
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   ├── user-center/
│   │   │   │   │   ├── data.ts                             — TypeScript 模块
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   ├── windfarm/
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   ├── turbine-data.ts                     — TypeScript 模块
│   │   │   │   │   ├── windfarm-data.ts                    — TypeScript 模块
│   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   ├── router/
│   │   │   │   ├── app-menus/
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   ├── guard/
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   ├── permission.ts                       — TypeScript 模块
│   │   │   │   │   ├── userLoginInfo.ts                    — TypeScript 模块
│   │   │   │   ├── routes/
│   │   │   │   │   ├── modules/
│   │   │   │   │   │   ├── dashboard.ts                        — TypeScript 模块
│   │   │   │   │   │   ├── data-acquisition.ts                 — TypeScript 模块
│   │   │   │   │   │   ├── lidar-wind-field.ts                 — TypeScript 模块
│   │   │   │   │   │   ├── load-mitigation.ts                  — TypeScript 模块
│   │   │   │   │   │   ├── power-optimization.ts               — TypeScript 模块
│   │   │   │   │   │   ├── user.ts                             — TypeScript 模块
│   │   │   │   │   ├── base.ts                             — TypeScript 模块
│   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   ├── types.ts                            — TypeScript 模块
│   │   │   │   ├── constants.ts                        — TypeScript 模块
│   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   ├── typings.d.ts                        — TypeScript 模块
│   │   │   ├── store/
│   │   │   │   ├── modules/
│   │   │   │   │   ├── app/
│   │   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── types.ts                            — TypeScript 模块
│   │   │   │   │   ├── tab-bar/
│   │   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── types.ts                            — TypeScript 模块
│   │   │   │   │   ├── user/
│   │   │   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── types.ts                            — TypeScript 模块
│   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   ├── types/
│   │   │   │   ├── global.ts                           — TypeScript 模块
│   │   │   │   ├── lidar.ts                            — TypeScript 模块
│   │   │   │   ├── mock.ts                             — TypeScript 模块
│   │   │   │   ├── power-analysis.ts                   — TypeScript 模块
│   │   │   ├── utils/
│   │   │   │   ├── auth.ts                             — TypeScript 模块
│   │   │   │   ├── env.ts                              — TypeScript 模块
│   │   │   │   ├── event.ts                            — TypeScript 模块
│   │   │   │   ├── index.ts                            — TypeScript 模块
│   │   │   │   ├── is.ts                               — TypeScript 模块
│   │   │   │   ├── route-listener.ts                   — TypeScript 模块
│   │   │   │   ├── setup-mock.ts                       — TypeScript 模块
│   │   │   ├── views/
│   │   │   │   ├── dashboard/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── GeoSceneViewer.locale.ts            — TypeScript 模块
│   │   │   │   │   │   ├── GeoSceneViewer.vue                  — Vue 组件
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── data-acquisition/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── ChannelResourceCard.vue             — Vue 组件
│   │   │   │   │   │   ├── ComputeResourceCard.vue             — Vue 组件
│   │   │   │   │   │   ├── DataQualityAnalysisCard.vue         — Vue 组件
│   │   │   │   │   │   ├── DeviceCommStatusCard.vue            — Vue 组件
│   │   │   │   │   │   ├── StorageResourceCard.vue             — Vue 组件
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── exception/
│   │   │   │   │   ├── 403/
│   │   │   │   │   │   ├── locale/
│   │   │   │   │   │   │   ├── en-US.ts                            — TypeScript 模块
│   │   │   │   │   │   │   ├── zh-CN.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   │   ├── 404/
│   │   │   │   │   │   ├── locale/
│   │   │   │   │   │   │   ├── en-US.ts                            — TypeScript 模块
│   │   │   │   │   │   │   ├── zh-CN.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   │   ├── 500/
│   │   │   │   │   │   ├── locale/
│   │   │   │   │   │   │   ├── en-US.ts                            — TypeScript 模块
│   │   │   │   │   │   │   ├── zh-CN.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── lidar-wind-filed/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── ConsistencyAlignmentChart.vue       — Vue 组件
│   │   │   │   │   │   ├── DataQualityPanel.vue                — Vue 组件
│   │   │   │   │   │   ├── DeviceInfoCard.vue                  — Vue 组件
│   │   │   │   │   │   ├── LidarInflowProfilePanel.vue         — Vue 组件
│   │   │   │   │   │   ├── LidarVolumeView.vue                 — Vue 组件
│   │   │   │   │   │   ├── TopRealtimeWindWave.vue             — Vue 组件
│   │   │   │   │   │   ├── TransferFunctionChart.vue           — Vue 组件
│   │   │   │   │   │   ├── WindRoseTiStats.vue                 — Vue 组件
│   │   │   │   │   ├── echarts-gl.d.ts                     — TypeScript 模块
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── load-mitigation/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── AmplitudeStructureComparison.vue    — Vue 组件
│   │   │   │   │   │   ├── EnergySpectrumComparison.vue        — Vue 组件
│   │   │   │   │   │   ├── HighAmplitudeRiskComparison.vue     — Vue 组件
│   │   │   │   │   │   ├── ImprovementStabilityStats.vue       — Vue 组件
│   │   │   │   │   │   ├── LoadCycleMigrationHeatmap.vue       — Vue 组件
│   │   │   │   │   │   ├── PeakQuantileEvidence.vue            — Vue 组件
│   │   │   │   │   │   ├── RmsImprovementOverview.vue          — Vue 组件
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── login/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── banner.vue                          — Vue 组件
│   │   │   │   │   │   ├── login-form.vue                      — Vue 组件
│   │   │   │   │   ├── locale/
│   │   │   │   │   │   ├── en-US.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── zh-CN.ts                            — TypeScript 模块
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── not-found/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── power-analysis/
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── BootstrapStabilityChart.vue         — Vue 组件
│   │   │   │   │   │   ├── DistributionShiftChart.vue          — Vue 组件
│   │   │   │   │   │   ├── GustResponse.vue                    — Vue 组件
│   │   │   │   │   │   ├── PowerCurveComparisonChart.vue       — Vue 组件
│   │   │   │   │   │   ├── StatSummaryCard.vue                 — Vue 组件
│   │   │   │   │   │   ├── TailCcdfChart.vue                   — Vue 组件
│   │   │   │   │   │   ├── VolatilitySummary.vue               — Vue 组件
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── redirect/
│   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── result/
│   │   │   │   │   ├── error/
│   │   │   │   │   │   ├── locale/
│   │   │   │   │   │   │   ├── en-US.ts                            — TypeScript 模块
│   │   │   │   │   │   │   ├── zh-CN.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   │   ├── success/
│   │   │   │   │   │   ├── locale/
│   │   │   │   │   │   │   ├── en-US.ts                            — TypeScript 模块
│   │   │   │   │   │   │   ├── zh-CN.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   ├── user/
│   │   │   │   │   ├── info/
│   │   │   │   │   │   ├── components/
│   │   │   │   │   │   │   ├── latest-activity.vue                 — Vue 组件
│   │   │   │   │   │   │   ├── latest-notification.vue             — Vue 组件
│   │   │   │   │   │   │   ├── my-project.vue                      — Vue 组件
│   │   │   │   │   │   │   ├── my-team.vue                         — Vue 组件
│   │   │   │   │   │   │   ├── user-info-header.vue                — Vue 组件
│   │   │   │   │   │   ├── locale/
│   │   │   │   │   │   │   ├── en-US.ts                            — TypeScript 模块
│   │   │   │   │   │   │   ├── zh-CN.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   │   │   ├── setting/
│   │   │   │   │   │   ├── components/
│   │   │   │   │   │   │   ├── basic-information.vue               — Vue 组件
│   │   │   │   │   │   │   ├── certification-records.vue           — Vue 组件
│   │   │   │   │   │   │   ├── certification.vue                   — Vue 组件
│   │   │   │   │   │   │   ├── enterprise-certification.vue        — Vue 组件
│   │   │   │   │   │   │   ├── security-settings.vue               — Vue 组件
│   │   │   │   │   │   │   ├── user-panel.vue                      — Vue 组件
│   │   │   │   │   │   ├── locale/
│   │   │   │   │   │   │   ├── en-US.ts                            — TypeScript 模块
│   │   │   │   │   │   │   ├── zh-CN.ts                            — TypeScript 模块
│   │   │   │   │   │   ├── index.vue                           — Vue 组件
│   │   │   ├── App.vue                             — Vue 组件
│   │   │   ├── env.d.ts                            — TypeScript 模块
│   │   │   ├── main.ts                             — TypeScript 模块
│   │   ├── .env.development                    — 项目文件
│   │   ├── .env.production                     — 项目文件
│   │   ├── .prettierignore                     — 项目文件
│   │   ├── babel.config.js                     — JavaScript 模块
│   │   ├── commitlint.config.js                — JavaScript 模块
│   │   ├── components.d.ts                     — TypeScript 模块
│   │   ├── echarts-gl-debug.html               — HTML 页面
│   │   ├── eslint.config.cjs                   — 项目文件
│   │   ├── index.html                          — HTML 页面
│   │   ├── package.json                        — JSON 配置
│   │   ├── prettier.config.cjs                 — 项目文件
│   │   ├── stylelint.config.cjs                — 项目文件
│   │   ├── tsconfig.json                       — JSON 配置
│   ├── octopus/ — Octopus 模块资产
│   │   ├── adapters/ — 接口适配器实现
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── alerting/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── automation/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── deployment/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── diagnostics/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── monitoring/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── orchestration/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── reports/ — 任务报告归档
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── rollback/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── runtime/ — 运行时内核与生命周期
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── __init__.py                         — 包导出入口
│   ├── platform_shared/ — 跨模块共享代码
│   │   ├── contracts/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── crosscutting/
│   │   │   ├── context/
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── debug/
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── diagnostics.py                      — Debug snapshot models for external runner diagnostics.
│   │   │   │   ├── ring_buffer.py                      — Small recent-failure buffer used by debug tooling.
│   │   │   │   ├── trace.py                            — Debug trace context and sink abstractions.
│   │   │   ├── observability/
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── audit.py                            — Helpers that bridge audit concepts into observability pipelines.
│   │   │   │   ├── logging.py                          — Structured logging data models.
│   │   │   │   ├── metrics.py                          — Metrics sink protocol shared by adapters and wrappers.
│   │   │   ├── resilience/
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── backoff.py                          — Backoff policy helpers.
│   │   │   │   ├── circuit_breaker.py                  — Minimal circuit-breaker model primitives.
│   │   │   │   ├── deadline.py                         — Deadline models for bounded operations.
│   │   │   │   ├── error_classifier.py                 — Stable error classification models.
│   │   │   │   ├── retry.py                            — Retry-policy models shared by wrappers and adapters.
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── kernel/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── messaging/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── security_primitives/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── masking.py                          — Helpers for masking sensitive values before they reach logs or traces.
│   │   ├── __init__.py                         — 包导出入口
│   ├── seahorse/ — Seahorse 模块资产
│   │   ├── exporters/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── bundle_exporter.py                  — seahorse JSON 包导出器。
│   │   │   ├── bundle_validator.py                 — Python 模块
│   │   │   ├── serialization.py                    — seahorse 序列化辅助 —— 校验和计算与规范化 JSON 导出。
│   │   │   ├── server_config_exporter.py           — seahorse ServerConfig handoff 导出入口。
│   │   │   ├── server_config_validator.py          — seahorse ServerConfig 契约校验入口。
│   │   │   ├── server_plan_exporter.py             — seahorse ServerConfig handoff 导出器。
│   │   │   ├── server_plan_validator.py            — seahorse ServerConfig 契约校验器。
│   │   │   ├── timeseries_exporter.py              — seahorse JSONL 时序导出器。
│   │   ├── generators/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── alarm_generator.py                  — seahorse 告警事件生成器。
│   │   │   ├── control_result_generator.py         — seahorse 控制回写响应生成器。
│   │   ├── models/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── bundle.py                           — seahorse 核心模型 —— 场景包（ScenarioBundle）。
│   │   │   ├── generation.py                       — seahorse 核心模型 —— 生成结果值。
│   │   │   ├── plan.py                             — seahorse 核心模型 —— 种子计划与端点规划。
│   │   │   ├── scenario.py                         — seahorse 核心模型 —— 场景配置、元数据与种子计划。
│   │   ├── orchestration/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── scenario_generator.py               — Python 模块
│   │   ├── ports/ — 抽象端口接口
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── generation_strategy.py              — seahorse 生成策略端口 —— GenerationStrategy Protocol。
│   │   ├── reference_data/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── gbt_30966_fields.py                 — Python 模块
│   │   │   ├── protocol_param_data.py              — Python 模块
│   │   │   ├── protocol_view_defs.py               — 协议端点参数展平视图定义 —— seahorse 参考数据。
│   │   │   ├── sample_data.py                      — Python 模块
│   │   ├── strategies/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── curve_generation.py                 — Python 模块
│   │   │   ├── random_generation.py                — seahorse 确定性随机值生成策略。
│   │   │   ├── registry.py                         — seahorse 生成策略注册表。
│   │   │   ├── replay_generation.py                — seahorse 回放生成策略。
│   │   ├── __init__.py                         — 包导出入口
│   │   ├── __main__.py                         — 模块 CLI 入口
│   ├── starfish/ — Starfish 模块资产
│   │   ├── adapters/ — 接口适配器实现
│   │   │   ├── config/ — 运行配置样例
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── drivers/ — driver adapter 或 backend 实现
│   │   │   │   ├── ads/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── ads_driver_adapter.py               — Beckhoff ADS DriverPort adapter。
│   │   │   │   ├── factory/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── iec/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── goose_driver_adapter.py             — IEC 61850 GOOSE DriverPort adapter。
│   │   │   │   │   ├── iec101_driver_adapter.py            — IEC 101 DriverPort adapter。
│   │   │   │   │   ├── sv_driver_adapter.py                — IEC 61850 SV DriverPort adapter。
│   │   │   │   ├── modbus/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── modbus_rtu_driver_adapter.py        — Modbus RTU DriverPort adapter。
│   │   │   │   │   ├── modbus_tcp_driver_adapter.py        — Modbus TCP DriverPort adapter。
│   │   │   │   ├── native/ — native runner 与进程支撑
│   │   │   │   │   ├── iec/
│   │   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   │   ├── iec104_driver_adapter.py            — IEC 104 native DriverPort adapter。
│   │   │   │   │   │   ├── iec61850_mms_driver_adapter.py      — IEC 61850 MMS native DriverPort adapter。
│   │   │   │   │   │   ├── iec61850_report_driver_adapter.py   — IEC 61850 Report native DriverPort adapter。
│   │   │   │   │   ├── opcua/
│   │   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   │   ├── opcua_driver_adapter.py             — OPC UA native DriverPort adapter。
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── protocol/ — 协议 driver adapter
│   │   │   │   │   ├── http/
│   │   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   │   ├── http_rest_driver_adapter.py         — HTTP REST DriverPort adapter。
│   │   │   │   │   ├── mqtt/
│   │   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   │   ├── mqtt_driver_adapter.py              — MQTT-like DriverPort adapter。
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── simulator/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── server_simulator_driver_adapter.py  — In-memory simulator DriverPort adapter。
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── backend_ports.py                    — Driver adapter 使用的 backend 协议。
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── api/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── server_manager_api.py               — Starfish server manager API facade。
│   │   ├── application/ — 应用层用例、端口与 runtime
│   │   │   ├── ports/ — 抽象端口接口
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── config_loader.py                    — Server config 加载 port。
│   │   │   │   ├── driver_factory.py                   — Driver factory port。
│   │   │   │   ├── driver_port.py                      — 统一 DriverPort。
│   │   │   │   ├── registry.py                         — Runtime registry port。
│   │   │   ├── runtime/ — 运行时内核与生命周期
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── context.py                          — Starfish application runtime kernel root。
│   │   │   │   ├── event_bus.py                        — RuntimeEvent 与 RuntimeEventBus 应用层事件缓冲。
│   │   │   │   ├── graph.py                            — Runtime v2 application 运行图模型。
│   │   │   │   ├── snapshot.py                         — RuntimeSnapshot 应用运行态快照模型。
│   │   │   │   ├── state.py                            — RuntimeState 应用运行态状态模型。
│   │   │   ├── use_cases/ — 应用用例与 workflow
│   │   │   │   ├── workflows/ — 组合用例 workflow
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── bootstrap.py                        — Starfish runtime bootstrap workflow。
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── runtime_control.py                  — Starfish runtime 控制用例。
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── domain/ — 领域模型与纯规则
│   │   │   ├── protocols/ — 协议领域模型
│   │   │   │   ├── iec101/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── asdu.py                             — IEC 60870-5-101 ASDU 头部编解码。
│   │   │   │   │   ├── codec.py                            — Python 模块
│   │   │   │   │   ├── common_address.py                   — IEC 60870-5-101 公共地址（CA）编解码。
│   │   │   │   │   ├── frame.py                            — IEC 60870-5-101 FT1.2 链路帧编解码。
│   │   │   │   │   ├── information_elements.py             — IEC 60870-5-101 信息体元素（Information Element）编解码。
│   │   │   │   │   ├── information_object.py               — IEC 60870-5-101 信息对象（Information Object）编解码。
│   │   │   │   │   ├── ioa.py                              — IEC 60870-5-101 信息对象地址（IOA）编解码。
│   │   │   │   │   ├── link_layer.py                       — Python 模块
│   │   │   │   │   ├── quality.py                          — IEC 60870-5-101 信息体质量描述符（Quality Descriptor）编解码。
│   │   │   │   │   ├── time.py                             — IEC 60870-5-101 CP56Time2a 7 字节时标信息元素。
│   │   │   │   │   ├── types.py                            — IEC 60870-5-101 协议类型标识和传输原因枚举。
│   │   │   │   ├── modbus/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── register_encoding.py                — Modbus 寄存器值编解码工具。
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── driver.py                           — starfish driver entry 领域值对象。
│   │   │   ├── server_config.py                    — starfish 领域契约模型。
│   │   ├── infrastructure/ — 基础设施实现
│   │   │   ├── drivers/ — driver adapter 或 backend 实现
│   │   │   │   ├── ads/
│   │   │   │   │   ├── ads_backend.py                      — Starfish Beckhoff ADS 协议 backend —— codebase-pending stub。
│   │   │   │   ├── iec/
│   │   │   │   │   ├── goose_backend.py                    — Starfish IEC 61850 GOOSE 协议 backend —— environment-pending stub。
│   │   │   │   │   ├── iec101_backend.py                   — Python 模块
│   │   │   │   │   ├── sv_backend.py                       — Starfish IEC 61850 Sampled Values 协议 backend —— environment-pending st
│   │   │   │   ├── modbus/
│   │   │   │   │   ├── modbus_rtu_pty_backend.py           — Python 模块
│   │   │   │   │   ├── modbus_tcp_server_backend.py        — Python 模块
│   │   │   │   ├── native/ — native runner 与进程支撑
│   │   │   │   │   ├── iec/
│   │   │   │   │   │   ├── iec104_native_backend.py            — Python 模块
│   │   │   │   │   │   ├── iec61850_mms_native_backend.py      — Python 模块
│   │   │   │   │   │   ├── iec61850_report_native_backend.py   — Starfish IEC61850 Report 协议 backend —— report/event 语义 + ReportQueue。
│   │   │   │   │   ├── opcua/
│   │   │   │   │   │   ├── opcua_native_backend.py             — Python 模块
│   │   │   │   ├── protocol/ — 协议 driver adapter
│   │   │   │   │   ├── http/
│   │   │   │   │   │   ├── http_rest_server_backend.py         — Starfish HTTP REST 协议真实 server backend。
│   │   │   │   │   ├── mqtt/
│   │   │   │   │   │   ├── mqtt_server_backend.py              — Python 模块
│   │   │   │   ├── simulator/
│   │   │   │   │   ├── server_simulator_backend.py         — starfish ServerSimulatorBackend —— 最小 in-memory stub 实现。
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── backend_factory.py                  — Starfish driver backend 创建与探测入口。
│   │   │   ├── file_loaders/ — 文件加载器实现
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── server_config_json_loader.py        — starfish server config JSON 驱动加载器。
│   │   │   ├── native/ — native runner 与进程支撑
│   │   │   │   ├── bin/
│   │   │   │   │   ├── iec101_client_runner                — 项目文件
│   │   │   │   │   ├── iec101_event_runner                 — 项目文件
│   │   │   │   │   ├── iec101_simulator_slave              — 项目文件
│   │   │   │   │   ├── iec104_client_runner                — 项目文件
│   │   │   │   │   ├── iec104_event_runner                 — 项目文件
│   │   │   │   │   ├── iec104_simulator_server             — 项目文件
│   │   │   │   │   ├── iec61850_goose_publisher_simulator  — 项目文件
│   │   │   │   │   ├── iec61850_goose_subscriber_runner    — 项目文件
│   │   │   │   │   ├── iec61850_mms_client_runner          — 项目文件
│   │   │   │   │   ├── iec61850_report_runner              — 项目文件
│   │   │   │   │   ├── iec61850_simulator_server           — 项目文件
│   │   │   │   │   ├── iec61850_sv_publisher_simulator     — 项目文件
│   │   │   │   │   ├── iec61850_sv_subscriber_runner       — 项目文件
│   │   │   │   │   ├── modbus_rtu_polling_runner           — 项目文件
│   │   │   │   │   ├── modbus_simulator_server             — 项目文件
│   │   │   │   │   ├── modbus_tcp_polling_runner           — 项目文件
│   │   │   │   │   ├── open62541_client_runner             — 项目文件
│   │   │   │   │   ├── open62541_source_simulator          — 项目文件
│   │   │   │   │   ├── open62541_subscription_runner       — 项目文件
│   │   │   │   ├── lib60870/
│   │   │   │   │   ├── iec101_client_runner.c              — C 源码
│   │   │   │   │   ├── iec101_event_runner.c               — C 源码
│   │   │   │   │   ├── iec101_simulator_slave.c            — C 源码
│   │   │   │   │   ├── iec104_client_runner.c              — C 源码
│   │   │   │   │   ├── iec104_event_runner.c               — C 源码
│   │   │   │   │   ├── iec104_simulator_server.c           — C 源码
│   │   │   │   ├── libiec61850/
│   │   │   │   │   ├── iec61850_goose_publisher_simulator.c — C 源码
│   │   │   │   │   ├── iec61850_goose_subscriber_runner.c  — C 源码
│   │   │   │   │   ├── iec61850_mms_client_runner.c        — C 源码
│   │   │   │   │   ├── iec61850_report_runner.c            — C 源码
│   │   │   │   │   ├── iec61850_simulator_server.c         — C 源码
│   │   │   │   │   ├── iec61850_sv_publisher_simulator.c   — C 源码
│   │   │   │   │   ├── iec61850_sv_subscriber_runner.c     — C 源码
│   │   │   │   ├── libmodbus/
│   │   │   │   │   ├── modbus_rtu_polling_runner.c         — C 源码
│   │   │   │   │   ├── modbus_simulator_server.c           — C 源码
│   │   │   │   │   ├── modbus_tcp_polling_runner.c         — C 源码
│   │   │   │   ├── open62541/
│   │   │   │   │   ├── open62541_client_runner.c           — C 源码
│   │   │   │   │   ├── open62541_simulator_server.c        — C 源码
│   │   │   │   │   ├── open62541_subscription_runner.c     — C 源码
│   │   │   │   ├── CMakeLists.txt                      — CMake 构建配置
│   │   │   │   ├── README.md                           — 项目总览说明
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── process_handle.py                   — Native 子进程句柄 —— NativeProcessHandle。
│   │   │   │   ├── runner_probe.py                     — Native runner 探查函数 —— probe_native_runner。
│   │   │   │   ├── runner_spec.py                      — Native runner 规格定义 —— NativeRunnerSpec dataclass。
│   │   │   │   ├── runtime.py                          — starfish native runner 启动辅助。
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── README.md                           — Starfish 源码阅读指南
│   │   ├── __init__.py                         — 包导出入口
│   │   ├── __main__.py                         — 模块 CLI 入口
│   │   ├── container.py                        — Starfish 默认 composition root。
│   ├── turtle/ — Turtle 模块资产
│   │   ├── adapters/ — 接口适配器实现
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── api/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── audit/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── auth/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── authorizer.py                       — 授权决策模型。
│   │   │   ├── credential.py                       — 凭证引用重导出。
│   │   │   ├── identity.py                         — 身份模型。
│   │   │   ├── policy.py                           — 访问策略端口抽象。
│   │   ├── change_control/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── compliance/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── audit_policy.py                     — 审计事件模型和 sink 端口。
│   │   │   ├── data_classification.py              — 数据分类标记。
│   │   │   ├── retention.py                        — 数据保留策略模型。
│   │   ├── deployment_policy/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── governance/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── policy/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── ports/ — 抽象端口接口
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── risk/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── runtime/ — 运行时内核与生命周期
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── sdk/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── security/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── certificate.py                      — 证书引用重导出。
│   │   │   ├── model.py                            — 安全引用模型。
│   │   │   ├── secret_provider.py                  — 密钥提供方端口。
│   │   │   ├── tls.py                              — TLS 配置模型。
│   │   ├── __init__.py                         — 包导出入口
│   ├── whale/ — Whale 模块资产
│   │   ├── aggregation/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── ads.py                              — ADS business aggregations for scenario1.
│   │   │   ├── periodic.py                         — Periodic 1-minute DWS aggregation.
│   │   │   ├── realtime.py                         — Realtime 5-second DWS aggregation.
│   │   ├── ingest/
│   │   │   ├── adapters/ — 接口适配器实现
│   │   │   │   ├── audit/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── db_audit_sink.py                    — 审计日志适配器。
│   │   │   │   │   ├── http_audit_sink.py                  — 审计日志适配器。
│   │   │   │   │   ├── multi_audit_sink.py                 — 可组合的审计 sink 适配器。提供多路审计事件转发和聚合错误处理。
│   │   │   │   ├── config/ — 运行配置样例
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── opcua_source_acquisition_definition_repository.py — 配置适配器。
│   │   │   │   │   ├── source_runtime_config_repository.py — 配置适配器。
│   │   │   │   ├── message/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── kafka_message_publisher.py          — 消息发布适配器。
│   │   │   │   │   ├── redis_streams_message_publisher.py  — 消息发布适配器。
│   │   │   │   │   ├── relational_outbox_message_publisher.py — 消息发布适配器。
│   │   │   │   ├── observability/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── file_sinks.py                       — 可观测性适配器。
│   │   │   │   ├── security/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── external_access_policy.py           — 基于外部 HTTP 的 ingest 运行时访问策略适配器。将权限决策委托给远程授权服务。
│   │   │   │   │   ├── file_access_policy.py               — 安全策略适配器。
│   │   │   │   ├── source/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── dispatch_source_acquisition_adapter.py — 多协议采集端口调度适配器。
│   │   │   │   │   ├── http_rest_source_acquisition_adapter.py — HTTP REST source 采集适配器。
│   │   │   │   │   ├── iec101_source_acquisition_adapter.py — IEC 101 source 采集适配器。
│   │   │   │   │   ├── iec104_source_acquisition_adapter.py — 协议采集适配器。
│   │   │   │   │   ├── iec104_source_write_adapter.py      — 协议采集适配器。
│   │   │   │   │   ├── iec61850_report_source_acquisition_adapter.py — IEC 61850 Report source 采集适配器。
│   │   │   │   │   ├── iec61850_source_acquisition_adapter.py — 协议采集适配器。
│   │   │   │   │   ├── iec61850_source_write_adapter.py    — 协议采集适配器。
│   │   │   │   │   ├── modbus_rtu_source_acquisition_adapter.py — Modbus RTU source 采集适配器。
│   │   │   │   │   ├── modbus_source_acquisition_adapter.py — 协议采集适配器。
│   │   │   │   │   ├── modbus_source_write_adapter.py      — 协议采集适配器。
│   │   │   │   │   ├── mqtt_source_acquisition_adapter.py  — MQTT source 采集适配器。
│   │   │   │   │   ├── opcua_source_acquisition_adapter.py — OPC UA source 采集适配器。
│   │   │   │   │   ├── opcua_source_write_adapter.py       — OPC UA source write adapter.
│   │   │   │   │   ├── static_source_acquisition_port_registry.py — 静态 source acquisition port registry。
│   │   │   │   │   ├── static_source_write_port_registry.py — Static source write port registry.
│   │   │   │   ├── state/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── redis_source_state_cache.py         — Python 模块
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── api/
│   │   │   │   ├── routes/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── acquisition_tasks.py                — 采集任务 CRUD 路由。
│   │   │   │   │   ├── audit_events.py                     — 审计事件查询路由。
│   │   │   │   │   ├── bundles.py                          — Bundle 元数据查询路由。
│   │   │   │   │   ├── health.py                           — 管理 健康检查 资源的 API 路由。
│   │   │   │   │   ├── leases.py                           — 管理 租约 资源的 API 路由。
│   │   │   │   │   ├── nodes.py                            — 管理 节点 资源的 API 路由。
│   │   │   │   │   ├── runtime_config.py                   — 管理 运行时配置 资源的 API 路由。
│   │   │   │   │   ├── scheduler_jobs.py                   — 管理 调度任务 资源的 API 路由。
│   │   │   │   │   ├── security_partitions.py              — 管理 安全分区 资源的 API 路由。
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── app.py                              — Ingest FastAPI 应用工厂。
│   │   │   │   ├── audit_middleware.py                 — 审计中间件。
│   │   │   │   ├── errors.py                           — API 错误定义。
│   │   │   │   ├── idempotency.py                      — 幂等键支持模块。为 ingest 运行时 CRUD API 提供防重复请求的中间件和服务。
│   │   │   │   ├── readyz.py                           — Python 模块
│   │   │   │   ├── schemas.py                          — Ingest 运行时 CRUD API 的 Pydantic schema 定义。
│   │   │   ├── bundle/
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── checksum.py                         — Bundle 校验和。
│   │   │   │   ├── model.py                            — Bundle 数据模型。
│   │   │   │   ├── redaction.py                        — Bundle 脱敏辅助函数。对 bundle 中的敏感字段按可配置规则做脱敏处理。
│   │   │   │   ├── service.py                          — Bundle 服务。
│   │   │   ├── decorators/
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── source_acquisition.py               — Python 模块
│   │   │   │   ├── source_write.py                     — 装饰器模块。
│   │   │   │   ├── state_cache.py                      — 装饰器模块。
│   │   │   ├── diagnostics/
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── capacity.py                         — Ingest runtime capacity —— 轻量端点/点位/读取容量扫描。
│   │   │   │   ├── probe.py                            — Ingest runtime probe —— 最小启动-健康-读取探测。
│   │   │   │   ├── profile.py                          — Ingest runtime profile —— 对 read 执行 N 次采样并统计耗时。
│   │   │   ├── docs/ — 项目长期文档
│   │   │   │   ├── DECISIONS.md                        — Ingest 模块决策
│   │   │   │   ├── 设计说明书.md                            — ingest 模块设计说明书
│   │   │   ├── domain/ — 领域模型与纯规则
│   │   │   │   ├── audit_event.py                      — 审计事件领域模型。
│   │   │   │   ├── write_security_profile.py           — 写入安全配置文件。
│   │   │   ├── entities/
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── node_state.py                       — 节点状态实体。
│   │   │   │   ├── source_health_state.py              — 数据源健康状态实体。
│   │   │   ├── file_ingest/
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── decoder.py                          — 文件接入专用解码器。
│   │   │   │   ├── detector.py                         — 文件落地完成检测器。
│   │   │   │   ├── models.py                           — 文件接入运行期数据模型与 DTO。
│   │   │   │   ├── repository.py                       — 文件接入仓储层。
│   │   │   │   ├── service.py                          — 文件接入服务。
│   │   │   ├── framework/
│   │   │   │   ├── persistence/
│   │   │   │   │   ├── orm/
│   │   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── base.py                             — SQLAlchemy 基础模型。定义 ingest 持久化层共用的 declarative base。
│   │   │   │   │   ├── init_db.py                          — 框架基础设施。
│   │   │   │   │   ├── runtime_db.py                       — 框架基础设施。
│   │   │   │   │   ├── session.py                          — 框架基础设施。
│   │   │   ├── ports/ — 抽象端口接口
│   │   │   │   ├── command/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── source_command_audit_port.py        — 端口接口定义。
│   │   │   │   ├── message/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── message_publisher_port.py           — 端口接口定义。
│   │   │   │   ├── runtime/ — 运行时内核与生命周期
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── access_policy_port.py               — ingest 运行时 access policy port。
│   │   │   │   │   ├── source_runtime_config_port.py       — ingest 运行时 source runtime config port。
│   │   │   │   │   ├── write_lease_port.py                 — ingest 运行时 write lease port。
│   │   │   │   ├── source/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── source_acquisition_definition_port.py — 端口接口定义。
│   │   │   │   │   ├── source_acquisition_port.py          — source 采集端口定义。
│   │   │   │   │   ├── source_acquisition_port_registry.py — 端口接口定义。
│   │   │   │   │   ├── source_write_port.py                — Source write/control port for ingest.
│   │   │   │   │   ├── source_write_port_registry.py       — 端口接口定义。
│   │   │   │   ├── state/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── source_state_cache_port.py          — source latest-state cache 端口定义。
│   │   │   │   │   ├── source_state_snapshot_reader_port.py — 端口接口定义。
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── audit.py                            — 端口接口定义。
│   │   │   │   ├── diagnostics.py                      — IngestRuntimeDiagnosticsPort — 采集运行时诊断端口.
│   │   │   │   ├── metrics.py                          — Ingest 指标 port 接口。声明计数器、直方图等指标契约，由具体 sink 实现。
│   │   │   ├── runtime/ — 运行时内核与生命周期
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── acquisition_mode.py                 — 采集模式定义。
│   │   │   │   ├── cli.py                              — ingest CLI 入口。
│   │   │   │   ├── entrypoint.py                       — ingest 启动入口。
│   │   │   │   ├── fencing.py                          — Fencing token 辅助模块。提供防脑裂的 fencing token 生成和验证能力。
│   │   │   │   ├── handlers.py                         — WorkerRuntime job handlers for ingest.
│   │   │   │   ├── job_assignment.py                   — 任务分配逻辑。
│   │   │   │   ├── job_status.py                       — 任务状态管理。
│   │   │   │   ├── lease.py                            — Python 模块
│   │   │   │   ├── message_pipeline_settings.py        — 消息管道配置。
│   │   │   │   ├── modes.py                            — 运行模式定义。
│   │   │   │   ├── node_runtime.py                     — 节点运行时管理。
│   │   │   │   ├── scheduler.py                        — 采集调度器。
│   │   │   │   ├── scheduler_factory.py                — 调度器工厂。
│   │   │   │   ├── scheduler_job.py                    — 调度任务定义。
│   │   │   │   ├── scheduler_settings.py               — 调度器配置。
│   │   │   │   ├── worker_runtime.py                   — Python 模块
│   │   │   │   ├── write_lease.py                      — Write-control specific lease guard.
│   │   │   ├── usecases/
│   │   │   │   ├── dtos/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── acquired_node_state.py              — 采集状态 DTO。
│   │   │   │   │   ├── source_acquisition_request.py       — 采集请求 DTO。
│   │   │   │   │   ├── source_acquisition_start_result.py  — SourceAcquisitionStartResult DTO — source 采集启动结果。
│   │   │   │   │   ├── source_connection_data.py           — 采集连接 DTO。
│   │   │   │   │   ├── source_write_request.py             — Source write request DTOs for the write/control use case.
│   │   │   │   │   ├── source_write_result.py              — 数据传输对象。
│   │   │   │   │   ├── state_publish_request.py            — 状态快照发布请求 DTO。承载一次发布操作所需的源标识、时间戳等参数。
│   │   │   │   │   ├── state_publish_result.py             — 数据传输对象。
│   │   │   │   ├── roles/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── polling_acquisition_role.py         — Polling 采集 role。
│   │   │   │   │   ├── subscription_acquisition_role.py    — SubscriptionAcquisitionRole — 启动订阅采集 session。
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── source_acquisition_use_case.py      — 统一 source 采集 usecase。
│   │   │   │   ├── source_command_use_case.py          — Python 模块
│   │   │   │   ├── state_snapshot_publish_use_case.py  — Python 模块
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── composition.py                      — Python 模块
│   │   │   ├── config.py                           — ingest 配置管理。
│   │   │   ├── message_pipeline.py                 — 消息管线抽象。定义采集数据输出的发布接口和内存实现。
│   │   ├── message_pipeline/
│   │   │   ├── adapters/ — 接口适配器实现
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── in_memory.py                        — 消息管道内存测试适配器。
│   │   │   │   ├── kafka.py                            — Python 模块
│   │   │   │   ├── pulsar.py                           — Pulsar 消息管道适配器（contract adapter）。
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── model.py                            — 消息管道领域模型。
│   │   │   ├── ports.py                            — 消息管道端口接口。
│   │   ├── model_asset/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── archive.py                          — 仿真归档服务。
│   │   │   ├── detector.py                         — 仿真文件类型检测器。
│   │   │   ├── models.py                           — 模型资产 DTO 和数据模型。
│   │   │   ├── repository.py                       — 模型资产持久化仓库。
│   │   │   ├── service.py                          — 模型资产导入编排服务。
│   │   ├── processing/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── cleaner.py                          — Cleaning rules for scenario1 normalized points.
│   │   │   ├── normalizer.py                       — Raw batch normalization for scenario1.
│   │   ├── shared/
│   │   │   ├── enums/
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── quality.py                          — Stable enums shared across scenario pipelines.
│   │   │   ├── persistence/
│   │   │   │   ├── orm/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── acquisition.py                      — 采集任务与点位状态模块.
│   │   │   │   │   ├── asset.py                            — Python 模块
│   │   │   │   │   ├── ingest_diagnostics.py               — 采集诊断模块 — ingest_source_health 与 ingest_runtime_event.
│   │   │   │   │   ├── ingest_runtime.py                   — Runtime persistence models for ingest API, scheduler, lease, and audit
│   │   │   │   │   ├── model_asset.py                      — 仿真模型资产 ORM 模型。
│   │   │   │   │   ├── organization.py                     — 组织模块.
│   │   │   │   │   ├── scada_ingest.py                     — Python 模块
│   │   │   │   │   ├── scada_protocol_param.py             — SCADA 协议参数模型 — 第一范式协议参数定义与值存储.
│   │   │   │   ├── template/
│   │   │   │   │   ├── OPCUA_client_connections.yaml       — YAML 配置
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── gbt_30966_fields.py                 — 已废弃的 GB/T 30966 字段定义模块。
│   │   │   │   │   ├── protocol_param_data.py              — 已废弃的协议参数定义模块。
│   │   │   │   │   ├── protocol_view_defs.py               — 已废弃的协议视图定义模块。
│   │   │   │   │   ├── sample_data.py                      — 已废弃的 SCADA 样例数据模块。
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── base.py                             — SQLAlchemy declarative base for all Whale ORM models.
│   │   │   │   ├── init_db.py                          — shared persistence 数据库初始化入口。
│   │   │   │   ├── session.py                          — shared persistence 层的 SQLAlchemy engine 与 session 工具。
│   │   │   ├── source/
│   │   │   │   ├── access/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── adapter.py                          — Reusable source access adapter interfaces.
│   │   │   │   │   ├── model.py                            — Reusable runtime models for source access adapters.
│   │   │   │   │   ├── opcua.py                            — Reusable OPC UA source access adapter.
│   │   │   │   ├── http_rest/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── client.py                           — HTTP REST 生产级 shared source backend。
│   │   │   │   ├── iec101/
│   │   │   │   │   ├── backends/
│   │   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   │   ├── base.py                             — IEC 101 backend 基础类型定义。
│   │   │   │   │   │   ├── serial_backend.py                   — IEC 101 串行通信 backend。
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── reader.py                           — IEC 101 source reader facade。
│   │   │   │   ├── iec104/
│   │   │   │   │   ├── backends/
│   │   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   │   ├── base.py                             — IEC 104 backend base types.
│   │   │   │   │   │   ├── lib60870_backend.py                 — IEC 104 client backend backed by native C runner subprocess.
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── reader.py                           — IEC 104 source reader/writer facade.
│   │   │   │   ├── iec61850/
│   │   │   │   │   ├── backends/
│   │   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   │   ├── base.py                             — IEC 61850 MMS backend base types.
│   │   │   │   │   │   ├── libiec61850_backend.py              — libiec61850-based IEC 61850 MMS client backend (subprocess runner).
│   │   │   │   │   │   ├── libiec61850_report_backend.py       — libiec61850-based IEC 61850 Report backend (subprocess runner).
│   │   │   │   │   │   ├── report_base.py                      — IEC 61850 Report backend base types.
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── reader.py                           — IEC 61850 MMS source reader facade.
│   │   │   │   │   ├── report_reader.py                    — IEC 61850 Report source reader facade.
│   │   │   │   ├── modbus/
│   │   │   │   │   ├── backends/
│   │   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   │   ├── base.py                             — Modbus TCP backend base types.
│   │   │   │   │   │   ├── libmodbus_backend.py                — Modbus TCP client backend backed by native C runner subprocess.
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── reader.py                           — Modbus TCP source reader/writer facade.
│   │   │   │   ├── modbus_rtu/
│   │   │   │   │   ├── backends/
│   │   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   │   ├── base.py                             — Modbus RTU backend 基础类型定义。
│   │   │   │   │   │   ├── serial_backend.py                   — Python 模块
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── reader.py                           — Modbus RTU source reader facade。
│   │   │   │   ├── mqtt/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── client.py                           — MQTT 生产级 shared source backend。
│   │   │   │   ├── opcua/
│   │   │   │   │   ├── backends/
│   │   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   │   ├── base.py                             — OPC UA 客户端后端抽象基类。
│   │   │   │   │   │   ├── factory.py                          — OPC UA 客户端后端工厂。
│   │   │   │   │   │   ├── open62541_backend.py                — Python 模块
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── reader.py                           — Open62541-backed OPC UA raw polling facade.
│   │   │   │   ├── scheduling/
│   │   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   │   ├── concurrency.py                      — Worker-local read concurrency control for high-frequency source pollin
│   │   │   │   │   ├── fixed_rate.py                       — Python 模块
│   │   │   │   │   ├── polling.py                          — Worker-local fixed-rate polling primitives for source acquisition.
│   │   │   │   │   ├── stagger.py                          — Deterministic stagger-offset helpers for worker-local source polling.
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── models.py                           — 统一的 source 层数据模型，用于 read / subscription batch 处理。
│   │   │   │   ├── ports.py                            — 优化后的 ports.py
│   │   │   │   ├── runner_resolution.py                — Shared native runner path resolution for production source clients.
│   │   │   ├── utils/
│   │   │   │   ├── time.py                             — Time utilities for deterministic scenario processing.
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── speed_layer/
│   │   │   ├── preprocessing/
│   │   │   │   ├── __init__.py                         — 包导出入口
│   │   │   │   ├── models.py                           — speed layer 预处理 Pipeline 运行期 DTO 与 dataclass。
│   │   │   │   ├── operators.py                        — Python 模块
│   │   │   │   ├── pipeline.py                         — speed layer 预处理 Pipeline — 固定 10 阶段编排。
│   │   │   │   ├── registry.py                         — speed layer 预处理 Operator / Strategy Registry。
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── light_processor.py                  — Python 模块
│   │   │   ├── metrics.py                          — speed layer 指标收集。
│   │   │   ├── runner.py                           — speed layer pipeline runner。
│   │   │   ├── writers.py                          — Python 模块
│   │   ├── storage/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── mart.py                             — 数据集市层（mart）——面向业务服务的预聚合数据。
│   │   │   ├── raw_archive.py                      — Python 模块
│   │   │   ├── raw_index.py                        — 原始时序索引层（raw_index）——TDengine 快速查询入口。
│   │   │   ├── serving_cache.py                    — 业务侧近实时 serving cache 层。
│   │   │   ├── simulation_result.py                — Python 模块
│   │   │   ├── standardized.py                     — 标准时序层（standardized）——TDengine 清洗后数据存储。
│   │   │   ├── warehouse.py                        — 数据仓库层（warehouse）——面向主题分析的数据存储。
│   │   │   ├── waveform.py                         — Python 模块
│   │   ├── __init__.py                         — 包导出入口
├── tests/ — 测试代码
│   ├── deployment/
│   │   ├── README.md                           — Deployment Tests
│   ├── e2e/ — 端到端测试
│   │   ├── __init__.py                         — 包导出入口
│   │   ├── conftest.py                         — E2E test fixtures: PostgreSQL + Redis + Kafka infrastructure.
│   │   ├── helpers.py                          — Shared helpers for e2e tests — importable utilities and constants.
│   │   ├── test_whale_field_minimal_smoke.py   — Python 模块
│   │   ├── test_whale_l5_kafka_pipeline_e2e.py — Python 模块
│   │   ├── test_whale_l5_storage_e2e.py        — Python 模块
│   ├── integration/ — 集成测试
│   │   ├── __init__.py                         — 包导出入口
│   │   ├── test_framework_db_init.py           — Integration tests for framework database initialization.
│   │   ├── test_http_rest_acquisition_chain.py — HTTP REST 全链路采集集成测试。
│   │   ├── test_iec101_acquisition_chain.py    — IEC 101 全链路采集集成测试。
│   │   ├── test_iec104_acquisition_chain.py    — IEC104 全链路采集集成测试。
│   │   ├── test_ingest_api_acquisition_task_crud.py — Acquisition-task CRUD integration tests.
│   │   ├── test_ingest_api_audit.py            — API audit integration tests.
│   │   ├── test_ingest_api_authorization_deny.py — Authorization deny E2E tests for ingest runtime API.
│   │   ├── test_ingest_api_bundle_metadata_crud.py — Bundle-metadata query API integration tests.
│   │   ├── test_ingest_api_dry_run_all_mutating_routes.py — Python 模块
│   │   ├── test_ingest_api_full_audit_matrix.py — Full audit matrix integration tests — verify every API action emits au
│   │   ├── test_ingest_api_idempotency_all_mutating_routes.py — Idempotency-Key coverage across all mutating CRUD route groups.
│   │   ├── test_ingest_api_idempotency_dry_run.py — Integration tests for API idempotency key and dry-run support.
│   │   ├── test_ingest_api_idempotency_dry_run_interaction.py — Idempotency-Key + dry_run=true interaction tests.
│   │   ├── test_ingest_api_node_lease_audit_query.py — Node / Lease / Audit-event query API integration tests.
│   │   ├── test_ingest_api_runtime_config_audit.py — Runtime-config API audit tests.
│   │   ├── test_ingest_api_runtime_config_crud.py — Runtime-config CRUD integration tests.
│   │   ├── test_ingest_api_scheduler_job_crud.py — Scheduler-job CRUD integration tests.
│   │   ├── test_ingest_api_security_partition_crud.py — Security-partition CRUD integration tests.
│   │   ├── test_ingest_audit_db_jsonl_consistency.py — Audit DB/JSONL sink consistency tests.
│   │   ├── test_ingest_audit_matrix_api_bundle_scheduler_write.py — Audit matrix tests covering API, bundle, scheduler, and write events.
│   │   ├── test_ingest_bundle_import_export.py — Bundle import/export integration tests.
│   │   ├── test_ingest_bundle_offline_one_way_flow.py — Offline one-way bundle flow tests.
│   │   ├── test_ingest_cache_to_kafka_pipeline.py — Integration test: cache snapshot → StateSnapshotPublishUseCase → Kafka
│   │   ├── test_ingest_dual_node_db_lease_e2e.py — Python 模块
│   │   ├── test_ingest_external_access_policy_contract.py — External access policy contract tests with a local HTTP stub server.
│   │   ├── test_ingest_external_audit_sink_contract.py — External audit/SIEM sink contract tests with a local HTTP stub server.
│   │   ├── test_ingest_file_ingest_integration.py — 文件接入模块集成测试。
│   │   ├── test_ingest_iec104_source_write.py  — Integration test for IEC 104 source write via SourceCommandUseCase.
│   │   ├── test_ingest_iec61850_mms_source_write.py — Python 模块
│   │   ├── test_ingest_iec61850_report_subscription.py — IEC 61850 Report subscription integration tests.
│   │   ├── test_ingest_lightweight_load_gate.py — Lightweight ingest load gate with in-memory/test sinks.
│   │   ├── test_ingest_modbus_source_write.py  — Python 模块
│   │   ├── test_ingest_observability_sink_smoke.py — Smoke test for deployment-ready JSONL observability sinks.
│   │   ├── test_ingest_opcua_source_write.py   — Integration test for OPC UA source write via SourceCommandUseCase.
│   │   ├── test_ingest_polling_retry_to_redis.py — Python 模块
│   │   ├── test_ingest_prodlike_access_policy.py — Production-like access policy integration tests.
│   │   ├── test_ingest_prodlike_audit_metrics_resilience.py — Audit and metrics resilience tests under prodlike dependency failures.
│   │   ├── test_ingest_prodlike_audit_sink.py  — Production-like audit sink integration tests.
│   │   ├── test_ingest_prodlike_endurance_smoke.py — Short-duration endurance smoke for the prodlike ingest compose profile
│   │   ├── test_ingest_prodlike_kafka_fault_injection.py — Kafka fault injection and recovery tests for prodlike ingest runtime.
│   │   ├── test_ingest_prodlike_kafka_publish.py — Production-like Kafka publish integration tests.
│   │   ├── test_ingest_prodlike_performance_profile.py — Performance profile conformance tests for ingest runtime.
│   │   ├── test_ingest_prodlike_postgres_fault_injection.py — PostgreSQL fault injection and recovery tests for prodlike ingest runt
│   │   ├── test_ingest_prodlike_postgres_runtime_db.py — Production-like PostgreSQL runtime DB integration tests.
│   │   ├── test_ingest_prodlike_redis_cache.py — Production-like Redis cache integration tests.
│   │   ├── test_ingest_prodlike_redis_fault_injection.py — Redis fault injection and recovery tests for prodlike ingest runtime.
│   │   ├── test_ingest_prodlike_scheduler_backpressure.py — Scheduler backpressure, missed-tick, and assignment-lag tests.
│   │   ├── test_ingest_prodlike_worker_failover.py — Worker crash, restart, fencing, and failover tests.
│   │   ├── test_ingest_runtime_alembic_migration.py — Alembic migration integration tests.
│   │   ├── test_ingest_runtime_alembic_postgres_matrix.py — Alembic PostgreSQL migration matrix — upgrade head & verify schema.
│   │   ├── test_ingest_runtime_alembic_sqlite_matrix.py — Alembic SQLite migration matrix — upgrade head & downgrade base.
│   │   ├── test_ingest_runtime_db_init.py      — Runtime DB initialization smoke.
│   │   ├── test_ingest_runtime_entrypoint_smoke.py — CLI smoke tests for ingest runtime entrypoints.
│   │   ├── test_ingest_runtime_migrate_entrypoint.py — Integration tests for the migrate CLI entrypoint.
│   │   ├── test_ingest_scheduler_active_standby_failover.py — Active-standby scheduler failover tests.
│   │   ├── test_ingest_scheduler_apscheduler_runtime.py — Integration tests for WorkerRuntime / APScheduler-driven ingestion.
│   │   ├── test_ingest_scheduler_cluster_assignment.py — Cluster scheduler assignment tests.
│   │   ├── test_ingest_scheduler_dual_active_partitioned.py — Dual-active partitioned scheduler tests.
│   │   ├── test_ingest_scheduler_graceful_shutdown.py — Integration tests for WorkerRuntime graceful shutdown.
│   │   ├── test_ingest_scheduler_missed_tick_and_stagger.py — Integration tests for missed_tick and stagger_offset behavior.
│   │   ├── test_ingest_security_partition_bundle_flow.py — Security partition one-way bundle flow tests for ingest.
│   │   ├── test_ingest_security_partition_smoke.py — Security partition sample-config smoke.
│   │   ├── test_ingest_source_acquisition_to_redis.py — Integration test for source server -> Redis latest-state cache.
│   │   ├── test_ingest_source_cache_message_e2e.py — Integration test for source -> cache -> message chain.
│   │   ├── test_ingest_source_cache_message_kafka_e2e.py — Kafka container E2E for source -> cache -> message.
│   │   ├── test_ingest_subscription_strategy.py — Integration tests for current subscription strategy boundaries.
│   │   ├── test_ingest_worker_runtime_executes_usecase_handlers.py — Integration tests for WorkerRuntime job-type handler dispatch.
│   │   ├── test_ingest_worker_runtime_handler_failure.py — Integration tests for WorkerRuntime handler failure and missing handle
│   │   ├── test_ingest_worker_runtime_shutdown_inflight.py — Integration tests for WorkerRuntime shutdown with inflight jobs.
│   │   ├── test_ingest_write_lease_fencing_e2e.py — Write lease / fencing / readback integration tests.
│   │   ├── test_l5_external_dependency_verification.py — Python 模块
│   │   ├── test_message_pipeline_inmemory_e2e.py — message_pipeline InMemory 全链路集成测试。
│   │   ├── test_message_pipeline_kafka_e2e.py  — message_pipeline Kafka 集成测试（contract-only）。
│   │   ├── test_modbus_rtu_acquisition_chain.py — Modbus RTU 全链路采集集成测试。
│   │   ├── test_model_asset_alembic_migration.py — model_asset Alembic migration 集成测试。
│   │   ├── test_model_asset_integration.py     — model_asset 模块集成测试。
│   │   ├── test_model_asset_postgres_integration.py — Python 模块
│   │   ├── test_mqtt_acquisition_chain.py      — MQTT 全链路采集集成测试。
│   │   ├── test_redis_state_cache_faults.py    — Integration tests for live Redis latest-state cache fault handling.
│   │   ├── test_shared_persistence_sample_data_init.py — 共享持久化样例初始化 PostgreSQL 集成测试。
│   │   ├── test_speed_layer_dlq_replay.py      — speed layer DLQ 与 replay 语义集成测试。
│   │   ├── test_speed_layer_index_standardized_pipeline.py — speed layer index 和 standardized 管道集成测试。
│   │   ├── test_speed_layer_raw_archive_pipeline.py — speed layer raw_archive 管道集成测试。
│   │   ├── test_sqlite_config_init.py          — Integration tests for the SQLite config initialization script.
│   │   ├── test_storage_simulation_result_tdengine_integration.py — TDengine simulation_result 真实写入/读回集成测试。
│   │   ├── test_storage_waveform_tdengine_integration.py — TDengine waveform 真实写入/读回集成测试。
│   │   ├── test_whale_writer_failure_recovery.py — Whale writer 故障恢复集成测试。
│   │   ├── test_whale_writer_switchover.py     — Whale writer 无缝切换集成测试。
│   ├── performance/ — 性能测试
│   │   ├── endurance/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   ├── load/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── conftest.py                         — Load test fixtures: PostgreSQL + Redis + Kafka, large NodeSets.
│   │   ├── stress/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── test_acquisition_pipeline_stress.py — Current-architecture stress smoke for ingest acquisition -> Redis late
│   │   ├── __init__.py                         — 包导出入口
│   ├── support/ — 测试支撑代码
│   │   ├── ingest_prodlike_runtime.py          — Shared helpers for prodlike ingest compose, endurance, and fault tests
│   │   ├── scada_sample_db.py                  — shared persistence SCADA sample DB 测试辅助函数。
│   │   ├── shared_persistence_sample_db.py     — Helpers for creating isolated shared persistence sample databases in t
│   ├── unit/ — 单元测试
│   │   ├── architecture/
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── test_seahorse_import_boundary.py    — seahorse / ingest / starfish import boundary 门禁测试。
│   │   │   ├── test_starfish_import_boundary.py    — starfish import boundary 门禁测试。
│   │   ├── seahorse/ — Seahorse 模块资产
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── test_bundle.py                      — Python 模块
│   │   │   ├── test_compat_wrappers.py             — 旧路径兼容包装器测试。
│   │   │   ├── test_generators.py                  — seahorse 生成器测试 —— 告警与控制回写。
│   │   │   ├── test_models.py                      — seahorse 核心模型序列化与确定性种子测试。
│   │   │   ├── test_orchestrator.py                — seahorse 最小编排器测试。
│   │   │   ├── test_reference_data_imports.py      — seahorse reference_data 新路径 import 测试。
│   │   │   ├── test_server_plan.py                 — seahorse ServerConfig 契约校验、handoff 导出与 CLI 测试。
│   │   │   ├── test_strategies.py                  — Python 模块
│   │   ├── shared/
│   │   │   ├── persistence/
│   │   │   │   ├── test_model_asset_orm.py             — model_asset ORM 表定义与约束单元测试。
│   │   │   │   ├── test_scada_protocol_params.py       — SCADA 协议参数模板与 ORM 单测.
│   │   │   │   ├── test_scada_protocol_views.py        — SCADA 协议视图单测.
│   │   │   │   ├── test_scada_sample_data_protocol_coverage.py — SCADA 多协议样例数据覆盖单测.
│   │   ├── starfish/ — Starfish 模块资产
│   │   │   ├── __init__.py                         — 包导出入口
│   │   │   ├── conftest.py                         — Starfish unit 测试子树的通用 marker 约束。
│   │   │   ├── test_iec101_asdu_objects.py         — Starfish IEC 60870-5-101 信息对象（Information Object）测试。
│   │   │   ├── test_iec101_codec.py                — Python 模块
│   │   │   ├── test_iec101_ft12_frame.py           — Python 模块
│   │   │   ├── test_iec101_information_elements.py — Python 模块
│   │   │   ├── test_iec101_link_layer.py           — Python 模块
│   │   │   ├── test_iec61850_facade.py             — Python 模块
│   │   │   ├── test_modbus_register_encoding.py    — Python 模块
│   │   │   ├── test_modbus_rtu_facade.py           — Starfish Modbus RTU PTY 轻量级 facade 测试。
│   │   │   ├── test_mqtt_facade.py                 — Python 模块
│   │   │   ├── test_native_runner_framework.py     — Python 模块
│   │   │   ├── test_opcua_iec104_facade.py         — Starfish OPC_UA / IEC104 facade 测试。
│   │   │   ├── test_probe_profile_capacity.py      — Python 模块
│   │   │   ├── test_protocol_facade.py             — Starfish 协议专用 facade 测试。
│   │   │   ├── test_remaining_protocols.py         — Python 模块
│   │   │   ├── test_runtime_api.py                 — starfish 高层运行时 API 测试。
│   │   │   ├── test_runtime_observability.py       — Runtime observability v1 单元测试。
│   │   │   ├── test_runtime_v2.py                  — Runtime v2.2 运行图与实例化契约测试。
│   │   │   ├── test_server_plan_loader.py          — Python 模块
│   │   │   ├── test_server_simulator_facade.py     — starfish ServerSimulatorDriverAdapter 测试。
│   │   │   ├── test_starfish_cli.py                — starfish CLI 测试。
│   │   ├── __init__.py                         — 包导出入口
│   │   ├── test_acquisition_job_handler.py     — AcquisitionJobHandler 单元测试。
│   │   ├── test_config.py                      — Unit tests for ingest configuration resolution.
│   │   ├── test_dual_node_write_lease_conflict.py — 双节点写入冲突与 lease/fencing 并发语义测试。
│   │   ├── test_http_rest_backend.py           — HTTP REST client backend 单元测试。
│   │   ├── test_http_rest_source_acquisition_adapter.py — HTTP REST 采集适配器单元测试。
│   │   ├── test_iec101_backend.py              — IEC 101 backend 单元测试。
│   │   ├── test_iec101_source_acquisition_adapter.py — IEC 101 source 采集适配器单元测试。
│   │   ├── test_iec104_backend.py              — Unit tests for IEC 104 backend (stdout protocol parsing).
│   │   ├── test_iec104_source_acquisition_adapter.py — Unit tests for IEC 104 source acquisition adapter.
│   │   ├── test_iec104_source_write_adapter.py — Unit tests for IEC 104 source write adapter.
│   │   ├── test_iec61850_mms_backend.py        — libiec61850 backend 单元测试。
│   │   ├── test_iec61850_report_acquisition_adapter.py — Python 模块
│   │   ├── test_iec61850_report_backend.py     — Python 模块
│   │   ├── test_iec61850_source_acquisition_adapter.py — Iec61850MmsSourceAcquisitionAdapter 单元测试。
│   │   ├── test_iec61850_source_write_adapter.py — Python 模块
│   │   ├── test_ingest_api_app.py              — FastAPI app factory tests.
│   │   ├── test_ingest_audit_event_schema.py   — Structured ingest audit event tests.
│   │   ├── test_ingest_audit_redaction.py      — Unit tests for audit event redaction.
│   │   ├── test_ingest_bundle_checksum.py      — Bundle checksum tests.
│   │   ├── test_ingest_bundle_redaction.py     — Bundle redaction tests.
│   │   ├── test_ingest_composition_injection.py — QA-1: composition.py 注入完整性测试。
│   │   ├── test_ingest_file_ingest_decoder.py  — 文件接入解码器单元测试。
│   │   ├── test_ingest_file_ingest_detector.py — 文件落地完成检测器单元测试。
│   │   ├── test_ingest_file_ingest_models.py   — 文件接入 DTO 模型单元测试。
│   │   ├── test_ingest_file_ingest_repository.py — 文件接入仓储层单元测试。
│   │   ├── test_ingest_file_ingest_service.py  — 文件接入服务单元测试。
│   │   ├── test_ingest_job_lease.py            — DB-backed lease semantics tests.
│   │   ├── test_ingest_metrics_events.py       — Metrics event emission tests for ingest core chains.
│   │   ├── test_ingest_no_source_lab_imports.py — 确保 ingest 生产代码不引入 tools.source_lab（目录已物理删除，此检查为历史门禁保留）。
│   │   ├── test_ingest_observability_sink.py   — Unit tests for lightweight ingest observability sinks.
│   │   ├── test_ingest_readyz.py               — Python 模块
│   │   ├── test_ingest_runtime_entrypoint.py   — CLI entrypoint tests for ingest runtime.
│   │   ├── test_ingest_runtime_modes.py        — Runtime mode parsing tests.
│   │   ├── test_ingest_runtime_orm_models.py   — Runtime ORM model registration tests.
│   │   ├── test_ingest_runtime_scheduler_import.py — Import smoke for the ingest runtime scheduler package.
│   │   ├── test_ingest_security_partition_config.py — Security partition config guard tests.
│   │   ├── test_ingest_source_adapter_capability_matrix.py — Ingest adapter capability matrix guard.
│   │   ├── test_ingest_write_lease.py          — Write lease service tests.
│   │   ├── test_ingest_write_lease_fencing.py  — Write lease fencing tests.
│   │   ├── test_ingest_write_security_profile.py — Unit tests for WriteSecurityProfile domain model.
│   │   ├── test_kafka_message_publisher.py     — Unit tests for the Kafka snapshot publisher.
│   │   ├── test_message_pipeline_adapters.py   — message_pipeline InMemory 适配器单元测试。
│   │   ├── test_message_pipeline_envelope.py   — message_pipeline 领域模型单元测试。
│   │   ├── test_message_pipeline_kafka_adapter.py — Kafka message_pipeline 适配器契约与配置测试。
│   │   ├── test_message_pipeline_ports.py      — message_pipeline 端口接口契约测试。
│   │   ├── test_modbus_rtu_backend.py          — Modbus RTU backend 单元测试。
│   │   ├── test_modbus_rtu_source_acquisition_adapter.py — Modbus RTU source 采集适配器单元测试。
│   │   ├── test_modbus_source_acquisition_adapter.py — ModbusSourceAcquisitionAdapter 单元测试。
│   │   ├── test_modbus_source_write_adapter.py — Python 模块
│   │   ├── test_model_asset_detector.py        — model_asset detector 单元测试。
│   │   ├── test_model_asset_models.py          — model_asset DTO 模型单元测试。
│   │   ├── test_model_asset_repository.py      — model_asset repository 单元测试。
│   │   ├── test_model_asset_service.py         — model_asset service 单元测试。
│   │   ├── test_mqtt_backend.py                — MQTT client backend 单元测试。
│   │   ├── test_mqtt_source_acquisition_adapter.py — MQTT 采集适配器单元测试。
│   │   ├── test_opcua_adapter_resolution.py    — OPC UA adapter 地址解析单元测试。
│   │   ├── test_opcua_source_acquisition_adapter.py — OPC UA source acquisition adapter 单元测试。
│   │   ├── test_opcua_source_write_adapter.py  — Python 模块
│   │   ├── test_open62541_backend.py           — Python 模块
│   │   ├── test_polling_acquisition_role.py    — PollingAcquisitionRole 单元测试。
│   │   ├── test_redis_source_state_cache.py    — Unit tests for the Redis latest-state cache adapter.
│   │   ├── test_redis_streams_message_publisher.py — Unit tests for the Redis Streams snapshot publisher.
│   │   ├── test_relational_outbox_message_publisher.py — Unit tests for the relational outbox snapshot publisher.
│   │   ├── test_scheduler_job_routes.py        — QA-5: scheduler_job stagger_offset_ms 持久化端到端测试。
│   │   ├── test_shared_source_runner_resolution.py — shared_source native runner path resolution boundary tests.
│   │   ├── test_source_acquisition_port_registry.py — StaticSourceAcquisitionPortRegistry 单元测试。
│   │   ├── test_source_acquisition_use_case.py — SourceAcquisitionUseCase 单元测试。
│   │   ├── test_source_command_audit.py        — SourceCommandUseCase audit tests.
│   │   ├── test_source_command_authorization_guard.py — Unit tests for AuthorizedSourceWritePort.
│   │   ├── test_source_command_lease_release.py — QA-2: SourceCommandUseCase 异常路径 lease release 测试。
│   │   ├── test_source_command_use_case.py     — SourceCommandUseCase 单元测试。
│   │   ├── test_source_command_write_lease_guard.py — Source command write lease guard tests.
│   │   ├── test_source_runtime_config_repository.py — Unit tests for the runtime-config repository.
│   │   ├── test_source_scheduling.py           — Unit tests for the worker-local source polling kernel.
│   │   ├── test_source_write_port_registry.py  — Source write port registry 单元测试。
│   │   ├── test_speed_layer_light_processor.py — Python 模块
│   │   ├── test_speed_layer_pipeline_runner.py — Python 模块
│   │   ├── test_speed_layer_preprocessing.py   — speed layer 预处理 Pipeline Round A 测试。
│   │   ├── test_state_snapshot_publish_use_case.py — Python 模块
│   │   ├── test_storage_raw_archive.py         — storage raw_archive 层单元测试。
│   │   ├── test_storage_raw_index.py           — storage raw_index 层单元测试。
│   │   ├── test_storage_serving_cache.py       — storage serving_cache Redis 适配器单元测试。
│   │   ├── test_storage_simulation_result.py   — storage simulation_result 单元测试。
│   │   ├── test_storage_standardized.py        — storage standardized 层单元测试。
│   │   ├── test_storage_waveform.py            — storage waveform 层单元测试。
│   │   ├── test_subscription_acquisition_role.py — SubscriptionAcquisitionRole unit tests.
│   │   ├── test_subscription_reconnect_baseline.py — Reconnect baseline read strategy tests for SubscriptionAcquisitionRole
│   │   ├── test_subscription_reconnect_runtime.py — Subscription runtime reconnect/backoff/max-retry tests.
│   │   ├── test_turtle_octopus_import_boundary.py — turtle/octopus 与 platform_shared 的 import boundary 门禁测试。
│   │   ├── test_worker_runtime_do_execute.py   — WorkerRuntime._do_execute handler dispatch 单元测试。
│   ├── TESTING.md                          — Whale 主平台测试指南
│   ├── __init__.py                         — 包导出入口
│   ├── conftest.py                         — Shared pytest fixtures for ingest integration tests.
│   ├── issue_trace.md                      — 测试问题追踪
├── .gitignore                          — Git 忽略规则
├── .mcp.json                           — MCP 配置
├── AGENTS.md                           — Codex/agent 仓库入口规则
├── CLAUDE.md                           — Claude/Codex 共享执行入口
├── README.md                           — BlueCrystal - 能源数据统一平台
├── alembic.ini                         — Alembic 主配置
├── pyproject.toml                      — Python 项目与工具配置
```
