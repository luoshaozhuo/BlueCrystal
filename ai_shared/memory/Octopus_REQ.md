# Octopus_REQ

## 一、文件定位

本文件描述 Octopus 运维执行面需求。Octopus 与 Whale 并列，负责运维观测、统一部署编排、监控、告警、诊断执行、自动化恢复、回滚和运行报告。

本文件不描述安全治理策略、权限审批、合规门禁和变更控制，这些归 Turtle；不描述 logging/metrics/trace/retry/debug helper，这些归 PlatformShared。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-NFR-002 | 承接自动化恢复、回滚执行、运行巡检 |
| P-NFR-004 | 承接监控、告警、诊断执行和运行报告 |
| P-AR-003 | 承接 Octopus 与 Whale/Turtle/PlatformShared 的边界 |

## 三、功能需求

### OC-FR-001 统一部署编排执行

- 类型：功能
- 优先级：高
- 需求描述：
  - Octopus 应统一编排 Whale、Turtle、Dolphin、Jellyfish、Manta 等组件的部署、升级、回滚和健康检查。
- 验收要点：
  - 读取各模块自己的部署定义。
  - 不接管单模块部署定义。
  - 部署准入由 Turtle 判断。

### OC-FR-002 监控与告警

- 类型：功能
- 优先级：高
- 需求描述：
  - Octopus 应采集、汇聚和展示日志、指标、trace、health、readyz、consumer lag、writer latency、checkpoint 等运行信号。
- 验收要点：
  - 支持告警规则。
  - 支持 dashboard 或等价展示。
  - 可消费 PlatformShared 标准上下文。

### OC-FR-003 诊断执行与巡检

- 类型：功能
- 优先级：高
- 需求描述：
  - Octopus 应提供运行诊断、依赖检查、现场预检、巡检和故障定位能力。
- 验收要点：
  - 支持模块级 smoke 调用。
  - 支持依赖矩阵检查。
  - 支持生成运行报告。

### OC-FR-004 自动化恢复与回滚执行

- 类型：功能
- 优先级：高
- 需求描述：
  - Octopus 应执行自动化恢复、重启、回滚、切换和恢复后验证。
- 验收要点：
  - 恢复动作受 Turtle 策略约束。
  - 恢复动作必须留痕。

## 四、架构约束

### OC-AR-001 Octopus 与 Whale 并列

- 类型：架构约束
- 优先级：高
- 需求描述：
  - Octopus 必须位于 `src/octopus`，不得位于 `src/whale/octopus`。
- 验收要点：
  - import boundary gate 覆盖该约束。

### OC-AR-002 单模块部署定义不集中

- 类型：架构约束
- 优先级：高
- 需求描述：
  - 单模块部署定义放各模块或 `deploy/<component>/<module>/`，Octopus 负责统一编排执行，不成为所有部署文件的集中堆放目录。
- 验收要点：
  - `deploy/whale/ingest` 等模块目录保留。

## 五、测试与验收需求

### OC-TEST-001 Octopus 边界测试

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - Octopus 必须具备 import boundary、部署目录边界和只执行不治理的边界测试。
- 验收要点：
  - 不定义安全治理策略。
  - 不替代 Turtle 审批。

## 六、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OC-FR-001 | P-NFR-004 | 统一部署编排执行 | FR | 高 | octopus | L0 | skeleton-ready | src/octopus 结构存在；deploy/whale 最小部署文档存在 | 边界测试待补 | 统一编排未实现 | 后续实现 orchestration/deployment runtime | 待更新 |
| OC-FR-002 | P-NFR-004 | 监控与告警 | FR | 高 | octopus | 未开始 | 未实现 | 无 | 无 | 全部 | 规划 monitoring/alerting | 待更新 |
| OC-FR-003 | P-NFR-004 | 诊断执行与巡检 | FR | 高 | octopus | 未开始 | 未实现 | 无 | 无 | 全部 | 规划 diagnostics/automation/report | 待更新 |
| OC-FR-004 | P-NFR-002 | 自动化恢复与回滚执行 | FR | 高 | octopus | 未开始 | 未实现 | 无 | 无 | 全部 | 规划 rollback/automation | 待更新 |
| OC-AR-001 | P-AR-003 | Octopus 与 Whale 并列 | AR | 高 | octopus | L3 | 已验证 | src/octopus 与 src/whale 并列；boundary test 升级至 79 tests 覆盖 platform_shared 全量边界 | import boundary tests (79 passed) | 无 | 无 | 2026-06-02 |
| OC-AR-002 | P-AR-003 | 单模块部署定义不集中 | AR | 高 | octopus + deploy | L0 | 部分实现 | deploy/whale 已存在 | 待补边界测试 | 统一编排未实现 | 补部署边界测试 | 待更新 |
| OC-TEST-001 | P-NFR-004 | Octopus 边界测试 | TEST | 高 | octopus | L3 | 已通过 | import boundary tests 覆盖并列结构与 platform_shared 边界（79 tests） | test_turtle_octopus_import_boundary.py (79 passed) | 运维执行行为未测试 | 后续实现后补充测试 | 2026-06-02 |
