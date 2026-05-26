# ADR-20260524-007: IEC 61850 MMS 生产读写第一闭环

## Status

Accepted

## Keywords

- IEC 61850
- MMS
- Production Read/Write
- libiec61850
- Native Runner
- MMS Direct Write

## Context

IEC 61850 MMS 是实现新能源场站数据接入的核心协议之一。本 ADR 记录第一闭环（Round 1）中做出的架构决策。

第一闭环的范围：
1. 实现 C 语言 MMS 客户端运行器（iec61850_mms_client_runner）的交互式 stdin/stdout 协议。
2. 在 `src/whale/shared/source/iec61850/` 下建立生产 client 层。
3. 实现 ingest acquisition 和 write adapter。
4. 注册到 composition 和 capability registry。
5. 通过生产准入门禁。
6. MMS 读和 MMS 写（SP/CF FC 的直接属性写入）。

后续轮次（Round 2-3）将覆盖 Report 订阅、capacity/profile 测试等，不在本 ADR 范围。

## Decision

### 1. 只实现 MMS 直接读/写，不实现 Report/GOOSE/SV

MMS 读（IedConnection_readObject）和 MMS 直接写（IedConnection_writeObject）是本闭环的唯一操作类型。Report 订阅、GOOSE、SV 留待后续轮次。

### 2. 每个命令独立建连

MMS 协议本身无连接池概念。客户端运行器在每个 READ/WRITE 命令后断开连接，下一个命令重新建连。这是与 OPC UA adapter 保持长连接的重要区别。

### 3. FC（Functional Constraint）从外部传入

FC 由调用方通过 connection params 传入：
- 读方向：`connection.params["fc"]`，默认 `"NONE"`
- 写方向：`execution.params["fc"]`，默认 `"SP"`

不凭 obj_ref 格式猜测 FC。

### 4. 写入类型白名单

支持以下 MMS 写入类型，由 libiec61850 的 MmsValue 工厂构造：

| MMS 类型 | C 构造函数 |
|---|---|
| BOOLEAN | MmsValue_newBoolean |
| INT32 | MmsValue_newIntegerFromInt32 |
| UINT32 | MmsValue_newUnsignedFromUint32 |
| INT64 | MmsValue_newIntegerFromInt64 |
| FLOAT32 | MmsValue_newFloat |
| FLOAT64 | MmsValue_newDouble |
| VISIBLE_STRING | MmsValue_newVisibleString |

不支持 select-before-operate、command-termination、enhanced-security 等控制块操作。

### 5. 协议行格式

stdout 协议行格式：

```
READ_RESULT\t<request_id>\t<obj_ref>\tok=<0|1>\t<status>\t<value_type>\t<value>
WRITE_RESULT\t<request_id>\t<obj_ref>\tok=<0|1>\t<status>\t<value_type>
```

### 6. 不依赖 source_lab task facade

与 OPC UA / Modbus 一致，ingest adapter 直接使用 `src/whale/shared/source/iec61850/reader.py`，不经过 `tools.source_lab.access`。

## Consequences

### 正面

1. 实现了 IEC 61850 MMS 生产读写第一闭环，覆盖了新能源场站最常用的 MMS 读测量值、写设点值场景。
2. 协议行格式简单，便于调试和扩展。
3. 每个命令独立建连，避免长连接资源泄漏。
4. 不对 Report/GOOSE/SV 产生耦合约束。

### 负面与约束

1. 每个读/写都需要建连和断连，存在网络开销。
2. 不支持 Report 订阅，实时性场景需等待后续轮次。
3. 写入类型限于直接 MMS 写入（select-before-operate 未实现）。
4. Simulator 的 `LogicalNode LLN0 has 0 fc components` 诊断日志输出到 stdout，集成测试需要跳过非协议行。

## Rejected Options

1. **使用绑定库（CFFI/ctypes）调用 libiec61850**：增加 GIL 和 C API 兼容性风险。采用子进程运行器保持进程隔离。
2. **MMS 聚合读（多条 obj_ref 一次请求）**：libiec61850 的 IedConnection_readObject 是单 obj_ref 接口。聚合读需自行管理并发，当前不做。
3. **长连接 + 心跳**：MMS 的 TCP 连接可保持，但生产环境网络复杂（防火墙/超时），每个命令独立建连更可靠。

## Implementation Status (Round 2 — 2026-05-24)

### Round 2 Achievements

| Item | Status | Description |
|---|---|---|
| A. Simulator stdout noise | ✅ Fixed | `dup`/`dup2` stdout→stderr redirect during server setup, LLN0 diagnostic no longer pollutes stdout |
| B. Gate test | ✅ Created | `test_iec61850_production_capacity_profile_gate.py` — 7 tests (runner construction, binary existence, stdout noise check, read/write/readback, metrics) |
| C. FLOAT32 write test | ✅ Added | `test_write_float32_then_readback` — writes 98.765 to SPCtrl3.setVal, verifies with pytest.approx |
| D. Registry precision | ✅ Updated | `write_limitation` now documents verified (BOOLEAN, INT32, FLOAT32) and unverified (UINT32, INT64, FLOAT64, VISIBLE_STRING) write types |

### Updated Negative Consequence

~~4. Simulator 的 `LogicalNode LLN0 has 0 fc components` 诊断日志输出到 stdout，集成测试需要跳过非协议行。~~

This is now **resolved**: the simulator C source uses `dup`/`dup2` to redirect library stdout to stderr during server setup, ensuring stdout contains only the `"READY"` protocol line.

### New Files (Round 2)

- `tools/source_lab/tests/access/test_iec61850_production_capacity_profile_gate.py` — capacity/profile/gate 门禁测试（7 tests）

### Modified Files (Round 2)

- `tools/source_lab/native/libiec61850/iec61850_simulator_server.c` — stdout→stderr redirect for library noise
- `tools/source_lab/access/runners/registry.py` — write type precision documentation
- `tests/integration/test_ingest_iec61850_mms_source_write.py` — added FLOAT32 write_then_readback test

## Implementation Status (Round 3 — 2026-05-24)

### Round 3 Achievements

| Item | Status | Description |
|---|---|---|
| A. All 7 write types verified | ✅ Done | Added SPCtrl4-7 (FLOAT64, VISIBLE_STRING, UINT32, INT64) to simulator; all 7 types verified via write_then_readback integration tests |
| B. Capacity/profile coverage | ✅ Confirmed | `iec61850_mms` is in `test_all_protocols_polling_capacity.py` and `test_all_protocols_polling_profile.py` (structural). Dedicated gate test covers functional verification |
| C. Stability smoke | ✅ Added | `test_repeated_read_20_times` (20 consecutive reads) + `test_repeated_write_readback_5_cycles` (5 write+readback cycles) |
| D. Report/GOOSE/SV boundary | ✅ Hardened | Registry correctly marks Report/GOOSE/SV: not production_client_write, not production_client_read. GOOSE/SV are `planned_native_runner` |
| E. Architecture boundary | ✅ Verified | No cross-import violations. UseCase boundaries confirmed clean. No old directory regression |
| F. ADR/project_tree/report | ✅ Updated | ADR Round 3 section added. Closure report created. project_tree updated |

### Verified Write Types (Final)

All 7 MMS direct write types verified via real write_then_readback against simulator:

| Type | Simulator Node | Integration Test | Priority |
| --- | --- | --- | --- |
| BOOLEAN | SPCtrl1.setVal | Round 1 | 1 |
| INT32 | SPCtrl2.setVal | Round 1 | 1 |
| FLOAT32 | SPCtrl3.setVal | Round 2 | 2 |
| FLOAT64 | SPCtrl4.setVal | Round 3 | 3 |
| VISIBLE_STRING | SPCtrl5.setVal | Round 3 | 3 |
| UINT32 | SPCtrl6.setVal | Round 3 | 3 |
| INT64 | SPCtrl7.setVal | Round 3 | 3 |

### All-Protocols Coverage Status

- `test_all_protocols_polling_capacity.py`: ✅ iec61850_mms included (structural: build_capacity_runner + supports_access_mode)
- `test_all_protocols_polling_profile.py`: ✅ iec61850_mms included (structural: build_capacity_runner)
- `test_iec61850_production_capacity_profile_gate.py`: ✅ 9 tests (functional against real simulator)
- `test_protocol_production_readiness_gate.py`: ✅ iec61850_mms in KNOWN_PRODUCTION_READ_PROTOCOLS

### Stability Smoke Test Results

- 20 consecutive MMS reads: 20/20 success
- 5 consecutive write+readback cycles: 5/5 success, values correctly toggled
- No stdout noise, no zombie processes, no stderr error swallowing

### New Files (Round 3)

- `tools/source_lab/tests/access/test_iec61850_production_capacity_profile_gate.py` — stability tests added (2 new: 7→9 total)

### Modified Files (Round 3)

- `tools/source_lab/native/libiec61850/iec61850_simulator_server.c` — added SPCtrl4-7 writable nodes (FLOAT64, VISIBLE_STRING, UINT32, INT64)
- `tools/source_lab/access/runners/registry.py` — updated to reflect all 7 types verified, no unverified types remain
- `tests/integration/test_ingest_iec61850_mms_source_write.py` — added 4 write type integration tests (9 total, from 5)
- `ai_shared/reports/iec61850_mms_stage_engineering_baseline_closure_report.md` — Round 3 closure report

### Remaining Limitations

1. Each READ/WRITE command independently connects/disconnects — no connection pooling.
2. No select-before-operate or command-termination control models.
3. No Report subscription, GOOSE, SV (separate phase, not MMS polling/read/write).
4. capacity/profile full-protocol orchestration with real hardware not covered.
5. Long-duration stability (> 1000 iterations) not covered.
6. Real MMS device E2E not covered.
7. Report Control Block configured in simulator but unused — not a concern for MMS read/write.

## Related Files

- `tools/source_lab/native/libiec61850/iec61850_mms_client_runner.c` — C 运行器
- `tools/source_lab/native/libiec61850/iec61850_simulator_server.c` — 模拟器服务器
- `src/whale/shared/source/iec61850/backends/base.py` — 后端接口与数据类型
- `src/whale/shared/source/iec61850/backends/libiec61850_backend.py` — 子进程后端
- `src/whale/shared/source/iec61850/reader.py` — 外观
- `src/whale/ingest/adapters/source/iec61850_source_acquisition_adapter.py` — 采集适配器
- `src/whale/ingest/adapters/source/iec61850_source_write_adapter.py` — 写入适配器
- `src/whale/ingest/composition.py` — 依赖注入组合根
- `tools/source_lab/access/runners/registry.py` — 能力注册表
- `tests/unit/test_iec61850_mms_backend.py` — 后端单元测试
- `tests/unit/test_iec61850_source_acquisition_adapter.py` — 采集适配器单元测试
- `tests/unit/test_iec61850_source_write_adapter.py` — 写入适配器单元测试
- `tests/integration/test_ingest_iec61850_mms_source_write.py` — 写入集成测试
- `tools/source_lab/tests/access/test_iec61850_mms_client_runner_write_protocol.py` — 运行器协议测试
