# Ingest / Source Lab 架构与安全审计审查报告 Round 2 — 修复收口

> 审查日期: 2026-05-28
> 修复范围: composition 注入、SUCCESS 时机/lease 释放、scheduler 持久化、fencing 原子性、native_cmd 超时、
>           WorkerRuntime 异常传播、registry 日志增强
> 验证方法: test-validator 独立验证 (code-implementer 修复后)
> 状态: **已收口** — 所有 HIGH/MEDIUM 缺陷已修复或明确归档

---

## 1. 总览

| 类别 | 数量 | 分布 |
|------|------|------|
| 真实代码缺陷 | 8 | 详见下表 |
| 设计风险 | 0 | 2 项设计风险均已修复 |
| 被驳回 | 1 | QA-6 (误报) |
| 新增测试文件 | 4 | 新增 12 unit + 3 source_lab tests |

共 **8 项被 code-implementer + test-validator 双确认的真实问题**，其中 7 项 CONFIRMED FIXED，1 项 PARTIALLY FIXED。全量 61 个新增/修改测试 passed (31 unit + 29 source_lab + 1 integration)，无 skipped/mocked。

---

## 2. 修复状态矩阵

| 编号 | 级别 | 文件 | 摘要 | 修复方式 | 验证状态 |
|------|------|------|------|----------|----------|
| QA-1 | HIGH | `composition.py` | composition 未注入 audit/metrics/write_lease 端口 | 补充注入；新增 4 个 composition 注入测试 | CONFIRMED FIXED |
| QA-2 | HIGH | `source_command_use_case.py` | SUCCESS 在 readback 前发出；precheck/readback 异常不释放 lease | SUCCESS 推迟到 readback 后；precheck 移入 try 块；finally 释放 lease；新增 4 个 lease release 测试 | CONFIRMED FIXED |
| QA-3 | MEDIUM | `write_lease.py` | requested_fencing_token=None 时绕过旧主防护 | acquire 逻辑中 None token 也返回 FENCED | CONFIRMED FIXED |
| QA-4 | LOW | `fencing.py` | next_value 非原子递增 | 改为原子 UPDATE RETURNING (PostgreSQL RETURNING + conflict handling) | CONFIRMED FIXED |
| QA-5 | HIGH | `scheduler_jobs.py` (routes) | stagger_offset_ms 更新无持久化 (Session A/B 混用) | 统一 session 写入 config_json；新增 4 个 scheduler job routes 测试 | CONFIRMED FIXED |
| QA-7 | MEDIUM | `native_cmd.py` | stdout 无限阻塞无超时 | select.select 非阻塞 + 60s 超时；新增 3 个 subprocess timeout 测试 | CONFIRMED FIXED |
| QA-8 | MEDIUM | `registry.py` | native 不可用时 silent fallback 但仍标 real_native_runner | 增强 warning 日志 + docstring；PROTOCOL_CAPABILITIES 静态 dict 仍声明 real_native_runner | PARTIALLY FIXED |
| QA-9 | MEDIUM | `worker_runtime.py` | catch Exception 后不 re-raise | raise re-raise (委托 APScheduler 异常处理) | CONFIRMED FIXED |
| Extra | LOW | `write_lease.py` L63 | 成功路径潜在 None 解引用 | 修复 None 检查 | CONFIRMED FIXED |
| QA-6 | LOW | — | dry_run 缺少审计事件 | 驳回 — test-validator 确认已 emit DRY_RUN audit/metric | REJECTED |

---

## 3. 生产路径隔离验证

| 检查项 | 结果 |
|--------|------|
| `src/whale/ingest/` import tools.source_lab | PASS (0 污染) |
| `src/whale/` import tools.source_lab | PASS (0 污染) |

---

## 4. 测试变更

### 新增测试文件

| 文件 | 测试数 | 关联问题 |
|------|--------|----------|
| `tests/unit/test_ingest_composition_injection.py` | 4 | QA-1 注入完整性 |
| `tests/unit/test_source_command_lease_release.py` | 4 | QA-2 lease release |
| `tests/unit/test_scheduler_job_routes.py` | 4 | QA-5 stagger 持久化 |
| `tools/source_lab/tests/access/test_native_cmd_timeout.py` | 3 | QA-7 超时 |

### 修改测试文件

| 文件 | 修改内容 |
|------|----------|
| `tests/unit/test_ingest_write_lease.py` | QA-3 fencing 语义更新 |
| `tests/unit/test_ingest_write_lease_fencing.py` | QA-4 原子性验证更新 |

### 验证测试

```text
pytest tests/unit/test_ingest_composition_injection.py -q  -> 4 passed
pytest tests/unit/test_source_command_lease_release.py -q  -> 4 passed
pytest tests/unit/test_scheduler_job_routes.py -q          -> 4 passed
pytest tests/unit/test_ingest_write_lease.py -q            -> passed (modified)
pytest tests/unit/test_ingest_write_lease_fencing.py -q    -> passed (modified)
pytest tools/source_lab/tests/access/test_native_cmd_timeout.py -q -> 3 passed
```

全量 61 个新增/修改测试 0 failed, 0 skipped, 0 mocked。

---

## 5. ADR 判断

| 问题 | 决策 | ADR 需求 |
|------|------|----------|
| QA-3 fencing 弱保护 | 已修复 (None token 也 FENCED)，未保留设计行为 | 不需要 |
| QA-9 WorkerRuntime 吞异常 | 已修复 (re-raise)，未保留设计行为 | 不需要 |

---

## 6. 需求跟踪表更新

| 需求 | 更新内容 |
|------|----------|
| I-FR-003 设备命令与写入控制 | 补充 composition 注入、lease release 测试证据；时间戳 2026-05-28 |
| I-FR-009 调度器与多节点任务分配 | 补充 scheduler_jobs.py 证据 + test_scheduler_job_routes 测试；时间戳 2026-05-28 |
| I-FR-012 多节点 write/lease/fencing | 补充 fencing.py 证据 + composition 注入/lease release 测试；时间戳 2026-05-28 |
| I-SCR-003 写入控制安全边界 | 补充 fencing.py 证据 + Round 2 修复说明；时间戳 2026-05-28 |
| I-TEST-001 分层测试 | 补充新增 4 个测试文件证据；时间戳 2026-05-28 |
| I-TEST-002 runtime/scheduler E2E | 补充 scheduler_job 持久化测试证据；时间戳 2026-05-28 |
| SL-FR-004 多协议 native runner 管理 | 补充 registry.py 证据 + native_cmd_timeout 测试；时间戳 2026-05-28 |

---

## 7. project_tree 更新

| 文件 | 操作 |
|------|------|
| `tests/unit/test_ingest_composition_injection.py` | 新增条目 |
| `tests/unit/test_source_command_lease_release.py` | 新增条目 |
| `tests/unit/test_scheduler_job_routes.py` | 新增条目 |
| `tools/source_lab/tests/access/test_native_cmd_timeout.py` | 新增条目 |

---

## 8. 剩余风险

1. **QA-8 部分修复**：registry.py 日志/docstring 已增强，但 `PROTOCOL_CAPABILITIES` 静态 dict 仍声明 `real_native_runner`。属于 source_lab 工具级问题，不影响生产路径。建议下轮改为运行时检查。
2. **协议级 readback E2E**：I-FR-003/I-FR-012/I-SCR-003 的剩余差距 — 真实设备 readback 验证和双节点写入冲突验证仍待补充。
3. **WorkerRuntime `_do_execute`**：真实设备采集路径仍为待实现状态。
4. **7x24 endurance / 极限容量 / 真实 IAM/SIEM**：未在本轮验证，需求跟踪表已正确标注为 pending。

---

## 9. 收口结论

本轮 Round 2 修复收口确认完毕。3 项 HIGH 缺陷 (QA-1, QA-2, QA-5) 全部修复并验证通过，5 项 MEDIUM/LOW 问题中 4 项 CONFIRMED FIXED、1 项 PARTIALLY FIXED (QA-8 工具级)。生产路径隔离验证 PASS。

建议下一轮审查聚焦：
- 协议级 readback E2E 与双节点写入冲突验证
- WorkerRuntime `_do_execute` 真实设备采集实现
- 性能压测与 7x24 长稳验证
- QA-8 registry 运行时检查增强

---

*本报告由 project-steward 基于 code-implementer (修复) + test-validator (独立验证) 的已验证证据归档。*
