# Turtle_REQ

## 一、文件定位

本文件描述 Turtle 治理控制面需求。Turtle 与 BlueCrystal 并列，负责治理、安全、审计、合规、策略、部署准入和变更控制。

本文件不描述运行监控平台、告警平台、部署执行脚本和自动化恢复执行，这些归 Octopus；不描述公共 logging/metrics/trace/retry/debug helper，这些归 PlatformShared。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-NFR-005 | 承接认证、鉴权、凭据、TLS、合规、安全区、审计和控制安全 |
| P-SCR-001 | 承接电力监控系统安全边界、控制命令授权和审计 |
| P-AR-003 | 承接 Turtle 与 BlueCrystal/PlatformShared 的边界 |

## 三、功能需求

### TU-FR-001 auth 身份与授权

- 类型：功能
- 优先级：高
- 需求描述：
  - Turtle 应提供 principal、actor、role、permission、policy decision 等身份与授权基础能力。
- 验收要点：
  - 支持授权检查。
  - 支持 allow/deny 决策表达。
  - 支持被 ingest 等模块以 port/adapter/composition 方式接入。

### TU-FR-002 security 安全基础模型

- 类型：功能
- 优先级：高
- 需求描述：
  - Turtle 应提供 TLS、证书、密钥、token、secret provider、安全模型等安全基础能力。
- 验收要点：
  - 凭据不得硬编码。
  - 支持外部 KMS/CA/secret provider 适配边界。

### TU-FR-003 compliance 合规与数据分类

- 类型：功能
- 优先级：高
- 需求描述：
  - Turtle 应提供数据分类、安全区、留存策略、审计策略和合规证据基础能力。
- 验收要点：
  - 数据分类分级可表达。
  - 安全区和数据流向可表达。
  - 留存策略可表达。

### TU-FR-004 audit 审计中心

- 类型：功能
- 优先级：高
- 需求描述：
  - Turtle 应提供审计事件模型、审计归集、审计查询和外部 SIEM 适配边界。
- 验收要点：
  - 支持 API、配置、控制、部署、模型和数据访问审计。
  - 支持审计 sink 可替换。

### TU-FR-005 policy / governance / risk

- 类型：功能
- 优先级：高
- 需求描述：
  - Turtle 应提供策略定义、策略版本、策略发布、API 治理、配置治理、模型治理、数据治理和风险策略能力。
- 验收要点：
  - 支持策略版本。
  - 支持风险等级和审批边界表达。

### TU-FR-006 deployment_policy / change_control

- 类型：功能
- 优先级：高
- 需求描述：
  - Turtle 应提供部署准入、环境边界、发布门禁、变更审批、变更记录和回滚约束。
- 验收要点：
  - 支持谁能部署、部署到哪里、是否通过门禁、是否需要审批、是否留痕。
  - 不执行部署动作。

## 四、架构约束

### TU-AR-001 Turtle 与 BlueCrystal 并列

- 类型：架构约束
- 优先级：高
- 需求描述：
  - Turtle 必须位于 `src/turtle`，不得位于 `src/whale/turtle`。
- 验收要点：
  - import boundary gate 覆盖该约束。

### TU-AR-002 Turtle 不承载运行时工具

- 类型：架构约束
- 优先级：高
- 需求描述：
  - Turtle 不承载 logging/metrics/trace/retry/debug helper，不执行部署动作，不采集运行指标。
- 验收要点：
  - 公共 helper 位于 platform_shared。
  - 执行与观测平台位于 octopus。

## 五、测试与验收需求

### TU-TEST-001 Turtle 边界与迁移测试

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - Turtle 必须具备 import boundary、auth/security/compliance 迁移、旧路径 ImportError 和接入型集成测试。
- 验收要点：
  - `whale.shared.crosscutting.auth/security/compliance` 不存在。
  - 旧路径 import 抛出 ImportError。
  - 业务代码不再 import 旧路径。

## 六、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TU-FR-001 | P-NFR-005 | auth 身份与授权 | FR | 高 | turtle | L3 simulator | 已实现并收口 | turtle.auth；Round4 删除 shared auth shim，全仓旧路径 import 无残留 | boundary 41 passed + integration 7 updated + compileall/ruff/mypy | 外部 IAM 未 L5 验证 | 外部 IAM 真实集成 | 2026-06-02 |
| TU-FR-002 | P-NFR-005 | security 安全基础模型 | FR | 高 | turtle | L3 simulator | 已实现并收口 | turtle.security；Round4 删除 shared security shim | boundary 41 passed + integration 7 updated + compileall/ruff/mypy | 外部 KMS/CA/secret provider 未 L5 验证 | 外部安全系统真实集成 | 2026-06-02 |
| TU-FR-003 | P-SCR-001 | compliance 合规与数据分类 | FR | 高 | turtle | L3 simulator | 部分实现 | turtle.compliance 已迁入；audit/policy/governance/risk 为空壳 | boundary 41 passed + compliance import 验证 | 审计治理、策略治理、风险治理未实现 | 实现 audit/policy/governance/risk | 2026-06-02 |
| TU-FR-004 | P-NFR-005/P-SCR-001 | audit 审计中心 | FR | 高 | turtle | L0 | skeleton-ready | turtle.audit 为空壳；ingest 内部审计 sink 仍为模块 adapter | 无完整 Turtle audit E2E | 审计归集中心未实现 | 实现 Turtle audit 事件模型与 sink port | 待更新 |
| TU-FR-005 | P-NFR-005 | policy / governance / risk | FR | 高 | turtle | L0 | skeleton-ready | turtle.policy/governance/risk 为空壳 | 无 | 策略治理和风险治理未实现 | 规划并实现策略版本与风险策略 | 待更新 |
| TU-FR-006 | P-SCR-001 | deployment_policy / change_control | FR | 高 | turtle | L0 | skeleton-ready | turtle.deployment_policy/change_control 为空壳 | 无 | 部署准入与变更控制未实现 | 实现部署准入与变更审批模型 | 待更新 |
| TU-AR-001 | P-AR-003 | Turtle 与 BlueCrystal 并列 | AR | 高 | turtle | L1 | 已验证 | src/turtle 与 src/whale 并列 | import boundary tests | 无 | 无 | 2026-06-02 |
| TU-AR-002 | P-AR-003 | Turtle 不承载运行时工具 | AR | 高 | turtle | L3 | 已验证并收口 | debug/observability/resilience 已从 whale.shared.crosscutting 迁出至 platform_shared；whale.shared.crosscutting 整棵目录已物理删除；全仓 0 个旧路径 import | boundary 79 passed（platform_shared boundary gate + AST scan）+ compileall/ruff/mypy strict clean | 无 | 持续维护 boundary gate | 2026-06-02 |
| TU-TEST-001 | P-NFR-004 | Turtle 边界与迁移测试 | TEST | 高 | turtle | L1/L3 | 已通过 | boundary test 从 41 tests 升级至 79 tests，覆盖 platform_shared 全量符号验证、旧路径 ImportError 运行时断言、上层依赖 AST 扫描；compileall/ruff/mypy PASS | test_turtle_octopus_import_boundary.py (79 tests) | 无 | 持续维护 boundary gate | 2026-06-02 |
