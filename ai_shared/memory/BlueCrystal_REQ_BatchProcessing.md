# BlueCrystal_REQ_BatchProcessing

## 一、文件定位

本文件描述 BlueCrystal `batch_layer` 内部的 `processing` 能力需求。

`processing` 不再作为 BlueCrystal 一级架构模块存在。它是 `batch_layer` 内部能力，用于从 `raw_archive` 读取数据，执行清洗、标准化、质量处理、时间对齐、规则版本管理和回灌重算，并将结果写入 `standardized` 数据层。

本文件不描述实时消费、不描述 `speed_layer` 的轻量处理、不描述 `ingest` 采集、不描述 `storage` 后端实现细节。

原 `Whale_REQ_Processing.md` 应删除或替换为本文件，避免继续把 `processing` 误读为 Whale 一级模块。

---

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-002 | 作为 Lambda 批处理链路中的规则处理能力，由 `batch_layer` 编排 |
| P-FR-004 | 承接 raw -> standardized 的清洗、标准化、质量处理、时间对齐 |
| P-DGR-001 | 承接规则版本、schema 版本、数据血缘、可复算和可追溯 |

---

## 三、功能需求

### BP-FR-001 raw_archive -> standardized 处理

- 类型：功能
- 优先级：高
- 责任模块：batch_layer/processing
- 需求描述：
  - `batch_layer.processing` 应从 `raw_archive` 读取原始归档数据，完成清洗、标准化、时间对齐和质量处理，并写入 `standardized` 数据层。
- 验收要点：
  - 支持按时间窗口读取 raw_archive。
  - 支持批次输入和批次输出。
  - 支持标准化输出。
  - 支持质量码处理。
  - 支持输出 rule_version、schema_version、lineage_id。
  - 不直接连接现场 source。
  - 不直接消费 message pipeline。

### BP-FR-002 数据清洗与异常处理

- 类型：功能
- 优先级：高
- 责任模块：batch_layer/processing
- 需求描述：
  - `batch_layer.processing` 应处理缺失值、异常值、重复值、乱序数据、迟到数据和时间戳异常。
- 验收要点：
  - 清洗规则可配置。
  - 处理结果可追溯。
  - 异常数据应有明确处置状态。
  - 不得静默丢弃异常数据。
  - 支持质量细节记录。

### BP-FR-003 补采、回灌与历史重算

- 类型：功能
- 优先级：高
- 责任模块：batch_layer/processing
- 需求描述：
  - `batch_layer.processing` 应支持补采、回灌、历史重算和重复执行。
- 验收要点：
  - 支持 replay_batch_id 或等价回灌批次标识。
  - 支持按 source_id、device_id、node_key、time_range 重算。
  - 支持规则版本切换后的重算。
  - 支持幂等写入。
  - 支持失败后从明确边界恢复。

### BP-FR-004 schema version 兼容处理

- 类型：功能
- 优先级：高
- 责任模块：batch_layer/processing
- 需求描述：
  - `batch_layer.processing` 应支持 raw envelope、raw archive schema 和 standardized schema 的版本兼容处理。
- 验收要点：
  - 支持 schema_version 读取。
  - 支持兼容性校验。
  - 不兼容 schema 必须进入明确失败状态或隔离区。
  - schema 兼容策略必须可测试。

---

## 四、非功能需求

### BP-NFR-001 可复算与可追溯

- 类型：非功能
- 优先级：高
- 责任模块：batch_layer/processing
- 需求描述：
  - 处理过程必须可复算，处理规则必须可版本化，处理结果必须可追溯。
- 验收要点：
  - 记录 job_id、rule_version、schema_version、input_range、output_range、lineage_id。
  - 可从 raw_archive 重新生成 standardized。
  - 处理规则变更不得污染既有数据。
  - 支持重算前后结果对比。

### BP-NFR-002 幂等与恢复

- 类型：非功能
- 优先级：高
- 责任模块：batch_layer/processing
- 需求描述：
  - 处理任务必须支持幂等执行、失败恢复、断点续跑和重复运行。
- 验收要点：
  - 同一 job_id 或同一 input_range 重复执行不产生错误重复数据。
  - sink 失败不得提交成功状态。
  - 失败原因必须可追踪。
  - 可从 checkpoint 或任务状态恢复。

---

## 五、架构约束

### BP-AR-001 处理能力归属 batch_layer

- 类型：架构约束
- 优先级：高
- 责任模块：batch_layer/processing
- 需求描述：
  - `processing` 不再作为 Whale 一级模块存在，应作为 `batch_layer` 内部能力被编排。
- 验收要点：
  - 代码组织应逐步迁移到 `src/whale/batch_layer/processing/`。
  - 不得继续扩展 `src/whale/processing/` 作为一级模块。
  - 如保留旧路径，只能作为迁移期 legacy，不得新增业务能力。
  - `batch_layer` 负责任务调度、状态管理和 processing 调用。

### BP-AR-002 与 speed_layer 职责分离

- 类型：架构约束
- 优先级：高
- 责任模块：batch_layer/processing
- 需求描述：
  - `batch_layer.processing` 负责复杂清洗、标准化、历史重算和回灌；`speed_layer` 只负责实时轻处理。
- 验收要点：
  - `speed_layer` 不承担复杂历史重算。
  - `batch_layer.processing` 不直接管理实时 consumer group。
  - 两者通过 raw_archive、standardized 和规则版本保持一致。

---

## 六、测试与验收需求

### BP-TEST-001 processing 规则测试

- 类型：测试与验收
- 优先级：高
- 责任模块：batch_layer/processing
- 需求描述：
  - `batch_layer.processing` 必须具备清洗、标准化、质量处理、回灌和 schema 兼容测试。
- 验收要点：
  - 覆盖正常数据、异常数据、缺失数据、乱序数据、重复数据。
  - 覆盖不同 rule_version。
  - 覆盖 schema_version 兼容与不兼容。
  - 覆盖幂等重跑。

### BP-TEST-002 raw_archive -> processing -> standardized E2E

- 类型：测试与验收
- 优先级：高
- 责任模块：batch_layer/processing
- 需求描述：
  - 必须具备从 raw_archive 读取、调用 processing、写入 standardized 的 E2E 验证。
- 验收要点：
  - 覆盖成功、失败、重试、断点续跑、重复执行。
  - 覆盖 lineage_id 和 rule_version。
  - 覆盖输出数据质量码。
  - skipped 不得作为完成证据。

---

## 七、禁止事项

- 不得把 `processing` 继续扩展为 Whale 一级模块。
- 不得直接连接现场 source。
- 不得直接消费 message pipeline。
- 不得绕过 `batch_layer` 的 job 状态管理。
- 不得绕过 `storage.standardized` 写入端口。
- 不得用测试结构替代生产 schema。
- 不得把 skipped 测试作为完成证据。

---

## 八、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BP-FR-001 | P-FR-004 | raw_archive -> standardized 处理 | FR | 高 | batch_layer/processing | - | 未实现 | batch processing 不在当前 6 轮 L5 收口范围内。复杂清洗/历史重算/全量重算属于 batch processing，待现场部署后启动 | 无 | 全部（未实现） | 现场部署后实现 raw_archive->standardized 批处理链路 | 2026-06-03 (Round 6) |
| BP-FR-002 | P-FR-004 | 数据清洗与异常处理 | FR | 高 | batch_layer/processing | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后实现数据清洗与异常处理 | 2026-06-03 (Round 6) |
| BP-FR-003 | P-FR-004/P-NFR-002 | 补采、回灌与历史重算 | FR | 高 | batch_layer/processing | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后实现补采/回灌/历史重算 | 2026-06-03 (Round 6) |
| BP-FR-004 | P-DGR-001 | schema version 兼容处理 | FR | 高 | batch_layer/processing | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后实现 schema 兼容处理 | 2026-06-03 (Round 6) |
| BP-NFR-001 | P-DGR-001 | 可复算与可追溯 | NFR | 高 | batch_layer/processing | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后实现可复算与可追溯 | 2026-06-03 (Round 6) |
| BP-NFR-002 | P-NFR-002 | 幂等与恢复 | NFR | 高 | batch_layer/processing | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后实现幂等与恢复 | 2026-06-03 (Round 6) |
| BP-AR-001 | P-AR-001 | 处理能力归属 batch_layer | AR | 高 | batch_layer/processing | - | 未实现 | 现有 src/whale/processing 待迁移，不在当前 L5 收口范围 | 无 | 全部（待迁移） | 现场部署后将 processing 迁入 batch_layer | 2026-06-03 (Round 6) |
| BP-AR-002 | P-FR-002 | 与 speed_layer 职责分离 | AR | 高 | batch_layer/processing | - | 未实现 | 边界已有设计，但未实现代码验证 | 无 | 全部（未实现） | 现场部署后补充职责边界测试 | 2026-06-03 (Round 6) |
| BP-TEST-001 | P-NFR-004 | processing 规则测试 | TEST | 高 | batch_layer/processing | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后补充规则测试 | 2026-06-03 (Round 6) |
| BP-TEST-002 | P-NFR-004 | raw_archive -> processing -> standardized E2E | TEST | 高 | batch_layer/processing | - | 未实现 | 不在当前 6 轮 L5 收口范围内 | 无 | 全部（未实现） | 现场部署后补充批处理 E2E | 2026-06-03 (Round 6) |
