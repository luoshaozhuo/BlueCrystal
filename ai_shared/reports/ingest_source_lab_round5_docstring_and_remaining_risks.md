# Round 5 docstring 治理、QA-8 修复、readback 实现与双节点 lease 收口报告

> 日期: 2026-05-29
> 范围: src/whale/ingest, src/whale/shared/source, tools/source_lab, tests, ai_shared/rules
> 状态: 收口（部分剩余风险明确列出）
> 证据来源: code-implementer + test-validator Agent result

## 1. 总览

| 项 | 结果 |
|---|---|
| 扫描文件总数 | 506 .py 文件（5 个根目录） |
| 本轮修复 docstring | 59（34 module + 20 schema class + 5 type:ignore 解释） |
| 规则更新 | coding.md Section 8.1-8.7 新增；python-docstring-cn.md 重写为多语言通用版 |
| QA-8 RunnerInfo 修复 | 5 种字段分离，5 tests PASS；PROTOCOL_CAPABILITIES 仍静态 |
| Readback 实现 | Modbus FC03+FC06 (3 tests) + IEC61850 MMS (3 tests)，L2 contract |
| 双节点 DB lease E2E | 真实 SQLite + LeaseService + FencingTokenRepository，7 tests PASS，L3 |
| WorkerRuntime | 8 handler L1 + 5 integration L2 tests PASS |
| 质量门禁 | compileall PASS, ruff PASS, mypy PASS, 61+ tests PASS |
| 注释违规 remaining | ~450 entries（已分类：English docstring ~350, API route 缺 docstring ~40, type:ignore ~50, 缺 public docstring ~15） |

## 2. 规则更新摘要

### 2.1 coding.md 变化

- 从 5 节扩充为 9 节，Section 2（架构与边界）新增，Section 3（接口、类型与契约）重写。
- 新增 Section 8（注释与文档注释），细化为 8.1-8.7：
  - 8.1 基本原则（英文业务注释明确为违规）
  - 8.2 文件头（module docstring 按文件类型要求）
  - 8.3 函数/方法 docstring
  - 8.4 API route docstring
  - 8.5 CLI command/entrypoint docstring
  - 8.6 复杂 private helper docstring
  - 8.7 测试 fixture/fake/mock/stub docstring
- Section 7（架构与边界）新增 declared/actual/validated 三元能力区分。
- Section 10（文档与需求状态）新增状态高估降级规则。

### 2.2 python-docstring-cn.md 变化

- 从 Python-only 重写为通用多语言规则（标题改为"通用注释与文档注释规则"）。
- Section 1-9 重编：适用范围、语言与格式、何时必写、必须说明什么、普通注释写法、类型与抑制指令、异常与清理、测试代码注释、禁止事项。
- 英文业务注释违规定义明确化。
- 分层检查要求：文件头、类/函数、测试证据三级分别检查。

## 3. 修改文件概要

本轮涉及文件 100+，以下为主要分组：

| 分组 | 文件数 | 操作类型 |
|---|---|---|
| ai_shared/rules/ (coding.md, python-docstring-cn.md, documentation.md, reporting.md, quality-gate.md, routing.md, testing.md, validation-routing.md) | 8 | 修改 |
| ai_shared/memory/ (project_tree.md, Whale_REQ_Ingest.md, Whale_REQ_SourceLab.md) | 3 | 修改 |
| ai_shared/agent_config/ (hooks, skills 重组) | ~40 | 新增/删除/移动 |
| .claude/ (agents, skills 重组, AGENTS.md, CLAUDE.md) | ~18 | 修改/删除 |
| src/whale/ingest/ (docstring 补全, QA-8, readback, 双节点 lease) | ~40 | 修改/新增 |
| src/whale/shared/source/ (readback 实现) | 5 | 修改 |
| tests/ (新增 handler/lease/readback/composition 测试) | ~15 | 新增/修改 |
| tools/source_lab/ (docstring, type:ignore, QA-8) | ~30 | 修改/新增 |

详细文件清单见 git status，完整违规清单见 `ingest_source_lab_docstring_violation_inventory_round5.md`。

## 4. 行为变化

- **QA-8 RunnerInfo 五种字段分离**：`declared_implementation_level`、`actual_implementation_level`、`actual_runtime_availability`、`fallback_reason`、`native_check_error`。从静态声明变为运行时可证伪，但 PROTOCOL_CAPABILITIES 全局静态 dict 未改为运行时检查。
- **Modbus 写入 readback**：write_single_register(FC06) 后 read_holding_registers(FC03) 验证。
- **IEC61850 写入 readback**：MMS write-then-read 验证。
- **双节点 lease 冲突**：使用真实 LeaseService + FencingTokenRepository + SQLite，替换 StubLeaseService。
- **WorkerRuntime handler 分发**：`_do_execute` 实现 `acquisition_job_handler`，asyncio.run() 桥接同步/异步。
- **规则体系**：注释与文档注释规则大幅细化，英文业务 docstring 明确为违规。

## 5. 检查与测试

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| `python -m compileall src/whale/ingest src/whale/shared/source tools/source_lab tests` | PASS | compile | 507 .py files verified |
| `ruff check src/whale/ingest/ src/whale/shared/source/` | PASS | lint | 0 new errors |
| `mypy src/whale/ingest/ src/whale/shared/source/` | PASS | type-check | 0 new issues |
| `pytest tests/unit/ -q` | PASS | test | 61+ passed, 0 failed |
| `pytest tests/unit/test_worker_runtime_do_execute.py -q` | 5 PASS | L1 | WorkerRuntime handler dispatch |
| `pytest tests/unit/test_acquisition_job_handler.py -q` | 8 PASS | L1 | AcquisitionJobHandler |
| `pytest tests/unit/test_dual_node_write_lease_conflict.py -q` | 7 PASS | L3 | 真实 SQLite + LeaseService + FencingTokenRepository |
| `pytest tests/unit/test_opcua_source_write_adapter.py -q` | 3 PASS | L2 | OPC UA readback contract |
| `pytest tests/unit/test_modbus_source_write_adapter.py -q` | 3 PASS | L2 | Modbus readback contract (FC03+FC06) |
| `pytest tests/unit/test_iec61850_source_write_adapter.py -q` | 3 PASS | L2 | IEC61850 readback contract (MMS write-then-read) |
| `pytest tests/unit/test_ingest_composition_injection.py -q` | 4 PASS | L1 | composition 注入完整性 |
| `pytest tests/unit/test_source_command_lease_release.py -q` | 4 PASS | L1 | lease 释放 |
| `pytest tests/unit/test_scheduler_job_routes.py -q` | 4 PASS | L1 | scheduler job 持久化 |
| `grep -R tools.source_lab src/whale/ingest` | PASS | gate | 无违规导入 |
| `pytest tools/source_lab/tests/access/test_protocol_production_readiness_gate.py -q` | 25 PASS (含 5 QA-8) | L3 | QA-8 RunnerInfo 验证 |
| `pytest tools/source_lab/tests/access/test_native_cmd_timeout.py -q` | 3 PASS | L1 | Native 超时 |

## 6. 证据与需求状态

| 条目 | 证据等级 | 状态 | 变化 | 说明 |
|---|---|---|---|---|
| I-FR-003 设备命令与写入控制 | L2 | 部分实现 | 提升 | Modbus/IEC61850 readback 从 NOT_IMPLEMENTED 提升到 L2 contract（各 3 tests） |
| I-FR-012 多节点 write/control lease 与 fencing | L3 | 部分实现 | 提升 | 双节点冲突从 StubLeaseService (L2) 提升到真实 SQLite + LeaseService + FencingTokenRepository (L3)，7 tests |
| I-SCR-003 写入控制安全边界 | L2 | 部分实现 | 提升 | 三协议 readback 均到 L2 contract |
| SL-FR-004 多协议 native runner 管理 | L3 | 部分实现 | PARTIAL | QA-8 RunnerInfo 5 字段分离 5 tests PASS；PROTOCOL_CAPABILITIES 仍静态高估，继续标 PARTIAL |
| I-FR-009 调度器与多节点任务分配 | L2 | 部分实现 | 持平 | WorkerRuntime handler dispatch L1/L2；真实设备采集仍 PENDING |
| I-TEST-001 分层测试 | L3 | 测试通过 | 持平 | 新增 15+ unit tests，门禁全部 PASS |

## 7. project_tree / ADR / 规则

- **project_tree**: 已更新。新增 6 个报告文件、1 个 hook 文件（comment-doc-gate.py）、1 个集成测试文件（test_ingest_dual_node_db_lease_e2e.py）；删除 3 个废弃 skill（feedback-archive, project-tree-read, report-archive）和 1 个废弃脚本（setup_shared_skills_link.sh）；skills 目录从 .md 重组为 SKILL.md 子目录格式。
- **ADR**: 无需新增。ADT-004 (production readiness gate) 已覆盖 QA-8 相关能力声明；PROTOCOL_CAPABILITIES 仍静态的问题可在下一轮决定是否需要单独 ADR。
- **规则**: coding.md 和 python-docstring-cn.md 已由 code-implementer 更新（见 2.1, 2.2 节摘要），本次由 project-steward 归档到本报告。

## 8. 剩余风险

### 8.1 docstring 治理 remaining inventory

| 类别 | 估算文件数 | 风险 |
|---|---|---|
| English module docstring（__init__.py + tools/source_lab） | ~350 | 大量简短英文描述需逐文件替换为中文；tools/source_lab 涉及密集协议缩写，翻译成本高 |
| API route handler 缺 docstring | ~40 | 需逐路由补充权限/审计/dry_run 语义，工作量大 |
| type:ignore 无解释（source_lab tools） | ~50 | 第三方库无 stub 导致；修复价值低于生产路径但合规要求仍存 |
| 缺 public 函数 docstring（adapter/sink 等） | ~15 | adapter emit/authorize 等方法需补中文 docstring |

不得将以上 remaining inventory 写成全量完成；不得将注释治理写成真实设备采集、readback E2E、双节点 DB E2E、7x24 或性能压测完成。

### 8.2 真实设备与生产验证

| 风险项 | 当前证据 | 风险等级 |
|---|---|---|
| WorkerRuntime 真实设备 handler 注册 | L1/L2（仅 simulator 路径） | 高 |
| Readback Modbus/IEC61850 | L2 contract（非真实设备） | 中 |
| 双节点写入冲突 E2E | L3（SQLite 单进程，非 PostgreSQL 多进程/多节点） | 中 |
| PROTOCOL_CAPABILITIES 静态高估 | QA-8 部分修复，全局 dict 仍静态 | 中 |
| 7x24 长期稳定 | 未执行 | 高 |
| 性能/压力测试 | 未执行（仅 performance profile 合成 benchmark） | 高 |

### 8.3 asyncio.run() 事件循环风险

WorkerRuntime 使用 `asyncio.run()` 每次创建新事件循环调用 handler。APScheduler 在线程中运行 job，`asyncio.run()` 在线程中创建新事件循环是标准实践，但每次创建/销毁有开销。长期高频率采集场景下需评估事件循环复用策略。

## 9. 下一步建议

1. **docstring 治理第 6 轮**：批量替换 ~350 English module docstring（__init__.py 优先生产路径），补 40 个 API route handler docstring。
2. **PROTOCOL_CAPABILITIES 改为运行时检查**：在下一轮将全局 dict 替换为 per-runner 运行时检查，消除静态高估风险。
3. **PostgreSQL 双节点真实多进程 E2E**：将当前 SQLite 单进程 L3 测试升级为 PostgreSQL 多独立进程版本。
4. **真实设备 handler 注册**：在生产路径注册真实 device handler，验证端到端采集闭环。
5. **Modbus/IEC61850 readback 真实设备验证**：在当前 L2 contract 基础上补充真实硬件/设备 smoke。
6. **长期稳定性测试**：安排 7x24 endurance 测试计划。
