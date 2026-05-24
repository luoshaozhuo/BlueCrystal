# ADR-20260523-001-source-lab-server-client-ingest-boundary

## Status

Accepted

## Keywords

- source_lab
- simulator
- production client
- ingest
- clean architecture
- dependency boundary

## Context

Whale 项目需要同时支持两类不同性质的 source 能力：

1. 本地开发、调试、容量测试使用的 source server / simulator。
2. 生产环境使用的 source client，用于从现场设备读取数据，并在后续支持写入 / 控制。

已有探查表明，`tools/source_lab` 已经包含 simulator、probe、capacity、profile、runner、provider 等能力，但这些能力并不都适合作为生产采集链路直接依赖。

同时，`src/whale/ingest` 已采用 clean architecture / port-adapter 结构，现有 `SourceAcquisitionUseCase` 通过 role 编排读取流程，通过 port 调用 source adapter，并通过 cache port 写入 Redis 状态缓存。

因此，需要先固化 source_lab、shared/source、ingest 三者的依赖方向和职责边界，避免后续开发把测试工具、生产 client、use case 职责混在一起。

本 ADR 只记录三层之间的依赖边界，不展开 source_lab 的 facade 类型，也不定义 write port 设计。后两者分别由后续 ADR 记录。

## Decision

### 1. source_lab 的总体边界

`tools/source_lab` 定位为 source 接入实验室与本地测试工具集合，主要用于：

- 启动本地 simulator / server。
- 执行 field probe。
- 执行 polling / subscription capacity 测试。
- 执行 profile / 性能画像。
- 为生产 client 设计提供验证材料和协议行为证据。

`tools/source_lab` 不作为 `src/whale/ingest` 的生产运行时依赖。

### 2. server / simulator 边界

source server / simulator 能力继续保留在 `tools/source_lab`。

它面向：

- 本地开发。
- 集成测试。
- 协议行为验证。
- 性能容量测试。
- 回归验证。

simulator 不进入生产部署主链路。

### 3. production client 边界

生产 client 能力应位于 `src/whale/shared/source`。

`shared/source` 承担：

- 协议 client 的生产级实现。
- native runner / backend 的生产级封装。
- `connect / read / subscribe / write / close` 等长期运行接口。
- 可被 ingest 或其他模块复用的 source access 能力。

`tools/source_lab` 中已有的 native runner、协议 stdout/stderr 约定、simulator 行为和测试矩阵，可以作为 `shared/source` 生产 client 实现的参考材料，但不直接成为 ingest 的依赖。

### 4. ingest 边界

`src/whale/ingest` 继续保持 use case / role / port / adapter 分层：

- use case 只负责业务入口、请求校验和模式分发。
- role 只负责编排 polling / subscription 等采集策略。
- port 只定义 ingest 对外部能力的抽象需求。
- adapter 负责把 source client、cache、message queue 等基础设施接入 port。
- ingest 不直接依赖 `tools/source_lab`。
- ingest 通过 port 依赖 `shared/source` 提供的生产 source client adapter。

### 5. 依赖方向

长期依赖方向为：

```text
tools/source_lab  ──用于测试/验证──▶ shared/source
ingest            ──通过 adapter──▶ shared/source
ingest            ──不得依赖──X──▶ tools/source_lab
shared/source     ──不得依赖──X──▶ ingest
```

## Consequences

### 收益

- 避免把测试工具误用为生产 client。
- 避免 ingest 直接耦合 source_lab 的 capacity/profile 任务模型。
- 保持 clean architecture 的 port-adapter 边界稳定。
- 为后续多协议生产 client 下沉到 `shared/source` 留出空间。
- 为 simulator 与 production client 分别演进提供清晰边界。

### 代价

- `tools/source_lab` 与 `shared/source` 之间可能存在部分协议子进程管理逻辑重复。
- 多协议生产 client 不能简单复用 source_lab runner，需要在 `shared/source` 中重新封装生产级 backend。
- 后续需要补充 shared/source 层的通用 source access 抽象和测试。

### 约束

- 不允许为了快速接入多协议而让 ingest 直接调用 `tools/source_lab/access/runners/*`。
- 不允许把 probe/capacity/profile 的测试配置模型泄漏到生产 use case。
- 不允许把 simulator 作为生产 source adapter 的一部分。
- 不允许通过修改 `SourceAcquisitionUseCase` 绕过 port-adapter 边界。

## Rejected Options

### 方案一：ingest 直接依赖 source_lab runner

拒绝。

原因：

- source_lab runner 当前主要服务 probe/capacity/profile。
- runner 返回指标和测试统计，不是生产采集 batch。
- 容易把测试参数、扫描逻辑、CLI 逻辑带入生产链路。
- 会破坏 ingest 的 port-adapter 边界。

### 方案二：把 simulator 移入 shared/source

拒绝。

原因：

- simulator 是开发测试工具，不是生产 client。
- shared/source 应保持生产 client 语义。
- simulator fleet、端口分配、mock server 生命周期管理不应污染生产包。

### 方案三：把 production client 放在 source_lab

拒绝。

原因：

- source_lab 是工具层，不是生产运行时层。
- 生产 client 需要被 ingest 与未来其他模块复用，应放在 shared/source。
- source_lab 的任务 facade 和生产 client facade 语义不同。

## Related Files

- `tools/source_lab/`
- `tools/source_lab/factory.py`
- `tools/source_lab/fleet.py`
- `tools/source_lab/access/`
- `tools/source_lab/protocols/`
- `tools/source_lab/native/`
- `src/whale/shared/source/`
- `src/whale/shared/source/access/`
- `src/whale/shared/source/opcua/`
- `src/whale/ingest/usecases/source_acquisition_use_case.py`
- `src/whale/ingest/usecases/roles/polling_acquisition_role.py`
- `src/whale/ingest/usecases/roles/subscription_acquisition_role.py`
- `src/whale/ingest/ports/source/source_acquisition_port.py`
- `src/whale/ingest/adapters/source/opcua_source_acquisition_adapter.py`

## Supersedes / Superseded By

None.
