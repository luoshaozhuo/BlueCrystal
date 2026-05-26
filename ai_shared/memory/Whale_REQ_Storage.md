# Whale_REQ_Storage

## 一、文件定位

本文件描述 Whale 存储层需求，包括 raw layer、standard layer、warehouse/mart layer 和 serving cache。

本文件不描述 source 协议采集，不描述 processing 的清洗算法。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-002 | 承接实时链路 raw 写入和 serving cache |
| P-FR-004 | 承接标准层与数仓层存储 |
| P-DGR-001 | 承接 schema、版本与血缘治理 |

## 三、功能需求

### ST-FR-001 raw storage 原始层

- 类型：功能
- 优先级：高
- 需求描述：
  - storage 模块应提供 raw layer，用于保存原始状态、原始事件、原始时序和原始消息归档。
- 验收要点：
  - 支持按 source_id、device_id、node_key、timestamp 查询。
  - 支持原始消息或原始值可追溯。

### ST-FR-002 standard storage 标准层

- 类型：功能
- 优先级：高
- 需求描述：
  - storage 模块应提供 standard layer，用于保存清洗、标准化、质量处理后的数据。
- 验收要点：
  - 支持 schema version。
  - 支持质量码。
  - 支持时间基准对齐。

### ST-FR-003 warehouse / mart 层

- 类型：功能
- 优先级：高
- 需求描述：
  - storage 模块应支持面向分析、聚合、报表和服务的数据仓库与数据集市层。
- 验收要点：
  - 支持主题数据组织。
  - 支持查询和服务接口承接。

### ST-FR-004 serving cache

- 类型：功能
- 优先级：高
- 需求描述：
  - storage 模块应支持业务侧近实时 serving cache。
- 验收要点：
  - 支持按业务 key 更新和读取。
  - 支持 TTL、stale、乱序保护。

## 四、非功能需求

### ST-NFR-001 存储性能、TTL 与冷热分层

- 类型：非功能
- 优先级：高
- 需求描述：
  - storage 模块应支持高频写入、范围查询、TTL、归档和冷热分层。
- 验收要点：
  - 支持写入吞吐指标。
  - 支持时间范围查询。
  - 支持归档策略。

## 五、数据治理需求

### ST-DGR-001 存储 schema 与血缘

- 类型：数据治理
- 优先级：高
- 需求描述：
  - storage 模块应维护 raw、standard、warehouse/mart 的 schema、版本和血缘关系。
- 验收要点：
  - schema 变更可追踪。
  - raw 到 standard 的处理链路可追溯。

## 六、测试与验收需求

### ST-TEST-001 存储层 E2E

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - storage 模块必须具备 raw、standard、warehouse/mart、serving cache 的写入和查询测试。
- 验收要点：
  - 验证写入、查询、TTL、归档、schema 兼容。

## 七、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ST-FR-001 | P-FR-002 | raw storage 原始层 | FR | 高 | storage | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| ST-FR-002 | P-FR-004 | standard storage 标准层 | FR | 高 | storage | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| ST-FR-003 | P-FR-005 | warehouse / mart 层 | FR | 高 | storage | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| ST-FR-004 | P-FR-002 | serving cache | FR | 高 | storage | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| ST-NFR-001 | P-NFR-001 | 存储性能、TTL 与冷热分层 | NFR | 高 | storage | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| ST-DGR-001 | P-DGR-001 | 存储 schema 与血缘 | DGR | 高 | storage | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| ST-TEST-001 | P-NFR-004 | 存储层 E2E | TEST | 高 | storage | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
