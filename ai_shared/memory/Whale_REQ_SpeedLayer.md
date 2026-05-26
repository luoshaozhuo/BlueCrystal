# Whale_REQ_SpeedLayer

## 一、文件定位

本文件描述 Whale 速度层需求。速度层消费 message pipeline 的实时数据，写入 raw storage，并更新业务侧 serving cache。

本文件不描述 ingest 采集，不描述批处理层复杂重算。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-002 | 承接实时链路中的消费、raw 写入和 serving cache 更新 |
| P-NFR-002 | 承接实时链路恢复和 offset 管理 |

## 三、功能需求

### SP-FR-001 消费 ingest 消息

- 类型：功能
- 优先级：高
- 需求描述：
  - speed layer 应从 message pipeline 消费 ingest 发布的实时消息。
- 验收要点：
  - 支持 consumer group。
  - 支持 offset 管理。
  - 支持消息 schema 校验。

### SP-FR-002 写入 raw storage

- 类型：功能
- 优先级：高
- 需求描述：
  - speed layer 应将实时消息写入 raw storage。
- 验收要点：
  - 支持幂等写入。
  - 支持失败重试。
  - 支持原始消息或原始状态保留。

### SP-FR-003 更新 serving cache

- 类型：功能
- 优先级：高
- 需求描述：
  - speed layer 应更新业务侧 serving cache，支撑近实时监视与业务查询。
- 验收要点：
  - 支持按 source/device/node 更新。
  - 支持 stale 和 TTL。
  - 支持乱序保护。

### SP-FR-004 实时轻处理

- 类型：功能
- 优先级：高
- 需求描述：
  - speed layer 应执行实时链路中的轻量去重、质量状态处理、时间戳校验和必要格式转换。
- 验收要点：
  - 支持重复消息识别。
  - 支持迟到或乱序数据策略。
  - 支持质量码透传。

## 四、非功能需求

### SP-NFR-001 近实时延迟与吞吐

- 类型：非功能
- 优先级：高
- 需求描述：
  - speed layer 应满足近实时消费、写 raw 和更新 serving cache 的时延要求。
- 验收要点：
  - 输出消费延迟、写入延迟、cache 更新延迟、consumer lag。

## 五、架构约束

### SP-AR-001 实时链路职责边界

- 类型：架构约束
- 优先级：高
- 需求描述：
  - speed layer 不承担复杂批处理、全量重算和数仓分层职责。
- 验收要点：
  - 复杂清洗、标准化和全量重算由 batch/processing 承担。

## 六、测试与验收需求

### SP-TEST-001 speed layer E2E

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - speed layer 必须具备 message -> raw -> serving cache 的 E2E 测试。
- 验收要点：
  - 验证消费、幂等写入、cache 更新、失败恢复和 offset 管理。

## 七、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SP-FR-001 | P-FR-002 | 消费 ingest 消息 | FR | 高 | speed_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SP-FR-002 | P-FR-002 | 写入 raw storage | FR | 高 | speed_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SP-FR-003 | P-FR-002 | 更新 serving cache | FR | 高 | speed_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SP-FR-004 | P-FR-002 | 实时轻处理 | FR | 高 | speed_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SP-NFR-001 | P-NFR-001 | 近实时延迟与吞吐 | NFR | 高 | speed_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SP-AR-001 | P-FR-002 | 实时链路职责边界 | AR | 高 | speed_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| SP-TEST-001 | P-NFR-004 | speed layer E2E | TEST | 高 | speed_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
