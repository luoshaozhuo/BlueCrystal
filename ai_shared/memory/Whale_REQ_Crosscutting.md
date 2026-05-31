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


## 八、模块级部署准入与接入边界

### CT-READY-001 crosscutting 独立模块接入准入

- 类型：模块级部署准入
- 优先级：高
- 需求描述：
  - crosscutting 模块应作为全项目横切能力提供方，可被 ingest、shared_source、message_pipeline、speed、storage、processing、batch、aggregation 等模块通过 decorator、wrapper、middleware 或 composition 接入。
  - crosscutting 不直接承接业务链路，不应替代业务模块自己的 use case、adapter、runtime 或协议实现。
- 验收要点：
  - 每类横切能力必须有清晰端口、包装器或中间件接入方式。
  - 业务模块可选择接入所需横切能力，不要求继承 mixin。
  - 接入方式不得污染业务 use case 核心逻辑。
  - 横切能力启用、禁用、降级必须可配置。
  - 横切能力自身异常不得静默吞掉，也不得无控制地阻断业务主链路；必须有明确 fail-open / fail-closed 策略。

### CT-READY-002 crosscutting 安全与合规基础能力准入

- 类型：模块级部署准入
- 优先级：高
- 需求描述：
  - crosscutting 模块应为各独立部署模块提供统一的安全、审计、脱敏、凭据和安全区表达基础能力。
  - crosscutting 不负责具体模块的生产部署拓扑，也不替代模块自己的安全分区验收。
- 验收要点：
  - 支持 actor/principal、权限检查、凭据脱敏、证书/密钥配置模型。
  - 支持审计事件基础 schema 和数据分类/安全区表达。
  - 支持日志、指标、trace、debug dump 的敏感信息脱敏。
  - debug dump 默认关闭。
  - 对外部 IAM/SIEM/KMS/证书系统的集成应通过端口或 adapter 表达。
  - 如果外部安全系统不可用，必须明确 fail-open / fail-closed 策略和审计记录。

### CT-READY-003 crosscutting 韧性与健康诊断准入

- 类型：模块级部署准入
- 优先级：高
- 需求描述：
  - crosscutting 模块应提供可复用的 retry、timeout、backoff、circuit breaker、错误分类、health、readiness 和诊断能力。
  - 具体业务模块需声明如何接入这些策略，以及哪些依赖属于本模块 readiness 条件。
- 验收要点：
  - retry/backoff/circuit breaker 策略可配置。
  - timeout/deadline 策略可配置。
  - health/readiness 可区分存活、就绪、降级和依赖不可用。
  - failure snapshot 不泄露敏感凭据。
  - 业务模块接入横切韧性能力时必须有集成测试。

### CT-READY-004 crosscutting 质量门禁

- 类型：模块级部署准入
- 优先级：高
- 需求描述：
  - crosscutting 作为公共基础能力模块，必须具备更严格的工程质量门禁。
- 验收要点：
  - compileall 或等价语法检查通过。
  - ruff 或等价 lint 检查通过。
  - mypy 或等价类型检查通过；未通过不得写质量门禁收口。
  - 单元测试和接入型集成测试通过。
  - 不得使用 mock/fake/stub 证据冒充真实外部 IAM/SIEM/KMS 接入完成。
  - 修改横切能力时，必须评估对接入模块的兼容性影响。

## 九、需求跟踪表

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
| CT-READY-001 | P-AR-001/P-NFR-004 | crosscutting 独立模块接入准入 | READY | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 需确认各业务模块通过 decorator/wrapper/middleware/composition 的接入证据 | 回填接入方式、集成测试与降级策略证据 | 待更新 |
| CT-READY-002 | P-NFR-005/P-SCR-001 | crosscutting 安全与合规基础能力准入 | READY | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 外部 IAM/SIEM/KMS/证书系统是否真实接入待核实 | 回填安全端口、adapter、脱敏和外部系统集成证据 | 待更新 |
| CT-READY-003 | P-NFR-002/P-NFR-004 | crosscutting 韧性与健康诊断准入 | READY | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | 需核实 retry/timeout/backoff/health/readiness 是否被业务模块接入 | 回填策略配置、接入测试和诊断输出证据 | 待更新 |
| CT-READY-004 | P-NFR-004 | crosscutting 质量门禁 | READY | 高 | crosscutting | 待核实 | 待代码核实 | 待读取源码/测试/报告 | 待补充 | compileall/ruff/mypy/pytest 状态待核实 | 执行质量门禁并回填结果 | 待更新 |
