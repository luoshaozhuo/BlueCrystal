# ingest / source_lab 模块级准入与需求边界复核 Round 10

> 日期: 2026-05-30
> 范围: `Whale_REQ_Ingest` / `Whale_REQ_SourceLab` / `Whale_REQ_Crosscutting` / `Whale_REQ_SharedSource` + `src/whale/ingest` + `src/whale/shared/source` + `tools/source_lab` + 关键 compose / scripts / tests / reports
> 状态: 需求边界基本完整；`ingest` 未达 production-ready；`source_lab` 达到受限工具准入但未收口
> 证据来源: 真实源码、测试、compose、脚本、质量门禁命令、现有 Round 8 报告

## 1. 总览

| 项 | 结果 |
|---|---|
| 四份需求文件边界 | 基本完整，无需继续扩需求 |
| 明显职责错放 | 未发现需要立即修正文案的严重错放 |
| 需求证据漂移 | 存在，部分需求表引用的报告路径当前仓库不存在 |
| `ingest` 模块可生产部署 | 否 |
| `ingest` 当前状态 | prodlike/test-ready，非 production-ready |
| `source_lab` 工具模块可独立运行/可用于准入验证 | 是，但带明确边界条件 |
| `source_lab` 工具准入是否收口 | 否 |
| `compileall` | passed |
| `ruff` | passed |
| `mypy src/whale/ingest src/whale/shared/source` | passed |
| `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` | 1 passed |
| `pytest tests/unit/test_worker_runtime_do_execute.py tests/unit/test_acquisition_job_handler.py tests/unit/test_source_command_use_case.py tests/unit/test_ingest_write_lease.py -q` | 23 passed |
| `pytest tools/source_lab/tests/access/test_protocol_production_readiness_gate.py tools/source_lab/tests/access/test_native_cmd_timeout.py -q` | 28 passed |

## 2. 需求边界复核

### 2.1 边界结论

| 文件 | 结论 | 说明 |
|---|---|---|
| `Whale_REQ_Ingest.md` | 基本完整 | 聚焦生产编排、runtime、API、scheduler、cache/message、write/control、模块部署准入，未把完整商业交付塞入模块需求 |
| `Whale_REQ_SourceLab.md` | 基本完整 | 聚焦 simulator/probe/profile/capacity/native runner/工具边界，明确不替代 production client |
| `Whale_REQ_Crosscutting.md` | 基本完整 | 聚焦日志、指标、trace、审计、认证鉴权、凭据、韧性、健康诊断等横切能力 |
| `Whale_REQ_SharedSource.md` | 基本完整 | 聚焦 production source client、协议 backend、read/write/subscription/report、资源管理 |

### 2.2 重复与错位

| 观察 | 结论 |
|---|---|
| `Ingest` 是否重写 `MessagePipeline` 内部主题/ACL/retention 细节 | 未重写，边界保持正确 |
| `Ingest` 是否重写 `SharedSource` 协议 backend 内部实现 | 未重写，边界保持正确 |
| `Ingest` 是否重写 `Crosscutting` 内部框架职责 | 未重写，只要求接入与验证 |
| `SourceLab` 是否被写成 production client | 未被写成 production client |
| 模块需求中是否塞入完整安装手册/版本发布/售后/许可证/全系统灾备 | 未发现 |

### 2.3 需要记录但不必改需求的点

1. 四份需求文件的边界表达已足够作为本轮验收基线，当前不需要继续扩需求。
2. 若继续修改需求，主要应是证据回填与状态同步，不是再扩职责。
3. 当前更大的问题在实现与证据闭环，而不是需求定义不足。

## 3. 发现的文档/证据漂移

| 项 | 结果 | 影响 |
|---|---|---|
| `Whale_REQ_Ingest.md` / `Whale_REQ_SourceLab.md` 中部分引用报告路径 | 当前仓库未找到对应文件 | 降低 READY 证据可追溯性 |
| `Round 8` 类型治理报告 | 存在且可读取 | 可支撑质量门禁结论 |
| `source_lab` / 安全部署类历史报告 | 部分路径在需求表中被引用，但仓库内未检索到 | 不能把需求表中的“已有报告”直接当成现行证据 |

说明：本轮未修改需求文件，因为问题在“证据引用漂移”，不是职责边界错误。

## 4. ingest 需求状态核验

### 4.1 I-FR / I-NFR / I-AR / I-SCR / I-TEST 摘要

| 条目 | 结论 | 证据等级 | 说明 |
|---|---|---|---|
| `I-FR-001` source->cache | 部分满足 | L3 | 有 simulator + production client 闭环，但长期订阅恢复仍待补强 |
| `I-FR-002` cache->message | 部分满足 | L3/L4 | Kafka/test-container 级闭环存在，但不等于生产 topic/ACL/retention 已验证 |
| `I-FR-003` write/control | 部分满足 | L2/L3 | dry-run、授权、lease、fencing、readback contract 有；真实设备 readback 缺失 |
| `I-FR-004` 多协议 adapter | 部分满足 | L1-L3 | 已接入协议有限，且依赖 shared_source 当前实现边界并不完全独立 |
| `I-FR-007` image/entrypoint | 基本满足 | L3/L4 | 单一 Dockerfile、`api/worker/api-worker/migrate` smoke 存在 |
| `I-FR-008` CRUD API | 部分满足 | L2/L4 | CRUD/idempotency/audit 有较强证据，API->worker 配置消费仍待补 |
| `I-FR-009` scheduler 多节点 | 部分满足 | L3/L4 | active_standby/dual_active/cluster 有测试，但 PostgreSQL 多进程与网络分区未完成 |
| `I-NFR-004` 唯一 runtime image | 基本满足 | L3/L4 | `Dockerfile` + 两套 compose + smoke 脚本存在 |
| `I-AR-002` source_lab 隔离 | 满足 | L1 + gate | import gate 命令与单测均通过 |
| `I-SCR-003` 写入控制安全边界 | 部分满足 | L2/L3 | 默认 disabled、授权、lease、fencing、审计存在；真实设备投产证据不足 |
| `I-TEST-001/002` | 部分满足 | L1-L4 | tests 数量和覆盖面较好，但仍不能外推为生产投产完成 |

### 4.2 I-READY 逐项核验

| 条目 | 结论 | 证据等级 | 当前判断 |
|---|---|---|---|
| `I-READY-001` 独立部署准入 | 部分满足 | L3/L4 | 有单一 image、统一 entrypoint、compose smoke；可部署不等于可投产 |
| `I-READY-002` 外部依赖准入矩阵 | 未满足 | L2/L4 | 真实 smoke 存在，但缺统一 required/optional、timeout、degradation、fail-open/fail-closed 矩阵 |
| `I-READY-003` 横切能力接入准入 | 部分满足 | L2/L3 | ingest 已接入审计/授权/metrics/trace/redaction/retry 等片段，但缺模块级接入矩阵与完整验证映射 |
| `I-READY-004` 安全分区部署约束 | 未满足 | L2/L3 | 有 bundle 单向流、外部授权/审计 contract；但端口矩阵、通信方向矩阵、最小开放面证据不足 |
| `I-READY-005` 写入控制投产准入 | 未满足 | L2/L3 | 真实写入默认关闭是对的，但真实设备 readback / 生产授权注入未闭合 |
| `I-READY-006` 多节点生产准入 | 未满足 | L2/L4 | SQLite/单进程与若干 integration 有，但 PostgreSQL 多进程、网络分区、旧主恢复未闭合 |
| `I-READY-007` 质量门禁 | 满足（工程门禁层） | L1-L4 | `compileall`/`ruff`/`mypy ingest+shared`/指定 pytest/import gate` 均通过 |

### 4.3 ingest 阻塞 production-ready 的硬项

1. `shared_source` 自身还不能稳妥视为“独立 production source client 已收口”，而 `ingest` 明确依赖它作为生产 source client。
2. `I-READY-002` 缺统一外部依赖准入矩阵，当前只有散落 smoke/contract/integration 证据。
3. `I-READY-004` 缺现行可追溯的模块级安全部署拓扑、端口矩阵、通信方向矩阵证据。
4. `I-READY-005` 写入控制没有真实设备 readback L5 证据，只能到 dry-run-ready / contract-ready。
5. `I-READY-006` 多节点证据尚未达到 PostgreSQL 多进程/网络分区/旧主恢复的生产验收强度。

## 5. source_lab 需求状态核验

### 5.1 SL-FR / SL-NFR / SL-AR / SL-TEST 摘要

| 条目 | 结论 | 证据等级 | 说明 |
|---|---|---|---|
| `SL-FR-001` facade | 满足 | L3 | contract 测试与协议矩阵存在 |
| `SL-FR-002` simulator | 部分满足 | L3 | 多协议 simulator 可运行；GOOSE/SV 需受控 L2 环境 |
| `SL-FR-003` probe/profile/capacity | 部分满足 | L4 | 多协议 capacity/profile 有证据，但部分协议/环境受限 |
| `SL-FR-004` native runner 管理 | 部分满足 | L3 | preflight/timeout/readiness gate 存在，但静态声明高估风险仍在 |
| `SL-FR-005` 动态 runtime | 部分满足 | L4 | 动态隔离验证较强，但 accepted-state/raw socket 环境边界仍需显式化 |
| `SL-AR-001` 工具层边界 | 满足 | L1/L2 | ingest import gate 通过，边界清楚 |
| `SL-TEST-001/002` | 部分满足 | L3/L4 | 工具验证证据强，但不能外推为 ingest production-ready |

### 5.2 SL-READY 逐项核验

| 条目 | 结论 | 证据等级 | 当前判断 |
|---|---|---|---|
| `SL-READY-001` 独立工具部署准入 | 部分满足 | L3/L4 | simulator/probe/profile/capacity/native timeout 等可以独立运行 |
| `SL-READY-002` 权限与运行环境边界 | 部分满足 | L3 | `source_lab_l2_test_env.sh` 清楚说明 veth/raw socket 条件，但 GOOSE/SV 仍仅限受控 L2 |
| `SL-READY-003` 证据边界 | 未收口 | L2/L3 | `test_protocol_production_readiness_gate.py` 已在守边界，但 `PROTOCOL_CAPABILITIES` 静态 dict 仍可能高估 runtime readiness |

### 5.3 协议边界结论

| 协议/能力 | 结论 |
|---|---|
| `opcua` / `modbus_tcp` / `iec61850_mms` | 工具侧验证较强，可用于准入验证 |
| `iec61850_report` | 工具侧验证可用，但不等于 production client/report backend 已投产 |
| `iec101` / `modbus_rtu` | 仅 gateway mode，不应写成完整 production protocol ready |
| `goose` / `sv` | 仅受控 L2 环境下可验证，不能写成普通环境默认 ready |
| `mqtt` / `http_rest` | 工具侧协议能力有限，需按能力矩阵保留限制 |

### 5.4 source_lab 阻塞收口项

1. `PROTOCOL_CAPABILITIES` 仍是静态字典，虽然已有 `RunnerInfo` 三元组修正，但调用方仍可能误用静态声明。
2. 原始套接字、`unshare -Urn`、`veth/netns`、root/capability 等运行前提仍需要更系统的准入文档与清理验证。
3. `gateway mode`、`NOT_IMPLEMENTED`、`受控 L2 环境` 的证据边界需要继续保持显式，不能用“测试通过”一句话覆盖。

## 6. shared_source 交叉核验结论

虽然本轮主目标不是单独给 `shared_source` 下最终结论，但它直接影响 `ingest` 准入，因此必须记录：

| 项 | 结论 |
|---|---|
| `mypy src/whale/ingest src/whale/shared/source` | passed |
| `shared_source` 是否 `import tools.source_lab` | 未发现直接 import |
| `shared_source` 是否与 `tools/source_lab` 完全独立 | 否 |
| 关键事实 | `opcua/modbus/iec104/iec61850` backend 默认 runner 路径都指向 `tools/source_lab/native/build` |

这意味着：

1. `Whale_REQ_SharedSource` 的“不得依赖 source_lab”在“Python import 边界”上基本成立；
2. 但在“默认 native runner 构建产物与文件路径依赖”上并未真正独立；
3. 因此不能把当前 `shared_source` 直接写成完全独立的 production client 已收口；
4. 这会反向阻塞 `ingest` 的 production-ready 结论。

## 7. 检查与测试

| 命令/检查 | 结果 | 分类 | 说明 |
|---|---|---|---|
| `grep -R "tools.source_lab\|from tools.source_lab\|import tools.source_lab" src/whale/ingest src/whale/shared/source || true` | passed | fixed | 未发现生产路径直接 import `tools.source_lab` |
| `python -m compileall src/whale/ingest src/whale/shared/source tools/source_lab tests tools/source_lab/tests -q` | passed | fixed | 无输出，按 exit code 0 判定通过 |
| `ruff check src/whale/ingest src/whale/shared/source tools/source_lab tests tools/source_lab/tests` | passed | fixed | `All checks passed!` |
| `mypy src/whale/ingest src/whale/shared/source` | passed | fixed | `Success: no issues found in 162 source files` |
| `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` | passed | fixed | `1 passed` |
| `pytest tests/unit/test_worker_runtime_do_execute.py tests/unit/test_acquisition_job_handler.py tests/unit/test_source_command_use_case.py tests/unit/test_ingest_write_lease.py -q` | passed | fixed | `23 passed` |
| `pytest tools/source_lab/tests/access/test_protocol_production_readiness_gate.py tools/source_lab/tests/access/test_native_cmd_timeout.py -q` | passed | fixed | `28 passed` |

## 8. 证据与需求状态

| 条目 | 证据等级 | 状态 | 说明 |
|---|---|---|---|
| `ingest` image/entrypoint/compose smoke | L3/L4 | 部分满足 | 可证明模块可部署和 prodlike smoke，不等于生产投产完成 |
| `ingest` import boundary gate | L1 | 满足 | 仅证明边界，不证明生产能力 |
| `ingest` 写入控制 | L2/L3 | 部分满足 | contract/readback 编排存在，真实设备投产证据不足 |
| `ingest` 多节点调度 | L3/L4 | 部分满足 | integration 较强，但仍缺 PostgreSQL 多进程/网络分区 |
| `source_lab` protocol readiness gate | L3 | 部分满足 | 工具模块准入有效，不外推到 ingest |
| `source_lab` timeout / native runner | L3 | 部分满足 | 可证明 runner timeout 可配置、可超时失败 |
| `shared_source` 独立 production client | L2/L3 | 未收口 | 与 `tools/source_lab/native/build` 存在默认路径耦合 |

## 9. 准入结论

### ingest

- 结论：**未达到“ingest 模块可生产部署”**。
- 当前状态：**已达到 prodlike/test-ready**，具备较强工程门禁与部署 smoke，但仍缺生产准入阻塞项闭环。

### source_lab

- 结论：**已达到“工具模块可独立运行/可用于准入验证”**，但属于**带约束条件的 tool-ready**。
- 当前状态：**未收口**，因为 runtime readiness 高估风险、raw socket/L2 环境边界、gateway/NOT_IMPLEMENTED 协议状态仍需持续显式化。

## 10. 是否需要继续改需求

不需要继续扩需求。

本轮判断：

1. 四份需求文件已足够作为模块级验收基线。
2. 当前主要缺口在实现、测试、部署证据和需求表证据回填同步。
3. 下一轮应优先改实现/测试/配置/报告同步，而不是再扩模块职责。

## 11. 下一步建议

1. 先处理 `shared_source` 与 `tools/source_lab/native/build` 的默认路径耦合，明确其是否要独立 native 交付，或下调 `SS-READY-*` 状态。
2. 为 `ingest` 补 `I-READY-002` 外部依赖准入矩阵：required/optional、timeout、retry/backoff、readiness、degradation、fail-open/fail-closed。
3. 为 `ingest` 补 `I-READY-004` 模块级部署拓扑、端口矩阵、通信方向矩阵，并同步修正需求表里引用但缺失的报告路径。
4. 为 `ingest` 补 `I-READY-005` 真实设备 readback 和 `I-READY-006` PostgreSQL 多进程/网络分区验证；在此之前不得标 production-ready。
5. 为 `source_lab` 把 readiness 判断进一步从 `PROTOCOL_CAPABILITIES` 静态字典迁移到 per-runner runtime readiness，避免工具准入高估。
