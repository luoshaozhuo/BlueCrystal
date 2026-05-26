# Whale_REQ_Crosscutting

## 一、文件定位

本文件描述 Whale 横切能力需求。横切能力包括日志、指标、追踪、审计、认证、鉴权、凭据、加密配置、数据分类、安全区、重试、超时、熔断、健康检查和诊断。

业务模块通过 decorator、wrapper、middleware 或 composition 接入横切能力。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-NFR-002 | 承接韧性策略 |
| P-NFR-004 | 承接可观测和诊断 |
| P-NFR-005 | 承接安全、认证、审计和合规 |

## 三、功能需求

### CT-FR-001 日志、指标与追踪

- 类型：功能
- 优先级：高
- 需求描述：
  - crosscutting 模块应提供全项目统一的 structured logging、metrics 和 tracing 能力。
- 验收要点：
  - 支持 trace_id、span_id、batch_id、source_id、protocol、duration_ms。
  - 支持 counter、histogram、gauge。

### CT-FR-002 韧性策略

- 类型：功能
- 优先级：高
- 需求描述：
  - crosscutting 模块应提供 retry、timeout、backoff、circuit breaker 和错误分类能力。
- 验收要点：
  - 策略可配置。
  - 业务模块可通过 decorator/wrapper/composition 接入。

### CT-FR-003 认证、鉴权、凭据与加密配置

- 类型：功能
- 优先级：高
- 需求描述：
  - crosscutting 模块应提供 authn、authz、credential、secret redaction、TLS/cert config 等能力。
- 验收要点：
  - 支持 actor/principal。
  - 支持权限检查。
  - 支持凭据脱敏。
  - 支持证书和密钥配置模型。

### CT-FR-004 审计、数据分类与安全区

- 类型：功能
- 优先级：高
- 需求描述：
  - crosscutting 模块应提供 audit、data classification、security zone 和 compliance record 能力。
- 验收要点：
  - 写入命令、跨区发布、配置变更生成审计记录。
  - 数据分类分级可表达。
  - 安全区和数据流向可表达。

### CT-FR-005 健康检查与诊断

- 类型：功能
- 优先级：高
- 需求描述：
  - crosscutting 模块应提供 health、readiness、debug dump、runtime report 和 failure snapshot 能力。
- 验收要点：
  - debug dump 默认关闭。
  - 诊断信息不泄露敏感凭据。

## 四、非功能需求

### CT-NFR-001 低侵入接入

- 类型：非功能
- 优先级：高
- 需求描述：
  - 横切能力应通过 decorator、wrapper、middleware 或 composition 接入业务模块。
- 验收要点：
  - 不要求业务模块继承 mixin。
  - 不污染 use case 核心逻辑。

## 五、安全合规需求

### CT-SCR-001 敏感信息保护

- 类型：安全合规
- 优先级：高
- 需求描述：
  - 横切能力必须保护凭据、证书、token、个人信息和敏感运行数据。
- 验收要点：
  - 日志、指标、trace、debug dump 不输出敏感信息。
  - 审计记录遵循最小必要原则。

## 六、测试与验收需求

### CT-TEST-001 横切能力测试

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - crosscutting 模块必须具备日志、指标、trace、audit、auth、retry、timeout、redaction 测试。
- 验收要点：
  - 业务模块接入横切能力有集成测试。
  - 敏感信息脱敏测试通过。

## 七、禁止事项

- 不得把 crosscutting 做成垃圾桶。
- 不得让业务模块通过 mixin 继承横切能力作为主方案。
- 不得在日志、指标、trace、debug dump 中输出敏感信息。

## 八、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CT-FR-001 | P-NFR-004 | 日志、指标与追踪 | FR | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| CT-FR-002 | P-NFR-002 | 韧性策略 | FR | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| CT-FR-003 | P-NFR-005 | 认证、鉴权、凭据与加密配置 | FR | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| CT-FR-004 | P-SCR-001 | 审计、数据分类与安全区 | FR | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| CT-FR-005 | P-NFR-004 | 健康检查与诊断 | FR | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| CT-NFR-001 | P-AR-001 | 低侵入接入 | NFR | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| CT-SCR-001 | P-SCR-001 | 敏感信息保护 | SCR | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
| CT-TEST-001 | P-NFR-004 | 横切能力测试 | TEST | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 待核实 | 回填实现状态与证据 | 待更新 |
