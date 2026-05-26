# ADR-20260524-009: source_lab ServerSimulatorFacade 统一契约

## Status

Accepted (v10 — Round 5-5 final protocol gate and GOOSE/SV CI validation boundary)

## Keywords

- source_lab
- ServerSimulatorFacade
- Simulator
- Protocol
- Factory
- Registry
- ADR-20260524-006

## Context

source_lab 存在多套 simulator 实现：

1. `tools/source_lab/protocols/common/simulators.py` — 基于 Python `_TcpThreadedSimulator` 的轻量 simulator。
2. `tools/source_lab/protocols/opcua/open62541_source_simulator.py` — 基于 open62541 C runner 子进程的 OPC UA simulator。
3. `tools/source_lab/opcua/` — 旧版 OPC UA simulator（已按 ADR-20260524-006 删除）。

各 simulator 接口不统一：

- `SourceSimulator` Protocol（`contracts.py`）：只有 `start()`, `stop()`, `writes()`, `endpoint`, `name`。
- 实际使用时需要分别构造、分别管理生命周期。
- 没有能力矩阵查询，无法静态判断 simulator 是否支持 read/write/subscribe/report。
- 没有统一的错误模型，不同 simulator 报错方式不一致。

## Decision

### 1. 定义 ServerSimulatorFacade Protocol

在 `tools/source_lab/protocols/common/simulator_facade.py` 中定义统一的异步 Protocol：

- `start()` / `stop()` / `health()` — 生命周期。
- `load_points(points)` — 加载点位配置。
- `read(point_keys)` — 读取内部值。
- `write(values)` — 协议写入。
- `subscribe(point_keys)` — 订阅推送。
- `report(point_keys)` — 报表订阅（IEC61850 Report 专用）。
- `update_values(values)` — 内部值注入。

每个方法返回 `SimulatorResult` / `ReadSimulatorResult` / `SimulatorHealth`，其中包含 `SimulatorStatus` 状态码。

### 2. 定义 SimulatorStatus 枚举

NOT_IMPLEMENTED 是合法状态码，不作为异常抛出。其他状态码包括 OK、BAD_REQUEST、ERROR、TIMEOUT、UNAVAILABLE、ALREADY_RUNNING、NOT_RUNNING 等。

### 3. 定义 SimulatorCapabilities

每个 facade 通过 `capabilities` 属性返回 `SimulatorCapabilities` frozen dataclass，声明各操作是否真正实现。

### 4. 默认 NOT_IMPLEMENTED 基类

`BaseSimulatorFacade` 所有方法默认返回 `SimulatorStatus.NOT_IMPLEMENTED`，子类只需 override 真正实现的方法。

### 6. 各协议 facade（Round 3.5 能力矩阵）

| 协议 | 文件 | start | stop | health | load_points | read | write | subscribe | report | update_values |
|------|------|-------|------|--------|-------------|------|-------|-----------|--------|---------------|
| opcua | `protocols/opcua/simulator.py` | ✅ | ✅ | ✅ | ✅ | ✅¹ | ✅² | ✅³ | ❌ | ✅ |
| modbus_tcp | `protocols/modbus/simulator.py` | ✅ | ✅ | ✅ | ✅ | ✅⁴ | ✅⁵ | ❌ | ❌ | ✅ |
| modbus_rtu | `protocols/modbus/simulator.py` | ✅ | ✅ | ✅ | ✅ | ✅¹⁰ | ❌ | ❌ | ❌ | ✅ |
| iec104 | `protocols/iec104/simulator.py` | ✅ | ✅ | ✅ | ✅ | ✅⁶ | ❌ | ❌ | ❌ | ✅ |
| iec61850_mms | `protocols/iec61850/simulator.py` | ✅⁷ | ✅ | ✅ | ✅ | ✅⁸ | ✅⁸ | ❌ | ❌ | ✅ |
| iec61850_report | `protocols/iec61850/simulator.py` | ✅⁷ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅⁹ | ✅⁹ | ✅ |
| iec101 | `protocols/iec101/simulator.py` | ✅ | ✅ | ✅ | ✅ | ✅¹¹ | ❌ | ❌ | ❌ | ✅ |
| mqtt | `protocols/mqtt/simulator.py` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ |
| http_rest | `protocols/http_rest/simulator.py` | ✅ | ✅ | ✅ | ✅ | ✅⑫ | ❌ | ❌ | ❌ | ✅ |
| iec61850_goose | `protocols/iec61850/simulator.py` | ✅⑭ | ✅ | ✅⑭ | ✅ | ❌ | ❌ | ✅⑮ | ❌ | ✅ |
| iec61850_sv | `protocols/iec61850/simulator.py` | ✅⑯ | ✅ | ✅⑯ | ✅ | ❌ | ❌ | ✅⑰ | ❌ | ✅ |

> ① OPC UA read: 通过生产 `OpcUaSourceReader` 真实读取（`prepare_read()` + `read_prepared_raw()`）。
> ② OPC UA write: 通过 open62541 原生 runner stdin 协议写入真实 OPC UA 服务器。
> ③ OPC UA subscribe: 通过 asyncua Client 创建真实订阅（MonitoredItems + DataChangeHandler）
> ④ Modbus TCP read: 优先通过 `NativeInteractiveRunner("modbus_tcp_polling_runner")` READ 命令 FC03 读取；fallback 到 raw TCP socket FC03。
> ⑤ Modbus TCP write: 通过 `NativeInteractiveRunner("modbus_tcp_polling_runner")` 发送 FC06 写寄存器命令。
> ⑥ IEC104 read: 通过生产 `Iec104SourceReader` 真实 interrogation 读取（do_name → IOA 映射）。
> ⑦ IEC61850 MMS/Report start: 启动 C 子进程 `iec61850_simulator_server`（非 Python TCP stub）。
> ⑧ MMS read/write: 通过 `NativeInteractiveRunner("iec61850_mms_client_runner")` 发送 MMS 读/写命令。
> ⑨ Report subscribe/report: 通过 `NativeInteractiveRunner("iec61850_report_runner")` 订阅 RCB 并收集报告事件。
> ⑩ Modbus RTU read: raw TCP socket FC03（RTU-over-TCP gateway 模式，无串口环境适用）。
> ⑪ IEC101 read: TCP gateway 模式发送 CS101 询问帧（C_IC_NA_1），解析 M_ME_NC_1/M_SP_NA_1 ASDU 获取值。
> ⑫ HTTP REST read: 通过 Python urllib HTTP GET 真实读取（绕过 http_proxy 代理环境变量）。
> ⑬ MQTT subscribe: 通过 Python TCP 套接字发起真实 MQTT CONNECT/CONNACK/SUBSCRIBE/SUBACK 握手验证。
> ⑭ GOOSE start/health: 启动 `iec61850_goose_publisher_simulator`，依赖 Linux L2 raw socket / CAP_NET_RAW / 可用 interface。
> ⑮ GOOSE subscribe: 通过 `iec61850_goose_subscriber_runner` 接收真实 GOOSE event；无 raw socket 权限时测试条件 skip，不标记 PASS。
> ⑯ SV start/health: 启动 `iec61850_sv_publisher_simulator`，依赖 Linux L2 raw socket / CAP_NET_RAW / 可用 interface。
> ⑰ SV subscribe: 通过 `iec61850_sv_subscriber_runner` 接收真实 sampled values；无 raw socket 权限时测试条件 skip，不标记 PASS。

#### Round 3 变更摘要

| 变更 | 之前 | 之后 |
|------|------|------|
| MMS read | NOT_IMPLEMENTED | 通过 C 子进程 + NativeInteractiveRunner 真实读取 |
| MMS write | NOT_IMPLEMENTED | 通过 C 子进程 + NativeInteractiveRunner 真实写入 |
| Report subscribe | NOT_IMPLEMENTED | 通过 C 子进程 + NativeInteractiveRunner 订阅 RCB |
| Report report | NOT_IMPLEMENTED | 通过 C 子进程 + NativeInteractiveRunner 收集事件 |
| Modbus TCP write | NOT_IMPLEMENTED | 通过 NativeInteractiveRunner FC06 真实写入 |
| OPC UA write | Python stub | 通过 open62541 原生 runner stdin 真实写入 |
| MMS start | Python TCP stub (返回垃圾数据) | 启动真实 C `iec61850_simulator_server` 子进程 |
| Report start | Python TCP stub (返回垃圾数据) | 启动真实 C `iec61850_simulator_server` 子进程 |

#### Round 3.5 变更摘要

| 变更 | 之前 | 之后 |
|------|------|------|
| OPC UA read | NOT_IMPLEMENTED | 通过生产 OpcUaSourceReader 真实读取 |
| Modbus TCP read | NOT_IMPLEMENTED | 通过 NativeInteractiveRunner READ 命令 + raw TCP FC03 fallback 真实读取 |
| IEC104 read | NOT_IMPLEMENTED | 通过生产 Iec104SourceReader 真实 interrogation 读取 |
| Modbus TCP read 后端 | 无 | C runner `modbus_tcp_polling_runner` 新增 `handle_read_command()`（FC03 读保持寄存器） |
| SimulatorSourceProvider 默认路径 | 旧同步 `_run_simulator_process`（`build_simulator`） | `_run_facade_process`（`create_server_simulator` → facade） |
| SourceSimulatorFleet 进程模型 | 固定使用 `_run_simulator_process` | 新增 `use_facade` 参数，默认 `True`，可选回退旧路径 |
| 协议门禁测试断言 | OPC UA/Modbus TCP/IEC104 read=False | read=True |

#### Round 5-2 变更摘要（2026-05-25）

| 变更 | 之前 | 之后 |
|------|------|------|
| Modbus RTU read | NOT_IMPLEMENTED | raw TCP socket FC03（RTU-over-TCP gateway 模式） |
| IEC101 read | NOT_IMPLEMENTED | TCP gateway 模式 CS101 询问帧 ASDU 解析 |
| ModbusRtuSimulator 寄存器值 | 硬编码 `\x00\x01` | 从 `_values` 字典读取真实值 |
| Iec101Simulator 响应 | 硬编码 ACK | 返回 M_ME_NC_1/M_SP_NA_1 ASDU 真实值 |
| capacity/profile E2E 矩阵 | 4 协议 | 6 协议（+iec101, +modbus_rtu） |
| 串口 native runner 预检 | 只检查二进制 | 检查 USB/ACM 串口设备，无串口时自动回退 Python runner |
| PROTOCOL_CAPABILITIES simulator_write_injection | iec101/modbus_rtu=False | iec101/modbus_rtu=True |

### 6. 工厂注册表

`protocols/registry.py` 新增：

- `create_server_simulator(protocol, source)` — 创建 facade 实例。
- `get_server_simulator_capabilities(protocol)` — 返回能力矩阵。
- `list_server_simulator_protocols()` — 列出已注册协议。

旧版 `get_simulator_factory()` 保持向后兼容。

### 7. 旧的 opcua/ 目录已删除（ADR-20260524-006）

`tools/source_lab/opcua/` 目录已删除，所有内容迁移到 `tools/source_lab/protocols/opcua/`。引用旧路径的导入已更新，`tests/support/source_lab_runtime.py` 的 namespace 映射已指向新路径。

## Consequences

### 正面

1. 所有 simulator 通过统一 `ServerSimulatorFacade` Protocol 类型接入。
2. 能力矩阵可通过 `capabilities` 静态查询，无需启动 simulator。
3. NOT_IMPLEMENTED 是合法返回状态，不抛出异常。
4. 工厂统一：`create_server_simulator("opcua")` 返回正确 facade。
5. 协议别名（如 `modbustcp` → `modbus_tcp`）正常解析。
6. 旧版 `get_simulator_factory()` 不受影响。
7. ADR-20260524-006 的旧目录删除要求已执行。
8. 契约测试覆盖所有 facade（134 tests）。
9. **Round 2：内部字典伪实现已全部替换为 NOT_IMPLEMENTED** — facade 方法只返回真实协议操作结果。
10. **Round 2：SimulatorSourceProvider 支持多协议** — 使用 `list_server_simulator_protocols()` 验证协议，通过 `PROTOCOL_CAPABILITIES` 映射数据库 application_protocol 构建源，通用地址构造（OPC UA 使用 logical_path，其他使用 point key）。
11. **Round 2：一致性测试** — `TestFacadeCapabilitiesConsistency` 验证 facade capabilities 不超出 `PROTOCOL_CAPABILITIES` 声明。
12. **Round 2：真实协议 Smoke 测试** — 8 lifecycle/TCP health/update_values 测试（Modbus TCP/IEC104/IEC61850 MMS/Report）。
13. **Round 3：MMS 真实读写** — MMS read/write 通过 C 子进程 + NativeInteractiveRunner 实现真实协议操作。
14. **Round 3：Report 真实订阅** — Report subscribe/report 通过 C 子进程 + NativeInteractiveRunner 实现真实 RCB 订阅。
15. **Round 3：Modbus TCP 真实写入** — Modbus TCP write 通过 NativeInteractiveRunner FC06 写寄存器实现。
16. **Round 3：Smoke 测试升级** — 新增 MMS read/write/readback、Report subscribe/report、Modbus TCP write/readback、OPC UA write 真实协议验证。
17. **Round 3.5：OPC UA/Modbus TCP/IEC104 真实读** — 三个主要协议 read 从 NOT_IMPLEMENTED 升级为真实协议操作。
18. **Round 3.5：Modbus TCP FC03 read C 支持** — `modbus_tcp_polling_runner.c` 新增 `handle_read_command()`，支持 interactive READ 模式。
19. **Round 3.5：SimulatorSourceProvider 默认路径已迁移** — `SourceSimulatorFleet.create()` 默认 `use_facade=True`，使用 `_run_facade_process`，通过 `create_server_simulator()` → facade 管理子进程生命周期。

### 约束

1. **Round 2**：内部字典读取和伪写入已降级为 NOT_IMPLEMENTED。read/write 不再能通过 facade 直接获取协议值。
2. **Round 2**：subscribe/report 对非订阅协议返回 NOT_IMPLEMENTED（IEC61850 Report 降级）。
3. **Round 2**：SimulatorSourceProvider 的 `_build_source_from_repository` 依赖数据库包含对应协议的服务器条目。
4. **Round 2**：OPC UA 的 open62541 子进程依赖 C 编译器，Smoke 测试在无编译环境时跳过。
5. **Round 3**：MMS/Report 的 C 子进程 `iec61850_simulator_server` 依赖 libiec61850 编译产物，Smoke 测试在无编译环境时跳过。
6. **Round 3**：Modbus TCP write 依赖 `modbus_tcp_polling_runner` C 编译产物；无编译环境时 fallback 为 NOT_IMPLEMENTED。
7. **Round 3.5**：SimulatorSourceProvider 默认使用 `ServerSimulatorFacade` 路径。旧 `_run_simulator_process` 保留为备用路径（`use_facade=False`）。
8. **Round 3.5**：OPC UA / IEC104 read 依赖对应协议的 production client import（`OpcUaSourceReader` / `Iec104SourceReader`），通过延迟导入降低启动失败风险。
9. **Round 3.5**：Modbus TCP read 依赖 `modbus_tcp_polling_runner` C 编译产物；无编译环境时 fallback 到 raw TCP socket FC03。
5. 部分 protocol 的 read/write 基于内部值存储，不涉及真实协议报文。
6. subscribe/report 对于非订阅协议返回 NOT_IMPLEMENTED。
7. GOOSE/SV facade 只开放 start/health/subscribe/update_values；read/write/report 必须返回 NOT_IMPLEMENTED。
8. 异步 facade 使用 `asyncio.to_thread` 包装同步 simulator，适用于 Python 轻量 simulator。

## Rejected Options

### 方案一：扩展现有 SourceSimulator Protocol

拒绝。`contracts.py` 的 `SourceSimulator` 只有生命周期方法，没有 read/write/subscribe 语义。扩展会导致现有实现者全部需要修改。

### 方案二：直接暴露原始 simulator 类

拒绝。不同类型 simulator 构造方式不同、错误处理不同、能力不同。无统一工厂和契约会导致调用方代码分支爆炸。

### 方案三：在 protocols/registry.py 中删除旧版 get_simulator_factory

拒绝。`get_simulator_factory` 仍被 `tools/source_lab/access/providers/simulator.py` 等其他模块使用。保持向后兼容，新增工厂函数不修改旧接口。

## Related Files

### 新增
- `tools/source_lab/protocols/common/simulator_models.py` — 数据模型 / 状态枚举
- `tools/source_lab/protocols/common/simulator_facade.py` — ServerSimulatorFacade Protocol
- `tools/source_lab/protocols/common/_base_facade.py` — 默认 NOT_IMPLEMENTED 基类
- `tools/source_lab/protocols/opcua/simulator.py` — OPC UA facade
- `tools/source_lab/protocols/modbus/simulator.py` — Modbus TCP/RTU facades
- `tools/source_lab/protocols/iec104/simulator.py` — IEC104 facade
- `tools/source_lab/protocols/iec61850/simulator.py` — IEC61850 MMS/Report/GOOSE/SV facades
- `tools/source_lab/protocols/iec101/simulator.py` — IEC101 facade
- `tools/source_lab/protocols/mqtt/simulator.py` — MQTT facade
- `tools/source_lab/protocols/http_rest/simulator.py` — HTTP REST facade
- `tools/source_lab/tests/access/test_server_simulator_facade_contract.py` — 契约测试
- `tools/source_lab/tests/access/test_server_simulator_factory.py` — 工厂测试
- `tools/source_lab/tests/access/test_protocol_directory_structure.py` — 目录结构测试

### 修改
- `tools/source_lab/protocols/registry.py` — 新增 create_server_simulator 等工厂函数
- `tests/support/source_lab_runtime.py` — namespace 重映射到 protocols/opcua/

### Round 2 新增
- `tools/source_lab/tests/access/test_server_simulator_facade_real_protocol_smoke.py` — 真实协议生命周期 smoke 测试（8 tests）

### Round 2 修改
- `tools/source_lab/protocols/opcua/simulator.py` — read 降级为 NOT_IMPLEMENTED，capabilities.read=False
- `tools/source_lab/protocols/modbus/simulator.py` — read/write 降级为 NOT_IMPLEMENTED，capabilities 清理
- `tools/source_lab/protocols/iec104/simulator.py` — read 降级为 NOT_IMPLEMENTED，capabilities 清理
- `tools/source_lab/protocols/iec61850/simulator.py` — read/write/subscribe/report 降级为 NOT_IMPLEMENTED，capabilities 清理
- `tools/source_lab/protocols/iec101/simulator.py` — read 降级为 NOT_IMPLEMENTED，capabilities 清理
- `tools/source_lab/protocols/mqtt/simulator.py` — read 降级为 NOT_IMPLEMENTED
- `tools/source_lab/protocols/http_rest/simulator.py` — read 降级为 NOT_IMPLEMENTED，capabilities 清理
- `tools/source_lab/tests/access/test_server_simulator_facade_contract.py` — 测试断言适配新 capabilities，新增一致性测试
- `tools/source_lab/tests/access/test_server_simulator_factory.py` — 测试断言适配新 capabilities
- `tools/source_lab/access/providers/simulator.py` — 多协议支持重构

### Round 3 修改
- `tools/source_lab/protocols/iec61850/simulator.py` — MMS/Report start 改用 C 子进程；MMS 实现真实 read/write；Report 实现真实 subscribe/report
- `tools/source_lab/protocols/modbus/simulator.py` — Modbus TCP 实现真实 write（NativeInteractiveRunner），capabilities.write=True
- `tools/source_lab/protocols/common/_interactive_runner.py` — NativeInteractiveRunner（从 Round 2 延续）
- `tools/source_lab/tests/access/test_server_simulator_facade_contract.py` — Modbus TCP capabilities 断言更新
- `tools/source_lab/tests/access/test_server_simulator_factory.py` — Modbus TCP capabilities 断言更新
- `tools/source_lab/tests/access/test_server_simulator_facade_real_protocol_smoke.py` — 新增 3 个真实协议 smoke 测试（Modbus TCP write+readback、Report subscribe/report、OPC UA write）
- `tools/source_lab/access/providers/simulator.py` — 移除未使用的 `create_server_simulator` 导入

### Round 3.5 修改

- `tools/source_lab/protocols/modbus/simulator.py` — Modbus TCP 实现真实 read（NativeInteractiveRunner READ + raw TCP FC03 fallback），capabilities.read=True
- `tools/source_lab/protocols/opcua/simulator.py` — OPC UA 实现真实 read（OpcUaSourceReader），capabilities.read=True
- `tools/source_lab/protocols/iec104/simulator.py` — IEC104 实现真实 read（Iec104SourceReader），capabilities.read=True
- `tools/source_lab/native/libmodbus/modbus_tcp_polling_runner.c` — 新增 `handle_read_command()`（FC03 读保持寄存器交互命令）
- `tools/source_lab/fleet.py` — 新增 `_run_facade_process()`、`use_facade` 参数、默认使用 facade 路径
- `tools/source_lab/tests/access/test_server_simulator_facade_contract.py` — OPC UA/Modbus TCP/IEC104 capabilities 断言 `read=True`
- `tools/source_lab/tests/access/test_server_simulator_factory.py` — OPC UA/Modbus TCP capabilities 断言 `read=True`

### 删除
- `tools/source_lab/opcua/` — 旧 OPC UA 目录（ADR-20260524-006）

## Supersedes / Superseded By

None. ADR-20260524-006（协议目录统一治理）的旧目录删除要求已在此 ADR 中最终完成。

## Round 4 — CI E2E 验收（2026-05-25）

### 变更摘要

| 变更 | 之前 | 之后 |
|------|------|------|
| capacity E2E smoke | 未实现（依赖数据库和编译环境） | 通过 _FacadeE2EProvider 绕过数据库、使用 Python lightweight runner，modbus_tcp 验证通过 |
| profile E2E smoke | 未实现 | 同上，modbus_tcp 验证通过 |
| NOT_IMPLEMENTED 验收 | 无专项测试 | 协议级断言 + 工厂级验证 |
| protocol 切换路径验证 | 无 | AST 静态分析验证 capacity.py/profile.py 无协议 if/else |
| 原生 runner 路径 bug | _find_executable 路径指向错误（.parents[4] 应为 .parents[2]） | 已修复，NativeCmdCapacityRunner 可找到编译产物 |
| 原生 runner duration 字段 | native_runner_map 使用 config.duration_s（字段不存在） | 已修复为 config.level_duration_s |

### 测试结果

| 套件 | 结果 |
|------|------|
| test_server_simulator_capacity_profile_e2e.py | 11 passed, 0 skipped（MMS 从 SKIP → PASS），0 failed |
| test_server_simulator_facade_contract.py | 135 passed, 0 failed |
| test_server_simulator_factory.py | 19 passed, 0 failed |
| test_protocol_directory_structure.py | 26 passed, 0 failed |
| test_protocol_production_readiness_gate.py | 17 passed, 0 failed |
| source_lab 全量 access 子集 | 580 passed, 13 skipped, 0 failed |
| source_lab 全量 | 586 passed, 22 skipped, 0 failed |

### 修正（Round 4 multi-protocol closure）

| 问题 | 变更 |
|------|------|
| MMS Python probe 不支持 C 模拟器 | 切换为 NativeCmdCapacityRunner（_Iec61850MmsNativeRunner），构建命令补充 fc 参数 |
| NativeCmdCapacityRunner 不记录时间戳 | _read_output_lines 在解析 SAMPLE 行时记录 time.time()；_NativeSession.response_timestamps 默认改为空列表 |
| _Iec61850MmsNativeRunner 缺少 fc 参数 | build_command 中补充 ep.params.get("fc", "NONE") |
| E2E 测试 MMS 连接参数不匹配 | _E2E_CONNECTION_KWARGS 的 ld_name 从 "LD0" 改为 "Simulator"，新增 params 包含 ln_class/do_name/da_name/fc |

### 测试结果（multi-protocol closure 后）

| 测试 | 结果 |
|------|------|
| modbus_tcp capacity E2E via facade fleet | PASS |
| modbus_tcp profile E2E via facade fleet | PASS |
| iec61850_mms capacity E2E via facade fleet | PASS（之前 SKIP） |
| iec61850_mms profile E2E via facade fleet | PASS（之前 SKIP） |
| NOT_IMPLEMENTED 验收（5 项） | PASS |
| NOT_IMPLEMENTED 工厂验收（2 项） | PASS |
| AST 协议分支验证（2 文件） | PASS |

### 新增文件

- `tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py` — E2E capacity/profile smoke + NOT_IMPLEMENTED 验收 + protocol 切换路径验证

### 修改文件

- `tools/source_lab/access/runners/native_cmd.py` — _find_executable 路径修正（.parents[4] → .parents[2]）；_read_output_lines 新增 SAMPLE 时间戳记录
- `tools/source_lab/access/runners/native_runner_map.py` — duration_s → level_duration_s；_Iec61850MmsNativeRunner 补充 fc 参数
- `tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py` — MMS 改为 NativeCmdCapacityRunner；ld_name 修正为 Simulator；断言升级为 PASS/FLAKY

## Round 4.1 — NativeCmdCapacityRunner 预检与 MMS 多点读取（2026-05-25）

### 变更摘要

| 变更 | 之前 | 之后 |
|------|------|------|
| NativeCmdCapacityRunner 二进制预检 | 构造从不抛异常；registry 的 try/except RuntimeError 是死代码 | 新增 `check_available()` 方法 + `NativeRunnerUnavailableError`；registry 正确捕获并回退 |
| MMS 读取点数 | 仅读 specs[0]（1 个 MMS 变量/次） | 读全部 specs 多点（3 个 MMS 变量/次），C CLI 新增 multi-point 格式 |
| value_count 报告 | `value_count = session.ok_reads`（SAMPLE 行数而非实际值） | 从 SUMMARY 第 3 字段解析总读取值；fallback 到 ok_reads |
| C runner CLI 协议 | 仅支持 argc == 11 的单点格式 | 新增 `argc >= 12` multi-point 格式：`<host> <port> <ied> <ld> <interval_ms> <count> <point_count> [<ln> <do> <da> <fc>]...`，保持 argc == 11 向后兼容 |

### 测试结果

| 套件 | 结果 |
|------|------|
| capacity/profile E2E（modbus_tcp + iec61850_mms） | 4 passed, 0 failed |
| NOT_IMPLEMENTED 验收 + AST 验证 | 7 passed, 0 failed |
| NativeCmdCapacityRunner 预检（新增） | 7 passed, 0 failed |
| source_lab 全量 | 593 passed, 22 skipped, 0 failed |

### 新增文件

- `tools/source_lab/tests/access/test_native_cmd_runner_preflight.py` — NativeCmdCapacityRunner 预检单元测试（7 tests）

### 修改文件

- `tools/source_lab/access/runners/native_cmd.py` — 新增 `NativeRunnerUnavailableError`、`check_available()`、`value_count` 字段、SUMMARY 值计数解析
- `tools/source_lab/access/runners/registry.py` — `build_capacity_runner()` 调用 `check_available()`，捕获 `NativeRunnerUnavailableError`
- `tools/source_lab/access/runners/native_runner_map.py` — `_Iec61850MmsNativeRunner.build_command()` 改为迭代所有 specs 生成 multi-point CLI 参数
- `tools/source_lab/native/libiec61850/iec61850_mms_client_runner.c` — 新增 `run_cli_polling_mode_multi()` 多点读取函数；`main()` 支持 multi-point CLI 格式

## Round 5-1 — OPC UA / IEC104 capacity/profile E2E 全协议收口（2026-05-25）

### 变更摘要

| 变更 | 之前 | 之后 |
|------|------|------|
| IEC104 facade start | Python TESTFR-only TCP stub | 真实 C `iec104_simulator_server` 子进程 + Python Iec104Simulator 数据持有器 |
| IEC104 capacity E2E | 未纳入 E2E 矩阵 | 已纳入，使用 `NativeCmdCapacityRunner`（`_Iec104NativeRunner`）通过 C `iec104_client_runner` interrogation 真实测量 |
| IEC104 profile E2E | 未纳入 | 已纳入，同上 |
| IEC104 E2E runner | `Iec104PollingRunner()`（仅 TESTFR） | `build_capacity_runner("iec104")`（真实 C runner） |
| OPC UA capacity E2E | 未纳入 E2E 矩阵 | 已纳入，使用 `OpcUaOpen62541CapacityRunner` 通过 `open62541_client_runner` 真实测量 |
| OPC UA profile E2E | 未纳入 | 已纳入，同上 |
| OPC UA E2E runner | 无（未纳入） | `OpcUaOpen62541CapacityRunner()` |
| OPC UA 原生 runner 路径 bug | `resolve_runner_path()` 使用 `parents[1]` 指向 `protocols/native/build/`（错误目录） | 使用 `parents[2]` 指向 `native/build/`（正确目录） |
| OPC UA facade health() | `_, host, port = endpoint.rpartition(":")` 将 host 赋值为 `:` | 修正为 `host, _, port_str`，host 恢复正常值 |
| E2E 测试矩阵 | 2 协议（modbus_tcp, iec61850_mms） | 4 协议（modbus_tcp, iec61850_mms, iec104, opcua） |

### 测试结果

| 套件 | 结果 |
|------|------|
| capacity/profile E2E（4 协议全矩阵） | 15 passed, 0 failed |
| OPC UA health smoke（test_opcua_facade_with_native_simulator） | PASS（之前 SKIP→FAIL，因路径 bug 和 health bug） |
| 真实协议 smoke 全量 | 12 passed, 1 skipped, 0 failed |
| NOT_IMPLEMENTED 验收 + AST 验证 | 7 passed, 0 failed |
| NativeCmdCapacityRunner 预检 | 7 passed, 0 failed |
| 目录结构 | 26 passed, 0 failed |
| 生产准入门禁 | 17 passed, 0 failed |
| source_lab access 全量 | 593 passed, 11 skipped, 0 failed, 0 warnings |
| source_lab 全量 | 599 passed, 20 skipped, 0 failed, 0 warnings |
| 项目级 unit 测试 | 305 passed, 0 failed |
| 项目级 integration 测试 | 35 passed, 0 failed |

### 修正

| 问题 | 文件 | 变更 |
|------|------|------|
| OPC UA 原生 runner 路径错误 | `open62541_source_simulator.py:525` | `parents[1]` → `parents[2]` |
| OPC UA health() 端点解析 host 为 `:` | `protocols/opcua/simulator.py:74` | `_, host, port` → `host, _, port_str` |
| PytestUnknownMarkWarning for `@pytest.mark.slow` | `pyproject.toml` | 新增 `slow` marker 注册 |

### 修改文件

- `tools/source_lab/protocols/iec104/simulator.py` — IEC104 facade 完整重写：Python stub + C iec104_simulator_server 子进程双架构
- `tools/source_lab/protocols/opcua/open62541_source_simulator.py` — `resolve_runner_path()` 路径修正（`parents[1]` → `parents[2]`）
- `tools/source_lab/protocols/opcua/simulator.py` — `health()` 端点解析 bug 修正
- `tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py` — E2E 矩阵从 2 协议扩展为 4 协议（iec104, opcua 加入）；iec104 runner 改用 `build_capacity_runner`；断言统一 PASS/FLAKY
- `pyproject.toml` — 注册 `slow` pytest marker

## Round 5-3 — MQTT/HTTP REST/OPC UA 订阅闭环与报告模板治理（2026-05-25）

### 变更摘要

| 变更 | 之前 | 之后 |
|------|------|------|
| HTTP REST facade read | NOT_IMPLEMENTED | 通过 Python urllib HTTP GET 真实读取（绕过 http_proxy 代理） |
| MQTT facade subscribe | Python stub（返回 OK 不验证） | 真实 TCP CONNECT/CONNACK/SUBSCRIBE/SUBACK 握手验证 |
| OPC UA facade subscribe | Python stub（返回 OK） | 通过 asyncua Client 创建真实订阅（MonitoredItems + DataChangeHandler） |
| HTTP REST polling runner | urllib.urlopen（受 http_proxy 影响） | build_opener(ProxyHandler({})) 绕过代理 |
| MQTT PROTOCOL_CAPABILITIES | simulator_write_injection=False | simulator_write_injection=True |
| HTTP REST PROTOCOL_CAPABILITIES | simulator_write_injection=False | simulator_write_injection=True |
| 报告模板 | ai_shared/reports/_template.md | ai_shared/templates/default_report_template.md |
| 报告模板门禁 | 无 | 新增门禁测试 test_ai_shared_report_template_references.py（5 cases） |
| reporting.md 规则 | 默认模板优先 | prompt 格式优先于默认模板 |
| E2E 测试矩阵 | 7 协议 polling + 4 协议 streaming | 8 协议 polling（+http_rest）+ 5 协议 streaming（+mqtt/+opcua） |
| Contract 测试 | http_rest/iec101/modbus_rtu read=False | http_rest/iec101/modbus_rtu read=True |
| 协议矩阵测试 | iec101/modbus_rtu 固定 native 名称 | 支持串口回退（无串口 → Python lightweight runner） |

### Round 5-3 决议收口

1. HTTP REST facade `read()` 已从 NOT_IMPLEMENTED 升级为真实 HTTP GET。
2. MQTT facade `subscribe()` 已从 stub 升级为真实 MQTT CONNECT/SUBSCRIBE 握手。
3. OPC UA facade `subscribe()` 已从 stub 升级为真实 asyncua subscription。
4. polling E2E 已覆盖 8 个协议。
5. streaming E2E 已覆盖 5 个协议。
6. 报告模板默认路径已迁移到 `ai_shared/templates/default_report_template.md`。
7. 反馈规则统一为：prompt 明确反馈格式时优先使用 prompt 格式；prompt 未指定反馈格式时才使用默认模板。

### 测试结果

| 套件 | 结果 |
|------|------|
| capacity/profile E2E（8 协议全矩阵） | 25 passed, 0 failed（含 streaming 新增） |
| 真实协议 smoke | 12 passed, 1 skipped, 0 failed |
| 报告模板门禁 | 5 passed, 0 failed |
| 契约测试（TestCapabilitiesReflectImplementation） | 13 passed, 0 failed |
| source_lab 全量 | 614 passed, 20 skipped, 0 failed |
| 项目级 unit 测试 | 305 passed, 0 failed |
| 项目级 integration 测试 | 35 passed, 0 failed |

### 新增文件

- `tools/source_lab/tests/access/test_ai_shared_report_template_references.py` — 报告模板路径治理门禁测试（5 cases）

### 修改文件

- `tools/source_lab/protocols/http_rest/simulator.py` — 实现真实 HTTP GET read()，绕过 http_proxy 代理
- `tools/source_lab/protocols/mqtt/simulator.py` — 实现真实 MQTT CONNECT/SUBSCRIBE 握手验证订阅
- `tools/source_lab/protocols/opcua/simulator.py` — subscribe() 从 stub 升级为 asyncua 真实订阅
- `tools/source_lab/access/runners/http_rest_polling.py` — urlopen → build_opener(ProxyHandler({})) 绕过代理
- `tools/source_lab/access/runners/registry.py` — PROTOCOL_CAPABILITIES MQTT/HTTP REST simulator_write_injection=True
- `tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py` — 新增 http_rest polling + mqtt/opcua streaming E2E
- `tools/source_lab/tests/access/test_server_simulator_facade_contract.py` — http_rest/iec101/modbus_rtu read=True 断言更新
- `tools/source_lab/tests/access/test_protocol_matrix.py` — 支持串口回退场景的 runner 名断言

> 注：本节对 `ai_shared/reports/_template.md` 的提及仅用于记录历史迁移，不代表当前运行配置仍引用旧路径。

## Round 5-4 — IEC61850 GOOSE/SV event and sampled-value closure（2026-05-25）

### Implementation Status

| 项目 | 状态 |
|------|------|
| pytest-asyncio 依赖治理 | `pyproject.toml` dev 依赖新增 `pytest-asyncio>=1.3,<2.0` |
| GOOSE facade | start/health/subscribe/update_values 已接入 native publisher/subscriber；read/write/report 保持 NOT_IMPLEMENTED |
| SV facade | start/health/subscribe/update_values 已接入 native publisher/subscriber；read/write/report 保持 NOT_IMPLEMENTED |
| GOOSE native runner | `iec61850_goose_publisher_simulator` 与 `iec61850_goose_subscriber_runner` target 可构建 |
| SV native runner | `iec61850_sv_publisher_simulator` 与 `iec61850_sv_subscriber_runner` target 可构建 |
| streaming capacity/profile | GOOSE/SV 已纳入 streaming E2E matrix；当前非 CAP_NET_RAW 环境条件 skip，不写 PASS |
| raw socket / CI 条件 | Linux L2 interface + CAP_NET_RAW/root；CI 可运行 `pytest -k "goose or sv" tools/source_lab/tests/access -q` |
| 最终 Round 5/5 影响 | 剩余工作聚焦协议矩阵最终验收、文档一致性与可选 load 环境验证 |

### NOT_IMPLEMENTED 边界

GOOSE / SV 只支持事件或采样订阅语义。`read()`、`write()`、`report()` 必须返回 `SimulatorStatus.NOT_IMPLEMENTED`；不得把 TCP health、进程启动或零事件采样视为协议 PASS。

## Round 5-5 — source_lab final protocol gate and GOOSE/SV CI validation（2026-05-25）

### Implementation Status

| 项目 | 状态 |
|------|------|
| 全协议 final capability matrix | 已新增最终矩阵门禁，覆盖 opcua、modbus_tcp、modbus_rtu、iec101、iec104、iec61850_mms、iec61850_report、iec61850_goose、iec61850_sv、mqtt、http_rest |
| 已完成协议 E2E | polling 保持 7 协议矩阵；streaming 保持 mqtt/opcua/iec61850_report，并纳入 GOOSE/SV 条件矩阵 |
| GOOSE/SV native target | publisher/subscriber target 可构建；四个 L2 binary 提供 `--version` 非网络探针 |
| GOOSE/SV 当前环境结果 | 当前执行环境 uid=1000，非 root，`capsh` 有效能力为空，无有效 CAP_NET_RAW；GOOSE/SV 真事件/真采样不得标记 PASS，状态为 framework closure + CI pending |
| GOOSE/SV CI 条件 | Linux runner 需 root 或 CAP_NET_RAW、可用 L2 interface（建议 `SOURCE_LAB_L2_INTERFACE=lo`）后运行 `sudo -E env SOURCE_LAB_L2_INTERFACE=lo pytest -k "goose or sv" tools/source_lab/tests/access -q` |
| NOT_IMPLEMENTED 边界 | GOOSE/SV read/write/report 继续返回 NOT_IMPLEMENTED；MQTT 不声明 read/write/report；HTTP REST 不声明 write/subscribe/report |
| production ready 区分 | source_lab simulator closure 不等同 ingest production ready；GOOSE/SV 不接入 ingest，不声明 production_client_subscribe=True |
| 治理回归 | pytest-asyncio 仍为测试依赖；报告模板默认路径仍为 `ai_shared/templates/default_report_template.md`，旧 `_template.md` 不恢复 |

### Final Matrix Boundary

Round 5-5 的最终门禁只允许把普通环境可复现通过的协议写为 CI verified。GOOSE/SV 只有在具备 root/CAP_NET_RAW 与可用 interface 的 CI runner 上接收到 event/sample count > 0 时，才可从 `framework closure + CI pending` 升级为 `CI verified`；target 构建、进程启动、TCP health 或零事件输出均不能替代真实协议事件/采样。
