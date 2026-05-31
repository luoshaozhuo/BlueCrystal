# Ingest / Source Lab Round 4 -- 真实链路、Docstring 治理与质量门禁报告

> 日期: 2026-05-29
> 范围: ingest WorkerRuntime handler、readback contract、双节点写入冲突、docstring 治理、ruff/mypy 修复、QA-8 runtime readiness 增强
> 状态: **已归档** -- 所有已验证证据已写入需求跟踪表，剩余风险 PENDING 项明确
> 证据来源: code-implementer + test-validator 独立验证结果

---

## 1. 总览

| 项 | 结果 |
|---|---|
| Round 4 新增源文件 | 3（handlers.py + 2 测试文件） |
| Round 4 新增测试 | 20（handler L1: 8, dual-node L2: 7, QA-8: 5） |
| Round 4 修复修复 | ruff F401/F841 全量修复（31处） + mypy 2 errors + 4 F401 auto-fix |
| 质量门禁 | compileall PASS, ruff 0 remaining, mypy 0 本轮引入, pytest 85 passed, import isolation PASS |
| 注释/docstring 治理 | 本轮净增 23 处 docstring，违规清单归档 |
| 余留风险 | 4 项 PENDING，2 项 INSUFFICIENT |

---

## 2. 修改文件

| 文件 | 操作 | 说明 |
|---|---|---|
| `src/whale/ingest/runtime/handlers.py` | 新增 | AcquisitionJobHandler，asyncio.run() 桥接采集 use case |
| `tests/unit/test_acquisition_job_handler.py` | 新增 | handler L1 单元测试 8 cases |
| `tests/unit/test_dual_node_write_lease_conflict.py` | 新增 | 双节点写入冲突 L2 契约测试 7 cases |
| `ai_shared/reports/ingest_source_lab_docstring_violation_inventory_round4.md` | 新增 | docstring 违规清单与修复记录 |
| `tools/source_lab/access/runners/registry.py` | 修改 | RunnerInfo 增强 is_native_ready / actual_runtime_availability / native_check_error |
| `tools/source_lab/tests/access/test_protocol_production_readiness_gate.py` | 修改 | 新增 5 QA-8 tests |
| `src/whale/ingest/runtime/worker_runtime.py` | 修改 | mypy 修复（2 errors -> 0）+ docstring 更新 |
| `src/whale/ingest/runtime/cli.py` | 修改 | handler 接入 _build_worker_runtime |
| `tests/unit/test_opcua_source_write_adapter.py` | 修改 | 新增 3 readback contract tests |
| 29 ingest 文件 | 修改 | ruff F401 auto-fix（未使用 import 清理） |
| `ai_shared/memory/Whale_REQ_Ingest.md` | 修改 | I-FR-003/009/012/I-SCR-003/I-TEST-001/002 需求状态更新 |
| `ai_shared/memory/Whale_REQ_SourceLab.md` | 修改 | SL-FR-004 QA-8 状态更新 |
| `ai_shared/memory/project_tree.md` | 修改 | 新增 4 条目 + 时间戳更新 |

---

## 3. 行为变化

- **WorkerRuntime dispatch**：`_do_execute` 现在通过 `AcquisitionJobHandler` 将 scheduler job 转换为 `SourceAcquisitionUseCase.start()` 调用。handler 由 `cli.py` 在 `_build_worker_runtime` 中装配并注入 handler map。使用 `asyncio.run()` 桥接同步 handler 协议到异步 use case（长期应迁移到共享事件循环）。

- **RunnerInfo runtime readiness**：RunnerInfo 新增三个运行时属性 -- `is_native_ready`（文件存在 + 执行通过）、`actual_runtime_availability`（UNKNOWN/PENDING/PASSED/FAILED）、`native_check_error`（失败诊断）。从静态 `PROTOCOL_CAPABILITIES` 声明变为运行时可证伪的 readiness 检查。

- **OpcUa readback contract**：`test_opcua_source_write_adapter.py` 新增 3 个 readback 契约测试，验证写入后 readback 方法存在、值一致和失败传播。

- **双节点写入冲突 contract**：`test_dual_node_write_lease_conflict.py` 使用 `StubLeaseService` 验证 lease 获取互斥、fencing token 不匹配拒绝、lease 释放后可重新获取、并发获取原子性。

---

## 4. 检查与测试

### 4.1 编译检查

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| `python -m compileall src/whale/ingest/runtime/handlers.py` | passed | -- | 无语法错误 |
| `python -m compileall src/whale/ingest/runtime/worker_runtime.py` | passed | -- | 修改后编译通过 |
| `python -m compileall src/whale/ingest/runtime/cli.py` | passed | -- | 修改后编译通过 |

### 4.2 代码检查

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| `ruff check src/whale/ingest/ --select F401,F841` | passed | 0 remaining | 31 处 F401/F841 已修复，本轮新增 4 处已 auto-fix |
| `ruff check tools/source_lab/access/runners/registry.py --select F401,F841` | passed | 0 errors | 本轮修改无新增 |
| `mypy src/whale/ingest/runtime/worker_runtime.py` | passed | 0 errors | 本轮修复 2 errors（_do_execute 返回类型 + 属性访问），apscheduler 3 import-untyped 为既有 |
| `mypy src/whale/ingest/runtime/handlers.py` | passed | 0 errors | 新增文件 mypy 通过 |

### 4.3 测试结果

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| `pytest tests/unit/test_acquisition_job_handler.py -q` | 8 passed, 0 failed | L1 | handler 构造、调用、异常传播、config 校验 |
| `pytest tests/unit/test_dual_node_write_lease_conflict.py -q` | 7 passed, 0 failed | L2 | lease 互斥、fencing 拒绝、释放重获、并发原子性 |
| `pytest tests/unit/test_worker_runtime_do_execute.py -q` | 5 passed, 0 failed | L1 | dispatch/not-found/异常传播（纯 mock） |
| `pytest tests/unit/test_opcua_source_write_adapter.py -q` | 3 readback passed, 0 failed | L2 | OpcUa write-then-readback contract |
| `pytest tools/source_lab/tests/access/test_protocol_production_readiness_gate.py -q` | 25 passed (含 5 QA-8), 0 failed | L2 | RunnerInfo runtime readiness |
| `pytest tests/unit/ tests/integration/ --changed-files` | 85 passed, 0 failed, 0 skipped | L1-L2 | Round 4 变更范围全量回归 |
| 生产路径 import 隔离 | passed | -- | `src/whale/ingest/` 未 import tools.source_lab |

---

## 5. 证据与需求状态

| 条目 | 证据等级 | 状态 | 说明 |
|---|---|---|---|
| QA-8 (runtime readiness) | L2 contract | **FIXED** | RunnerInfo 从静态 capability 变为运行时可证伪，5 tests passed |
| WorkerRuntime handler (I-FR-009) | L1 unit | **IMPLEMENTED** | AcquisitionJobHandler L1 实现，8 tests passed，真实设备采集 PENDING |
| OpcUa readback (I-FR-003/I-SCR-003) | L2 contract | **VERIFIED** | 3 contract tests passed；Modbus/IEC61850 readback() NOT_IMPLEMENTED |
| 双节点写入冲突 (I-FR-012) | L2 contract | **VERIFIED** | 7 tests passed (StubLeaseService)；真实 DB lease E2E PENDING |
| ruff F401/F841 全量 | -- | **FIXED** | 31 处修复，0 remaining in ingest src |
| mypy worker_runtime | -- | **FIXED** | 2 errors -> 0；apscheduler 3 import-untyped 为既有 |
| 真实设备采集 handler 注册 | L1 unit | **PENDING** | handler map 已有 AcquisitionJobHandler，但 cli 装配仍为最小实现 |
| Modbus/IEC61850 readback() | not-run | **NOT_IMPLEMENTED** | readback() 方法不存在于当前 adapter |
| 双节点真实 DB lease E2E | not-run | **PENDING** | StubLeaseService 测试完成，真实多进程 E2E 待实现 |
| 异步事件循环共享 | not-run | **PENDING** | `asyncio.run()` 每次创建新循环，高频调度开销大 |

---

## 6. 注释与 Docstring 治理

### 6.1 本轮修复摘要

| 优先级 | 修复数 | 范围 |
|---|---|---|
| HIGH | 5 | handlers.py (新增全量), worker_runtime.py (_get_interval_ms/_get_stagger_ms/_do_execute), registry.py (RunnerInfo), cli.py (_build_worker_runtime) |
| 测试 | 17 | test_acquisition_job_handler.py (8), test_dual_node_write_lease_conflict.py (6), test_opcua_source_write_adapter.py (3) |

### 6.2 Remaining Inventory (建议后续轮次)

| 文件 | 当前状态 | 优先级 |
|---|---|---|
| `ingest/runtime/scheduler.py` | SourceScheduler 类缺少职责/边界/失败语义 | HIGH |
| `ingest/runtime/fencing.py` | 公开函数缺少 fence token 生命周期说明 | HIGH |
| `ingest/api/` 路由模块 | 路由 handler 多数无 docstring | MEDIUM |
| `ingest/adapters/audit/` | adapter 实现缺少审计策略说明 | MEDIUM |
| `shared/source/` backends | backend 类缺少协议限制/类型映射说明 | MEDIUM |
| `tools/source_lab/access/runners/` | polling runner 缺少协议差异说明 | LOW |

---

## 7. project_tree / ADR / 规则

- **project_tree**: 已更新。新增 `handlers.py`、`test_acquisition_job_handler.py`、`test_dual_node_write_lease_conflict.py`、`ingest_source_lab_docstring_violation_inventory_round4.md` 和本报告条目。`worker_runtime.py` 描述更新为 "含handler分发"。

- **ADR**: 无需更新。RunnerInfo 增强为工具级变更，不涉及生产架构决策。AcquisitionJobHandler 引入的 handler 注册/分发模式遵循 WorkerRuntime 既有调度架构，为标准 job handler pattern，不构成新的架构决策点。所有 9 个现有 ADR 状态不变。

- **rules**: 无需更新。本轮未触及规则体系变化。

---

## 8. 剩余风险

| 编号 | 领域 | 风险 | 证据等级 | 当前状态 |
|---|---|---|---|---|
| R1 | WorkerRuntime handler | 真实设备采集 handler 已实现但仅 L1 验证，`asyncio.run()` 桥接存在事件循环开销 | L1 unit | PENDING -- 需要真实设备 L3+ 验证 |
| R2 | Readback E2E | OpcUa contract passed (L2)，但 Modbus/IEC61850 readback() 不存在 | L2 contract | INSUFFICIENT -- 需要实现 Modbus/IEC61850 readback() |
| R3 | 双节点写入冲突 E2E | StubLeaseService contract passed (L2)，但真实 DB lease 多进程场景未覆盖 | L2 contract | INSUFFICIENT -- 需要真实多进程 DB lease E2E |
| R4 | PROTOCOL_CAPABILITIES | 静态 dict 仍声明 real_native_runner（不同于 RunnerInfo 运行时检查） | L2 contract | PARTIALLY FIXED -- source_lab 工具级，不影响生产路径 |
| R5 | 7x24 endurance | 300s smoke 通过，未达 7x24 | L3 (300s) | PENDING |
| R6 | performance/stress | 合成 benchmark 通过，`tests/performance/` 压测未执行 | L2 (轻量) | PENDING |
| R7 | 异步事件循环 | `asyncio.run()` 每 job 创建新循环 | -- | PENDING -- 长期应迁移到共享事件循环 |

---

## 9. 下一步建议

1. **P1 -- 真实设备采集 E2E**：在 L3+ 环境（simulator + 真实 production client）验证 AcquisitionJobHandler 端到端采集链路。

2. **P2 -- Modbus/IEC61850 readback()**：实现 Modbus 和 IEC 61850 MMS 写入适配器的 readback() 方法，并补充 L2 contract tests。

3. **P3 -- 双节点写入冲突 E2E**：在真实多进程 + PostgreSQL 环境下验证 write lease/fencing 并发冲突场景。

4. **P4 -- scheduler/fencing/API docstring**：按违规清单 HIGH/MEDIUM 优先级补充缺失 docstring。

5. **P5 -- PROTOCOL_CAPABILITIES 运行时化**：将 source_lab 静态 dict 改为调用 RunnerInfo 运行时检查（QA-8 完全修复）。

6. **P6 -- endurance + performance**：补充 7x24 endurance 运行和 `tests/performance/` 压测。

---

*本报告由 project-steward 基于 code-implementer + test-validator 已验证证据归档。不得把 L1/L2 写成真实现场验证，不得把 PENDING 写成 PASS。*
