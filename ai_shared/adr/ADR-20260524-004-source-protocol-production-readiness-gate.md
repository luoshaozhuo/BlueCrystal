# ADR-20260524-004-source-protocol-production-readiness-gate

## Status

Accepted

## Keywords

- protocol production readiness
- capability registry
- production_client_read
- production_client_write
- capacity gate
- profile gate
- access framework
- quality gate

## Context

Whale 项目已在前两轮实现了 OPC UA 和 Modbus TCP 两条协议的 production read/write 能力接入。在接入过程中发现以下治理缺口：

1. **capability registry 缺乏写操作精度**：`write=true` 或 `production_client_write=true` 不能表达"只支持 FC06、不支持 FC05/FC15/FC16"。这会导致后续代码误认为 Modbus TCP 具备完整写能力。

2. **production client 标记缺乏自动化校验**：没有自动化门禁验证 `production_client_read=true` 是否真的有 `shared/source/{protocol}` 生产 client 和 ingest adapter。

3. **新增协议缺乏 capacity/profile 硬性门禁**：现有 `test_all_protocols_polling_capacity.py` 只验证 registry → factory → runner 构建路由，不验证真实协议 Simulator 上的 `read_once` 执行。这容易导致"registry PASS 但实际不能读"的假通过。

4. **Python lightweight runner 不能作为 production client 证据**：`python_lightweight_runner` 实现等级不应被当作 production client read/write 的证据。必须与 `real_native_runner` 区分。

5. **ADR 引用错误**：Round 2 报告错误地将 ADR-20260523-002 引用为"能力矩阵升级"，实际其主题是 source_lab Task Facade 边界。

因此需要建立生产协议准入门禁规则与对应的自动化测试，固化前两轮的工程质量。

## Decision

### 1. 新增 capability registry 字段

每个 `PROTOCOL_CAPABILITIES` 条目必须包含：

- `supported_write_operations: tuple[str, ...]` — 已实现的具体写操作列表。
- `unsupported_write_operations: tuple[str, ...]` — 未实现的具体写操作列表。

`production_client_write=true` 时 `supported_write_operations` 必须非空。
`production_client_write=false` 时 `supported_write_operations` 必须为空。

### 2. 建立协议生产准入自动化门禁

新增 `tools/source_lab/tests/access/test_protocol_production_readiness_gate.py`，覆盖以下规则：

**production_client_read 门禁：**

- 已知 production 协议（OPC UA、Modbus TCP）的 `shared/source/{protocol}/` 目录必须存在。
- 已知 production 协议的 `ingest/adapters/source/{protocol}_source_acquisition_adapter.py` 必须存在。
- 已知 production 协议的 capacity runner 必须可构建（`build_capacity_runner`）。
- Python lightweight runner 不得标记 production_client_write=true。

**production_client_write 门禁：**

- `production_client_write=true` 协议的 ingest write adapter 必须存在。
- `production_client_write=true` 协议的 `supported_write_operations` 必须非空。

**capability integrity 门禁：**

- 全协议 `supported_write_operations` / `unsupported_write_operations` 字段完整性校验。
- `production_client_write=true` 与 `supported_write_operations` 一致性校验。
- `production_client_write=false` 不得有非空 `supported_write_operations`。
- Modbus TCP 必须明确列出 FC06 为支持、FC05/FC15/FC16 为不支持。

### 3. 新增协议 capacity/profile 门禁测试

新增 `tools/source_lab/tests/access/test_modbus_tcp_production_capacity_profile_gate.py`，覆盖：

- Native runner 编译可用性验证。
- `read_once` 对真实 `ModbusTcpSimulator` 执行验证。
- 多次读调用的成功率、耗时、吞吐量指标收集。

后续每新增生产协议，必须参照此文件创建对应的 capacity/profile gate 测试。

### 4. 门禁测试质量要求

- 所有门禁测试不得 skipped。
- 缺少环境时必须以 actionable error message 明确 fail，而不是静默跳过。
- 不得仅 registry 构造对象后通过，必须执行真实协议路径或等价可验证路径。

### 5. ADR 引用规范

报告中引用 ADR 时，必须从 `ai_shared/adr/ADR索引.md` 核对 ADR 主题，不得凭记忆或推测填写。

## Consequences

### 收益

- `supported_write_operations` / `unsupported_write_operations` 消除写能力夸大风险。
- 自动化门禁防止新协议生产 client 标记错误。
- capacity/profile gate 测试确保新协议的真实可读性。
- Python lightweight runner 不再被误当作 production client 证据。
- ADR 引用正确性通过规则固化。

### 代价

- 新增协议时需要同时写 capacity/profile gate 测试（约一个文件 5 个测试）。
- 现有 `PROTOCOL_CAPABILITIES` 配置需要维护写操作枚举值。
- 门禁测试需要 simulator 或 mock server 配合。

### 约束

- 不允许为通过门禁而跳过 test 或降低断言。
- 不允许用 `python_lightweight_runner` 实现等级对应 production client 状态。
- 不允许把 `tools/source_lab` 的 task facade 输出作为 production client 的证据。
- 不允许把 capacity/profile 的任务模型泄漏到 ingest use case。

## Rejected Options

### 方案一：只在项目文档中约定规则，不做自动化测试

拒绝。

原因：

- 纯约定容易被后续修改忽略。
- 前两轮已出现 write 能力夸大风险。
- 自动化门禁是工程质量的最后一道防线。

### 方案二：在 CI 层面做门禁，不在单元测试层面做

拒绝。

原因：

- CI 层门禁反馈周期长，开发者本地修改时无法即时感知。
- 项目当前没有成熟 CI 基础设施。
- pypress 门禁测试路径短、反馈快。

### 方案三：仅在 registry.py 中增加注释说明

拒绝。

原因：

- 注释不能阻止错误标记。
- 注释不能验证 `shared/source/{protocol}` 和 adapter 是否存在。
- 注释不能验证 capacity/profile 实际执行。

## Related Files

- `tools/source_lab/access/runners/registry.py`
- `tools/source_lab/tests/access/test_protocol_service_capabilities.py`
- `tools/source_lab/tests/access/test_protocol_production_readiness_gate.py`
- `tools/source_lab/tests/access/test_modbus_tcp_production_capacity_profile_gate.py`
- `tools/source_lab/tests/access/test_all_protocols_polling_capacity.py`
- `tools/source_lab/tests/access/test_all_protocols_polling_profile.py`
- `src/whale/shared/source/opcua/`
- `src/whale/shared/source/modbus/`
- `src/whale/ingest/adapters/source/opcua_source_acquisition_adapter.py`
- `src/whale/ingest/adapters/source/opcua_source_write_adapter.py`
- `src/whale/ingest/adapters/source/modbus_source_acquisition_adapter.py`
- `src/whale/ingest/adapters/source/modbus_source_write_adapter.py`
- `ai_shared/reports/source_modbus_tcp_production_read_write_report.md`

## Supersedes / Superseded By

None.
