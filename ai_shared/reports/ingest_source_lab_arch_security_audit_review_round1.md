# Ingest / Source Lab 架构与安全审计审查报告 Round 1

> 审查日期: 2026-05-28
> 审查范围: ingest 写入指令流、租约守卫、调度持久化、Native 运行器、WorkerRuntime
> 审查方法: 人工代码审查 (code-implementer) + 独立验证 (test-validator) + 测试可靠性评估
> 状态: **未收口** — 存在 3 HIGH 缺陷及多项设计风险，建议降级后再评估

---

## 1. 总览

| 类别 | 数量 | 级别分布 |
|------|------|----------|
| 真实代码缺陷 | 6 | HIGH: 3, MEDIUM: 1, LOW: 2 |
| 设计风险 | 2 | MEDIUM: 2 |
| 测试证据不足 | 4 | 关联 QA-1, QA-2, QA-5, QA-7 |
| 文档/需求高估 | 0 | — |

审查共发现 **8 项被双确认的问题**，其中 3 项 HIGH、3 项 MEDIUM、2 项 LOW。原 code-implementer 提出的 QA-6（dry_run 缺少审计事件）经 test-validator 独立验证后 **驳回**，实际代码已 emit DRY_RUN 审计与指标。

---

## 2. 真实代码缺陷

### QA-1 (HIGH) — composition.py 未注入 audit / metrics / write_lease 端口

| 项目 | 内容 |
|------|------|
| 文件 | `src/whale/ingest/composition.py` L373-375 |
| 验证状态 | code-implementer 确认 / test-validator 确认 |
| 描述 | `SourceCommandUseCase` 构造时未传递 `audit_port`、`metrics_port`、`write_lease_port`，导致运行时这三个端口为 None |
| 影响 | 写入指令流缺失审计、指标、租约守卫，可能造成并发写入冲突、不可审计、不可观测 |
| 跟踪 | 现有单元测试绕过 composition 直接构造 use case，未发现该问题 |
| 建议 | **必须修复**：composition.py 中补充注入；补充 composition 级集成测试覆盖注入完整性 |

### QA-2 (HIGH) — SourceCommandUseCase readback 前 emit SUCCESS；异常路径不释放 lease

| 项目 | 内容 |
|------|------|
| 文件 | `src/whale/ingest/usecases/source_command_use_case.py` |
| 子项 Q2-A | L199-215 `emit SUCCESS` 实际写入在 L216-254 readback 之前发出 |
| 子项 Q2-B | L145-167 precheck 在 try 块外 (L169)，raise 不释放 lease |
| 子项 Q2-C | L218-226 readback raise 跳出 try 块 (L170-197)，lease 不释放 |
| 验证状态 | code-implementer 确认 / test-validator 确认三个子项 |
| 影响 | 错误地将"写入中"报告为成功；precheck/readback 异常导致租约泄漏，最终 blocking 其他写入 |
| 跟踪 | 测试 `test_source_command_write_lease_guard.py` 使用纯 mock 不覆盖 lease release 失败路径 |
| 建议 | **必须修复**：(1) SUCCESS 推迟到 readback 验证后；(2) precheck 移入 try 块或用 finally 释放；(3) readback 异常确保 release；(4) 补充异常路径集成测试 |

### QA-5 (HIGH) — create_scheduler_job stagger_offset_ms 更新无持久化

| 项目 | 内容 |
|------|------|
| 文件 | `src/whale/ingest/runtime/scheduler.py` |
| 描述 | `create_scheduler_job` 中使用一个 session (Session A) 查询 row，row 变为 detached 后在 Session B 中修改 `stagger_offset_ms` 但不做 `merge` / `add`，导致修改不被持久化 |
| 验证状态 | code-implementer 确认 / test-validator 确认 Session A vs B 混用 |
| 影响 | 每次调度任务创建后的 stagger 偏移量修改不生效，重启后丢失 |
| 跟踪 | 当前无任何测试端到端覆盖 `create_scheduler_job` API（test-validator 确认） |
| 建议 | **必须修复**：统一 session，或使用 `session.merge()`；补充 create_scheduler_job 端到端集成测试 |

### QA-4 (LOW) — FencingTokenRepository.next_value 并发非原子递增

| 项目 | 内容 |
|------|------|
| 文件 | `src/whale/ingest/runtime/fencing.py` |
| 描述 | `next_value` 实现为 SELECT 后 UPDATE（TOCTOU 模式），非原子递增，并发场景可能产生重复 fencing token |
| 验证状态 | code-implementer 确认 / test-validator 确认 |
| 影响 | 低概率产生 fence 冲突（基于数据库行锁/序列才是正确方案） |
| 建议 | 改为数据库序列（PostgreSQL `SERIAL` / `SEQUENCE`）或 upsert 原子操作 |

### QA-7 (MEDIUM) — NativeCmdCapacityRunner 无限阻塞 stdout 无超时

| 项目 | 内容 |
|------|------|
| 文件 | `tools/source_lab/runners/native_cmd.py` |
| 描述 | `_read_output_lines` L86 `for raw_line in proc.stdout` 不设超时；subprocess 若异常 hang 住将永久阻塞 |
| 验证状态 | code-implementer 确认 / test-validator 确认 |
| 影响 | source_lab 工具级问题，不直接进入生产路径。但可能导致 CI 任务 hung |
| 跟踪 | `test_native_process_protocol.py` 使用 StringIO fake，不覆盖真实 subprocess blocking read |
| 建议 | 使用 `select` / `threading` 或 `asyncio.wait_for` 添加超时机制；补充 subprocess timeout 集成测试 |

### Extra (LOW) — WriteLeaseService.acquire 成功路径潜在 None 解引用

| 项目 | 内容 |
|------|------|
| 文件 | `src/whale/ingest/runtime/write_lease.py` L63 |
| 描述 | 成功路径上存在潜在 None 解引用 |
| 验证状态 | test-validator 独立发现并确认 |
| 影响 | 特定条件可能引发 AttributeError |
| 建议 | 修复 None 检查或提前守卫 |

---

## 3. 设计风险

### QA-3 (MEDIUM) — WriteLeaseService.acquire 在 requested_fencing_token 缺失时绕过旧主防护

| 项目 | 内容 |
|------|------|
| 文件 | `src/whale/ingest/runtime/write_lease.py` |
| 描述 | same-holder reconnection 场景下，fencing 弱保护：若 `requested_fencing_token` 缺失，绕过旧主防护直接 acquire |
| 验证状态 | code-implementer 确认 / test-validator 确认 |
| 影响 | 故障切换重连时可能产生写入冲突 |
| 建议 | 在 acquire 逻辑中，即使 same-holder 也校验 token 有效性；或要求 caller 必须提供 token |

### QA-9 (MEDIUM) — WorkerRuntime 吞 handler 异常不外抛

| 项目 | 内容 |
|------|------|
| 文件 | `src/whale/ingest/runtime/worker_runtime.py` L349-364 |
| 描述 | `catch Exception` 后记录 metric/audit 但不 re-raise |
| 验证状态 | code-implementer 确认 / test-validator 确认有 metric/audit 记录 |
| 影响 | APScheduler 不会感知 handler 失败，无法触发 retry/failover；上游 caller 收到静默成功。当前有观测能力但无传播机制 |
| 建议 | 评估是否需要 re-raise（或委托给 APScheduler 的异常处理机制）；若自行处理，确保 caller 可感知 |

### QA-8 (MEDIUM) — registry 在 native 不可用时 silent fallback 但仍标 real_native_runner

| 项目 | 内容 |
|------|------|
| 文件 | `tools/source_lab/runners/registry.py` L941-947 |
| 描述 | native 运行器不可用时 silent fallthrough，但 capabilily 仍固定声明 `real_native_runner` |
| 验证状态 | code-implementer 确认 / test-validator 确认 |
| 影响 | source_lab 工具级问题。上层调用者信任 capabilily 字段判断能力，可能误以为 native 可用 |
| 建议 | 运行时检查 native 可用性并更新 capabilily 声明，或 raise 明确错误 |

---

## 4. 被驳回项

| 原问题 | 级别 | 驳回原因 |
|--------|------|----------|
| QA-6: dry_run 缺少审计事件 | LOW | test-validator 独立验证确认 `source_command_use_case.py` L79-83 已 emit DRY_RUN audit/metric 事件 |

---

## 5. 测试证据不足清单

以下问题因测试覆盖缺失，建议修复后补充测试再更新需求状态：

| 关联缺陷 | 测试缺口 | 现有测试 | 建议 |
|----------|----------|----------|------|
| QA-1 | composition 注入完整性 | `test_source_command_use_case.py` 绕过 composition 直接构造 | 新增 composition 级注入验证测试 |
| QA-2 | lease release 在异常路径 | `test_source_command_write_lease_guard.py` 纯 mock，不覆盖失败路径 | 新增 precheck/readback 异常 → lease 释放 集成测试 |
| QA-5 | create_scheduler_job 端到端 | 无任何测试覆盖该 API | 新增 create_scheduler_job 全链路集成测试（含序列化验证） |
| QA-7 | subprocess stdout 超时 | `test_native_process_protocol.py` StringIO fake | 新增真实 subprocess hang → timeout 测试 |

---

## 6. 建议降级/待修复后更新清单

以下项在修复前建议**暂不更新需求跟踪状态**（已列在 Whale_REQ_Ingest.md / Whale_REQ_SourceLab.md 中的相关条目应标注 pending-fix）：

| 需求条目（建议） | 关联问题 | 建议处理 |
|------------------|----------|----------|
| 写入指令用例 - 审计完整性 | QA-1, QA-2 | 待注入和异常释放修复后更新 |
| 写入租约守卫 - 冲突保护 | QA-1, QA-2, QA-3 | 待 fencing 修复 + lease 释放修复后更新 |
| 调度作业持久化 | QA-5 | 待 session 修复后更新 |
| Native 运行器可靠性 | QA-7, QA-8 | 待超时机制 + 能力声明修复后更新 |
| WorkerRuntime 异常处理 | QA-9 | 待评估修复方向后更新 |

---

## 7. 剩余风险总结

1. **生产路径 3 个 HIGH 缺陷**：composition 注入缺失、SUCCESS 时机错误 + lease 泄漏、调度持久化丢失 — 直接影响写入正确性和可靠性，建议优先修复。
2. **设计争议 2 项**：fencing 弱保护、WorkerRuntime 吞异常 — 需架构决策是否调整行为。
3. **测试缺口 4 处**：当前纯 mock/unit 级测试结构无法暴露上述 HIGH 缺陷，建议补充 composition 级集成测试和异常路径集成测试。
4. **结果有效性**：审查基于代码静态分析和测试验收，未进行运行时故障注入或压力测试。

---

## 8. 下一步建议

1. **修复 HIGH 缺陷** (QA-1, QA-2, QA-5) 优先执行，由 code-implementer 处理。
2. **补充测试缺口**，由 test-validator 独立验证。
3. **修复后执行 `requirement-trace`** 更新需求跟踪表。
4. **考虑 ADR**：若 QA-3（fencing 弱保护）、QA-9（WorkerRuntime 吞异常）需长期架构决策，宜新增 ADR。
5. **此报告归档**后，下一轮审查宜聚焦 production-readiness gate 覆盖和 failover 场景。

---

*本报告由 project-steward 基于 code-implementer + test-validator 的已验证证据归档。*
