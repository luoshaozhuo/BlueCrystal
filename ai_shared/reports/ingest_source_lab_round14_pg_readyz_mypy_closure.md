# Round 14 PG E2E 与 compose readyz 阻塞项修复 + source_lab mypy 第二阶段 -- 文档收口

> 日期: 2026-05-30
> 范围: ingest PG E2E migration 修复、compose readyz E2E 验证、source_lab mypy phase 2 收口、需求表描述更新
> 状态: 三个阻塞项已收口；ingest 未达到 production-ready；source_lab 未达到 fully-closed tool-ready
> 证据来源: code-implementer + test-validator Round 14 handoff 验证

## 1. 总览

| 项 | 结果 |
|---|---|
| PG E2E migration gap | 已修复（SQLite L3 7/7, PG L4 3/4, 1 pre-existing concurrency bug） |
| compose readyz E2E | 8/8 组件聚合 PASS（L4），敏感数据脱敏正确，degraded 语义正确 |
| source_lab mypy phase 2 | 非测试源码 0 errors / 107 files（4 历史错误文件清零） |
| field readback 状态 | WRITE_ENABLED=false, CONFIRM_FLAG=false 双重门确认，无 L5 伪造 |
| 需求表准确度 | I-READY-006、SL-READY-001 描述已更新至最新证据 |

## 2. 修改文件

| 文件 | 操作 | 说明 |
|---|---|---|
| `scripts/run_ingest_pg_lease_fault_injection.sh` | 修改 | 添加 Alembic migration 步骤（migration gap 修复） |
| `scripts/run_ingest_compose_readyz_e2e.sh` | 修改 | HTTP_PROXY 修复 + migration + Kafka 等待超时 120s->240s |
| `tests/integration/test_ingest_dual_node_db_lease_e2e.py` | 修改 | 防御性 migration（每条测试前确保 schema 就绪） |
| `tools/source_lab/access/runtime/dynamic_cli.py` | 修改 | mypy 14 errors -> 0（isinstance 收窄 + 局部变量显式标注） |
| `tools/source_lab/protocols/opcua/simulator.py` | 修改 | mypy 1 error -> 0（_NoopHandler 类替代 None） |
| `tools/source_lab/protocols/registry.py` | 修改 | mypy 1 error -> 0（Callable[..., T] 替代 type） |
| `tools/source_lab/access/providers/simulator.py` | 修改 | mypy 1 error -> 0（值类型从 object 收窄为联合类型） |
| `ai_shared/reports/source_lab_mypy_phase2_closure_round14.md` | 新增 | source_lab mypy 第二阶段治理明细报告 |
| `ai_shared/memory/Whale_REQ_Ingest.md` | 修改 | I-READY-002/006/007 需求状态更新 |
| `ai_shared/memory/Whale_REQ_SourceLab.md` | 修改 | SL-READY-001/003 需求状态更新 |
| `ai_shared/memory/project_tree.md` | 修改 | 新增 Round 14 报告文件条目 |

## 3. 行为变化

- PG E2E 测试和脚本现包含明确的 Alembic migration 步骤，不再依赖外部 DB 初始化
- compose readyz E2E 等待超时从 120s 提升到 240s（Kafka/Redis 启动较慢的 CI 环境兼容）
- compose readyz 敏感数据脱敏正确（`WHALE_DATABASE_URL`、`KAFKA_BOOTSTRAP_SERVERS` 等不泄露真实值）
- source_lab 4 个关键文件 mypy 类型安全，无 Any 滥用

## 4. 检查与测试

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| `mypy tools/source_lab --exclude 'tests/'` | passed | L2 | 0 errors / 107 source files |
| `scripts/run_ingest_compose_readyz_e2e.sh` | passed | L4 | 8/8 组件聚合 PASS；degraded 语义正确；脱敏正确 |
| `pytest tests/integration/test_ingest_dual_node_db_lease_e2e.py -q --db=sqlite` | 7/7 passed | L3 | SQLite dual-node lease E2E |
| `pytest tests/integration/test_ingest_dual_node_db_lease_e2e.py -q --db=postgresql` | 3/4 passed | L4 | PG: acquire/release/concurrent_read OK |
| `scripts/run_ingest_pg_lease_fault_injection.sh` | failed (partial) | L4 | pre-existing concurrency bug: fencing_token INSERT race (IntegrityError) |
| `pytest tests/unit/test_ingest_write_security_profile.py` | passed | L1 | WRITE_ENABLED=false, CONFIRM_FLAG=false 确认 |

## 5. 证据与需求状态

| 条目 | 证据等级 | 状态 | 说明 |
|---|---|---|---|
| I-READY-006 (PG migration gap) | L4 | partial (已修复) | PG migration gap 已修复；SQLite 7/7；PG 3/4；1 pre-existing fence_token concurrency bug |
| I-READY-002 (compose readyz) | L4 | 已验证 | 8/8 组件聚合 E2E PASS；redis/adapter 在 compose 中 not_ready（测试环境预期） |
| SL-READY-001 (source_lab mypy phase 2) | L3 | 部分实现 | 非测试源码 0 errors；全量（含测试）172 errors / 27 test files 未治理 |
| SL-READY-003 (证据边界) | L2/L3 | 部分实现 | 4 关键文件 mypy 清零；source_lab PASS 仍不得外推为 ingest production-ready |
| I-READY-005 (field readback) | L2/L3 | 部分实现 | WRITE_ENABLED=false, CONFIRM_FLAG=false 确认；无 L5 伪造 |

## 6. project_tree / ADR / 规则

- project_tree: 已更新（新增 Round 14 报告条目，header 日期更新）
- ADR: 无需更新（本轮不涉及架构/接口契约/schema/部署策略变化）
- rules: 无需更新（本轮不涉及规则体系变化）

## 7. 剩余风险

- **fencing_token 并发 INSERT race (Pre-existing, IntegrityError)**：双节点同时获取 fencing_token 时可能触发唯一约束冲突。非本轮引入，但阻塞 PG E2E 全绿。需针对修复后回归 PG 双进程。
- **L5 field readback 缺失**：三协议真实设备 readback E2E 仍未执行。当前只有 L2 contract（各 3 tests）模拟 readback。按 field plan 执行现场验证后方可提升为 L5。
- **compose 中 redis_state_cache / source_adapter_registry not_ready**：测试环境无真实 Redis / adapter registry，导致 readyz degraded。生产环境需要有条件就绪后回归 full-health E2E。
- **source_lab 测试目录 mypy 未清零**：172 errors / 27 test files。按既定策略不强制清零，但因此 source_lab 不能写成 fully-closed tool-ready。

## 8. 判定声明

### ingest production-ready：否

**理由**：
1. PG concurrency bug（fencing_token INSERT race）未修复 — 多节点写入控制正确性未完全过 PG L4
2. L5 field readback 完全缺失 — 写入控制安全边界只有 L2 contract，未经过真实设备验证
3. compose 中两个组件 degraded（测试环境预期，但生产环境回归缺失）

ingest 当前状态：**模块级 quality gate 收口**（compileall/ruff/mypy/import bounday/source_lab 隔离全部通过），**核心链路 L3-L4 验证通过**（acquisition/cache/message/scheduler/write-lease），但 **production-ready 因 L5 缺失和 PG concurrency bug 而阻塞**。

### source_lab fully-closed tool-ready：否

**理由**：
1. 测试目录 mypy 172 errors / 27 test files 未治理
2. 非测试源码 mypy 已清零（107 files, 0 errors），工程质量达到 release-candidate

source_lab 当前状态：**非测试源码 mypy 清零**，**协议能力矩阵闭环**（11 协议全部 simulator/probe/profile/capacity 覆盖），**动态 runtime 闭环**（11 协议动态隔离验证），但 **fully-closed tool-ready 因测试 mypy 未清零而差一步**。

## 9. 下一步建议

1. **修复 fencing_token 并发 INSERT race**：用 `INSERT ... ON CONFLICT DO NOTHING RETURNING` 或 advisory lock 消除 IntegrityError。修复后回归 PG 双进程 full E2E。
2. **执行 field readback plan（Round 11 制定）**：选择一个现场环境对三协议（OPC UA/Modbus/IEC61850 MMS）执行真实 write-readback E2E，将 I-READY-005 从 L2 提升到 L5。
3. **测试目录 mypy cleanup**：对 tools/source_lab/tests/ 执行 mypy 治理（27 files, 172 errors），目标达到全量 source_lab mypy 0 errors。
4. **生产环境 compose readyz 回归**：在具备真实 Redis/adapter registry 的环境执行 readyz full-health E2E。
5. **网络分区与旧主恢复 E2E**：补 I-READY-006 中 post-fencing_token-fix 的网络分区和旧主恢复验收。
