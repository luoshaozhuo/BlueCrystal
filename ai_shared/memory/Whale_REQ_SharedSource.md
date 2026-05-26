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
| opcua | 待核实 | 待核实 | 待核实 | NOT_IMPLEMENTED | 待核实 | 待核实 | 待核实 | 待核实 | 待代码核实 |
| modbus_tcp | 待核实 | 待核实 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 待核实 | 待核实 | 待核实 | 待核实 | 待代码核实 |
| iec104 | 待核实 | 待核实 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 待核实 | 待核实 | 待核实 | 待核实 | 待代码核实 |
| iec61850_mms | 待核实 | 待核实 | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 待核实 | 待核实 | 待核实 | 待核实 | 待代码核实 |
| iec61850_report | NOT_IMPLEMENTED | NOT_IMPLEMENTED | 待核实 | 待核实 | 待核实 | 待核实 | 待核实 | 待核实 | 待代码核实 |

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

## 八、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SS-FR-001 | P-FR-001 | production source client | FR | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-FR-002 | P-FR-001 | 多协议 backend | FR | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-FR-003 | P-FR-001 | read/write/subscription/report 能力 | FR | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-NFR-001 | P-NFR-001 | 协议真实性与性能 | NFR | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-NFR-002 | P-NFR-002/P-NFR-005 | 资源管理与安全 | NFR | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-AR-001 | P-AR-001/P-AR-002 | shared_source 不依赖 ingest/source_lab | AR | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-TEST-001 | P-NFR-004 | production client 测试准入 | TEST | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
