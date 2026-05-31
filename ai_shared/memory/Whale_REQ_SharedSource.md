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
| SS-FR-001 | P-FR-001 | production source client | FR | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-FR-002 | P-FR-001 | 多协议 backend | FR | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-FR-003 | P-FR-001 | read/write/subscription/report 能力 | FR | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-NFR-001 | P-NFR-001 | 协议真实性与性能 | NFR | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-NFR-002 | P-NFR-002/P-NFR-005 | 资源管理与安全 | NFR | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-AR-001 | P-AR-001/P-AR-002 | shared_source 不依赖 ingest/source_lab | AR | 高 | shared_source | L2/L3 | 部分实现 | `src/whale/shared/source/runner_resolution.py`; `tests/unit/test_shared_source_runner_resolution.py`; `tests/unit/test_ingest_no_source_lab_imports.py`; `ai_shared/adr/ADR-20260530-010-shared-source-production-runner-artifact-boundary.md` | `pytest tests/unit/test_shared_source_runner_resolution.py -q` -> 5 passed；`pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed | Python import 边界成立，且默认 runner 路径已不再指向 `tools/source_lab/native/build`；但生产 runner artifact 交付/安装证据仍待补齐 | 补独立 production runner artifact 安装与现场验证证据 | 2026-05-30 |
| SS-TEST-001 | P-NFR-004 | production client 测试准入 | TEST | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SS-READY-001 | P-AR-001/P-AR-002 | shared_source 独立部署与被装配准入 | READY | 高 | shared_source | L2/L3 | 部分实现 | `src/whale/shared/source/runner_resolution.py`; 各协议 backend；source adapter tests；Round 11 ADR/report | 已补 production runner path / dev fallback 边界；ingest/shared_source 仍无 `tools.source_lab` import | 仍缺独立 production runner artifact 的交付与部署 runbook，因此不能写 fully production-ready | 回填 artifact 安装、PATH/环境变量发布流程和现场验收 | 2026-05-30 |
| SS-READY-002 | P-FR-001/P-NFR-001 | shared_source 协议能力准入 | READY | 高 | shared_source | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 需核实每个协议 declared/runtime/evidence 是否分离，readback 是否真实可用 | 回填 capability matrix、readback、unsupported 和真实协议证据 | 待更新 |
| SS-READY-003 | P-NFR-002/P-NFR-005 | shared_source 安全与资源准入 | READY | 高 | shared_source | L2/L3 | 部分实现 | timeout/cleanup/backend tests；`tests/unit/test_iec61850_mms_backend.py`; `tests/unit/test_iec61850_report_backend.py`; `tests/unit/test_shared_source_runner_resolution.py` | runner 缺失、timeout、cleanup、report reconnect 等已有单测；本轮新增 runner unavailable/build hint 边界测试 | 凭据保护、认证配置和独立 artifact 交付仍需进一步归档 | 回填生产配置与现场故障分类证据 | 2026-05-30 |
| SS-READY-004 | P-NFR-004 | shared_source 质量门禁 | READY | 高 | shared_source | L3 | 部分实现 | Round 8 / Round 10 / Round 11 质量报告；shared_source unit/integration tests | `compileall` PASS；`ruff check` PASS；`mypy src/whale/ingest src/whale/shared/source` PASS；Round 11 针对性 shared_source tests PASS | shared_source 质量门禁通过不等于 field/readback/runner artifact 生产收口 | 保持 shared_source 质量门禁与独立准入边界分开追踪 | 2026-05-30 |
