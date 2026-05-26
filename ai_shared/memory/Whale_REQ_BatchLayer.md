# Whale_REQ_BatchLayer

## 一、文件定位

本文件描述 Whale batch layer 需求。batch layer 负责任务调度、raw 读取、processing 编排、standard 写入和任务状态管理。

本文件不描述 processing 规则细节，不描述实时 speed layer。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-002 | 承接 Lambda 批处理链路 |
| P-NFR-002 | 承接批任务恢复、幂等和状态管理 |

## 三、功能需求

### BL-FR-001 批处理调度

- 类型：功能
- 优先级：高
- 需求描述：
  - batch layer 应定期或按任务从 raw storage 读取数据，触发 processing 任务。
- 验收要点：
  - 支持定时调度。
  - 支持按时间窗口调度。
  - 支持手动补跑。

### BL-FR-002 批处理状态管理

- 类型：功能
- 优先级：高
- 需求描述：
  - batch layer 应管理批处理任务状态、进度、失败重试和断点续跑。
- 验收要点：
  - 记录 job_id、status、input_range、output_range、retry_count、failure_reason。

### BL-FR-003 raw -> standard 批处理链路

- 类型：功能
- 优先级：高
- 需求描述：
  - batch layer 应编排 raw layer 到 standard layer 的批处理链路。
- 验收要点：
  - 从 raw 读取。
  - 调用 processing。
  - 写入 standard。
  - 记录血缘。

## 四、非功能需求

### BL-NFR-001 可恢复与幂等

- 类型：非功能
- 优先级：高
- 需求描述：
  - batch layer 应支持失败恢复、幂等执行、重复运行和任务追踪。
- 验收要点：
  - 重复执行不产生错误重复数据。
  - 失败后可从明确边界恢复。

## 五、测试与验收需求

### BL-TEST-001 批处理 E2E

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - batch layer 必须具备 raw -> processing -> standard 的 E2E 测试。
- 验收要点：
  - 覆盖成功、失败、重试、断点续跑、重复执行。

## 六、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BL-FR-001 | P-FR-002 | 批处理调度 | FR | 高 | batch_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| BL-FR-002 | P-NFR-002 | 批处理状态管理 | FR | 高 | batch_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| BL-FR-003 | P-FR-004 | raw -> standard 批处理链路 | FR | 高 | batch_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| BL-NFR-001 | P-NFR-002 | 可恢复与幂等 | NFR | 高 | batch_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| BL-TEST-001 | P-NFR-004 | 批处理 E2E | TEST | 高 | batch_layer | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
