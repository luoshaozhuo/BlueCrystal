# Round 16：field readback L5 现场验证准备与生产准入最终判定

> 日期: 2026-05-31
> 范围: `scripts/run_ingest_write_readback_smoke.sh` 加固、L5 evidence template、入口 smoke 自检、需求表里程碑更新
> 状态: 收口完成（L5 仍为唯一阻塞项）
> 证据来源: code-implementer Round 16 实施

## 1. 总览

| 项 | 结果 |
|---|---|
| write-readback smoke 脚本 CLI 加固 | fixed -- 新增 --dry-run/--protocol/--confirm/--write-enabled/--audit-output/--evidence-report CLI 参数，evidence report sed 分隔符修复 |
| L5 现场验证证据模板 | 已创建 -- `ai_shared/reports/ingest_field_readback_l5_evidence_template.md` |
| 入口 smoke 自检 | 10/10 PASS (L2 contract) |
| field readback L5 | 仍 partial -- 真实设备未到位 |
| ingest production-ready 判定 | **不得标 production-ready**，唯一阻塞：L5 field readback |

## 2. Task A：现场 readback 验证包固化

### 2.1 脚本修改

| 文件 | 操作 | 说明 |
|---|---|---|
| `scripts/run_ingest_write_readback_smoke.sh` | 修改 | 新增 CLI 参数解析（--dry-run/--protocol/--confirm/--write-enabled/--audit-output/--evidence-report/--help）；协议别名支持（modbus->modbus_tcp, iec61850->iec61850_mms）；evidence report sed 分隔符修复（/ -> \|）；write_evidence_report 重写为 printf 构造避免 heredoc+sed 脆弱性 |

### 2.2 脚本能力矩阵

| 能力 | 状态 | 说明 |
|---|---|---|
| --dry-run 默认 | PASS | 默认 WRITE_ENABLED=false，不产生设备流量 |
| --protocol 协议选择 | PASS | opcua/modbus/iec61850/all，含别名映射 |
| CONFIRM_FLAG 双重安全门 | PASS | WRITE_ENABLED=true 但 CONFIRM_FLAG!=true 拒绝写入 (rc=1) |
| --evidence-report 证据报告 | PASS | 生成含验证环境/证据等级/验证结果/注意事项的 Markdown 报告 |
| --audit-output 审计输出 | PASS | JSONL 格式审计，无凭据泄露 |
| --help 输出 | PASS | 包含所有必要选项说明和安全警告 |
| 无效协议拒绝 | PASS | rc=4，清晰错误信息 |
| 未知选项拒绝 | PASS | rc=4，清晰错误信息 |
| 凭据泄露防护 | 已确认 | 审计日志/帮助输出/stdout 均无 password/token/secret 等敏感关键词 |
| 三协议测试覆盖 | PASS | OPC UA (3 tests) / Modbus TCP (3 tests) / IEC 61850 MMS (9 tests) |

### 2.3 未改动项（已具备能力）

- endpoint/host/port -- 由底层 pytest 测试文件和 shared_source backend 管理，脚本为编排层
- node/register/reference -- 同上
- write value 与 expected readback value -- 同上
- actor/reason/trace_id/command_id -- 由 use case 和 audit 层管理
- WRITE_ENABLED=false 默认 -- 保持
- timeout -- 由 pytest 测试内部管理
- failure code 分类 -- classify_failure() 函数覆盖 pytest 全部退出码

## 3. Task B：现场验证输入模板

| 文件 | 操作 | 说明 |
|---|---|---|
| `ai_shared/reports/ingest_field_readback_l5_evidence_template.md` | 新增 | L5 现场验证证据收集最小字段集模板 |

模板覆盖字段：
- 站点/环境标识、安全区
- 协议（OPC UA/Modbus TCP/IEC 61850 MMS）及协议特定字段
- 设备/网关型号与地址
- 点位（NodeId/Register/Reference）
- 写入前基线值、写入值、即时回读值、延迟回读值
- 值恢复（回写原值）
- 审计事件 ID、lease ID、fencing token
- 操作人、审批/确认链
- 风险控制措施检查清单
- 失败截图/日志路径
- 证据等级判定（L5 field / L4 integration / L3 simulator）
- 日期/时间戳、验证人签名、审批人签名
- 失败场景验证（未授权写入、lease 冲突、source timeout）
- 凭据泄露检查

## 4. Task C：现场验证 dry-run 自检

### 4.1 dry-run 行为确认

| 检查项 | 结果 |
|---|---|
| dry-run 不产生真实网络流量到设备 | 确认 -- WRITE_ENABLED=false，pytest simulator/native 测试不连接真实设备 |
| audit 文件能生成 | 确认 -- AUDIT_OUTPUT 指定路径可生成 JSONL 审计 |
| evidence 文件能生成 | 确认 -- EVIDENCE_REPORT 指定路径可生成 Markdown 报告 |
| 参数缺失时稳定失败 | 确认 -- 无效协议 rc=4，未知选项 rc=4 |
| CONFIRM_FLAG 缺失时拒绝真实写入 | 确认 -- WRITE_ENABLED=true 但 CONFIRM_FLAG!=true -> rc=1 |
| WRITE_ENABLED=false 时拒绝真实写入 | 确认 -- 默认行为，clearly states NOT field validation |
| 失败码稳定 | 确认 -- RC_OK=0, RC_CONFIRM_FAILED=1, RC_TEST_FAILED=2, RC_ENV_MISSING=3, RC_INVALID_PROTO=4, RC_INTERNAL_ERROR=5 |

### 4.2 入口 smoke 自检

| 文件 | 操作 | 说明 |
|---|---|---|
| `scripts/test_ingest_write_readback_smoke_contract.sh` | 新增 | 入口脚本 CLI 契约自检（L2 contract） |

自检结果：**10/10 PASS**

| # | 测试项 | 结果 |
|---|---|---|
| 1 | 脚本存在且可执行 | PASS |
| 2 | --help 包含所有必要选项 (11 项) | PASS |
| 3 | 无效协议拒绝 (rc=4) | PASS |
| 4 | WRITE_ENABLED=true 无 CONFIRM 拒绝 (rc=1) | PASS |
| 5 | --protocol opcua 仅运行 OPC UA | PASS |
| 6 | 协议别名 modbus -> modbus_tcp | PASS |
| 7 | 协议别名 iec61850 -> iec61850_mms | PASS |
| 8 | dry-run 默认 WRITE_ENABLED=false | PASS |
| 9 | 证据报告生成正确（含 L3 标注） | PASS |
| 10 | 审计日志无凭据泄露 | PASS |
| 11 | --help 输出无敏感凭据泄露 | PASS |
| 12 | 三协议 write-readback 测试文件存在 | PASS |

注：自检脚本计数器区分了帮助选项批量检查（通过不计数，仅失败计数），因此最终汇总为 10 passed, 0 failed, 10 total。

## 5. Task D：生产准入状态更新

### 5.1 需求跟踪表更新

| 条目 | 更新前状态 | 更新后状态 | 证据等级 | 说明 |
|---|---|---|---|---|
| I-READY-005 | 部分实现 (L2/L3) | 部分实现 (L2/L3) | L2/L3 | Round 16: 脚本 CLI 加固（--dry-run/--protocol/--confirm/双安全门），evidence template 已就绪，入口 smoke 自检 10/10 PASS；L5 field readback 仍 pending -- 唯一阻塞项 |
| I-READY-006 | 已实现 (L4) | 已实现 (L4) | L4 | 保持 Round 15 状态：PG L4 4/4，fencing_token race 已修复 |
| I-READY-007 | 已实现 (L3) | 已实现 (L3) | L3 | 保持 Round 15 状态：mypy 全量清零，compileall/ruff/import boundary 通过 |
| SL-READY-001 | 部分实现 (L3) | 部分实现 (L3) | L3 | 保持 Round 15 状态 |
| SL-READY-003 | 部分实现 (L2/L3) | 部分实现 (L2/L3) | L2/L3 | 保持 Round 15 状态 |

### 5.2 ingest 整体 production-ready 判定

| 判定项 | 状态 | 说明 |
|---|---|---|
| PG E2E | L4 PASS | 4/4 PG 容器真实执行 |
| compose readyz | L4 PASS | 8/8 组件聚合 PASS |
| mypy 全量 | 0 errors / 202 files | source_lab 全量清零，ingest+shared_source 全量通过 |
| import boundary | PASS | 生产路径无 source_lab import |
| runner path | PASS | shared_source 不再隐式落回 tools/source_lab/native/build |
| crosscutting matrix | 8/8 PASS | 全部横切能力已接入 |
| write-readback smoke script | 10/10 PASS | CLI 契约加固完成，evidence template 就绪 |
| **L5 field readback** | **PENDING -- 唯一阻塞项** | 三协议真实设备/网关 readback 未执行 |
| **ingest production-ready** | **不得标 production-ready** | 阻塞于 L5 field readback |

**最终判定：ingest 整体标 prodlike-ready / production-ready blocked by L5 field readback。**

### 5.3 新增需求条目：I-READY-008 ingest 现场验证准备就绪

- 类型：生产部署准入
- 优先级：高
- 需求描述：
  - ingest 写入控制链路在具备真实设备/网关环境前，应完成现场验证包（脚本、模板、自检、入口）的全套准备工作。
- 验收要点：
  - 写入回读脚本支持 --dry-run 默认、--protocol 选择、CONFIRM 双安全门、evidence report 生成。
  - L5 现场证据模板覆盖全部必要字段。
  - 入口自检全部通过。
  - 不把 dry-run 写成 L5 passed。
- 状态：已实现 (L2 contract)
- 证据：Round 16 脚本加固、evidence template、入口自检 10/10 PASS
- 更新时间：2026-05-31

## 6. Task E：最终报告（本报告）

本报告即 Task E 交付物。关键结论：

### 6.1 当前可生产准入项

1. **PG E2E**：L4 PASS（4/4 真实 PG 容器执行，fencing_token race 已修复）
2. **compose readyz**：L4 PASS（8/8 组件聚合，敏感数据脱敏正确）
3. **mypy 全量**：0 errors（202 files 全覆盖）
4. **import boundary**：PASS（生产路径无 source_lab import）
5. **runner path**：PASS（shared_source 不隐式落回 tools/source_lab/native/build）
6. **crosscutting matrix**：8/8 PASS（全部横切能力已接入）
7. **write-readback smoke**：脚本 CLI 加固 10/10，evidence template 就绪

### 6.2 唯一剩余阻塞项

**L5 field readback**：三协议（OPC UA / Modbus TCP / IEC 61850 MMS）真实设备/网关 write-readback 验证。

- 当前证据：L2 contract（三协议各 3 readback contract tests）+ L3 simulator/native
- L5 条件：真实设备 endpoint、真实网关、真实授权链路、操作人、审批链、审计归档
- 无真实设备环境，不得标 L5 passed

### 6.3 L5 现场执行步骤

按照 `ai_shared/reports/ingest_write_readback_field_validation_plan_round11.md` 执行：

1. 部署前准入：明确目标协议/设备/网关/点位白名单，确认 runner artifact 已安装，确认 WRITE_ENABLED 仅受控窗口开启
2. 现场单点 readback：baseline read -> authorized write -> immediate readback -> delayed readback -> 审计核对 -> 回写原值
3. 失败场景：unauthorized write 被拒绝、lease/fencing conflict 被拒绝、timeout 返回显式错误、审计可追踪失败动作

使用 `ai_shared/reports/ingest_field_readback_l5_evidence_template.md` 逐字段记录。

### 6.4 dry-run 自检结果

入口 smoke 自检 10/10 PASS（见 4.2 节及 `scripts/test_ingest_write_readback_smoke_contract.sh`）。

### 6.5 不能标 production-ready 的明确原因

```
ingest 写入控制链路的全部安全机制（lease/fencing/audit/readback/decorator/dry-run）
已通过 L2 contract + L3 simulator/native + L4 PG 级别验证。

但写入控制的最终闭环——向真实物理设备/网关下发命令并核实 readback——仍未执行。
在真实设备/网关/授权链路的 L5 field readback 完成前，
ingest 不得标 production-write-ready，整体不得标 production-ready。
```

### 6.6 下一步现场执行 handoff

1. 运维团队：准备目标设备/网关清单、写入白名单、操作人授权
2. 现场工程师：按 `ingest_write_readback_field_validation_plan_round11.md` 执行三协议 write-readback
3. 现场工程师：按 `ingest_field_readback_l5_evidence_template.md` 逐字段填入证据
4. 质量团队：审计归档审核
5. 开发团队：根据 L5 证据更新 I-READY-005 为 completed，将 ingest 标为 production-ready

## 7. project_tree / ADR / 规则

- project_tree: 已更新 -- 新增 Round 16 报告文件、evidence template、smoke contract 测试
- ADR: 无需更新 -- 本次为现场验证包固化和脚本 CLI 加固，不产生新架构决策
- rules: 无需更新 -- 未产生新的规则体系变更

## 8. 说明

- 本报告不把 dry-run/script/L3 simulator 写成 L5 field passed
- 本报告不把 ingest 标为 production-ready
- 本报告明确唯一剩余阻塞项：L5 field readback
- 质量门禁保持全量通过状态（mypy/ruff/compileall/import boundary）
