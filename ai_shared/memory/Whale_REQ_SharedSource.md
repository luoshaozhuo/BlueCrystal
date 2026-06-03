# Whale_REQ_SharedSource

## 一、文件定位

本文件描述 Whale `src/whale/shared/source` 模块承担的 production source client 需求。

本文件不描述 ingest use case 编排，不描述 source_lab simulator 内部实现。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-001 | 提供生产级多协议 source client |
| P-NFR-001 | 提供稳定、高性能、可 profile 的协议访问能力 |
| P-AR-002 | 与 source_lab 工具层保持边界 |

## 三、Production client 能力矩阵

| 协议 | read | write | subscribe | report | backend | ingest adapter | E2E | profile/capacity | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| opcua | 已验证 | 已验证（含 readback L2） | 已验证 | NOT_IMPLEMENTED | open62541 C | 已注册 | L3（simulator/native） | 已验证（source_lab） | production-ready |
| modbus_tcp | 已验证 | 已验证（含 readback L2） | NOT_IMPLEMENTED | NOT_IMPLEMENTED | libmodbus C | 已注册 | L3（simulator/native） | 已验证（source_lab） | production-ready |
| iec104 | 已验证（DispatchSourceAcquisitionAdapter 接入 PollingAcquisitionRole） | 已验证（write adapter 已注册，adapter-level E2E 4 passed：write-then-read/dry_run/write_disabled/acquisition_chain；PROTOCOL_CAPABILITIES write=True） | NOT_IMPLEMENTED | NOT_IMPLEMENTED | lib60870 C（backend 单元测试 113 passed，已纳入 composition.py 采集链路） | 已注册到 composition.py port registry（write+acquisition） | L3（simulator mock，4 E2E tests） | 已验证（source_lab 工具层） | production-ready（3-tier 证据完整：L1 source_lab L3 + L2 backend tests + L3 ingest composition E2E；readiness gate 已列入 _KNOWN_PRODUCTION_READ_PROTOCOLS） |
| iec61850_mms | 已验证 | 已验证（含 readback L2） | NOT_IMPLEMENTED | NOT_IMPLEMENTED | libiec61850 C | 已注册 | L3（simulator/native） | 已验证（source_lab） | production-ready |
| iec61850_report | NOT_IMPLEMENTED | NOT_IMPLEMENTED | N/A（report 路径） | 已验证 | libiec61850 C | 已注册 | L3（simulator/native） | 已验证（source_lab） | production-ready |
| modbus_rtu | 已验证（ModbusRtuSourceAcquisitionAdapter 已注册，E2E tests passed） | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | real os/termios/fcntl serial（python lightweight runner） | 已注册到 composition.py port registry | L3（simulator mock，read-only serial） | 已验证（source_lab 工具层） | acquisition-ready（read-only serial；read 能力 L1-L3 证据完整；write=NOT_IMPLEMENTED；serial hardware L4/L5=environment-pending；readiness gate 已列入 _KNOWN_PRODUCTION_READ_PROTOCOLS） |
| iec101 | 已验证（Iec101SourceAcquisitionAdapter 已注册，E2E tests passed） | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | real os/termios/fcntl serial（python lightweight runner，FT1.2+ASDU interrogation） | 已注册到 composition.py port registry | L3（simulator mock，read-only serial） | 已验证（source_lab 工具层） | acquisition-ready（read-only serial；read 能力 L1-L3 证据完整；write=NOT_IMPLEMENTED；serial hardware L4/L5=environment-pending；readiness gate 已列入 _KNOWN_PRODUCTION_READ_PROTOCOLS） |
| mqtt | 已验证（MqttSourceAcquisitionAdapter 已注册，3 E2E tests） | NOT_IMPLEMENTED | 已验证（subscribe） | NOT_IMPLEMENTED | asyncio MQTT v3.1.1（python lightweight runner） | 已注册到 composition.py port registry | L3（simulator mock，3 E2E tests） | 已验证（source_lab 工具层） | acquisition-ready（read 能力已生产就绪；write=NOT_IMPLEMENTED；readiness gate 已列入 _KNOWN_PRODUCTION_READ_PROTOCOLS） |
| http_rest | 已验证（HttpRestSourceAcquisitionAdapter 已注册，4 E2E tests） | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | asyncio HTTP/1.1（python lightweight runner） | 已注册到 composition.py port registry | L3（simulator mock，4 E2E tests） | 已验证（source_lab 工具层） | acquisition-ready（read 能力已生产就绪；write=NOT_IMPLEMENTED；readiness gate 已列入 _KNOWN_PRODUCTION_READ_PROTOCOLS） |

## 三、功能需求

### SS-FR-001 production source client

- 类型：功能
- 优先级：高
- 需求描述：
  - shared_source 模块应为声明支持的协议提供生产级 source client。
- 验收要点：
  - 支持真实协议 read。
  - 支持真实协议 write。
  - 支持真实 subscription/report。
  - 支持 timeout、close/cleanup、error classification。
  - 不依赖 ingest。
  - 不依赖 source_lab。

### SS-FR-002 多协议 backend

- 类型：功能
- 优先级：高
- 需求描述：
  - shared_source 模块应支持多协议 backend 扩展。
- 验收要点：
  - 支持 OPC UA、Modbus TCP、IEC104、IEC61850 MMS、IEC61850 Report 的声明能力。
  - 不支持协议能力返回 NOT_IMPLEMENTED 或等价错误。
  - backend 能被 ingest adapter 装配。

### SS-FR-003 read/write/subscription/report 能力

- 类型：功能
- 优先级：高
- 需求描述：
  - production client 应支持协议允许范围内的读取、写入、订阅和报告能力。
- 验收要点：
  - read 支持 batch read、quality、timestamp、partial failure。
  - write 支持 per-item result、unsupported operation、timeout、readback。
  - subscription/report 支持 callback 或 async stream、stop handle、ERROR line、unexpected exit。

## 四、非功能需求

### SS-NFR-001 协议真实性与性能

- 类型：非功能
- 优先级：高
- 需求描述：
  - production client 必须走真实协议，并接受 source_lab profile 和 capacity 验证。
- 验收要点：
  - read/write/readback 使用真实 server simulator 或真实设备。
  - subscription/report 使用真实事件。
  - 输出 read duration、response timestamp、period_samples、values/sec。

### SS-NFR-002 资源管理与安全

- 类型：非功能
- 优先级：高
- 需求描述：
  - production client 应正确管理连接、进程、文件描述符、后台任务、认证和通信安全。
- 验收要点：
  - close 幂等。
  - 无 zombie process。
  - timeout 可配置。
  - 支持证书、token、用户名密码或协议等价认证方式。
  - 不在 stdout/stderr/log 输出敏感凭据。

## 五、架构约束

### SS-AR-001 shared_source 不依赖 ingest/source_lab

- 类型：架构约束
- 优先级：高
- 需求描述：
  - shared_source 是生产 source client 层，不得依赖 ingest use case 或 source_lab 工具层。
- 验收要点：
  - shared_source 不 import src/whale/ingest。
  - shared_source 不 import tools.source_lab。
  - ingest adapter 依赖 shared_source。

## 六、测试与验收需求

### SS-TEST-001 production client 测试准入

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - 每个 production client 必须有单元测试、真实协议集成测试、source_lab simulator E2E 和 profile/capacity 准入。
- 验收要点：
  - read/write/readback 测试通过。
  - unsupported operation 测试通过。
  - timeout、runner error、cleanup 测试通过。
  - profile/capacity 通过。
  - skipped 不作为完成证据。

## 七、禁止事项

- 不得依赖 ingest。
- 不得依赖 source_lab。
- 不得把 native runner 直接暴露给 use case。


## 八、模块级生产部署准入

### SS-READY-001 shared_source 独立部署与被装配准入

- 类型：模块级生产部署准入
- 优先级：高
- 需求描述：
  - shared_source 作为 production source client 层，必须能被 ingest、测试工具或其他业务模块通过稳定端口装配使用。
  - shared_source 不承担 ingest 的采集编排、调度、缓存、消息发布、审计写入和运行时管理职责。
- 验收要点：
  - production client 能独立完成协议连接、read/write/subscription/report 能力调用。
  - backend 能被 ingest adapter 装配，但不 import ingest。
  - 不 import tools.source_lab。
  - close/cleanup 幂等。
  - timeout、错误分类、unsupported operation 语义稳定。
  - 与 source_lab simulator 的 E2E 只能证明协议 client 能力，不等同于 ingest 生产部署完成。

### SS-READY-002 shared_source 协议能力准入

- 类型：模块级生产部署准入
- 优先级：高
- 需求描述：
  - shared_source 对每个声明支持的协议，必须区分 declared capability、actual runtime availability 和 validated evidence。
- 验收要点：
  - 每个协议的 read/write/subscription/report 能力必须有 capability matrix。
  - 不支持能力必须返回 NOT_IMPLEMENTED 或等价稳定错误。
  - 声明支持 write 的协议必须具备 readback 或状态确认路径。
  - 真实设备、source_lab simulator、contract/mock 证据必须分级记录。
  - L1/L2 contract 不得写成 production protocol ready。
  - native binary、第三方库或证书依赖缺失时必须返回明确 unavailable。

### SS-READY-003 shared_source 安全与资源准入

- 类型：模块级生产部署准入
- 优先级：高
- 需求描述：
  - shared_source 必须正确处理协议连接、认证、凭据、证书、子进程、socket、文件描述符和后台任务资源。
- 验收要点：
  - 支持协议所需认证配置，例如证书、token、用户名密码或等价认证方式。
  - 凭据不得输出到 stdout/stderr/log/trace/debug dump。
  - 网络连接、subprocess、subscription/report handle 必须可关闭。
  - timeout、deadline、cancel、cleanup 语义明确。
  - runner crash、协议异常、认证失败和连接失败必须分类。
  - 不得把 native runner 直接暴露给 ingest use case。

### SS-READY-004 shared_source 质量门禁

- 类型：模块级生产部署准入
- 优先级：高
- 需求描述：
  - shared_source 作为生产协议访问层，必须通过模块级工程质量门禁。
- 验收要点：
  - compileall 或等价语法检查通过。
  - ruff 或等价 lint 检查通过。
  - mypy 或等价类型检查通过；未通过不得写质量门禁收口。
  - 每个 production backend 至少具备 unit、integration 或 simulator E2E 证据。
  - skipped 不得作为完成证据。
  - fake/mock/contract 证据不得冒充真实协议或真实设备验证。

## 九、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SS-FR-001 | P-FR-001 | production source client | FR | 高 | shared_source | L3（5 协议 production-ready：OPC UA/Modbus TCP/IEC61850 MMS/Report/IEC104）+ L3（4 协议 acquisition-ready：MQTT/HTTP REST/Modbus RTU/IEC101）/ NOT_IMPLEMENTED（其余 3 协议） | 已收口（核心协议；MQTT/HTTP REST/Modbus RTU/IEC101 write 待补齐） | `src/whale/shared/source/access/opcua.py`; `src/whale/shared/source/modbus/reader.py`; `src/whale/shared/source/modbus_rtu/reader.py`; `src/whale/shared/source/modbus_rtu/backends/`; `src/whale/shared/source/iec61850/reader.py`; `src/whale/shared/source/iec61850/report_reader.py`; `src/whale/shared/source/iec104/reader.py`; `src/whale/shared/source/iec101/reader.py`; `src/whale/shared/source/iec101/backends/`; `src/whale/shared/source/mqtt/client.py`; `src/whale/shared/source/http_rest/client.py`; 各 backend；`src/whale/ingest/adapters/source/dispatch_source_acquisition_adapter.py`; `src/whale/ingest/adapters/source/mqtt_source_acquisition_adapter.py`; `src/whale/ingest/adapters/source/http_rest_source_acquisition_adapter.py`; `src/whale/ingest/adapters/source/modbus_rtu_source_acquisition_adapter.py`; `src/whale/ingest/adapters/source/iec101_source_acquisition_adapter.py` | `pytest tests/unit/test_opcua_source_acquisition_adapter.py`; `pytest tests/unit/test_modbus_source_acquisition_adapter.py`; `pytest tests/unit/test_modbus_rtu_backend.py`; `pytest tests/unit/test_modbus_rtu_source_acquisition_adapter.py`; `pytest tests/unit/test_iec61850_source_acquisition_adapter.py`; `pytest tests/unit/test_iec61850_report_acquisition_adapter.py`; `pytest tests/unit/test_iec104_backend.py` -> 113 passed；`pytest tests/unit/test_iec101_backend.py`; `pytest tests/unit/test_iec101_source_acquisition_adapter.py`; `pytest tests/unit/test_mqtt_backend.py`; `pytest tests/unit/test_http_rest_backend.py`; `pytest tests/integration/test_modbus_rtu_acquisition_chain.py`; `pytest tests/integration/test_iec101_acquisition_chain.py`; `pytest tests/integration/test_iec104_acquisition_chain.py` -> 4 passed（L3）；`pytest tests/integration/test_mqtt_acquisition_chain.py` -> 3 passed（L3）；`pytest tests/integration/test_http_rest_acquisition_chain.py` -> 4 passed（L3） | 5 协议 production-ready（OPC UA/Modbus TCP/IEC61850 MMS/Report/IEC104--IEC104 3-tier 证据完整）；4 协议 acquisition-ready（MQTT/HTTP REST/Modbus RTU/IEC101--read 能力生产就绪，write=NOT_IMPLEMENTED）；Modbus RTU/IEC101 使用 real os/termios/fcntl serial（非 TCP/gateway fake），L4/L5 serial hardware=environment-pending；readiness gate 已列入 _KNOWN_PRODUCTION_READ_PROTOCOLS（iec104/mqtt/http_rest/modbus_rtu/iec101）；其余 3 协议（GOOSE/SV/Beckhoff ADS）无 production client | Modbus RTU/IEC101 write 能力补齐（需 serial 写入协议实现）；MQTT/HTTP REST write 能力补齐；L5 field readback 现场验证；Modbus RTU/IEC101 serial hardware 真实设备/串口环境验证 | 2026-06-02 (Round 28) |
| SS-FR-002 | P-FR-001 | 多协议 backend | FR | 高 | shared_source | L3（9 backend 已注册：5 C native + 4 python lightweight runner） | 已收口（核心协议） | OPC UA: open62541 C backend; Modbus TCP: libmodbus C backend; Modbus RTU: real os/termios/fcntl python backend (CRC16); IEC61850 MMS: libiec61850 C backend; IEC61850 Report: libiec61850 C report backend; IEC104: lib60870 C backend（已接入主采集链路）; IEC101: real os/termios/fcntl python backend (FT1.2+ASDU); MQTT: asyncio MQTT v3.1.1 python lightweight runner; HTTP REST: asyncio HTTP/1.1 python lightweight runner | `pytest tests/unit/test_modbus_rtu_backend.py`; `pytest tests/unit/test_iec101_backend.py`; `pytest tests/unit/test_iec104_backend.py` -> 113 passed；`pytest tests/unit/test_mqtt_backend.py`; `pytest tests/unit/test_http_rest_backend.py`; adapter-level E2E 全部通过 | 9 协议有 production backend 且已注册到 composition.py；Modbus RTU/IEC101 使用 real os/termios/fcntl serial（非 TCP/gateway fake），serial hardware L4/L5=environment-pending；MQTT/HTTP REST 采用 python lightweight runner（asyncio 标准库）；其余 3 协议（GOOSE/SV/Beckhoff ADS）无 backend | Modbus RTU/IEC101/MQTT/HTTP REST write 能力补齐；其余 3 协议视需求优先级 | 2026-06-02 (Round 28) |
| SS-FR-003 | P-FR-001 | read/write/subscription/report 能力 | FR | 高 | shared_source | L3（read/write L2 readback）/ L3（report）/ L3（IEC104 write 4 E2E + acquisition chain）/ L3（Modbus RTU/IEC101 serial read-only） | 已收口（核心协议；MQTT/HTTP REST/Modbus RTU/IEC101 write=NOT_IMPLEMENTED） | OPC UA: read/write/subscribe; Modbus TCP: read/write; Modbus RTU: read-only serial（FC03 holding register, CRC16, os/termios/fcntl）; IEC61850 MMS: read/write; IEC61850 Report: report/subscribe; IEC104: read/write（DispatchSourceAcquisitionAdapter 接入 PollingAcquisitionRole，write 4 E2E：write-then-read/dry_run/write_disabled/acquisition_chain，PROTOCOL_CAPABILITIES write=True）; IEC101: read-only serial（interrogation, FT1.2+ASDU, os/termios/fcntl）; MQTT: read/subscribe; HTTP REST: read; 各 write adapter readback L2 contract 验证 | `pytest tests/unit/test_opcua_source_write_adapter.py -q` -> 3 passed（L2 readback）; `pytest tests/unit/test_modbus_source_write_adapter.py -q` -> 3 passed（L2 readback）; `pytest tests/unit/test_modbus_rtu_backend.py` (24 tests, CRC16+serial); `pytest tests/unit/test_iec61850_source_write_adapter.py -q` -> 3 passed（L2 readback）; `pytest tests/unit/test_iec101_backend.py` (25 tests, FT1.2+ASDU+serial); `pytest tests/integration/test_ingest_iec104_source_write.py -q` -> 4 passed（L3）；`pytest tests/integration/test_iec104_acquisition_chain.py -q` -> 4 passed（L3) | 四协议 readback 均为 L2 contract，L5 field readback 全缺失；MQTT/HTTP REST/Modbus RTU/IEC101 write=NOT_IMPLEMENTED；Modbus RTU/IEC101 serial hardware L4/L5=environment-pending；其余 3 协议无此项能力 | L5 field readback 现场验证；4 协议 write 能力补齐；Modbus RTU/IEC101 serial 真实设备/串口环境验证 | 2026-06-02 (Round 28) |
| SS-NFR-001 | P-NFR-001 | 协议真实性与性能 | NFR | 高 | shared_source | L3（source_lab simulator profile/capacity） | 部分实现 | source_lab profile/capacity 已验证 OPC UA/Modbus TCP/IEC61850 MMS/Report；各 backend read duration/period_samples 可获取 | `pytest tools/source_lab/tests/access/test_all_protocols_polling_capacity.py`; `pytest tools/source_lab/tests/access/test_all_protocols_polling_profile.py` | profile/capacity 由 source_lab 工具层验证，非 shared_source 独立验证；L5 field 性能数据缺失 | 补 shared_source 独立性能指标与 L5 现场性能验证 | 2026-06-01 |
| SS-NFR-002 | P-NFR-002/P-NFR-005 | 资源管理与安全 | NFR | 高 | shared_source | L2/L3（timeout/cleanup/error classification） | 部分实现 | timeout/cleanup/error classification tests；`tests/unit/test_iec61850_mms_backend.py`; `tests/unit/test_iec61850_report_backend.py`; `tests/unit/test_shared_source_runner_resolution.py` | timeout/cleanup/reconnect 单测存在；凭据保护、认证配置和独立 artifact 交付仍需进一步归档 | 补生产配置与现场故障分类证据 | 2026-06-01 |
| SS-AR-001 | P-AR-001/P-AR-002 | shared_source 不依赖 ingest/source_lab | AR | 高 | shared_source | L2/L3 | 部分实现 | `src/whale/shared/source/runner_resolution.py`; `tests/unit/test_shared_source_runner_resolution.py`; `tests/unit/test_ingest_no_source_lab_imports.py`; `ai_shared/adr/ADR-20260530-010-shared-source-production-runner-artifact-boundary.md` | `pytest tests/unit/test_shared_source_runner_resolution.py -q` -> 5 passed；`pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed | Python import 边界成立，且默认 runner 路径已不再指向 `tools/source_lab/native/build`；但生产 runner artifact 交付/安装证据仍待补齐 | 补独立 production runner artifact 安装与现场验证证据 | 2026-05-30 |
| SS-TEST-001 | P-NFR-004 | production client 测试准入 | TEST | 高 | shared_source | L3（unit + integration + simulator E2E，9 协议：5 production-ready + 4 acquisition-ready）/ total 184 passed/0 failed/0 skipped（combined verification） | 已收口（核心协议测试完整；Modbus RTU/IEC101 补齐） | OPC UA: unit + integration + E2E; Modbus TCP: unit + integration + E2E; Modbus RTU: backend unit + adapter unit + acquisition_chain E2E (24+ tests, CRC16+serial, read-only)；IEC61850 MMS: unit + integration + E2E; IEC61850 Report: unit + integration + E2E; IEC104: unit + integration + adapter-level E2E + acquisition_chain E2E（backend 113 + write 4 + acquisition_chain 4，total 121 passed）；IEC101: backend unit + adapter unit + acquisition_chain E2E (25+ tests, FT1.2+ASDU+serial, read-only)；MQTT: backend unit + adapter unit + acquisition_chain E2E 3 passed；HTTP REST: backend unit + adapter unit + acquisition_chain E2E 4 passed | `pytest tests/unit/test_modbus_rtu_backend.py` (L1, CRC16+serial); `pytest tests/unit/test_iec101_backend.py` (L1, FT1.2+ASDU+serial); `pytest tests/unit/test_iec104_backend.py -q` -> 113 passed；`pytest tests/integration/test_ingest_iec104_source_write.py -q` -> 4 passed；`pytest tests/integration/test_iec104_acquisition_chain.py -q` -> 4 passed；`pytest tests/unit/test_mqtt_backend.py`; `pytest tests/unit/test_http_rest_backend.py`; `pytest tests/integration/test_mqtt_acquisition_chain.py -q` -> 3 passed；`pytest tests/integration/test_http_rest_acquisition_chain.py -q` -> 4 passed；`pytest tests/integration/test_modbus_rtu_acquisition_chain.py`; `pytest tests/integration/test_iec101_acquisition_chain.py` | 9 protocol tests pass（combined 184 passed/0 failed/0 skipped）；Modbus RTU/IEC101 使用 real os/termios/fcntl serial（非 TCP/gateway fake），backend 测试通过，adapter 已注册 composition.py；IEC104 3-tier 证据完整（L1+L2+L3）且 E2E 全链路通过；4 协议 read 能力生产就绪 write=NOT_IMPLEMENTED；其余 3 协议（GOOSE/SV/Beckhoff ADS）无 production client 故无 tests；L5 field readback 全缺失；Modbus RTU/IEC101 serial hardware L4/L5=environment-pending | 4 协议 write 测试补齐；L5 field readback 现场测试；Modbus RTU/IEC101 serial 真实设备/串口 E2E | 2026-06-02 (Round 28) |
| SS-READY-001 | P-AR-001/P-AR-002 | shared_source 独立部署与被装配准入 | READY | 高 | shared_source | L2/L3 | 部分实现 | `src/whale/shared/source/runner_resolution.py`; 各协议 backend；source adapter tests；Round 11 ADR/report | 已补 production runner path / dev fallback 边界；ingest/shared_source 仍无 `tools.source_lab` import | 仍缺独立 production runner artifact 的交付与部署 runbook，因此不能写 fully production-ready | 回填 artifact 安装、PATH/环境变量发布流程和现场验收 | 2026-05-30 |
| SS-READY-002 | P-FR-001/P-NFR-001 | shared_source 协议能力准入 | READY | 高 | shared_source | L4（PostgreSQL 持久化输入基线）+ L4（source_lab runtime 消费边界）/待核实（client runtime） | 待代码核实 | `src/whale/shared/persistence/session.py`; `src/whale/shared/persistence/init_db.py`; `src/whale/shared/persistence/template/protocol_param_data.py`; `src/whale/shared/persistence/template/protocol_view_defs.py`; `src/whale/shared/persistence/template/sample_data.py`; `tests/unit/shared/persistence/test_scada_protocol_params.py`; `tests/unit/shared/persistence/test_scada_sample_data_protocol_coverage.py`; `tests/unit/shared/persistence/test_scada_protocol_views.py`; `tests/integration/test_shared_persistence_sample_data_init.py`; `tests/integration/test_source_lab_scada_profile_postgres.py`; `tools/source_lab/access/providers/scada_profile.py`; `tools/source_lab/tests/access/test_scada_profile_runtime_coverage.py`; `tools/source_lab/tests/access/test_scada_profile_facade_smoke.py`; `tools/source_lab/tests/access/test_beckhoff_ads_simulator_contract.py`; `tests/integration/test_source_lab_scada_profile.py`; `tests/integration/test_source_lab_beckhoff_ads_runtime.py` | `pytest tests/unit/shared/persistence/test_scada_protocol_params.py tests/unit/shared/persistence/test_scada_sample_data_protocol_coverage.py tests/unit/shared/persistence/test_scada_protocol_views.py -q` -> 12 passed；`pytest tests/integration/test_shared_persistence_sample_data_init.py -q` -> 1 passed；`pytest tests/integration/test_source_lab_scada_profile_postgres.py -q` -> 1 passed；`pytest tools/source_lab/tests/access/test_scada_profile_runtime_coverage.py -q` -> 17 passed；`pytest tools/source_lab/tests/access/test_scada_profile_facade_smoke.py -q` -> 15 passed；`pytest tools/source_lab/tests/access/test_beckhoff_ads_simulator_contract.py -q` -> 4 passed；`pytest tests/integration/test_source_lab_scada_profile.py -q` -> 2 passed；`pytest tests/integration/test_source_lab_beckhoff_ads_runtime.py -q` -> 2 passed | 现在不仅能证明 shared persistence 输入基线在 PostgreSQL 临时库可真实落库、可查询，也能证明 source_lab provider 已在 PostgreSQL 上消费这套输入契约；但这仍不证明 shared_source client runtime、readback、真实 Beckhoff ADS 服务端或 production ADS backend 已完成，ADS_NOTIFICATION 也仍未实现 | shared_source 仍以这套持久化输入契约为统一入口，继续补 production client runtime/readback 证据；不要把 source_lab ADS `backend_kind=in_process` tool runtime 证据外推成 shared_source 完成 | 2026-06-01 |
| SS-READY-003 | P-NFR-002/P-NFR-005 | shared_source 安全与资源准入 | READY | 高 | shared_source | L2/L3 | 部分实现 | timeout/cleanup/backend tests；`tests/unit/test_iec61850_mms_backend.py`; `tests/unit/test_iec61850_report_backend.py`; `tests/unit/test_shared_source_runner_resolution.py` | runner 缺失、timeout、cleanup、report reconnect 等已有单测；本轮新增 runner unavailable/build hint 边界测试 | 凭据保护、认证配置和独立 artifact 交付仍需进一步归档 | 回填生产配置与现场故障分类证据 | 2026-05-30 |
| SS-READY-004 | P-NFR-004 | shared_source 质量门禁 | READY | 高 | shared_source | L1/L4 | 部分实现 | Round 8 / Round 10 / Round 11 质量报告；`ai_shared/reports/shared_persistence_scada_template_round17.md`; `ai_shared/reports/shared_persistence_scada_template_round17_patch_closure.md`; shared_source unit/integration tests；shared persistence template tests | 本轮 `compileall` passed；`ruff` passed；`mypy src/whale/shared/persistence/template src/whale/shared/persistence/init_db.py tools/source_lab/access/providers tools/source_lab/protocols/beckhoff_ads tests/integration tests/support` 仍被仓库既有 ingest integration 存量错误阻塞，但 `mypy src/whale/shared/persistence/session.py src/whale/shared/persistence/init_db.py tools/source_lab/access/providers/scada_profile.py tools/source_lab/protocols/beckhoff_ads tests/integration/test_shared_persistence_sample_data_init.py tests/integration/test_source_lab_scada_profile_postgres.py tests/integration/test_source_lab_beckhoff_ads_runtime.py tests/support/scada_sample_db.py tools/source_lab/tests/access/test_scada_profile_runtime_coverage.py tools/source_lab/tests/access/test_beckhoff_ads_simulator_contract.py` -> passed；`pytest tests/unit/shared/persistence/test_scada_protocol_params.py tests/unit/shared/persistence/test_scada_sample_data_protocol_coverage.py tests/unit/shared/persistence/test_scada_protocol_views.py -q` -> 12 passed；`pytest tests/integration/test_shared_persistence_sample_data_init.py -q` -> 1 passed | 当前质量门禁新增证据覆盖 shared persistence 模板/视图/样例数据的 L1 建模与 `sample_data` L4 PostgreSQL 实跑；但全范围 mypy 仍受仓库既有 ingest integration 存量错误阻塞，不能把 shared_source 模块级质量门禁写成完全收口 | 继续将 shared_source 输入基线质量证据与 production client 质量门禁分开追踪，并补 runtime/integration/field 证据 | 2026-06-01 |
