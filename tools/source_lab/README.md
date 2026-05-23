# source_lab Multi-Protocol Source Access Lab

## 1. Positioning

`tools/source_lab` 是 Whale 的现场 source access 实验室。

职责：
- 模拟现场 source（OPC UA / Modbus / IEC 60870 / IEC 61850 / MQTT / HTTP REST）
- 执行 probe（连通性探测）、profile（单配置诊断）、capacity（容量扫描）
- 验证接入链路、输出容量和诊断报告
- 通过 pytest 对注册表、runner、CLI、多协议集成进行自动化验证

不是生产 ingest 主链路，不修改 `src/whale`。

当前支持多协议测试闭环，但不是所有协议都有完整工业标准栈实现。
协议能力模型已从 protocol-only 升级为 **application_protocol + service_type + transport** 三元组。

具体实现等级见第 5 节"协议能力矩阵"。

### 1.1 关键术语

| 术语 | 说明 |
| --- | --- |
| **application_protocol** | 协议族，如 OPC_UA、MODBUS、IEC61850 |
| **service_type** | 协议族下的服务类型，如 READ、GOOSE、REPORT |
| **transport** | 传输层类型，如 TCP、SERIAL、ETHERNET_L2 |
| **access_mode** | 访问模式大类：polling（轮询）、streaming（订阅） |
| **current_implementation_level** | 当前实现等级 |
| **target_implementation_level** | 目标实现等级（一次性到位目标） |

## 2. Logical Architecture

```
CLI Layer                                    # CLI 入口
  field_probe.py                               - 连通性探测
  field_capacity.py                            - 容量扫描（polling/subscribe）
  field_profile.py                             - 单配置诊断 profile
        |
Application Service Layer                   # 应用服务编排
  access/probe.py                             - probe 服务
  access/field_capacity.py                    - capacity 服务
  access/profile.py                           - profile 服务
  access/capacity.py                          - capacity 编排
        |
Provider Layer                              # source 运行时规格构建
  access/providers/base.py                   - 基类与 DTO
  access/providers/field.py                  - 由 TSV 构建 runtime source
  access/providers/file_field.py             - 由导出文件构建
  access/providers/simulator.py              - 由 simulator 规格构建
  access/providers/expanded_field.py         - runtime 展开
        |
Runner Layer                                # 协议 runner 实现
  access/runners/registry.py                  - 多协议注册表与工厂（含 SERVICE_CAPABILITIES）
  access/runners/base.py                      - CapacityRunner / SubscriptionRunner 协议
  access/runners/open62541_serial_polling.py  - OPC UA polling（调用 native executable）
  access/runners/open62541_subscription.py    - OPC UA subscribe（调用 native executable）
  access/runners/generic_polling.py           - Python 通用 polling 基类
  access/runners/generic_streaming.py         - Python 通用 streaming 基类
  access/runners/modbus_tcp_polling.py        - Modbus TCP polling（native libmodbus runner）
  access/runners/modbus_rtu_polling.py        - Modbus RTU polling（native libmodbus runner）
  access/runners/iec101_polling.py            - IEC101 polling（native lib60870 runner）
  access/runners/iec101_event.py              - IEC101 event（native lib60870 runner）
  access/runners/iec104_polling.py            - IEC104 polling（native lib60870 runner）
  access/runners/iec104_event.py              - IEC104 event（native lib60870 runner）
  access/runners/iec61850_mms_polling.py      - IEC61850 MMS polling（native libiec61850 runner）
  access/runners/iec61850_report.py           - IEC61850 Report（native libiec61850 runner）
  access/runners/mqtt_subscription.py         - MQTT subscribe（Python socket）
  access/runners/http_rest_polling.py         - HTTP REST polling（Python urllib）
  access/runners/native_process.py            - native 子进程管理基类
  access/runners/protocol.py                  - stdout/stderr 协议解析
        |
Protocol Simulator Layer                   # simulator 实现
  factory.py                                  - 协议 simulator 工厂
  fleet.py                                    - 多进程 fleet 管理
  protocols/registry.py                       - 协议 simulator 注册表
  protocols/common/simulators.py              - Modbus/IEC101/IEC104/IEC61850/MQTT/HTTP simulator
  protocols/common/point_mapping.py           - 点映射工具
  opcua/open62541_source_simulator.py         - OPC UA open62541 simulator（native 进程）
  opcua/address_space.py                      - OPC UA address space 构建
        |
Native Runner Layer                        # C executable runner（四个协议族）
  native/open62541/                           - OPC UA open62541 C runners
    open62541_client_runner.c                   - polling runner
    open62541_subscription_runner.c             - subscription runner
    open62541_simulator_server.c               - simulator server
  native/libmodbus/                           - Modbus TCP/RTU C runners & simulator
    modbus_tcp_polling_runner.c                 - Modbus TCP polling
    modbus_rtu_polling_runner.c                 - Modbus RTU polling
    modbus_simulator_server.c                  - Modbus TCP simulator
  native/lib60870/                            - IEC 60870 (101/104) C runners & simulators
    iec104_client_runner.c                      - IEC104 polling client
    iec104_event_runner.c                       - IEC104 event subscriber
    iec104_simulator_server.c                   - IEC104 server simulator
    iec101_client_runner.c                      - IEC101 serial client
    iec101_event_runner.c                       - IEC101 event receiver
    iec101_simulator_slave.c                    - IEC101 serial slave
  native/libiec61850/                         - IEC 61850 MMS/GOOSE/SV C runners & simulators
    iec61850_mms_client_runner.c                - MMS polling client
    iec61850_report_runner.c                    - Report subscription runner
    iec61850_goose_subscriber_runner.c          - GOOSE L2 subscriber
    iec61850_goose_publisher_simulator.c        - GOOSE publisher simulator
    iec61850_sv_subscriber_runner.c             - Sampled Values L2 subscriber
    iec61850_sv_publisher_simulator.c           - SV publisher simulator
    iec61850_simulator_server.c                 - MMS/Report IedServer simulator
  native/CMakeLists.txt                       - CMake 构建（所有协议的 native runner）
  native/README.md                            - native runner 协议说明
        |
Test Layer                                  # 自动化测试
  tests/                                       - pytest 测试套件
  tests/access/                                - registry / probe / profile / capacity / CLI 测试
  tests/fixtures/                              - TSV 测试夹具
  tests/support/                               - 测试辅助函数
```

## 3. Physical Architecture

```
tools/source_lab/
├── README.md                             # 本文件
├── __init__.py                           # 包初始化
├── contracts.py                          # SourceSimulator 协议接口
├── factory.py                            # 协议 simulator 工厂
├── fleet.py                              # 多进程 fleet 管理
├── model.py                              # SimulatedSource / SimulatedPoint 模型
├── sources.py                            # 端口分配策略
├── field_capacity.py                     # CLI: 容量扫描
├── field_probe.py                        # CLI: 连通性探测
├── field_profile.py                      # CLI: 单配置诊断
│
├── access/                               # 核心 access 逻辑
│   ├── __init__.py
│   ├── capacity.py                       # 容量场景编排
│   ├── config.py                         # 环境变量配置
│   ├── field_capacity.py                 # field capacity 服务
│   ├── probe.py                          # probe 服务（多协议 handshake）
│   ├── profile.py                        # profile 服务
│   ├── README.md                         # 模块说明
│   │
│   ├── common/                           # 共享辅助
│   │   ├── access_model.py               # AccessBatch / AccessMode
│   │   ├── cpu.py                        # CPU 映射
│   │   ├── io.py                         # TSV / JSON I/O
│   │   ├── progress.py                   # 进度条
│   │   ├── scheduling.py                 # RunnerEndpointPlan
│   │   ├── table.py                      # 表格渲染
│   │   └── utils.py                      # 工具函数
│   │
│   ├── polling/                          # polling 容量/诊断
│   │   ├── capacity.py                   # polling 容量扫描执行
│   │   ├── capacity_rows.py              # 容量结果行构建
│   │   ├── metrics.py                    # polling 指标
│   │   ├── model.py                      # CapacityMode / TickResult
│   │   ├── profile.py                    # polling profile
│   │   ├── reporter.py                   # polling 报告
│   │   └── worker.py                     # polling worker
│   │
│   ├── subscribe/                        # subscribe 容量/诊断
│   │   ├── capacity.py                   # subscribe 容量扫描执行
│   │   ├── capacity_model.py             # subscribe 能力模型
│   │   ├── capacity_plan.py              # 容量探索计划
│   │   ├── capacity_rows.py              # 容量结果行构建
│   │   ├── capacity_scan.py              # 尝试选择
│   │   ├── metrics.py                    # subscribe 指标
│   │   ├── model.py                      # SubscribeScanConfig
│   │   ├── profile.py                    # subscribe profile
│   │   ├── reporter.py                   # subscribe 报告
│   │   ├── scan.py                       # 扫描核心
│   │   └── worker.py                     # subscribe worker
│   │
│   ├── providers/                        # source 运行时规格
│   │   ├── base.py                       # SourceRuntimeSpec
│   │   ├── expanded_field.py             # 运行时展开
│   │   ├── field.py                      # TSV field provider
│   │   ├── file_field.py                 # 文件 field provider
│   │   └── simulator.py                  # simulator provider
│   │
│   └── runners/                          # 协议 runner 实现
│       ├── registry.py                   # 协议注册表与工厂（含 PROTOCOL_CAPABILITIES + SERVICE_CAPABILITIES）
│       ├── base.py                       # CapacityRunner / SubscriptionRunner
│       ├── generic_polling.py            # Python 通用 polling 基类
│       ├── generic_streaming.py          # Python 通用 streaming 基类
│       ├── open62541_serial_polling.py   # OPC UA polling -> native executable
│       ├── open62541_subscription.py     # OPC UA subscribe -> native executable
│       ├── modbus_tcp_polling.py         # Modbus TCP -> native libmodbus runner
│       ├── modbus_rtu_polling.py         # Modbus RTU -> native libmodbus runner
│       ├── iec101_polling.py             # IEC101 polling -> native lib60870 runner
│       ├── iec101_event.py               # IEC101 event -> native lib60870 runner
│       ├── iec104_polling.py             # IEC104 polling -> native lib60870 runner
│       ├── iec104_event.py               # IEC104 event -> native lib60870 runner
│       ├── iec61850_mms_polling.py       # IEC61850 MMS -> native libiec61850 runner
│       ├── iec61850_report.py            # IEC61850 Report -> native libiec61850 runner
│       ├── mqtt_subscription.py          # MQTT subscribe（Python socket）
│       ├── http_rest_polling.py          # HTTP REST（Python urllib）
│       ├── native_process.py             # native 子进程管理
│       └── protocol.py                   # stdout/stderr 协议解析
│
├── opcua/                                # OPC UA 专用（open62541）
│   ├── __init__.py
│   ├── address_space.py                  # OPC UA address space
│   └── open62541_source_simulator.py     # open62541 simulator wrapper
│
├── protocols/                            # 多协议 simulator
│   ├── registry.py                       # 协议 simulator 注册表
│   ├── common/
│   │   ├── point_mapping.py              # 点映射
│   │   └── simulators.py                 # Modbus / IEC101/104/61850 / MQTT / HTTP simulator
│   ├── modbus/
│   │   └── __init__.py
│   ├── iec101/
│   │   └── __init__.py
│   ├── iec104/
│   │   └── __init__.py
│   ├── iec61850/
│   │   └── __init__.py
│   ├── mqtt/
│   │   └── __init__.py
│   └── http_rest/
│       └── __init__.py
│
├── native/                               # C native runner（四个协议族）
│   ├── CMakeLists.txt                    # 21 targets, 所有协议的 native runner
│   ├── README.md                         # native runner 协议说明
│   ├── open62541/                        # OPC UA C 源码
│   │   ├── open62541_client_runner.c
│   │   ├── open62541_subscription_runner.c
│   │   └── open62541_simulator_server.c
│   ├── libmodbus/                        # Modbus TCP/RTU C 源码
│   │   ├── modbus_tcp_polling_runner.c
│   │   ├── modbus_rtu_polling_runner.c
│   │   └── modbus_simulator_server.c
│   ├── lib60870/                         # IEC 60870 (101/104) C 源码
│   │   ├── iec104_client_runner.c
│   │   ├── iec104_event_runner.c
│   │   ├── iec104_simulator_server.c
│   │   ├── iec101_client_runner.c
│   │   ├── iec101_event_runner.c
│   │   └── iec101_simulator_slave.c
│   └── libiec61850/                      # IEC 61850 MMS/GOOSE/SV C 源码
│       ├── iec61850_mms_client_runner.c
│       ├── iec61850_report_runner.c
│       ├── iec61850_goose_subscriber_runner.c
│       ├── iec61850_goose_publisher_simulator.c
│       ├── iec61850_sv_subscriber_runner.c
│       ├── iec61850_sv_publisher_simulator.c
│       └── iec61850_simulator_server.c
│
└── tests/                                # pytest 测试套件
    ├── README.md                         # 测试说明
    ├── TEST_AUDIT.md                     # 测试审计追踪
    ├── conftest.py                       # pytest fixtures
    ├── __init__.py
    │
    ├── access/                           # registry / probe / capacity / profile / CLI 测试
    │   ├── test_protocol_registry.py      # 注册表测试（协议级）
    │   ├── test_protocol_matrix.py        # 协议矩阵测试
    │   ├── test_protocol_service_capabilities.py  # 三元组服务能力测试
    │   ├── test_all_protocols_probe.py    # 多协议 probe 测试
    │   ├── test_all_protocols_polling_profile.py
    │   ├── test_all_protocols_polling_capacity.py
    │   ├── test_all_protocols_streaming_profile.py
    │   ├── test_all_protocols_streaming_capacity.py
    │   ├── test_open62541_serial_polling_runner.py
    │   ├── test_open62541_subscription_runner.py
    │   ├── test_native_process_protocol.py
    │   ├── test_iec61850_lightweight_semantics.py
    │   ├── test_field_probe_cli.py
    │   ├── test_field_capacity_cli.py
    │   ├── test_field_profile_cli.py
    │   ├── test_access_probe_protocol_handshake.py
    │   ├── test_access_probe_protocol_semantics.py
    │   ├── test_protocol_simulator_factory.py
    │   └── ... (metrics / reporter / worker / scheduling 测试)
    │
    ├── fixtures/simulator/               # 测试夹具
    │   ├── field_servers.tsv
    │   └── signal_profile_items.tsv
    ├── fixtures/db_export/               # schema-contract 夹具
    │   ├── field_servers.tsv
    │   └── signal_profile_items.tsv
    └── support/
        └── sources.py                    # 测试辅助函数
```

## 4. Implementation Level Definitions

| 等级 | 标签 | 说明 |
| --- | --- | --- |
| 真实 native runner | `real_native_runner` | 真实 C runner，可执行文件由 native C 源码编译产生，Python 通过 subprocess 调用，stdout 输出结构化协议行 |
| Python 轻量 runner | `python_lightweight_runner` | Python 层轻量 runner，可能使用 socket/http/mqtt 包或轻量协议帧，不代表完整工业协议栈 |
| 模拟 runner | `fake_or_simulated_runner` | 主要用于 source_lab profile/capacity 测试闭环的模拟 runner，不代表真实现场协议兼容 |
| 语义探测 | `semantic_probe_only` | 只做最小协议语义探测或握手验证，不代表完整协议解析 |
| 计划中 native runner | `planned_native_runner` | 后续计划接入真实 C runner，但当前未实现 |

每个协议的当前实现等级和**目标实现等级**现在分开记录于注册表：

- **current_implementation_level** — 当前真实实现状况
- **target_implementation_level** — 下一阶段"一次性到位"目标

详见第 5 节协议能力矩阵和第 6 节"统一协议模型"。

## 5. Protocol Capability Matrix

### 5.1 当前实现状态 (current)

```text
CLI 协议名            polling  subscribe  current_backend                         current_implementation_level
──────                ───────  ────────   ────────────────────────────────────    ──────────────────────────
opcua                 yes      yes        open62541 executable runner             real_native_runner
modbus_tcp            yes      no         libmodbus executable runner              real_native_runner
modbus_rtu            yes      no         libmodbus executable runner              real_native_runner
iec101                yes      yes        lib60870-C executable runner             real_native_runner
iec104                yes      yes        lib60870-C executable runner             real_native_runner
iec61850_mms          yes      no         libiec61850 executable runner            real_native_runner
iec61850_report       no       yes        libiec61850 executable runner            real_native_runner
mqtt                  no       yes        Python socket (MQTT 握手)                python_lightweight_runner
http_rest             yes      no         Python urllib (HTTP GET)                 python_lightweight_runner
```

### 5.2 目标实现状态 (target)

```text
协议族                  service_type      transport       target_backend                        target_implementation_level
──────                  ────────────      ─────────       ────────────────────────────────       ──────────────────────────
OPC UA                  READ              TCP             open62541 executable runner            real_native_runner
OPC UA                  SUBSCRIBE         TCP             open62541 executable runner            real_native_runner
MODBUS                  TCP_READ          TCP             libmodbus executable runner            real_native_runner
MODBUS                  RTU_READ          SERIAL          libmodbus executable runner            real_native_runner
IEC101                  INTERROGATION     SERIAL          lib60870-C executable runner            real_native_runner
IEC101                  SPONTANEOUS       SERIAL          lib60870-C executable runner            real_native_runner
IEC104                  INTERROGATION     TCP             lib60870-C executable runner            real_native_runner
IEC104                  SPONTANEOUS       TCP             lib60870-C executable runner            real_native_runner
IEC61850                MMS_READ          TCP             libiec61850 executable runner           real_native_runner
IEC61850                REPORT            TCP             libiec61850 executable runner           real_native_runner
IEC61850                GOOSE             ETHERNET_L2     libiec61850 GOOSE executable runner     real_native_runner
IEC61850                SV                ETHERNET_L2     libiec61850 SV executable runner        real_native_runner
MQTT                    SUBSCRIBE         MQTT            Python MQTT runner (mature client)      python_lightweight_runner
HTTP_REST               REQUEST           HTTP/HTTPS      Python HTTP runner (mature client)      python_lightweight_runner
```

### 5.3 关键限制说明

1. **all_protocols 测试通过 ≠ 完整工业协议栈合规**
   - `test_all_protocols_*` 系列测试验证的是 source_lab 多协议 access 框架闭环：CLI 参数链路、provider→runner→metrics→reporter 链路、profile/capacity 报告输出链路
   - 不等价于验证每个工业协议的完整标准栈合规性

2. **real_native_runner 协议列表（已有真实 C runner）**
   - **OPC UA** — open62541 C runners（`native/open62541/*.c`），已验证 capacity（50 server / 419 vars / 40 Hz）
   - **Modbus TCP/RTU** — libmodbus C runners（`native/libmodbus/*.c`），Python 通过 subprocess 调用
   - **IEC101 / IEC104** — lib60870-C runners（`native/lib60870/*.c`），含 polling、event、simulator
   - **IEC61850 MMS / REPORT** — libiec61850 runners（`native/libiec61850/*.c`），含 MMS polling、Report subscription 及 IedServer simulator
   - 所有 native runner 遵循 stdout 严格协议行格式（READY → SAMPLE/BATCH/NOTIFY → SUMMARY → DONE/ERROR），
     诊断日志走 stderr，Python 通过 `native_process.py` 包装调用

3. **IEC61850 GOOSE / SV 当前为 planned_native_runner**
   - C 源码（`native/libiec61850/iec61850_goose_*.c`, `iec61850_sv_*.c`）已编写并编译
   - 需要 raw Ethernet L2 能力，在 CI/无特权容器环境中无法运行
   - 当前有 executable 但不纳入自动化测试，register 标记为 `planned_native_runner`

4. **Modbus TCP/RTU** 已从 Python socket 升级为 **libmodbus native runner**
   - 有 libmodbus C polling runner 和 simulator server
   - 有 CMake target，编译为独立 executable
   - 有 Python subprocess wrapper
   - 通过 stdout 协议行输出

5. **IEC101/IEC104** 已从 Python socket 升级为 **lib60870-C native runner**
   - 含 polling (总召) 和 event (主动上报) 两种 runner
   - 有 IEC104 和 IEC101 serial 两种 simulator
   - 有 CMake target，编译为独立 executable

6. **GOOSE / SV** 源码已编写并编译，需 ETHERNET_L2 环境

## 6. Unified Protocol Model

### 6.1 三元组模型

协议能力从 protocol-only 升级为：

```
application_protocol + service_type + transport
```

**application_protocol** 常量：

| 常量 | 说明 |
| --- | --- |
| `OPC_UA` | OPC UA 统一架构 |
| `MODBUS` | Modbus 协议族 |
| `IEC101` | IEC 60870-5-101 |
| `IEC104` | IEC 60870-5-104 |
| `IEC61850` | IEC 61850 协议族 |
| `MQTT` | MQTT 物联网协议 |
| `HTTP_REST` | HTTP REST API |

**service_type** 常量：

| 常量 | 说明 | 关联 protocol |
| --- | --- | --- |
| `READ` | OPC UA 读服务 | OPC_UA |
| `SUBSCRIBE` | OPC UA 订阅 | OPC_UA, MQTT |
| `TCP_READ` | Modbus TCP 读 | MODBUS |
| `RTU_READ` | Modbus RTU 读 | MODBUS |
| `INTERROGATION` | IEC 总召 | IEC101, IEC104 |
| `SPONTANEOUS` | 主动上报 | IEC101, IEC104 |
| `MMS_READ` | IEC61850 MMS 读 | IEC61850 |
| `REPORT` | IEC61850 Report | IEC61850 |
| `GOOSE` | 面向通用对象的变电站事件 | IEC61850 |
| `SV` | 采样值 (Sampled Values) | IEC61850 |
| `REQUEST` | HTTP 请求 | HTTP_REST |

**transport** 常量：

| 常量 | 说明 |
| --- | --- |
| `TCP` | TCP 传输 |
| `SERIAL` | 串口传输 |
| `ETHERNET_L2` | 二层以太网（GOOSE/SV 专属） |
| `MQTT` | MQTT 传输 |
| `HTTP` | HTTP 传输 |
| `HTTPS` | HTTPS 传输 |

### 6.2 IEC61850 协议族

IEC61850 是一个**顶层协议族**，其下的服务类型包括：

| service_type | transport | 说明 | 当前状态 |
| --- | --- | --- | --- |
| `MMS_READ` | TCP | IEC61850 MMS 读（等同旧 CLI 中 iec61850_mms） | real_native_runner |
| `REPORT` | TCP | IEC61850 报告（等同旧 CLI 中 iec61850_report） | real_native_runner |
| `GOOSE` | ETHERNET_L2 | 面向通用对象的变电站事件 | planned_native_runner |
| `SV` | ETHERNET_L2 | 采样值 (Sampled Values) | planned_native_runner |

**GOOSE 和 SV 不作为独立顶层 protocol。** 它们是 IEC61850 协议族下的 service_type。
- `iec61850_goose` 和 `iec61850_sv` 如出现在 CLI 参数中，仅为 deprecated alias，
  不推荐作为顶层 protocol 使用。
- 推荐新形式：`--protocol IEC61850 --service-type GOOSE`（见第 6.4 节 CLI 扩展）。

### 6.3 旧 CLI 协议名 → 三元组映射

| 旧 CLI 协议名 | application_protocol | service_type | transport | 说明 |
| --- | --- | --- | --- | --- |
| `opcua` | OPC_UA | READ / SUBSCRIBE | TCP | 按 access_mode 选择 READ(polling) 或 SUBSCRIBE(subscribe) |
| `modbus_tcp` | MODBUS | TCP_READ | TCP | |
| `modbus_rtu` | MODBUS | RTU_READ | SERIAL | |
| `iec101` | IEC101 | INTERROGATION / SPONTANEOUS | SERIAL | 按 access_mode 选择 |
| `iec104` | IEC104 | INTERROGATION / SPONTANEOUS | TCP | 按 access_mode 选择 |
| `iec61850_mms` | IEC61850 | MMS_READ | TCP | |
| `iec61850_report` | IEC61850 | REPORT | TCP | |
| `iec61850_goose` | IEC61850 | GOOSE | ETHERNET_L2 | **Deprecated alias** — 不推荐作为顶层 protocol |
| `iec61850_sv` | IEC61850 | SV | ETHERNET_L2 | **Deprecated alias** — 不推荐作为顶层 protocol |
| `mqtt` | MQTT | SUBSCRIBE | MQTT | |
| `http_rest` | HTTP_REST | REQUEST | HTTP/HTTPS | |

### 6.4 CLI 扩展 (--service-type)

**旧 CLI 形式仍完全支持：**

```bash
python -m tools.source_lab.field_probe --protocol opcua ...
python -m tools.source_lab.field_probe --protocol iec61850_mms ...
python -m tools.source_lab.field_probe --protocol iec61850_report ...
```

**新形式（--service-type 参数已实现）：**

```bash
# --service-type 已实现，适用于 field_probe / field_capacity / field_profile
python -m tools.source_lab.field_probe --protocol IEC61850 --service-type MMS_READ ...
python -m tools.source_lab.field_probe --protocol IEC61850 --service-type REPORT ...
python -m tools.source_lab.field_probe --protocol IEC61850 --service-type GOOSE ...
python -m tools.source_lab.field_probe --protocol IEC61850 --service-type SV ...
```

当前代码（`registry.py` 内部）已经支持通过 `resolve_service_triple()` 和
`SERVICE_CAPABILITIES` 进行三元组表达和验证。CLI 层面的 `--service-type` 参数已在 Phase 1 实现，
支持 `field_probe`、`field_capacity`、`field_profile` 三个 CLI 入口。

## 7. Runner Stdout/Stderr Contract

对于 native runner 路径（OPC UA open62541、Modbus libmodbus、IEC60870 lib60870-C、IEC61850 libiec61850）：

- **stdout**: 只允许结构化协议行（`READY...`、`ERROR...`、其他定义的控制行）
  - 非预期 stdout 文本计为协议噪声
  - 正常测试 `runner_protocol_noise_count` 应为 0
- **stderr**: 承载日志和诊断
  - Python wrapper 使用 `stdout=PIPE`、`stderr=PIPE`
  - stderr 异步 drain 并附加到失败上下文
- **ERROR 协议行应立即失败**

非 native runner（Python lightweight / fake / semantic）不遵循此严格协议行约束。

## 8. Data Model Design (下一阶段方案)

### 8.1 设计原则

1. 不把正式协议参数主存储放进 `metadata_json`
2. 不使用 `param1` / `param2` / `param3` 等无语义列
3. 采用第一范式 (1NF)

### 8.2 建议表结构

```text
scada_communication_endpoint       # 通用 endpoint 表
scada_protocol_param_def           # 协议参数定义表
scada_endpoint_param_value         # endpoint 协议参数值表
scada_signal_profile_item          # signal profile 项表
scada_signal_param_def             # signal 参数定义表
scada_signal_item_param_value      # signal profile 项参数值表

# 下游 view 展开供 source_lab / 运维使用
v_scada_endpoint_opcua
v_scada_endpoint_modbus_tcp
v_scada_endpoint_modbus_rtu
v_scada_endpoint_iec104
v_scada_endpoint_iec61850_mms
v_scada_endpoint_iec61850_goose
v_scada_endpoint_iec61850_sv
```

### 8.3 scada_communication_endpoint 建议通用列

```text
endpoint_id          — 唯一标识
ied_id               — IED 标识
access_point_name    — 访问点名称
endpoint_name        — endpoint 名称
application_protocol — 协议族（OPC_UA / MODBUS / IEC61850 等）
service_type         — 服务类型（READ / GOOSE / SV 等）
transport            — 传输层（TCP / SERIAL / ETHERNET_L2）
host                 — 主机
port                 — 端口
namespace_uri        — OPC UA 命名空间 URI
security_policy      — 安全策略
security_mode        — 安全模式
auth_type            — 认证类型
credential_ref       — 凭据引用
heartbeat_interval_ms — 心跳间隔
description          — 描述
created_at           — 创建时间
updated_at           — 更新时间
```

### 8.4 GOOSE/SV 参数表达

GOOSE 参数（通过参数定义和值表表达，不是 JSON）：

```text
network_interface    — 网卡名称
vlan_id              — VLAN ID
app_id               — 应用标识
multicast_mac        — 组播 MAC 地址
go_cb_ref            — GOOSE 控制块引用
dataset_ref          — 数据集引用
min_time_ms          — 最小时间间隔
max_time_ms          — 最大时间间隔
```

SV 参数：

```text
network_interface    — 网卡名称
vlan_id              — VLAN ID
app_id               — 应用标识
multicast_mac        — 组播 MAC 地址
sv_cb_ref            — SV 控制块引用
dataset_ref          — 数据集引用
sample_rate_hz       — 采样率
asdu_count           — ASDU 数量
```

### 8.5 协议专用 View

以下 view 将展开协议通用信息和参数值，供 source_lab 和运维使用：

```text
v_scada_endpoint_opcua
v_scada_endpoint_modbus_tcp
v_scada_endpoint_modbus_rtu
v_scada_endpoint_iec104
v_scada_endpoint_iec61850_mms
v_scada_endpoint_iec61850_report
v_scada_endpoint_iec61850_goose
v_scada_endpoint_iec61850_sv
v_scada_endpoint_mqtt
v_scada_endpoint_http_rest
```

这些 view 将在下一阶段实施统一 endpoint 模型时创建。

## 9. Native Runner 实现状态

### 9.1 已实现的 native runner

以下协议已完成 native C runner（真实工业协议栈编译为独立 executable）：

| 协议 | backend | 状态 |
| --- | --- | --- |
| OPC UA | open62541 C runners | 已实现，已验证 capacity |
| Modbus TCP | libmodbus C runner | 已实现 |
| Modbus RTU | libmodbus C runner | 已实现 |
| IEC101 | lib60870-C runners | 已实现（polling + event） |
| IEC104 | lib60870-C runners | 已实现（polling + event） |
| IEC61850 MMS | libiec61850 C runner | 已实现 |
| IEC61850 Report | libiec61850 C runner | 已实现 |
| IEC61850 GOOSE | libiec61850 C runner（需 ETHERNET_L2） | 已编译，需 L2 环境 |
| IEC61850 SV | libiec61850 C runner（需 ETHERNET_L2） | 已编译，需 L2 环境 |

### 9.2 不要求 native runner

| 协议 | backend | 说明 |
| --- | --- | --- |
| MQTT | Python MQTT runner（成熟 client 库） | 不要求 native C runner |
| HTTP_REST | Python HTTP runner（成熟 HTTP 库） | 不要求 native C runner |

### 9.3 Native runner 创建条件

只有**同时满足以下所有条件**时，才能创建新的 native 子目录：

- 有 `.c` 源码
- 有 CMake target
- 能编译 executable
- 有 Python subprocess wrapper
- 有 stdout 协议测试
- 有 profile / capacity 集成测试

当前 `native/` 目录已包含 open62541、libmodbus、lib60870、libiec61850 四个子目录，
共 21 个 C 源文件。所有协议（除 GOOSE/SV 需 L2 环境外）均有 CMake target、Python wrapper
和集成测试覆盖。

## 10. Test Categories

### 10.1 Registry / Matrix / Service Capability Unit Tests

验证注册表、协议矩阵、三元组服务能力：

```bash
pytest tools/source_lab/tests/access/test_protocol_registry.py           # 11 个协议级注册表测试
pytest tools/source_lab/tests/access/test_protocol_matrix.py              # 2 个矩阵测试
pytest tools/source_lab/tests/access/test_protocol_service_capabilities.py # 38 个三元组能力测试
pytest tools/source_lab/tests/access/test_all_protocols_probe.py
pytest tools/source_lab/tests/access/test_all_protocols_polling_profile.py
pytest tools/source_lab/tests/access/test_all_protocols_polling_capacity.py
pytest tools/source_lab/tests/access/test_all_protocols_streaming_profile.py
pytest tools/source_lab/tests/access/test_all_protocols_streaming_capacity.py
```

### 10.2 Runner / Protocol Tests

验证 runner 层和协议边界：

```bash
pytest tools/source_lab/tests/access/test_open62541_serial_polling_runner.py
pytest tools/source_lab/tests/access/test_open62541_subscription_runner.py
pytest tools/source_lab/tests/access/test_native_process_protocol.py
pytest tools/source_lab/tests/access/test_native_runners_availability.py
pytest tools/source_lab/tests/access/test_iec61850_lightweight_semantics.py
pytest tools/source_lab/tests/access/test_access_probe_protocol_handshake.py
pytest tools/source_lab/tests/access/test_access_probe_protocol_semantics.py
```

### 10.3 CLI Wiring Tests

验证 CLI 参数链、服务编排、输出合同：

```bash
pytest tools/source_lab/tests/access/test_field_probe_cli.py
pytest tools/source_lab/tests/access/test_field_capacity_cli.py
pytest tools/source_lab/tests/access/test_field_profile_cli.py
```

### 10.4 Integration / Smoke Tests

验证 simulator fleet + CLI 集成（需要 native build）：

```bash
pytest tools/source_lab/tests/test_open62541_source_simulation_single_server_smoke.py
pytest tools/source_lab/tests/test_source_simulation_multi_server_polling_capacity.py -s
pytest tools/source_lab/tests/test_source_simulation_multi_server_polling_profile.py -s
pytest tools/source_lab/tests/test_source_simulation_multi_server_subscribe_capacity.py -s
pytest tools/source_lab/tests/test_source_simulation_multi_server_subscribe_profile.py -s
```

### 10.5 Run All Access Tests

```bash
pytest tools/source_lab/tests/access -q    # 约 290+ tests
```

### 10.6 Run All source_lab Tests

```bash
pytest tools/source_lab/tests -q           # 约 300+ tests（含 native-dependent tests）
```

### 10.7 Static Checks

```bash
python -m compileall tools/source_lab
ruff check tools/source_lab
mypy tools/source_lab
```

## 11. CLI Usage

### 11.1 Probe

```bash
python -m tools.source_lab.field_probe \
  --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
  --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
  --protocol <protocol> \
  --samples 5 \
  --timeout 5 \
  --tcp-timeout 3 \
  --concurrency 16
```

Probe 支持的全部协议：`opcua`、`modbus_tcp`、`modbus_rtu`、`iec101`、`iec104`、`iec61850_mms`、`http_rest`（polling 模式）、`mqtt`、`iec61850_report`（streaming 模式）。

`iec61850_goose` 和 `iec61850_sv` 为 deprecated alias，当前没有 runner 实现。
未来将通过 `--service-type GOOSE` / `--service-type SV` 形式支持（planned CLI extension）。

### 11.2 Polling Capacity

```bash
python -m tools.source_lab.field_capacity \
  --access-mode polling \
  --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
  --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
  --protocol <protocol> \
  --process-count-start 1 --process-count-step 1 --process-count-max 1 \
  --server-count-start 10 --server-count-step 20 --server-count-max 30 \
  --hz-start 10 --hz-step 20 --hz-max 30 \
  --duration 6 --warmup 1 \
  --source-update-enabled true \
  --output-dir tools/source_lab/tests/tmp/polling_capacity
```

Polling capacity 支持协议：`opcua`、`modbus_tcp`、`modbus_rtu`、`iec101`、`iec104`、`iec61850_mms`、`http_rest`。

### 11.3 Subscribe Capacity

```bash
python -m tools.source_lab.field_capacity \
  --access-mode subscribe \
  --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
  --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
  --protocol <protocol> \
  --process-count-start 1 --process-count-step 1 --process-count-max 1 \
  --server-count-start 10 --server-count-step 10 --server-count-max 20 \
  --sample-hz-start 20 --sample-hz-step 20 --sample-hz-max 40 \
  --source-update-hz-start 10 --source-update-hz-step 20 --source-update-hz-max 30 \
  --duration 6 --warmup 1 \
  --source-update-enabled true \
  --queue-size 1 \
  --output-dir tools/source_lab/tests/tmp/subscribe_capacity
```

Subscribe capacity 支持协议：`opcua`、`iec101`、`iec104`、`iec61850_report`、`mqtt`。

### 11.4 Polling Profile

```bash
python -m tools.source_lab.field_profile \
  --access-mode polling \
  --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
  --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
  --protocol <protocol> \
  --process-count 1 --server-count 50 --hz 20 \
  --duration 10 --warmup 2 \
  --runner-trace true --runner-trace-top-n 5 \
  --output-dir tools/source_lab/tests/tmp/polling_profile
```

### 11.5 Subscribe Profile

```bash
python -m tools.source_lab.field_profile \
  --access-mode subscribe \
  --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
  --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
  --protocol <protocol> \
  --process-count 1 --server-count 50 \
  --sample-hz 50 --source-update-hz 50 \
  --duration 20 --warmup 3 \
  --runner-trace true --runner-trace-top-n 5 \
  --queue-size 1 \
  --output-dir tools/source_lab/tests/tmp/subscribe_profile
```

## 12. Multi-Protocol Command Examples

假设：
- `SERVERS=tools/source_lab/tests/fixtures/simulator/field_servers.tsv`
- `ITEMS=tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv`

Polling 协议全部示例：

```bash
for p in opcua modbus_tcp modbus_rtu iec101 iec104 iec61850_mms http_rest; do
  python -m tools.source_lab.field_probe --servers "$SERVERS" --profile-items "$ITEMS" --protocol "$p" --samples 5 --timeout 5 --tcp-timeout 3 --concurrency 8
  python -m tools.source_lab.field_profile --access-mode polling --servers "$SERVERS" --profile-items "$ITEMS" --protocol "$p" --process-count 1 --server-count 10 --hz 10 --duration 15 --warmup 3 --timeout 5 --source-update-enabled true --source-update-hz 10 --output-dir tools/source_lab/tests/tmp/profile_"$p"
  python -m tools.source_lab.field_capacity --access-mode polling --servers "$SERVERS" --profile-items "$ITEMS" --protocol "$p" --process-counts 1 --server-counts 10 --hz 10 --duration 15 --warmup 3 --timeout 5 --source-update-enabled true --source-update-hz 10 --output-dir tools/source_lab/tests/tmp/capacity_"$p"
done
```

Streaming 协议全部示例：

```bash
for p in opcua iec101 iec104 iec61850_report mqtt; do
  python -m tools.source_lab.field_probe --servers "$SERVERS" --profile-items "$ITEMS" --protocol "$p" --samples 5 --timeout 5 --tcp-timeout 3 --concurrency 8
  python -m tools.source_lab.field_profile --access-mode subscribe --servers "$SERVERS" --profile-items "$ITEMS" --protocol "$p" --process-count 1 --server-count 10 --sample-hz 20 --queue-size 1 --duration 15 --warmup 3 --timeout 5 --source-update-enabled true --source-update-hz 20 --output-dir tools/source_lab/tests/tmp/profile_sub_"$p"
  python -m tools.source_lab.field_capacity --access-mode subscribe --servers "$SERVERS" --profile-items "$ITEMS" --protocol "$p" --process-counts 1 --server-counts 10 --sample-hz 10,20 --source-update-hz-values 10,20 --queue-size 1 --duration 15 --warmup 3 --timeout 5 --source-update-enabled true --output-dir tools/source_lab/tests/tmp/capacity_sub_"$p"
done
```

## 13. Environment Variables

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `SOURCE_SIM_PORT_START` | 22000 | simulator 端口范围起始 |
| `SOURCE_SIM_PORT_END` | 22999 | simulator 端口范围结束 |
| `SOURCE_SIM_FLEET_START_CONCURRENCY` | 8 | fleet 启动并发数 |
| `SOURCE_SIM_FLEET_START_STAGGER_MS` | 50 | fleet 启动间隔（ms） |
| `SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S` | 120 | fleet 启动超时（s） |
| `SOURCE_SIM_POLL_*` | — | polling smoke 设置 |
| `SOURCE_SIM_SUB_*` | — | subscribe smoke 设置 |
| `SOURCE_SIM_POLL_PERIOD_MAX_TOLERANCE_RATIO` | 0.2 | polling 周期最大容忍比 |
| `SOURCE_SIM_POLL_PERIOD_MEAN_ERROR_RATIO` | 0.2 | polling 周期平均误差比 |

`SOURCE_SIM_LOAD_*` 已废弃，应使用 `SOURCE_SIM_POLL_*` / `SOURCE_SIM_SUB_*`。

## 14. Development Constraints

- 只允许修改 `tools/source_lab/**`
- 不允许修改 `src/`、`tests/`（非 source_lab 目录）、`pyproject.toml`、`requirements.txt`
- native runner stdout 协议解析保持严格
- 诊断信息走 stderr，不走 stdout
- 新协议通过 registry/factory 扩展，不在服务编排中硬编码分支
- 不保留空的 native 占位目录
- 所有协议的实现等级必须在 README 中如实标明
- GOOSE / SV 不作为独立顶层 protocol，它们是 IEC61850 协议族下的 service_type
- 不使用 `param1` / `param2` 或 `metadata_json` 作为正式协议参数主存储
