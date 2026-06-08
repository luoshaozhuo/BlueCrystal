# BlueCrystal_REQ_ServingAggregation

## 一、文件定位

本文件描述 BlueCrystal 中面向查询、数仓和数据集市的聚合能力需求。

`aggregation` 不再作为 BlueCrystal 一级架构模块存在。它应归入 `serving`、`storage.warehouse`、`storage.mart` 或后续 Dolphin 业务能力服务的内部能力，用于构建实时聚合、周期聚合和业务主题聚合结果。

本文件不描述 source 接入，不描述 raw 写入，不描述基础清洗逻辑，不描述 Dolphin 业务服务的完整实现。

原 `Whale_REQ_Aggregation.md` 应删除或替换为本文件，避免继续把 `aggregation` 误读为 Whale 一级模块。

---

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-005 | 承接业务主题聚合、查询服务和服务层数据构建 |
| P-DGR-001 | 承接口径、规则版本、血缘和可重算 |
| P-FR-002 | 承接实时链路和批处理链路输出后的聚合消费 |

---

## 三、功能需求

### SA-FR-001 实时聚合

- 类型：功能
- 优先级：高
- 责任模块：serving/aggregation 或 storage/warehouse
- 需求描述：
  - 聚合能力应支持基于 `speed_layer` 输出、`serving_cache` 或 `standardized` 数据的近实时聚合。
- 验收要点：
  - 支持窗口聚合。
  - 支持质量码策略。
  - 支持迟到数据策略。
  - 支持按 station、device、node_key、business_key 聚合。
  - 支持 serving 查询读取。
  - 不直接连接现场 source。
  - 不负责 raw 写入。

### SA-FR-002 周期聚合

- 类型：功能
- 优先级：高
- 责任模块：storage/warehouse 或 storage/mart
- 需求描述：
  - 聚合能力应支持基于 `standardized`、`warehouse` 或 `mart` 的周期聚合。
- 验收要点：
  - 支持小时、日、月等周期。
  - 支持补跑。
  - 支持历史重算。
  - 支持聚合口径版本。
  - 支持聚合结果可追溯。

### SA-FR-003 业务主题聚合

- 类型：功能
- 优先级：高
- 责任模块：storage/mart、serving 或 Dolphin
- 需求描述：
  - 聚合能力应支持面向风电、光伏、储能、并网点、设备健康、能量统计、功率预测、运行绩效和资产价值分析等业务主题的数据集构建。
- 验收要点：
  - 输出主题数据集。
  - 支持服务层读取。
  - 支持口径版本。
  - 支持指标来源追溯。
  - 支持后续 Dolphin 能力服务复用。

### SA-FR-004 聚合结果服务化

- 类型：功能
- 优先级：高
- 责任模块：serving
- 需求描述：
  - 聚合结果应通过 Whale `serving` 层提供稳定查询能力，支撑 Dolphin、Jellyfish 和 Manta 使用。
- 验收要点：
  - 支持分页、过滤、时间范围查询。
  - 支持指标口径查询。
  - 支持数据新鲜度标识。
  - 支持统一错误语义。
  - 不允许 Web 工作台直接耦合底层存储表。

---

## 四、非功能需求

### SA-NFR-001 一致性与可重算

- 类型：非功能
- 优先级：高
- 责任模块：serving/aggregation 或 storage/warehouse/mart
- 需求描述：
  - 聚合能力应保证聚合口径、时间窗口、质量规则、输入范围和版本可追踪。
- 验收要点：
  - 记录 aggregation_rule_version。
  - 记录 input_range 和 output_range。
  - 支持历史重算。
  - 支持重算前后结果对比。
  - 支持异常聚合任务追踪。

### SA-NFR-002 查询性能与缓存

- 类型：非功能
- 优先级：高
- 责任模块：serving
- 需求描述：
  - 聚合结果应满足业务查询、报表查询和工作台展示的响应要求。
- 验收要点：
  - 支持热点聚合结果缓存。
  - 支持查询耗时指标。
  - 支持 cache stale 标识。
  - 支持容量评估。

---

## 五、架构约束

### SA-AR-001 聚合能力非一级模块

- 类型：架构约束
- 优先级：高
- 责任模块：serving/storage
- 需求描述：
  - `aggregation` 不再作为 Whale 一级模块存在，应作为 `serving`、`storage.warehouse`、`storage.mart` 或后续 Dolphin 能力服务的内部能力实现。
- 验收要点：
  - 不得继续扩展 `src/whale/aggregation/` 作为一级模块。
  - 如保留旧路径，只能作为迁移期 legacy，不得新增业务能力。
  - 新实现优先放入 `src/whale/serving/aggregation/`、`src/whale/storage/warehouse/` 或 `src/whale/storage/mart/`。
  - 面向业务服务的高级聚合可由 Dolphin 承接，但应通过 Whale serving 读取数据。

### SA-AR-002 聚合层职责边界

- 类型：架构约束
- 优先级：高
- 责任模块：serving/storage
- 需求描述：
  - 聚合能力不直接连接现场 source，不负责 raw_archive 写入，不承担基础清洗和标准化职责。
- 验收要点：
  - 输入来自 `standardized`、`warehouse`、`mart`、`speed_layer` 或 `serving_cache`。
  - 输出到 `warehouse`、`mart`、`serving` 或 Dolphin。
  - 复杂清洗由 `batch_layer.processing` 承担。
  - 实时轻处理由 `speed_layer` 承担。

---

## 六、测试与验收需求

### SA-TEST-001 聚合规则测试

- 类型：测试与验收
- 优先级：高
- 责任模块：serving/aggregation 或 storage/warehouse/mart
- 需求描述：
  - 聚合能力必须具备实时聚合、周期聚合和业务主题聚合测试。
- 验收要点：
  - 覆盖窗口边界。
  - 覆盖迟到数据。
  - 覆盖质量码。
  - 覆盖补跑重算。
  - 覆盖 aggregation_rule_version。

### SA-TEST-002 聚合结果查询 E2E

- 类型：测试与验收
- 优先级：高
- 责任模块：serving
- 需求描述：
  - 必须具备从标准化数据或数仓数据生成聚合结果，并通过 serving 查询的 E2E 验证。
- 验收要点：
  - 验证聚合写入。
  - 验证查询读取。
  - 验证口径版本。
  - 验证时间范围过滤。
  - 验证数据新鲜度。
  - skipped 不得作为完成证据。

---

## 七、禁止事项

- 不得把 `aggregation` 继续扩展为 Whale 一级模块。
- 不得直接连接现场 source。
- 不得负责 raw_archive 写入。
- 不得承担基础清洗、标准化和质量处理职责。
- 不得让 Manta 或 Jellyfish 直接查询底层存储表。
- 不得把 skipped 测试作为完成证据。

---

## 八、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SA-FR-001 | P-FR-005 | 实时聚合 | FR | 高 | serving/aggregation | - | 未实现 | 聚合/服务层不在当前 6 轮 L5 收口范围内。serving_cache (Redis) L5 verified 但仅覆盖近实时 cache，不覆盖聚合查询 | 无 | 全部（未实现） | 现场部署后实现实时聚合 | 2026-06-03 (Round 6) |
| SA-FR-002 | P-FR-005 | 周期聚合 | FR | 高 | storage/warehouse 或 storage/mart | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后实现周期聚合 | 2026-06-03 (Round 6) |
| SA-FR-003 | P-FR-005 | 业务主题聚合 | FR | 高 | storage/mart/serving/Dolphin | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后实现业务主题聚合 | 2026-06-03 (Round 6) |
| SA-FR-004 | P-FR-005 | 聚合结果服务化 | FR | 高 | serving | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后实现 serving 服务化接口 | 2026-06-03 (Round 6) |
| SA-NFR-001 | P-DGR-001 | 一致性与可重算 | NFR | 高 | serving/storage | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后实现一致性与可重算 | 2026-06-03 (Round 6) |
| SA-NFR-002 | P-NFR-001/P-NFR-004 | 查询性能与缓存 | NFR | 高 | serving | - | 未实现 | 不在当前 6 轮 L5 收口范围内；serving_cache L5 verified 仅覆盖近实时 cache | 无 | 全部（未实现） | 现场部署后实现查询性能与缓存 | 2026-06-03 (Round 6) |
| SA-AR-001 | P-AR-001 | 聚合能力非一级模块 | AR | 高 | serving/storage | - | 未实现 | 现有 src/whale/aggregation 待迁移，不在当前 L5 收口范围 | 无 | 全部（待迁移） | 现场部署后将 aggregation 迁入 serving/storage | 2026-06-03 (Round 6) |
| SA-AR-002 | P-FR-002 | 聚合层职责边界 | AR | 高 | serving/storage | - | 未实现 | 边界已有设计，但未实现代码验证 | 无 | 全部（未实现） | 现场部署后补充职责边界测试 | 2026-06-03 (Round 6) |
| SA-TEST-001 | P-NFR-004 | 聚合规则测试 | TEST | 高 | serving/storage | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后补充聚合规则测试 | 2026-06-03 (Round 6) |
| SA-TEST-002 | P-NFR-004 | 聚合结果查询 E2E | TEST | 高 | serving | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后补充聚合查询 E2E | 2026-06-03 (Round 6) |
