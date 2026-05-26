# Whale_REQ_MessagePipeline

## 一、文件定位

本文件描述 Whale 消息管道需求。消息管道承担 ingest 与 speed layer/downstream consumers 之间的异步解耦。

本文件不描述 source 协议采集，不描述 speed layer 的业务处理逻辑。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-002 | 承接实时链路中的异步解耦、消息留存和回放 |
| P-NFR-005 | 承接消息认证、授权和加密 |

## 三、功能需求

### MP-FR-001 消息主题、分区与 key 策略

- 类型：功能
- 优先级：高
- 需求描述：
  - message pipeline 应承载 ingest 发布的数据，并通过 topic、partition、key 策略解耦上游 ingest 与下游 speed layer。
- 验收要点：
  - topic 可配置。
  - key 策略可配置。
  - partition 策略可配置。
  - 支持按 source_id、device_id、station_id 或业务 key 保序。

### MP-FR-002 消息 envelope 与 schema version

- 类型：功能
- 优先级：高
- 需求描述：
  - message pipeline 中的消息必须具备统一 envelope 和 schema_version。
- 验收要点：
  - 消息包含 schema_version、message_id、message_type、trace_id、source_id、published_at、items。
  - 支持 schema 演进和兼容策略。

### MP-FR-003 重试、DLQ、回放与留存

- 类型：功能
- 优先级：高
- 需求描述：
  - message pipeline 应支持发送失败重试、dead letter topic、消息留存和回放。
- 验收要点：
  - 支持 retry policy。
  - 支持 DLQ 或等价失败隔离。
  - 支持按 topic 和时间窗口回放。
  - 支持留存周期配置。

## 四、非功能需求

### MP-NFR-001 吞吐、积压与可用性

- 类型：非功能
- 优先级：高
- 需求描述：
  - message pipeline 应支撑 ingest 高吞吐发布、下游消费积压和短时峰值流量。
- 验收要点：
  - 输出 publish latency、consumer lag、retry count、backlog 指标。
  - 支持 producer/consumer 健康检查。

### MP-NFR-002 认证、鉴权与加密

- 类型：非功能
- 优先级：高
- 需求描述：
  - message pipeline 应支持认证、授权、TLS 和最小权限 topic 访问。
- 验收要点：
  - 支持 SASL/SSL 或等价安全机制。
  - 凭据不硬编码。
  - 日志不输出敏感信息。

## 五、架构约束

### MP-AR-001 异步解耦边界

- 类型：架构约束
- 优先级：高
- 需求描述：
  - message pipeline 应作为 ingest 与 speed layer 的异步解耦边界。
- 验收要点：
  - ingest 不直接调用 speed layer。
  - speed layer 通过 consumer group 消费消息。

## 六、测试与验收需求

### MP-TEST-001 消息管道 E2E

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - message pipeline 必须具备 producer、broker、consumer 的 E2E 验证。
- 验收要点：
  - 验证消息发布、消费、schema、key、失败处理和 DLQ。

## 七、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MP-FR-001 | P-FR-002 | 消息主题、分区与 key 策略 | FR | 高 | message_pipeline | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| MP-FR-002 | P-FR-002 | 消息 envelope 与 schema version | FR | 高 | message_pipeline | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| MP-FR-003 | P-NFR-002 | 重试、DLQ、回放与留存 | FR | 高 | message_pipeline | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| MP-NFR-001 | P-NFR-001 | 吞吐、积压与可用性 | NFR | 高 | message_pipeline | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| MP-NFR-002 | P-NFR-005 | 认证、鉴权与加密 | NFR | 高 | message_pipeline | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| MP-AR-001 | P-FR-002 | 异步解耦边界 | AR | 高 | message_pipeline | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| MP-TEST-001 | P-NFR-004 | 消息管道 E2E | TEST | 高 | message_pipeline | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
