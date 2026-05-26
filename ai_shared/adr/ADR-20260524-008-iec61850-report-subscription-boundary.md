# ADR-20260524-008: IEC 61850 Report 订阅采集第一闭环

## Status

Accepted (v2 — Round 2 completed)

## Keywords

- IEC 61850
- Report
- Subscription
- RCB
- Event
- Streaming
- URCB

## Context

IEC 61850 Report 是 IEC 61850 标准定义的订阅/事件能力，通过 ReportControlBlock (RCB) 配置数据集的订阅关系，由服务器主动推送数据变化。Report 与 MMS polling read/write 是不同能力：

1. MMS polling read/write 是客户端驱动的请求-响应模式。
2. Report 是服务器驱动的发布-订阅模式。
3. Report 通过 RCB 的 `RptEna` 属性启用，数据变化通过回调通知。

前一阶段已完成 IEC61850 MMS production read/write 收口（ADR-20260524-007）。Report 订阅作为独立能力，需要独立文件、独立 backend、独立 adapter，不得与 MMS 共享实现。

## Decision

### 1. Report 是 subscription/event 能力，不属于 MMS write

Report 订阅通过 `SourceAcquisitionPort.start_subscription()` 接入 ingest，不通过 `SourceWritePort`。这符合 ADR-20260523-003 中 read/acquisition 与 write/control 分离的约定。

### 2. Report 使用 stdin/stdout 子进程运行器

与 MMS backend 一致，Report 也使用 C 子进程运行器（`iec61850_report_runner`）通过 stdin/stdout 协议通信：

**stdout 协议行：**

```
READY                                — 连接并订阅成功
REPORT\t<rcb>\t<ts>\t<seq>\t<n>\t<v1>\t<v2>…  — 报告事件
ERROR\t<reason>                      — 错误
STOPPED                              — 正常停止
```

**stdin 命令：**

```
QUIT                                 — 停止订阅
```

支持 `--version` 参数。

**运行器不输出任何非协议行到 stdout，stderr 承载诊断信息。**

### 3. Report/GOOSE/SV 分离

- Report：已完成第一闭环。`production_client_subscribe=true`，通过 `iec61850_report_runner` 实现。
- GOOSE：仍为 `planned_native_runner`，在 registry 中明确标记为未实现。
- SV：仍为 `planned_native_runner`，在 registry 中明确标记为未实现。

Report 的完成不代表 GOOSE/SV 完成。

### 4. Reconnect 与异常传播（Round 2）

Round 2 在 backend 层面实现了自动 reconnect：

1. `LibIec61850ReportBackend` 在 reader loop 检测到 stdout EOF（子进程异常退出）时触发 `_on_unexpected_exit`。
2. 非 `_closed` 状态下，按指数退避（1s, 2s, ... max 5s）重新启动子进程，最多 `max_reconnect_attempts` 次（默认 0 = 不重连）。
3. 重连成功通过 `error_callback("reconnected")` 通知 adapter。
4. 重连失败或重试用尽通过 `error_callback("subscription_terminated:...")` 通知 adapter。
5. ERROR 协议行（非致命）直接转发 `error_callback`，不触发重连。
6. Adapter 端 `_ReportSubscriptionHandle` 的 `closed` 属性和 `error` 属性暴露终止状态，`_mark_closed` 在收到 `subscription_terminated` 时调用。
7. `max_reconnect_attempts` 通过 `execution.params` 传递，默认 1 次。

异常传播链路：
```
C runner stdout EOF
  → backend._on_unexpected_exit()
    → 尝试重连（如果 enabled）
      → 成功: error_callback("reconnected")
      → 失败: error_callback("subscription_terminated:reconnect_failed:...")
    → 不重连: error_callback("subscription_terminated:...")
      → handle._mark_closed() → handle.closed = True
```

### 5. 文件结构

```
src/whale/shared/source/iec61850/
├── backends/
│   ├── report_base.py               — RawReportEvent 类型
│   └── libiec61850_report_backend.py — Report 子进程 backend
└── report_reader.py                  — Iec61850ReportSourceReader facade

src/whale/ingest/adapters/source/
└── iec61850_report_source_acquisition_adapter.py  — ingest adapter

tools/source_lab/native/libiec61850/
└── iec61850_report_runner.c          — C 子进程运行器（已重写协议）
```

### 6. registry 能力标记

`iec61850_report` 新增：
- `production_client_subscribe: true`
- `supported_subscription_operations: ("report_subscription",)`
- `unsupported_subscription_operations: ("polling_read", "goose", "sv")`
- `production_client_write` 保持 `false`

`iec61850_mms` 不受 Report 实现影响。
`iec61850_goose` / `iec61850_sv` 仍为 `planned_native_runner`。

## Consequences

### 正面（Round 1 + Round 2）

1. IEC61850 Report 订阅第一闭环可运行，通过 simulator 验证。
2. native report runner 协议测试通过（`--version`、stdout noise=0、REPORT 解析、QUIT 停止）。
3. shared/source report backend 单元测试通过（含 reconnect、error callback）。
4. ingest report acquisition adapter 单元测试通过（含 handle closed、reconnect 配置）。
5. integration 能收到真实 Report event。
6. stdout noise = 0。
7. MMS / OPC UA / Modbus TCP / IEC104 回归全部通过。
8. registry 不误标 GOOSE/SV。
9. **Round 2: 自动 reconnect 实现** — exponential backoff + max_attempts 控制。
10. **Round 2: 异常传播** — ERROR 协议行、unexpected exit、subscription_terminated 通过 error_callback 传播。
11. **Round 2: 接入 composition** — `Iec61850ReportSourceAcquisitionAdapter` 注册到 `resolved_acquisition_registry`。
12. **Round 2: 生产门禁验收** — 13 项 gate tests（二进制存在、version、连接 READY、event 接收、seq_num 单调性、stdout noise=0、registry 标记）。
13. **Round 2: 短周期稳定性 smoke** — 8 秒内至少接收 5 个 REPORT event。
14. **Round 3: source_lab load 测试隔离** — `@pytest.mark.load` 测试通过 conftest 自动跳过，需要 `-m load` 显式执行。
15. **Round 3: 测试补充（共 +8 tests）** — reconnect failure 测试、unexpected STOPPED error 测试、dataset mapping log warning 验证（values 不足 / 超出）、quality/timestamp/node_key 稳定性、composition 注册验证（含 alias 和 write registry 排除验证）。
16. **Round 3: 回归确认** — unit 305 passed, integration 35 passed, access 379 passed, 4 协议 regression 18 passed, Report 专项 88 passed。

### 约束（持续）

1. 不支持 GOOSE / SV。
2. 不支持 buffered report (BRCB)，只测试了 unbuffered (URCB)。
3. 不支持 data set 动态映射；report event values 按 data set 顺序映射到 items。
4. reconnect 在 backend 层实现，不涉及 `SubscriptionAcquisitionRole` 的 baseline read 流程。
5. source_lab 中 `@pytest.mark.load` 标记的测试（5 文件，含 multi-server 容量和 profile）不属于 gate 测试，默认被跳过。

## Rejected Options

### 方案一：把 Report 当成 MMS read 实现

拒绝。Report 是服务器推送的订阅能力，与 MMS request-response 语义不同。使用 MMS polling 模拟 Report 会引入不必要的延迟和带宽浪费。

### 方案二：在现有 MMS backend 中增加 Report 能力

拒绝。MMS backend 围绕 command-response 模式设计（connect → read/write → disconnect）。Report 需要长连接、异步回调、不同生命周期管理。混入 MMS backend 会破坏现有逻辑。

### 方案三：使用 Python 纯实现 Report 客户端

拒绝。libiec61850 C 库已提供完整的 `IedConnection_installReportHandler`、`ClientReportControlBlock` API。复用 C runner 方案保持与 MMS backend 一致的架构风格。

## Related Files

### Round 1

- `tools/source_lab/native/libiec61850/iec61850_report_runner.c` — C 运行器
- `tools/source_lab/native/libiec61850/iec61850_simulator_server.c` — 模拟器（已配置 RCB）
- `src/whale/shared/source/iec61850/backends/report_base.py` — Report 事件类型
- `src/whale/shared/source/iec61850/backends/libiec61850_report_backend.py` — 子进程 backend
- `src/whale/shared/source/iec61850/report_reader.py` — facade
- `src/whale/ingest/adapters/source/iec61850_report_source_acquisition_adapter.py` — ingest adapter
- `tools/source_lab/access/runners/registry.py` — 能力注册表
- `tools/source_lab/tests/access/test_iec61850_report_runner_protocol.py` — 协议测试
- `tests/unit/test_iec61850_report_backend.py` — backend 单元测试
- `tests/unit/test_iec61850_report_acquisition_adapter.py` — adapter 单元测试
- `tests/integration/test_ingest_iec61850_report_subscription.py` — 集成测试

### Round 2 (新增 / 修改)

- `src/whale/ingest/composition.py` — composition 注册 Report adapter
- `tools/source_lab/tests/access/test_iec61850_report_capacity_profile_gate.py` — 生产门禁验收 gate tests
- `tools/source_lab/tests/access/test_protocol_production_readiness_gate.py` — 生产就绪门禁（新增 iec61850_report 路径）

## Supersedes / Superseded By

None.
