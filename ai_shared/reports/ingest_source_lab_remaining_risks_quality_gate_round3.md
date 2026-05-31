# Ingest / Source Lab 质量门禁 Round 3 — 余留风险归档与需求治理

> 报告日期: 2026-05-28
> 范围: Round 2 修复收口后余留风险 + Round 3 WorkerRuntime dispatch 测试 + SourceLab RunnerInfo RunnerInfo 语义增强
> 验证方法: project-steward 基于 code-implementer + test-validator 已验证证据归档
> 状态: **已归档** — 所有已验证证据已写入需求跟踪表，余留风险分类明确

---

## 1. 总览

| 类别 | 数量 | 说明 |
|------|------|------|
| Round 2 HIGH 修复 | 3 | QA-1, QA-2, QA-5 CONFIRMED FIXED |
| Round 2 MEDIUM 修复 | 4 | QA-3, QA-4, QA-7 CONFIRMED FIXED; QA-8 PARTIALLY FIXED |
| Round 2 LOW 修复 | 1 | QA-9 CONFIRMED FIXED (WorkerRuntime re-raise) |
| Round 3 新增测试 | 1 | `test_worker_runtime_do_execute.py` (5 passed, 纯 mock dispatch) |
| CI 总测试数 | 378 unit + 237 integration = 615 passed | 0 failed |

---

## 2. 余留风险矩阵

| 编号 | 领域 | 风险 | 证据等级 | 当前状态 | 阻塞项 |
|------|------|------|----------|----------|--------|
| R1 | WorkerRuntime `_do_execute` | 真实设备采集 handler 未注册 | L1 (纯 mock dispatch) | PENDING — docstring 明确标注 PENDING，单元测试只覆盖 dispatch/not-found/异常传播，不覆盖真实采集 | 需要实现 production-level handler 并接入 SourceAcquisitionUseCase |
| R2 | Readback E2E | 所有 readback 测试使用纯 mock | L1 (mock only) | INSUFFICIENT — `_execute_one` 的 readback 路径仅通过 mock 验证，生产 adapter 未实现 readback() | 需要协议级 readback E2E（OPC UA / Modbus / IEC 61850 MMS）|
| R3 | 双节点写入冲突 | 无完整双 WorkerRuntime E2E | L1 (contract only) | INSUFFICIENT — fencing 原子性已验证，但无双节点并行写入冲突 E2E | 需要双 WorkerRuntime + 真实 DB lease E2E |
| R4 | QA-8 PROTOCOL_CAPABILITIES | 静态 dict 仍声明 real_native_runner | L2 (日志/docstring 增强) | PARTIALLY FIXED — RunnerInfo RunnerInfo 提供运行时实施级别检查，但 PROTOCOL_CAPABILITIES 静态 dict 未改为运行时检查 | source_lab 工具级问题，不影响生产路径 |
| R5 | 7x24 endurance | 仅 300s smoke | L3 (300s smoke) | PENDING — endurance smoke 300s 通过，但未达 7x24 | 需要 7x24 endurance 运行与监控 |
| R6 | performance/stress | 轻量 load gate 通过 | L2 (轻量验证) | PENDING — 性能基线配置已就绪，合成 benchmark 通过，但 `tests/performance/` 压测未执行 | 需要 performance/stress 压测 |

---

## 3. 质量门禁结果

### 3.1 编译检查

| 检查项 | 结果 |
|--------|------|
| py_compile (`src/whale/ingest/runtime/worker_runtime.py`) | PASS |
| py_compile (`src/whale/ingest/runtime/write_lease.py`) | PASS |
| py_compile (`src/whale/ingest/runtime/fencing.py`) | PASS |

### 3.2 代码检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| ruff (`worker_runtime.py`) | 0 errors | 本轮清理了 3 个 unused import (Callable, Any, JobAssignment, RuntimeMode, NodeHeartbeat) |
| ruff (全量 src/whale/ingest/) | 10 F401/F841 | 全部既有，非本轮引入 |
| mypy (`worker_runtime.py`) | 2 errors | L463 `no-any-return` + `call-overload`，既有问题，非本轮引入 |
| mypy (全量 src/) | ~350 errors | 全部既有 |

### 3.3 测试结果

| 测试套件 | 数量 | 状态 |
|----------|------|------|
| `tests/unit/` | 378 passed | 0 failed / 0 skipped |
| `tests/integration/` | 237 passed | 0 failed / 0 skipped |
| Round 3 新增: `test_worker_runtime_do_execute.py` | 5 passed | handler dispatch/not-found/异常传播/空字典/多类型 |
| Round 2 新增: `test_ingest_composition_injection.py` | 4 passed | QA-1 注入完整性 |
| Round 2 新增: `test_source_command_lease_release.py` | 4 passed | QA-2 lease release |
| Round 2 新增: `test_scheduler_job_routes.py` | 4 passed | QA-5 stagger 持久化 |
| Round 2 新增: `tools/source_lab/tests/access/test_native_cmd_timeout.py` | 3 passed | QA-7 超时 |

### 3.4 生产路径隔离

| 检查项 | 结果 |
|--------|------|
| `src/whale/ingest/` import tools.source_lab | PASS (0 污染) |
| `tools/source_lab` 未进入生产路径 | PASS |

---

## 4. 需求跟踪表更新摘要

| 需求 | 更新内容 |
|------|----------|
| I-FR-009 | 新增 `test_worker_runtime_do_execute.py` 证据 (5 passed); gap 明确标注 `_do_execute` 真实采集 PENDING |
| I-TEST-001 | 新增 `test_worker_runtime_do_execute.py` 证据; unit 计数从 355 更新为 378 passed |
| I-TEST-002 | 新增 `test_worker_runtime_do_execute.py` 证据; 总测试数从 592 更新为 597 passed |
| SL-FR-004 | Round 2 已更新: 含 QA-8 PARTIALLY FIXED 说明 |

### 证据等级标注

以下需求状态为「部分实现 / L2」，证据等级必须如实标注：

| 需求 | 证据等级 | 主要差距 |
|------|----------|----------|
| I-FR-003 | **L2 (mock contract only)** — readback E2E 仅 mock 验证，生产 adapter 未实现 readback() | 协议级 readback E2E |
| I-FR-012 | **L2 (mock contract only)** — fencing/finally/lease 已验证，但无双节点写入冲突 E2E | 双节点写入冲突与协议级 readback |
| I-SCR-003 | **L2 (mock contract only)** — 写入安全边界已验证，但真实 write/control 默认关闭 | 真实写控制与 readback E2E |

---

## 5. project_tree / ADR 更新

### project_tree

| 文件 | 操作 |
|------|------|
| `tests/unit/test_worker_runtime_do_execute.py` | 新增条目 |
| `ai_shared/reports/ingest_source_lab_arch_security_audit_review_round1.md` | 新增条目 |
| `ai_shared/reports/ingest_source_lab_arch_security_audit_review_round2_fix_closure.md` | 新增条目 |
| `ai_shared/memory/project_tree.md` 头部时间戳 | 更新至 Round 3 |

### ADR

本轮确立的变更：
- **RunnerInfo RunnerInfo / actual_implementation_level**: source_lab 工具级变更，不涉及生产架构决策，不需要 ADR。
- **WorkerRuntime 异常传播策略 re-raise**: 属于 bug fix (QA-9)，非设计决策，不需要 ADR。

---

## 6. 收口结论

Round 3 质量门禁归档完毕：

1. **所有 HIGH/MEDIUM Round 2 缺陷已修复并验证**：QA-1/2/5 CONFIRMED FIXED, QA-3/4/7/9 CONFIRMED FIXED, QA-8 PARTIALLY FIXED（工具级）。
2. **WorkerRuntime `_do_execute` PENDING**：dispatch 路径已验证（5 tests，纯 mock），但真实设备采集 handler 未注册。需求跟踪表标记 PENDING，不得高估。
3. **Readback E2E 与双节点写入冲突 INSUFFICIENT**：需求状态已标注为 L2 (mock contract only)，不得写为真实现场验证。
4. **RunnerInfo RunnerInfo 语义变化**：下轮建议将 PROTOCOL_CAPABILITIES 静态 dict 改为运行时检查（QA-8 完全修复）。
5. **质量门禁结果归档**：ruff 0 new errors / mypy 350 existing / py_compile PASS / pytest 378+237 passed / production import isolation PASS。

---

*本报告由 project-steward 基于 code-implementer (修复) + test-validator (独立验证) 的已验证证据归档。*
