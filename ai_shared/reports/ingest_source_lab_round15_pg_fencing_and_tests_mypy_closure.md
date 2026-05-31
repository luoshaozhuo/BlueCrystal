# Round 15：PG fencing_token 并发竞态修复 + source_lab 全量 mypy 收口

> 日期: 2026-05-31
> 范围: `src/whale/ingest/runtime/fencing.py`, `src/whale/ingest/runtime/write_lease.py`, `tools/source_lab/` mypy 全量
> 状态: 收口完成
> 证据来源: code-implementer Round 15 实施 + test-validator Round 15 独立验证

## 1. 总览

| 项 | 结果 |
|---|---|
| fencing_token 并发竞态修复 | fixed — INSERT ON CONFLICT DO UPDATE RETURNING |
| PG E2E | 4/4 L4 PASS（真实 PG 容器执行） |
| source_lab 全量 mypy | 0 errors / 202 files（cmd/src/tests 全覆盖） |
| field readback L5 | 仍 partial — 真实设备未到位 |
| 需求表准确度 | I-READY-006 / SL-READY-001 / SL-READY-003 / I-READY-007 已更新 |

## 2. 修改文件

| 文件 | 操作 | 说明 |
|---|---|---|
| `src/whale/ingest/runtime/fencing.py` | 修改 | acquire 改为 INSERT ON CONFLICT DO UPDATE RETURNING 原子操作 |
| `src/whale/ingest/runtime/write_lease.py` | 修改 | IntegrityError 映射为 LEASE_CONFLICT |
| `tools/source_lab/tests/access/test_open62541_subscription_runner.py` | 修改 | mypy 类型标注修复 |
| `tools/source_lab/tests/access/test_open62541_serial_polling_runner.py` | 修改 | mypy 类型标注修复 |
| `tools/source_lab/tests/access/test_access_progress_reporting.py` | 修改 | mypy 类型标注修复 |
| `tools/source_lab/tests/access/_dynamic_runtime_test_utils.py` | 修改 | mypy 类型标注修复 |
| `tools/source_lab/tests/access/test_dynamic_operation_journal_audit.py` | 修改 | mypy 类型标注修复 |
| `tools/source_lab/tests/access/test_dynamic_subscription_endpoint_adjustment.py` | 修改 | mypy 类型标注修复 |
| `tools/source_lab/tests/access/test_field_provider.py` | 修改 | mypy 类型标注修复 |
| `tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py` | 修改 | mypy 类型标注修复 |
| `tools/source_lab/tests/access/test_server_simulator_facade_contract.py` | 修改 | mypy 类型标注修复 |
| `tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py` | 修改 | mypy 类型标注修复 |
| `ai_shared/reports/source_lab_tests_mypy_closure_round15.md` | 新增 | mypy 治理终点报告 |
| `ai_shared/reports/ingest_source_lab_round15_pg_fencing_and_tests_mypy_closure.md` | 新增 | 本报告 |
| `ai_shared/memory/Whale_REQ_Ingest.md` | 更新 | I-READY-006 / I-READY-007 需求表 |
| `ai_shared/memory/Whale_REQ_SourceLab.md` | 更新 | SL-READY-001 / SL-READY-003 需求表 |
| `ai_shared/memory/project_tree.md` | 更新 | 新增 Round 15 报告文件 |

## 3. 行为变化

- **fencing_token acquire 原子化**：原 acquire 使用 SELECT-then-UPDATE 两阶段路径，并发场景下存在 INSERT race（IntegrityError）。改为 `INSERT ON CONFLICT DO UPDATE RETURNING` 单原子操作，消除竞态窗口。
- **IntegrityError -> LEASE_CONFLICT**：write_lease 将 PG IntegrityError 正确映射为 LEASE_CONFLICT，调用方无需感知 DB 层细节。
- **source_lab tests mypy 172 -> 0**：10 个剩余有 mypy errors 的测试文件全部修复，含类型标注补齐、isinstance 收窄、Callable 类型声明。

## 4. 检查与测试

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| `mypy src/whale/ingest src/whale/shared/source --strict` | passed | L3 | ingest 与 shared_source 全量无错误 |
| `mypy tools/source_lab/ --strict` | passed | L3 | source_lab 全量 0 errors / 202 files（cmd/src/tests 全覆盖） |
| `compileall python` | passed | L2 | 全量编译无错误 |
| `ruff check` | passed | L2 | 全量 lint 无错误 |
| `pytest tests/unit/test_ingest_write_lease.py -q` | 3 passed | L1 | 写入租约单测 |
| `pytest tests/unit/test_ingest_write_lease_fencing.py -q` | passed | L1 | fencing 单测 |
| `pytest tests/unit/test_dual_node_write_lease_conflict.py -q` | 7 passed | L2 | 双节点冲突单测 |
| `pytest tests/integration/test_ingest_dual_node_db_lease_e2e.py -q` | 7 passed | L4 | SQLite L3 dual-node lease E2E |
| `pytest tests/integration/test_ingest_prodlike_postgres_fault_injection.py -q` | 4 passed | L4 | PG L4 fault injection，含 fencing_token 并发测试 |
| `bash scripts/run_ingest_pg_lease_fault_injection.sh` | 4/4 L4 PASS | L4 | PG 容器真实执行：lease_acquire/release/concurrent_read/fencing_token |
| `pytest tools/source_lab/tests/access/ -q` | 734 passed, ~10 env-failed | L3/L4 | 10 个失败均为 native runner 二进制缺失，非代码问题 |

## 5. 证据与需求状态

| 条目 | 证据等级 | 状态 | 说明 |
|---|---|---|---|
| I-READY-006 | L4 | 已实现（注1） | SQLite L3 7/7 + PG L4 4/4，fencing_token race 已修复 |
| I-READY-007 | L3 | 已实现 | source_lab 全量 mypy 0 errors / 202 files，质量门禁全收口 |
| SL-READY-001 | L3 | 部分实现 | mypy 0 errors 达成，但 10 env-failed + L5 field readback pending |
| SL-READY-003 | L2/L3 | 部分实现 | quality gate 证据更新为全量 mypy 0 errors |
| I-READY-005 | L2/L3 | 部分实现 | L5 field readback waiting on real devices，WRITE_ENABLED=false 双重安全门确认 |

注1：I-READY-006 "已实现" 以代码级 PG 多进程验证为准；真实现场多节点跨主机部署未验证，标注为 known-gap。

## 6. project_tree / ADR / 规则

- project_tree: 已更新 — 新增 Round 15 报告文件，更新版本号描述
- ADR: 无需更新 — 本次为原有架构内的竞争条件修复，不产生新 ADR
- rules: 无需更新 — 未产生新的规则体系变更

## 7. 剩余风险

- **L5 field readback（真实设备）**：三协议 OPC UA / Modbus / IEC 61850 的写入 readback 仅达 L2 contract 级别，真实设备现场验证仍 pending。ingest 写入控制不得标记 production-write-ready。
- **真实现场多节点跨主机部署**：I-READY-006 仅通过 PG 多进程验证，真实现场多节点跨主机部署（网络延迟、时钟偏差、网络分区）未验证。
- **10 个 source_lab access 环境失败**：native runner 二进制缺失（非代码问题），不影响 mypy 全量清零结论，但 source_lab 全量 access 验证不可用。
- **network partition / 旧主恢复**：多节点故障场景 E2E 仍未收口。

### production-ready 声明

- **ingest 写入控制**：未达到 production-ready。L5 field readback 缺失，WRITE_ENABLED=false 正确。
- **ingest 多节点调度**：PG L4 fencing_token race 已修复，达成代码级 production-ready。真实现场跨主机验证仍为 known-gap。
- **ingest 质量门禁**：已收口。mypy/ruff/compileall/import boundary 全部通过。
- **source_lab**：mypy 治理已 fully-closed（0 errors / 202 files）。但 native runner 二进制缺失导致 10 tests environment-failed，source_lab 整体仍未达到 fully-closed tool-ready。L5 field readback 与多节点部署未完成则 ingest 整体不达 production-ready。

## 8. 下一步建议

1. **真实现场多节点跨主机部署验证**：部署 2+ ingest 实例到真实硬件，验证 assignment/lease/fencing 在真实网络环境下的行为。
2. **L5 field readback 真实设备验证**：配合现场设备接入计划，执行三协议真实设备 write + readback。
3. **native runner 二进制构建自动化**：将 CMake 构建纳入 CI，消除 10 source_lab access tests 的环境依赖。
4. **network partition 故障注入**：在 real multi-host 基础上补网络分区与旧主恢复 E2E。
