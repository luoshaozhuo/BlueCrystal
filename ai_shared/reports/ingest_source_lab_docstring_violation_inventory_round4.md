# Ingest / Source Lab docstring 违规清单 Round 4

> 报告日期: 2026-05-29
> 范围: src/whale/ingest, src/whale/shared/source, tools/source_lab, tests
> 依据规则: ai_shared/rules/python-docstring-cn.md, ai_shared/rules/coding.md Section 7

## Round 4 已修复

| 文件 | 修复内容 | 类型 |
|------|----------|------|
| `worker_runtime.py` | `_get_interval_ms` / `_get_stagger_ms` 补充 Returns/边界说明 | docstring |
| `handlers.py` (新增) | `AcquisitionJobHandler` 完整 docstring（职责、局限、参数、Raises） | docstring |
| `handlers.py` (新增) | `_build_request_from_config` 和所有 helper 函数 docstring | docstring |
| `registry.py` | `RunnerInfo` 新增 `actual_runner`、`actual_runtime_availability` 属性及 docstring | docstring |
| `cli.py` | `_build_worker_runtime` 新增 Args/Returns docstring | docstring |
| `test_protocol_production_readiness_gate.py` (新增) | 4 个新测试附带完整 docstring | 测试 docstring |
| `test_acquisition_job_handler.py` (新增) | 全文件 docstring + 8 tests with docstrings | 测试 docstring |
| `test_dual_node_write_lease_conflict.py` (新增) | 全文件 docstring + 6 tests with docstrings | 测试 docstring |
| `test_opcua_source_write_adapter.py` (修改) | 新增 readback 测试类及 3 tests with docstrings | 测试 docstring |

## 高优先级 PENDING (ingest runtime/usecase/adapter/API/lease/fencing/audit)

以下文件当前无或缺少关键 docstring，应在后续轮次补充：

| 文件 | 当前状态 | 优先级 |
|------|----------|--------|
| `ingest/runtime/scheduler.py` | `SourceScheduler` 类缺少职责/边界/失败语义说明 | HIGH |
| `ingest/runtime/fencing.py` | 公开函数缺少 fence token 生命周期说明 | HIGH |
| `ingest/api/` 路由模块 | 路由 handler 函数多数无 docstring | MEDIUM |
| `ingest/adapters/audit/` | adapter 实现缺少审计策略说明 | MEDIUM |
| `ingest/usecases/source_command_use_case.py` | 公开方法缺少完整的 side effect/concurrency 说明 | MEDIUM |

## 中优先级 PENDING (shared/source)

| 文件 | 当前状态 | 优先级 |
|------|----------|--------|
| `shared/source/modbus/backends/` | backend 类缺少协议限制说明 | MEDIUM |
| `shared/source/iec61850/backends/` | MMS/Report 后端缺少 MMS 类型映射说明 | MEDIUM |
| `shared/source/opcua/backends/` | open62541 后端缺少 namespace 处理说明 | MEDIUM |

## 低优先级 PENDING (source_lab, tests)

| 范围 | 当前状态 | 优先级 |
|------|----------|--------|
| `tools/source_lab/access/runners/` 各 runner | polling runner 缺少协议差异说明 | LOW |
| `tests/` 既有 mock 测试 | 部分 mock 测试未标注证据等级 | LOW |

## 修复策略

- **第 1 层**（本轮已完成）：ingest runtime/usecase/adapter 关键路径（handlers, worker_runtime, RunnerInfo, composition）
- **第 2 层**（建议后续）：scheduler, fencing, API 路由, audit adapter
- **第 3 层**（建议后续）：shared/source backend, source_lab runner
- **第 4 层**（建议后续）：tests 证据等级标注

## 违规统计

| 范围 | 公开类/函数总数(估算) | 缺少 docstring(估算) | 本轮修复 |
|------|----------------------|---------------------|----------|
| ingest runtime/usecase | ~45 | ~15 | 5 |
| ingest api/adapter | ~120 | ~40 | 1 |
| shared/source | ~40 | ~20 | 0 |
| source_lab | ~80 | ~30 | 1 |
| tests | ~200 | ~60 | 17 |

本轮净增 docstring: 23 处（新增文件 + 既有文件补充）。
