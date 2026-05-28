# Whale_REQ_Ingest

## 一、文件定位

本文件描述 Whale `src/whale/ingest` 模块承担的生产级采集编排、运行时调度、配置管理、状态缓存、消息发布、写入控制、异常恢复、部署形态和验收需求。

本文件不描述 `source_lab` simulator 内部实现，不描述 `shared_source` production client 内部实现，不描述 speed layer、storage、batch layer 和 processing 的内部实现。

`source_lab` 可作为外部 simulator / probe / profile / capacity / E2E 验收工具，但不得进入 `ingest` 生产运行路径。`shared_source` 是 production source client 层，`ingest` 通过 port-adapter 装配并编排其能力。

## 二、上承项目级需求

| 项目级需求 | 本模块承接方式 |
|---|---|
| P-FR-001 | 编排 source -> cache、cache -> message、write/control、多协议采集任务运行 |
| P-FR-002 | 作为 Kappa 实时入口，将数据发布到 message pipeline，并承接实时链路任务调度 |
| P-FR-003 | 承接高频时序接入的调度、缓存、运行监控和容量验收 |
| P-DGR-001 | 承接 source、connection、point、signal profile、protocol params、runtime config、bundle 的配置治理 |
| P-NFR-001 | 接受 profile/capacity、load、E2E 和部署态 smoke 验收 |
| P-NFR-002 | 承接 7x24 稳定运行、任务恢复、lease、fencing、graceful shutdown |
| P-NFR-003 | 通过 port-adapter 保持 cache、message、DB、source client 和审计 sink 可替换 |
| P-NFR-004 | 输出日志、指标、追踪、审计、诊断和运行报告 |
| P-NFR-005 | 落实安全分区、认证、授权、审计、凭据保护和写入控制边界 |
| P-AR-001 | 保持 use case、role、port、adapter、runtime、infrastructure 边界 |
| P-AR-002 | 保持 source_lab 工具层、shared_source production client、ingest 编排层分离 |
| P-SCR-001 | 承接电力监控系统安全分区、单向流向、控制反向下发风险控制 |

## 三、链路能力矩阵

| 链路 | use case / runtime | port | adapter / infra | E2E | 目标状态 |
|---|---|---|---|---|---|
| source -> cache | SourceAcquisitionUseCase / worker | SourceAcquisitionPort / StateCachePort | source adapter / cache adapter | simulator + production client | 运行闭环 |
| cache -> message | StateSnapshotPublishUseCase / worker | MessagePublisherPort | Kafka 或等价 publisher | Kafka/test container/verifiable publisher | 运行闭环 |
| source -> cache -> message | 组合链路 | 多 port | 多 adapter | source_lab simulator + cache + MQ | 运行闭环 |
| source write/control | SourceCommandUseCase / write worker | SourceWritePort / SourceCommandAuditPort | write adapter / audit sink | dry-run + enabled profile | 安全闭环 |
| runtime CRUD | API runtime | RuntimeConfigPort / AuditPort | FastAPI / local runtime DB | API E2E | 运行闭环 |
| scheduler assignment | worker runtime | JobAssignmentPort / LeasePort | APScheduler + DB lease | multi-node E2E | 运行闭环 |
| import/export bundle | CLI/API runtime | BundlePort / AuditPort | file bundle + checksum | offline E2E | 运行闭环 |
| node heartbeat | worker/API runtime | NodeRuntimePort | local runtime DB | failover E2E | 运行闭环 |
| write lease/fencing | write worker | WriteLeasePort / AuditPort | DB lease / fencing token | dual-active E2E | 安全闭环 |

## 四、运行模式与部署形态

ingest 采用唯一 runtime image，不区分开发环境与生产环境。开发环境直接按生产运行形态启动。

唯一 image 通过 entrypoint 区分运行角色：

```text
api
worker
api-worker
import-bundle
export-bundle
migrate
```

必须支持四种运行模式：

```text
standalone
active_standby
dual_active_partitioned
cluster
```

四种模式必须共用统一的：

```text
node heartbeat
job assignment
job lease
fencing token
local runtime DB
operation audit
runtime metrics
bundle import/export
```

单机模式只是多节点模型的特例，不得另建一套不可演进的单机专用调度逻辑。

推荐技术组件：

```text
FastAPI
Pydantic v2
SQLAlchemy 2.x
Alembic
APScheduler 3.x
Typer
Docker / Docker Compose
```

除非有明确工程收益，不得自造成熟组件已覆盖的基础设施能力。

## 五、功能需求

### I-FR-001 source -> cache 采集链路

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块应从 production source client 读取数据，转换为统一状态批次，并写入状态缓存。
  - 采集链路应支持 polling、subscription、report/event 等模式。
- 验收要点：
  - 支持 SourceAcquisitionUseCase。
  - 支持 polling、subscription、report/event。
  - 支持启动 subscription/report 前 baseline read。
  - 支持 Redis 或等价 cache 后端。
  - 支持 source unavailable、timeout、partial failure 分类。
  - 采集失败不得污染 cache 中其他 source 的状态。
  - source_lab 只能作为外部 simulator/E2E 工具，不得被生产路径 import。

### I-FR-002 cache -> message pipeline 发布链路

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块应从 cache 读取状态快照或状态变更，并发布到 message pipeline。
  - 默认目标为 Kafka，同时必须通过 MessagePublisherPort 保持可替换。
- 验收要点：
  - 提供独立 StateSnapshotPublishUseCase。
  - 不与 SourceAcquisitionUseCase 耦合。
  - 支持 message envelope、schema_version、trace_id、message_id、item_count。
  - 发布失败不得破坏 source -> cache 主链路。
  - 支持 Kafka 或 test container Kafka 的真实 E2E。
  - 支持发布失败重试、失败隔离和可观测指标。

### I-FR-003 设备命令与写入控制

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块应支持面向 source 的写入、设点、控制和命令下发。
  - 写入/控制必须与采集链路隔离。
- 验收要点：
  - 提供 SourceWritePort。
  - 提供 SourceCommandUseCase。
  - 支持 dry_run。
  - 真实写入默认关闭。
  - 支持 actor、trace_id、command_id。
  - 支持写入后 readback 或状态确认。
  - 支持 per-item result、partial failure、timeout、unsupported operation。
  - 所有写入命令必须审计。
  - 多节点模式下必须经 write lease、fencing token 和授权检查后才能真实下发。

### I-FR-004 多协议 ingest adapter

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块应通过 adapter 接入 shared_source production client，实现多协议采集、订阅、报告和写入控制。
- 验收要点：
  - 每个声明支持的协议必须具备 acquisition adapter。
  - 每个声明支持写入的协议必须具备 write adapter。
  - adapter 不得 import source_lab。
  - 不支持能力必须返回 NOT_IMPLEMENTED 或等价错误。
  - adapter 能被 runtime worker 按任务配置装配。
  - 每个新增 adapter 必须具备 unit、integration、simulator E2E 和 capability matrix 验证。
  - GOOSE/SV 是否进入 ingest production registry 必须单独论证安全边界，不得因 source_lab true PASS 自动进入生产 registry。

### I-FR-005 统一配置加载

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块应从统一配置源加载 source、connection、point、signal profile、protocol params、runtime settings、scheduler settings 和 security partition profile。
- 验收要点：
  - 支持 source_id、protocol、endpoint、protocol-specific params。
  - 支持 node_key、address、IOA、NodeId、LD/LN/DO/DA。
  - 支持 value_type、writable、subscribable、reportable。
  - 支持 acquisition_mode、interval、subscription/report 参数。
  - 支持 task enabled/disabled、priority、partition_key、assignment policy。
  - 支持安全分区、通信方向、bundle version、checksum。
  - schema 与字段必须以 ORM、migration 和配置模型为准。
  - 禁止凭记忆推断字段，禁止创建无来源字段。

### I-FR-006 端到端 ingest 管道

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 模块必须支持从 source simulator 到 cache，再到 message pipeline 的完整链路验证。
- 验收要点：
  - E2E 使用 source_lab server simulator。
  - E2E 使用 production source client。
  - E2E 写入真实或测试 cache。
  - E2E 发布到真实 Kafka、test container Kafka 或可验证 publisher。
  - E2E 验证消息 payload、质量码、时间戳和 trace_id。
  - E2E 覆盖成功、source failure、cache failure、MQ failure、partial failure。

### I-FR-007 统一 ingest runtime image 与 entrypoint

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 必须采用唯一 runtime image，并通过 entrypoint 区分 API、worker、组合模式、配置包导入导出和迁移任务。
- 验收要点：
  - 支持 entrypoint：api、worker、api-worker、import-bundle、export-bundle、migrate。
  - 各 entrypoint 共用同一配置模型、local runtime DB 和日志/指标/审计基础设施。
  - 不区分开发环境与生产环境的实现路径；开发环境使用生产形态 Docker/Docker Compose 启动。
  - entrypoint 参数错误必须返回明确错误码。
  - 支持 graceful shutdown。
  - 支持 health/readiness endpoint 或等价健康检查。

### I-FR-008 采集任务 CRUD API

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 应提供 Web API 形式的 CRUD，用于管理 source、connection、point、signal profile、acquisition task、scheduler job、security partition profile 和 bundle metadata。
- 验收要点：
  - API 基于 FastAPI 或等价成熟框架。
  - schema 基于 Pydantic v2 或等价数据模型。
  - 支持 create/read/update/delete/list/filter/pagination。
  - 支持 optimistic concurrency，例如 version / expected_version。
  - 支持 idempotency key 或等价防重复机制。
  - 支持 dry-run validation。
  - 支持 NOT_FOUND、CONFLICT、VALIDATION_ERROR、DENIED 等稳定错误语义。
  - 查询成功、查询失败、deny、validation error、conflict 均必须审计。
  - CRUD 变更必须写入 local runtime DB，并能被 worker 调度侧读取。

### I-FR-009 调度器与多节点任务分配

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 应内置 scheduler，用于管理 polling、subscription、report/event、snapshot publish 和 write/control 等任务，并支持多节点 assignment、lease、fencing 和 failover。
- 验收要点：
  - 调度器可基于 APScheduler 3.x 或等价成熟组件。
  - 支持 standalone、active_standby、dual_active_partitioned、cluster 四种运行模式。
  - 支持 node heartbeat。
  - 支持 job assignment。
  - 支持 job lease。
  - 支持 fencing token。
  - 支持任务抢占、续约、过期释放和 failover。
  - 支持 partition_key，保证 dual_active_partitioned 下同一分区不被多个节点重复采集。
  - 支持任务错峰、抖动控制和重调度。
  - 支持 scheduler metrics：lease_renewal、assignment_lag、missed_tick、job_duration、failover_count。
  - 单机模式必须复用同一多节点模型，不能另建单机专用 scheduler。

### I-FR-010 local runtime DB 与 migration

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 应提供 local runtime DB，用于持久化配置、节点状态、任务 assignment、lease、fencing token、bundle metadata、审计记录和运行快照。
- 验收要点：
  - ORM 基于 SQLAlchemy 2.x 或等价方案。
  - migration 基于 Alembic 或等价方案。
  - 支持 migrate entrypoint。
  - schema 必须覆盖 node、job、lease、assignment、runtime_config、bundle、audit、operation_log。
  - 支持事务一致性。
  - 支持唯一约束、version 字段和必要索引。
  - 支持 runtime DB 初始化与升级测试。
  - 允许第一阶段使用 SQLite/PostgreSQL 可替换适配，但端口边界必须清晰。

### I-FR-011 配置包 import/export 与离线更新

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 应支持配置包文件导入导出，以适配安全隔离区、离线部署和单向数据流场景。
- 验收要点：
  - 支持 import-bundle entrypoint。
  - 支持 export-bundle entrypoint。
  - bundle 必须包含 version、checksum、schema_version、created_at、source。
  - 后续可扩展 signature；第一阶段必须预留 signed/unsigned 状态。
  - import 前必须 validate。
  - import 失败不得污染现有 accepted config。
  - 支持 dry-run import。
  - 支持导出 redacted bundle 与 raw bundle。
  - redacted bundle 不允许直接导入为 accepted config。
  - 单向链路场景下，采集区不能实时接收管理区指令时，必须可通过拷贝 bundle 文件更新任务配置。
  - bundle import/export 必须审计。

### I-FR-012 多节点 write/control lease 与 fencing

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 多节点部署下，写入/控制链路必须独立于采集任务 lease，并具备 write lease、fencing token、授权和审计，避免双主误下发。
- 验收要点：
  - write/control 默认 disabled。
  - 启用真实写入必须显式配置 profile。
  - 支持 write lease acquisition / renewal / release / expiry。
  - 支持 fencing token 随命令传递并记录审计。
  - 支持 actor、role、reason、trace_id、command_id。
  - 支持 dry-run、precheck、readback。
  - lease 冲突必须返回 CONFLICT 或 DENIED。
  - lease 过期后不得继续下发。
  - 多节点 failover 后旧节点命令必须被 fencing 拒绝。
  - 所有 allow、deny、failed、conflict、timeout、readback mismatch 必须审计。

### I-FR-013 API 查询与操作全量审计

- 类型：功能
- 优先级：高
- 需求描述：
  - ingest 对所有 API 请求、配置变更、查询、导入导出、任务调度、lease 操作和写入控制输出结构化审计事件。
- 验收要点：
  - deny 必须审计。
  - 查询成功必须审计。
  - 查询失败必须审计。
  - validation error 必须审计。
  - conflict 必须审计。
  - 审计字段至少包括 request_id、actor、action、resource_type、resource_id、decision、result、reason_code、http_status、trace_id、client_ip、node_id、timestamp。
  - 配置变更需记录 before_version、after_version、changed_fields。
  - 审计 sink 通过端口抽象，可替换为 JSONL、DB、SIEM 或平台审计后端。
  - 审计中不得输出敏感凭据。

## 六、非功能需求

### I-NFR-001 性能与容量

- 类型：非功能
- 优先级：高
- 需求描述：
  - ingest 模块应满足多设备、高频、长期采集要求。
- 验收要点：
  - 支持 profile/capacity 验证。
  - 支持 p95/p99 延迟、jitter、missed tick、period_samples、values/sec。
  - 新增协议不得绕过 profile/capacity。
  - 支持轻量 load gate 与重型 stress/performance 分层。
  - 支持 scheduler 侧 missed tick、assignment lag 和 lease renewal latency 指标。

### I-NFR-002 稳定性与故障恢复

- 类型：非功能
- 优先级：高
- 需求描述：
  - ingest 模块应处理 source 断连、协议超时、cache 异常、message queue 异常、runner 崩溃、进程退出、节点故障、lease 过期和配置导入失败。
- 验收要点：
  - polling timeout 可恢复。
  - subscription/report 断线不静默停止。
  - reconnect 后 baseline read。
  - Kafka 发布失败不阻塞 source -> cache。
  - 支持 backoff、最大重试次数和 graceful shutdown。
  - 支持 worker crash 后由其他节点接管 assignment。
  - 支持 local runtime DB 中断后的明确降级或失败语义。
  - 支持 bundle import 失败 rollback。

### I-NFR-003 可观测性、审计与安全

- 类型：非功能
- 优先级：高
- 需求描述：
  - ingest 模块应对采集、缓存、发布、写入、调度、CRUD、bundle、lease 和节点运行链路输出结构化日志、指标、审计和诊断上下文。
- 验收要点：
  - 日志包含 source_id、protocol、batch_id、trace_id、command_id、job_id、node_id、lease_id、error_code、duration_ms。
  - 指标包含 read/write/cache/kafka/reconnect/scheduler/lease/API/bundle 相关计数和耗时。
  - 写命令记录 actor、command_id、trace_id、result、failure_reason、timestamp。
  - API 与 CRUD 全量审计。
  - 诊断输出不得泄露敏感凭据。
  - debug dump 默认关闭。

### I-NFR-004 部署一致性与唯一 runtime image

- 类型：非功能
- 优先级：高
- 需求描述：
  - ingest 的开发、测试和生产部署必须使用同一 runtime image 和同一 entrypoint 机制，不维护独立开发专用运行路径。
- 验收要点：
  - Dockerfile 或等价构建产物唯一。
  - Docker Compose 示例按生产形态编排。
  - api/worker/api-worker/import-bundle/export-bundle/migrate 均从同一 image 启动。
  - 配置差异通过环境变量、配置文件或 bundle 表达，不通过不同代码路径表达。
  - CI 至少验证 image build 和关键 entrypoint smoke。

### I-NFR-005 多节点高可用与一致性

- 类型：非功能
- 优先级：高
- 需求描述：
  - ingest 应支持多节点部署下的任务高可用、避免重复采集、避免双主写入、保证故障后可恢复。
- 验收要点：
  - active_standby 下 standby 可接管。
  - dual_active_partitioned 下分区互斥。
  - cluster 下 assignment/lease/fencing 一致。
  - 网络分区或节点超时后必须有明确失败/接管语义。
  - write/control 不得因双主导致重复下发。
  - 支持节点恢复后的旧 lease fencing。

### I-NFR-006 CRUD/API 全量审计与合规

- 类型：非功能
- 优先级：高
- 需求描述：
  - ingest API、bundle、scheduler、lease、write/control 和配置变更必须满足审计完整性、敏感信息保护和可追溯要求。
- 验收要点：
  - allow/deny/success/failed/not_found/validation_error/conflict 均生成审计事件。
  - 查询类 API 也生成审计事件。
  - 审计事件 schema 稳定。
  - 审计 sink 可替换。
  - 日志、指标、trace、audit 不输出密码、token、证书私钥等敏感信息。
  - 支持审计事件测试和安全 smoke。

## 七、架构约束

### I-AR-001 use case / role / port / adapter 边界

- 类型：架构约束
- 优先级：高
- 需求描述：
  - ingest 模块必须保持 use case、role、port、adapter、composition 的职责边界。
- 验收要点：
  - SourceAcquisitionUseCase 只处理采集。
  - SourceCommandUseCase 只处理写入/控制。
  - StateSnapshotPublishUseCase 只处理 cache -> message。
  - composition 负责装配。
  - runtime/scheduler 不直接依赖具体 source client，而是通过 port-adapter 装配。

### I-AR-002 source_lab 隔离

- 类型：架构约束
- 优先级：高
- 需求描述：
  - ingest 生产路径不得直接依赖 source_lab。
- 验收要点：
  - ingest 不 import tools.source_lab。
  - source_lab runner 不作为 production client。
  - source_lab 只能作为测试、profile、capacity、E2E 外部工具。

### I-AR-003 runtime / API / worker / scheduler 边界

- 类型：架构约束
- 优先级：高
- 需求描述：
  - ingest runtime 应区分 API 接入、worker 执行、scheduler 调度、bundle CLI 和 migration 职责，但共用同一配置模型与 local runtime DB。
- 验收要点：
  - API 负责 CRUD、查询、校验和审计。
  - worker 负责执行 acquisition、publish、write/control。
  - scheduler 负责 assignment、lease、heartbeat、fencing。
  - import/export-bundle 负责离线配置流转。
  - migrate 负责 DB schema 管理。
  - api-worker 只是组合启动模式，不得引入另一套逻辑。

### I-AR-004 多节点调度一致性边界

- 类型：架构约束
- 优先级：高
- 需求描述：
  - ingest 多节点调度必须以 local runtime DB 中的 assignment、lease、fencing token 为一致性边界。
- 验收要点：
  - 不得依赖单进程内存判断任务归属。
  - 任务执行前必须校验 lease/fencing。
  - 续约失败后 worker 必须停止对应任务或进入安全失败状态。
  - write/control 使用独立 write lease，不得复用采集 lease。

### I-AR-005 配置包与隔离区边界

- 类型：架构约束
- 优先级：高
- 需求描述：
  - 隔离区和单向流向场景下，ingest 必须支持通过配置包文件更新任务，不依赖管理区对采集区的实时调用。
- 验收要点：
  - 采集区可离线 import bundle。
  - 管理区可 export bundle。
  - bundle 带 version/checksum。
  - import 前 validate，失败 rollback。
  - 不形成未经论证的跨安全分区实时控制通道。

## 八、安全合规需求

### I-SCR-001 电力监控系统安全分区

- 类型：安全合规
- 优先级：高
- 需求描述：
  - ingest 部署、source 接入、cache、message queue、runtime DB、bundle 文件和控制写入必须服从电力监控系统安全分区和边界防护要求。
- 验收要点：
  - 明确 ingest、source、cache、MQ、runtime DB 所在区。
  - 明确跨区流向。
  - 控制命令链路需单独安全评估。
  - simulator 不进入生产控制链路。
  - 配置包跨区流转必须有 version/checksum 和审计。

### I-SCR-002 隔离区配置流转与单向链路约束

- 类型：安全合规
- 优先级：高
- 需求描述：
  - 当采集区只能单向向外发送数据、不能接收管理区实时指令时，ingest 必须支持通过受控 bundle 文件完成任务配置更新。
- 验收要点：
  - 支持离线导入 accepted config。
  - 支持校验 checksum。
  - 支持导入审计。
  - 支持导入失败 rollback。
  - 支持 redacted export 用于审查。
  - raw bundle 仅允许在受控本机或受控介质中使用。
  - 不得要求采集区开放实时 CRUD API 给管理区。

### I-SCR-003 写入控制安全边界

- 类型：安全合规
- 优先级：高
- 需求描述：
  - 写入、设点、控制命令属于高风险反向控制链路，必须默认关闭，并经过授权、lease、fencing、审计和 readback/确认。
- 验收要点：
  - 默认 disabled。
  - 真实写入需显式 profile。
  - 支持 actor/role/reason。
  - 支持 write lease/fencing token。
  - 支持 command audit。
  - 支持 readback 或状态确认。
  - 支持 deny 审计。
  - 双主或 lease 冲突时必须拒绝下发。

## 九、测试与验收需求

### I-TEST-001 分层测试与协议准入测试

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - ingest 模块必须具备 unit、integration、E2E、performance、fault injection、security smoke 测试。
- 验收要点：
  - use case 有 unit test。
  - adapter 有 unit/integration test。
  - source->cache->message 有 E2E。
  - write/control 有 dry-run 和真实写入测试。
  - skipped 不得作为完成证据。
  - failed 必须修复或明确归档为阻塞。

### I-TEST-002 runtime / scheduler / CRUD / bundle / multi-node E2E

- 类型：测试与验收
- 优先级：高
- 需求描述：
  - ingest 必须具备覆盖 runtime image、entrypoint、CRUD API、scheduler、多节点 assignment/lease/fencing、bundle import/export 和 write lease 的 E2E 验收。
- 验收要点：
  - image build smoke。
  - api entrypoint smoke。
  - worker entrypoint smoke。
  - api-worker entrypoint smoke。
  - migrate entrypoint smoke。
  - import-bundle/export-bundle smoke。
  - CRUD API E2E。
  - deny/query success/query failure audit E2E。
  - standalone scheduler E2E。
  - active_standby failover E2E。
  - dual_active_partitioned no-duplicate E2E。
  - cluster assignment/lease E2E。
  - write lease/fencing E2E。
  - bundle checksum/rollback E2E。
  - security partition smoke。
  - skipped 不得作为完成证据。

## 十、禁止事项

- 不得 import tools.source_lab。
- SourceAcquisitionUseCase 不得处理 write/control。
- SourceCommandUseCase 不得处理 acquisition。
- Kafka 发布不得塞入 SourceAcquisitionUseCase。
- 真实写入不得默认开启。
- 不得为 standalone 模式另建一套不可演进的单机 scheduler。
- 不得用内存状态替代多节点 assignment/lease/fencing。
- 不得把 source_lab dynamic runtime 直接搬进 ingest production path。
- 不得把 redacted bundle 导入为 accepted config。
- 不得在日志、指标、trace、audit、debug dump 中输出敏感凭据。
- 不得把 skipped 测试作为完成证据。

## 十一、需求跟踪表

| 编号 | 上承需求 | 标题 | 类型 | 优先级 | 责任模块 | 验证等级 | 实现状态 | 实现证据 | 验收测试 | 差距 | 下一步 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I-FR-001 | P-FR-001/P-FR-002 | source -> cache 采集链路 | FR | 高 | ingest | L3 | 运行闭环通过 | `src/whale/ingest/usecases/source_acquisition_use_case.py`; `src/whale/ingest/usecases/roles/`; `src/whale/ingest/adapters/state/redis_source_state_cache.py`; `tests/integration/test_ingest_source_cache_message_e2e.py` | `pytest tests/unit/test_source_acquisition_use_case.py -q` -> 12 passed; `pytest tests/integration/test_ingest_source_cache_message_e2e.py -q` -> 2 passed | 长连接 subscription/report 的真实协议级恢复仍依赖各 adapter/backend 后续补证 | 补协议级断线恢复与长期运行归档 | 2026-05-27 |
| I-FR-002 | P-FR-002 | cache -> message pipeline 发布链路 | FR | 高 | ingest | L3 | 运行闭环通过 | `src/whale/ingest/usecases/state_snapshot_publish_use_case.py`; `src/whale/ingest/adapters/message/kafka_message_publisher.py`; `tests/integration/test_ingest_source_cache_message_kafka_e2e.py` | `pytest tests/unit/test_state_snapshot_publish_use_case.py -q` -> 17 passed; `pytest tests/integration/test_ingest_source_cache_message_kafka_e2e.py -q` -> 1 passed | 已有 Kafka/container 级闭环，但仍不是生产部署 topic/ACL/retention 验证 | 补部署态 Kafka smoke 与权限配置验证 | 2026-05-27 |
| I-FR-003 | P-FR-001/P-SCR-001 | 设备命令与写入控制 | FR | 高 | ingest | L2 | 部分实现 | `src/whale/ingest/usecases/source_command_use_case.py`; `src/whale/ingest/ports/command/source_command_audit_port.py`; `src/whale/ingest/adapters/observability/file_sinks.py`; `src/whale/ingest/domain/write_security_profile.py`; `src/whale/ingest/decorators/source_write.py`; `src/whale/ingest/composition.py` | `pytest tests/unit/test_source_command_use_case.py tests/unit/test_source_command_audit.py -q` -> 11 passed; `pytest tests/unit/test_ingest_write_security_profile.py tests/unit/test_source_command_authorization_guard.py -q` -> 15 passed | 新增 WriteSecurityProfile 领域模型、AuthorizedSourceWritePort 授权装饰器、composition root 集成（默认 allow-all）；OPC UA readback 已实现但需真实 server E2E | 补协议级 readback E2E 与生产授权策略注入 | 2026-05-27 |
| I-FR-004 | P-FR-001 | 多协议 ingest adapter | FR | 高 | ingest | L1 | 部分实现 | `src/whale/ingest/adapters/source/`; `src/whale/ingest/adapters/source/static_source_acquisition_port_registry.py`; `tests/unit/test_ingest_source_adapter_capability_matrix.py` | `pytest tests/unit/test_ingest_source_adapter_capability_matrix.py -q` -> 2 passed; `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed | 仅覆盖当前已接入 adapter；IEC101/Modbus RTU/MQTT/HTTP REST/GOOSE/SV 未进入 production registry，且 GOOSE/SV 仍缺安全论证 | 补 capability matrix、unsupported 语义和新增协议准入测试 | 2026-05-27 |
| I-FR-005 | P-DGR-001 | 统一配置加载 | FR | 高 | ingest | L1 | 部分实现 | `src/whale/ingest/adapters/config/source_runtime_config_repository.py`; `src/whale/ingest/ports/runtime/source_runtime_config_port.py`; `src/whale/shared/persistence/orm/` | `pytest tests/unit/test_source_runtime_config_repository.py -q` -> 2 passed | 现有仓库只证明可从共享 ORM 读取局部 runtime 数据；未打通 source/connection/point/profile/protocol params 到 composition/use case/runtime/scheduler 装配 | 补统一配置模型、runtime DB schema 和装配级 E2E | 2026-05-27 |
| I-FR-006 | P-FR-002 | 端到端 ingest 管道 | FR | 高 | ingest | L3 | 运行闭环通过 | `tests/integration/test_ingest_source_cache_message_e2e.py`; `tests/integration/test_ingest_source_cache_message_kafka_e2e.py` | `pytest tests/integration/test_ingest_source_cache_message_e2e.py -q` -> 2 passed; `pytest tests/integration/test_ingest_source_cache_message_kafka_e2e.py -q` -> 1 passed | 当前闭环限于 source->cache->message，不等同 runtime/API/deployment ready | 补 image/entrypoint/deploy smoke 与失败注入 E2E | 2026-05-27 |
| I-FR-007 | P-NFR-003/P-AR-001 | 统一 ingest runtime image 与 entrypoint | FR | 高 | ingest_runtime | L3 | 测试通过 | `Dockerfile`; `src/whale/ingest/runtime/entrypoint.py`; `src/whale/ingest/runtime/cli.py`; `src/whale/ingest/api/app.py`; `docker-compose.ingest-dev.yaml`; `scripts/run_ingest_runtime_compose_smoke.sh` | `pytest tests/unit/test_ingest_runtime_entrypoint.py -q` -> 5 passed; `pytest tests/integration/test_ingest_runtime_entrypoint_smoke.py -q` -> passed; `docker compose -f docker-compose.ingest-dev.yaml config` -> success; `docker build -t whale-ingest-runtime:dev .` -> success; `bash scripts/run_ingest_runtime_compose_smoke.sh` -> healthz/readyz/migrate/worker/api-worker/CRUD 全部通过 | 已验证唯一 image、统一 entrypoint、Docker compose 全链路 smoke（healthz/readyz/migrate/worker/api-worker/host-port CRUD），未跳过任何验证；graceful shutdown 信号语义仍待补强 | 补 graceful shutdown 断言与长期运行 worker 调度验证 | 2026-05-27 |
| I-FR-008 | P-FR-005/P-NFR-005 | 采集任务 CRUD API | FR | 高 | ingest_api | L2 | 部分实现 | `src/whale/ingest/api/app.py`; `src/whale/ingest/api/routes/acquisition_tasks.py`; `src/whale/ingest/api/routes/runtime_config.py`; `src/whale/ingest/api/routes/scheduler_jobs.py`; `src/whale/ingest/api/routes/security_partitions.py`; `src/whale/ingest/api/routes/bundles.py`; `src/whale/ingest/api/routes/nodes.py`; `src/whale/ingest/api/routes/leases.py`; `src/whale/ingest/api/routes/audit_events.py`; `src/whale/ingest/api/audit_middleware.py`; `src/whale/ingest/api/idempotency.py`; `src/whale/shared/persistence/orm/acquisition.py`; `src/whale/shared/persistence/orm/scada_ingest.py` | `pytest tests/unit/test_ingest_api_app.py -q` -> 4 passed; `pytest tests/integration/test_ingest_api_scheduler_job_crud.py -q` -> 5 passed; `pytest tests/integration/test_ingest_api_security_partition_crud.py -q` -> 1 passed; `pytest tests/integration/test_ingest_api_bundle_metadata_crud.py -q` -> 1 passed; `pytest tests/integration/test_ingest_api_node_lease_audit_query.py -q` -> 3 passed; `pytest tests/integration/test_ingest_api_idempotency_dry_run_interaction.py -q` -> 9 passed; `pytest tests/integration/ -k 'idempotency or dry_run' -q` -> 48 passed; `bash scripts/ci_ingest_runtime_gate.sh` -> 7/7 passed（无 skip） | 幂等性fingerprint增加query_string参数区分dry_run（9个交互测试覆盖6场景），全量幂等性+dry_run测试48 passed；全量CI门禁7/7通过（含PG matrix + compose smoke）；API→worker配置消费闭环仍缺失 | 补 API→worker 配置消费闭环 | 2026-05-27 |
| I-FR-009 | P-NFR-002 | 调度器与多节点任务分配 | FR | 高 | ingest_scheduler | L3 | 测试通过 | `src/whale/ingest/runtime/scheduler.py`; `src/whale/ingest/runtime/modes.py`; `src/whale/ingest/runtime/node_runtime.py`; `src/whale/ingest/runtime/job_assignment.py`; `src/whale/ingest/runtime/lease.py`; `src/whale/ingest/runtime/fencing.py`; `src/whale/ingest/runtime/worker_runtime.py` | `python -c 'import importlib; importlib.import_module("whale.ingest.runtime.scheduler")'` -> success; `pytest tests/unit/test_ingest_runtime_scheduler_import.py -q` -> 1 passed; `pytest tests/unit/test_ingest_runtime_modes.py -q` -> 2 passed; `pytest tests/unit/test_ingest_job_lease.py -q` -> 4 passed; `pytest tests/integration/test_ingest_scheduler_active_standby_failover.py -q` -> passed; `pytest tests/integration/test_ingest_scheduler_dual_active_partitioned.py -q` -> passed; `pytest tests/integration/test_ingest_scheduler_cluster_assignment.py -q` -> passed; `pytest tests/integration/test_ingest_scheduler_apscheduler_runtime.py -q` -> 5 passed; `pytest tests/integration/test_ingest_scheduler_missed_tick_and_stagger.py -q` -> 2 passed; `pytest tests/integration/test_ingest_scheduler_graceful_shutdown.py -q` -> 3 passed | 新增 APScheduler WorkerRuntime E2E，覆盖执行/跳过/missed_tick/stagger/graceful shutdown/lease release；真实设备采集路径 `_do_execute` 待实现 | 补真实设备 `_do_execute` 实现与进程信号级 stop 验证 | 2026-05-27 |
| I-FR-010 | P-DGR-001/P-NFR-002 | local runtime DB 与 migration | FR | 高 | ingest_runtime_db | L3 | 测试通过 | `src/whale/ingest/framework/persistence/runtime_db.py`; `src/whale/shared/persistence/orm/ingest_runtime.py`; `alembic.ini`; `alembic/env.py`; `alembic/versions/20260527_000001_ingest_runtime_initial.py`; `alembic/versions/20260527_000002_add_audit_index_and_job_stagger.py`; `alembic/versions/20260527_000003_add_idempotency_record.py`; `tests/integration/test_ingest_prodlike_postgres_runtime_db.py` | `pytest tests/integration/test_ingest_runtime_db_init.py -q` -> 2 passed; `pytest tests/unit/test_ingest_runtime_orm_models.py -q` -> 3 passed; `pytest tests/integration/test_ingest_runtime_alembic_migration.py -q` -> passed; `pytest tests/integration/test_ingest_runtime_alembic_sqlite_matrix.py -q` -> 5 passed; `pytest tests/integration/test_ingest_runtime_migrate_entrypoint.py -q` -> 3 passed; `pytest tests/integration/test_ingest_runtime_entrypoint_smoke.py -q` -> passed; `bash scripts/run_ingest_runtime_compose_smoke.sh` -> migrate success; `bash scripts/run_pg_migration_matrix.sh` -> 3/3 passed（upgrade/downgrade/index/columns 全验证）; `pytest tests/integration/test_ingest_prodlike_postgres_runtime_db.py -q` -> 4 passed（CRUD/lease/audit/readiness 真实 PG） | 新增第二版迁移（audit index + stagger column）、第三版迁移（幂等性记录表），SQLite 矩阵覆盖 upgrade/downgrade/upgrade 幂等；PostgreSQL 矩阵 3/3 真实运行通过（含 compose 自动拉起 PG），自动清理容器；新增 prodlike PG runtime DB 4 tests（CRUD/lease/audit/readyz）| 补 operation_log 表设计 | 2026-05-27 |
| I-FR-011 | P-DGR-001/P-SCR-001 | 配置包 import/export 与离线更新 | FR | 高 | ingest_bundle | L2 | 测试通过 | `src/whale/ingest/bundle/model.py`; `src/whale/ingest/bundle/checksum.py`; `src/whale/ingest/bundle/redaction.py`; `src/whale/ingest/bundle/service.py`; `src/whale/ingest/runtime/entrypoint.py` | `pytest tests/unit/test_ingest_bundle_checksum.py -q` -> 3 passed; `pytest tests/unit/test_ingest_bundle_redaction.py -q` -> 2 passed; `pytest tests/integration/test_ingest_bundle_import_export.py -q` -> passed; `pytest tests/integration/test_ingest_bundle_offline_one_way_flow.py -q` -> passed | 已验证 raw/redacted export、dry-run import、checksum/schema_version 校验、rollback 与离线单向导入闭环；signature 扩展和 accepted config 归档策略仍待深化 | 补 signature 扩展点与 accepted config 版本归档 | 2026-05-27 |
| I-FR-012 | P-SCR-001/P-NFR-002 | 多节点 write/control lease 与 fencing | FR | 高 | ingest_write_runtime | L2 | 部分实现 | `src/whale/ingest/runtime/write_lease.py`; `src/whale/ingest/ports/runtime/write_lease_port.py`; `src/whale/ingest/usecases/source_command_use_case.py`; `src/whale/ingest/ports/command/source_command_audit_port.py`; `src/whale/ingest/domain/write_security_profile.py`; `src/whale/ingest/decorators/source_write.py`; `src/whale/ingest/composition.py` | `pytest tests/unit/test_ingest_write_lease.py -q` -> 3 passed; `pytest tests/unit/test_ingest_write_lease_fencing.py -q` -> passed; `pytest tests/unit/test_source_command_write_lease_guard.py -q` -> 3 passed; `pytest tests/unit/test_ingest_write_security_profile.py tests/unit/test_source_command_authorization_guard.py -q` -> 15 passed; `pytest tests/integration/test_ingest_write_lease_fencing_e2e.py -q` -> passed | 新增 WriteSecurityProfile 协议级 allow/deny、AuthorizedSourceWritePort 装饰器及 composition root 集成（默认 allow-all）；OPC UA readback 已实现，真实设备 E2E 和协议级读确认仍待补充 | 补协议级 readback E2E、双节点写入冲突验证与生产授权注入 | 2026-05-27 |
| I-FR-013 | P-NFR-004/P-NFR-005 | API 查询与操作全量审计 | FR | 高 | ingest_audit | L3 | 测试通过 | `src/whale/ingest/domain/audit_event.py`; `src/whale/ingest/api/audit_middleware.py`; `src/whale/ingest/adapters/audit/db_audit_sink.py`; `src/whale/ingest/adapters/audit/http_audit_sink.py`; `src/whale/ingest/adapters/audit/multi_audit_sink.py`; `src/whale/ingest/adapters/observability/file_sinks.py`; `src/whale/ingest/runtime/cli.py`; `tests/integration/test_ingest_prodlike_audit_sink.py`; `tests/integration/test_ingest_external_audit_sink_contract.py`; `config/ingest/audit_sink.external.example.yaml` | `pytest tests/unit/test_ingest_audit_event_schema.py -q` -> 3 passed; `pytest tests/unit/test_ingest_audit_redaction.py -q` -> 4 passed; `pytest tests/integration/test_ingest_api_audit.py -q` -> passed; `pytest tests/integration/test_ingest_api_runtime_config_audit.py -q` -> passed; `pytest tests/integration/test_ingest_api_full_audit_matrix.py -q` -> 5 passed; `pytest tests/integration/test_ingest_audit_matrix_api_bundle_scheduler_write.py -q` -> 5 passed; `pytest tests/integration/test_ingest_audit_db_jsonl_consistency.py -q` -> 1 passed; `pytest tests/integration/test_ingest_bundle_offline_one_way_flow.py -q` -> passed; `pytest tests/integration/test_ingest_write_lease_fencing_e2e.py -q` -> passed; `pytest tests/integration/test_ingest_prodlike_audit_sink.py -q` -> 6 passed; `pytest tests/integration/test_ingest_external_audit_sink_contract.py -q` -> 5 passed | 新增 HttpIngestAuditSink 外部SIEM转发（batch/retry/redact/no-throw）及 DualIngestAuditSink+JsonlIngestAuditSink fallback；真实外部SIEM集成待平台团队现场部署 | 真实SIEM集成待平台团队实施 | 2026-05-28 |
| I-NFR-001 | P-NFR-001 | 性能与容量 | NFR | 高 | ingest | L3 | 测试通过 | `tests/integration/test_ingest_lightweight_load_gate.py`; `src/whale/ingest/ports/metrics.py`; `src/whale/ingest/runtime/worker_runtime.py`; `config/ingest/performance.prodlike.yaml`; `scripts/run_ingest_prodlike_performance_profile.sh` | `pytest tests/integration/test_ingest_lightweight_load_gate.py -q` -> 1 passed; `pytest tests/integration/test_ingest_scheduler_apscheduler_runtime.py -q` -> 5 passed; `pytest tests/integration/test_ingest_prodlike_performance_profile.py -q` -> 9 passed; `bash scripts/run_ingest_prodlike_performance_profile.sh` -> 0 failures | 新增性能基线配置（throughput/latency/resource/error budget目标）和合成benchmark（bundle export 2382/s, dry-import 6009/s）；`tests/performance/` 压测和真实硬件性能验证仍待执行 | 补 performance/stress 压测与真实硬件验证 | 2026-05-28 |
| I-NFR-002 | P-NFR-002 | 稳定性与故障恢复 | NFR | 高 | ingest | L3 | 运行闭环通过 | `src/whale/ingest/usecases/roles/subscription_acquisition_role.py`; reconnect/baseline tests; `src/whale/ingest/runtime/worker_runtime.py`; `src/whale/ingest/runtime/cli.py`; `scripts/run_ingest_prodlike_endurance_smoke.sh`; `tests/integration/test_ingest_prodlike_worker_failover.py`; `tests/integration/test_ingest_prodlike_postgres_fault_injection.py`; `tests/integration/test_ingest_prodlike_redis_fault_injection.py`; `tests/integration/test_ingest_prodlike_kafka_fault_injection.py`; `tests/integration/test_ingest_prodlike_audit_metrics_resilience.py` | `pytest tests/unit/test_subscription_reconnect_baseline.py tests/unit/test_subscription_reconnect_runtime.py -q` -> 3 passed; `pytest tests/integration/test_ingest_scheduler_graceful_shutdown.py -q` -> 3 passed; `pytest tests/integration/test_ingest_prodlike_worker_failover.py -q` -> 5 passed; `pytest tests/integration/test_ingest_prodlike_postgres_fault_injection.py -q` -> 4 passed; `pytest tests/integration/test_ingest_prodlike_redis_fault_injection.py -q` -> 4 passed; `pytest tests/integration/test_ingest_prodlike_kafka_fault_injection.py -q` -> 4 passed; `pytest tests/integration/test_ingest_prodlike_audit_metrics_resilience.py -q` -> 4 passed; `bash scripts/run_ingest_prodlike_endurance_smoke.sh --duration-seconds 300` -> 300s passed | Round 2 故障注入回归全部通过：PG/Redis/Kafka 每项 4 tests、audit/metrics 4 tests、300s endurance 通过；healthz 无副作用、readyz 超时探针修复 | 补 performance/stress 压测与 7x24 长稳验证 | 2026-05-28 |
| I-NFR-003 | P-NFR-004/P-NFR-005 | 可观测性、审计与安全 | NFR | 高 | ingest | L3 | 测试通过 | `src/whale/ingest/ports/metrics.py`; `src/whale/ingest/ports/command/source_command_audit_port.py`; `src/whale/ingest/adapters/observability/file_sinks.py`; `src/whale/ingest/runtime/worker_runtime.py`; `src/whale/ingest/decorators/state_cache.py`; `src/whale/ingest/adapters/audit/multi_audit_sink.py` | `pytest tests/unit/test_ingest_metrics_events.py -q` -> 1 passed; `pytest tests/integration/test_ingest_observability_sink_smoke.py -q` -> 1 passed; `pytest tests/unit/test_ingest_audit_redaction.py -q` -> 4 passed; `pytest tests/integration/test_ingest_audit_db_jsonl_consistency.py -q` -> 1 passed; `pytest tests/integration/test_ingest_api_full_audit_matrix.py -q` -> 5 passed; `pytest tests/integration/test_ingest_prodlike_scheduler_backpressure.py -q` -> 4 passed | 新增 worker metrics p95/p99 汇总、state-cache failure audit、dual audit sink fallback 可见性；真实 Docker Kafka/Redis 故障期间 metrics/audit 连续性回归仍 pending | 补生产级观测后端集成、故障连续性回归与告警规则 | 2026-05-28 |
| I-NFR-004 | P-NFR-003 | 部署一致性与唯一 runtime image | NFR | 高 | ingest_deployment | L3 | 测试通过 | `Dockerfile`; `docker-compose.ingest-dev.yaml`; `docker-compose.ingest-prodlike.yaml`; `src/whale/ingest/runtime/entrypoint.py`; `src/whale/ingest/runtime/cli.py`; `scripts/run_ingest_runtime_compose_smoke.sh`; `scripts/run_ingest_prodlike_dependency_smoke.sh` | `pytest tests/integration/test_ingest_runtime_entrypoint_smoke.py -q` -> passed; `docker compose -f docker-compose.ingest-dev.yaml config` -> success; `docker compose -f docker-compose.ingest-prodlike.yaml config` -> success; `docker build -t whale-ingest-runtime:dev .` -> success; `bash scripts/run_ingest_runtime_compose_smoke.sh` -> healthz/readyz/migrate/worker/api-worker/host-port CRUD 全部通过; `bash scripts/run_ingest_prodlike_dependency_smoke.sh` -> 24/24 passed（含 migrate entrypoint/real PG-Redis-Kafka） | 新增 prodlike compose：同一 image 区分 api/worker/migrate 角色，支持 `DATABASE_URL` / `REDIS_URL` / mounted policy / dual audit JSONL volume；真实依赖 smoke 已通过 | 补 graceful shutdown 长稳与生产网络/安全策略现场验证 | 2026-05-28 |
| I-NFR-005 | P-NFR-002 | 多节点高可用与一致性 | NFR | 高 | ingest_scheduler | L1 | 测试通过 | `src/whale/ingest/runtime/modes.py`; `src/whale/ingest/runtime/scheduler.py`; `src/whale/ingest/runtime/lease.py`; `src/whale/ingest/runtime/fencing.py`; `src/whale/ingest/runtime/worker_runtime.py`; `src/whale/ingest/runtime/cli.py` | `pytest tests/unit/test_ingest_runtime_modes.py -q` -> 2 passed; `pytest tests/unit/test_ingest_job_lease.py -q` -> 4 passed; `pytest tests/integration/test_ingest_scheduler_active_standby_failover.py -q` -> passed; `pytest tests/integration/test_ingest_scheduler_dual_active_partitioned.py -q` -> passed; `pytest tests/integration/test_ingest_scheduler_cluster_assignment.py -q` -> passed; `pytest tests/integration/test_ingest_scheduler_apscheduler_runtime.py -q` -> 5 passed; `pytest tests/integration/test_ingest_scheduler_missed_tick_and_stagger.py -q` -> 2 passed; `pytest tests/integration/test_ingest_scheduler_graceful_shutdown.py -q` -> 3 passed; `pytest tests/integration/test_ingest_prodlike_worker_failover.py -q` -> 5 passed; `pytest tests/integration/test_ingest_prodlike_scheduler_backpressure.py -q` -> 4 passed | 已补真实 worker CLI 路径、worker failover、missed tick、assignment lag 与背压测试；7x24 endurance、真实 Docker fault injection 和现场网络分区仍未完成 | 继续补 fault injection、容量压测与真实 worker 恢复验证 | 2026-05-28 |
| I-NFR-006 | P-NFR-005/P-NFR-004 | CRUD/API 全量审计与合规 | NFR | 高 | ingest_audit | L3 | 测试通过 | `src/whale/ingest/domain/audit_event.py`; `src/whale/ingest/api/audit_middleware.py`; `src/whale/ingest/adapters/audit/db_audit_sink.py`; `src/whale/ingest/adapters/audit/multi_audit_sink.py`; `src/whale/ingest/adapters/observability/file_sinks.py`; `src/whale/ingest/runtime/cli.py`; `src/whale/ingest/runtime/write_lease.py` | `pytest tests/unit/test_ingest_audit_event_schema.py -q` -> 3 passed; `pytest tests/unit/test_ingest_audit_redaction.py -q` -> 4 passed; `pytest tests/integration/test_ingest_api_audit.py -q` -> passed; `pytest tests/integration/test_ingest_api_runtime_config_audit.py -q` -> passed; `pytest tests/integration/test_ingest_api_full_audit_matrix.py -q` -> 5 passed; `pytest tests/integration/test_ingest_audit_matrix_api_bundle_scheduler_write.py -q` -> 5 passed; `pytest tests/integration/test_ingest_audit_db_jsonl_consistency.py -q` -> 1 passed; `pytest tests/integration/test_ingest_bundle_offline_one_way_flow.py -q` -> passed; `pytest tests/integration/test_ingest_write_lease_fencing_e2e.py -q` -> passed; `pytest tests/integration/test_ingest_prodlike_audit_sink.py -q` -> 6 passed | DB/JSONL 双 sink 已形成可配置生产基线，敏感字段脱敏与 deny 审计已验证；外部审计后端与现场合规归档仍待补充 | 补外部审计后端 smoke 与合规留痕归档 | 2026-05-28 |
| I-AR-001 | P-AR-001 | use case / role / port / adapter 边界 | AR | 高 | ingest | L1 | 测试通过 | `src/whale/ingest/usecases/`; `src/whale/ingest/ports/`; `src/whale/ingest/adapters/`; `src/whale/ingest/composition.py` | `pytest tests/unit/test_source_acquisition_use_case.py -q` -> 12 passed; `pytest tests/unit/test_state_snapshot_publish_use_case.py -q` -> 17 passed | acquisition/write/publish 边界清晰，但 runtime/API/worker/scheduler 边界尚未形成 | 补 runtime/API/scheduler 边界测试 | 2026-05-27 |
| I-AR-002 | P-AR-002 | source_lab 隔离 | AR | 高 | ingest | L1 | 测试通过 | `tests/unit/test_ingest_no_source_lab_imports.py`; `src/whale/ingest/` | `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed | 生产路径隔离成立；测试/E2E 仍可外部使用 source_lab simulator | 保持 import gate 并扩到新 runtime/API 入口 | 2026-05-27 |
| I-AR-003 | P-AR-001 | runtime / API / worker / scheduler 边界 | AR | 高 | ingest_runtime | L3 | 测试通过 | `src/whale/ingest/api/`; `src/whale/ingest/runtime/`; `src/whale/ingest/bundle/`; `src/whale/ingest/framework/persistence/runtime_db.py`; `scripts/run_ingest_runtime_compose_smoke.sh`; `src/whale/ingest/runtime/worker_runtime.py` | `pytest tests/unit/test_ingest_runtime_entrypoint.py -q` -> 5 passed; `pytest tests/unit/test_ingest_api_app.py -q` -> 4 passed; `pytest tests/integration/test_ingest_runtime_entrypoint_smoke.py -q` -> passed; `pytest tests/integration/test_ingest_scheduler_apscheduler_runtime.py -q` -> 5 passed; `pytest tests/integration/test_ingest_api_scheduler_job_crud.py -q` -> 5 passed; `bash scripts/run_ingest_runtime_compose_smoke.sh` -> success | 新增 6 个 CRUD 路由模块 + APScheduler WorkerRuntime + AccessPolicyPort + 幂等性中间件，API/worker/scheduler 边界清晰可独立 smoke；13 tests 覆盖授权拒绝 E2E；composition 总装配和真实 worker 调度循环待补强 | 补 composition 总装配与 worker/scheduler 组合 E2E | 2026-05-27 |
| I-AR-004 | P-NFR-002 | 多节点调度一致性边界 | AR | 高 | ingest_scheduler | L1 | 部分实现 | `src/whale/shared/persistence/orm/ingest_runtime.py`; `src/whale/ingest/runtime/job_assignment.py`; `src/whale/ingest/runtime/lease.py`; `src/whale/ingest/runtime/fencing.py`; `src/whale/ingest/runtime/scheduler.py` | `pytest tests/unit/test_ingest_job_lease.py -q` -> 4 passed; `pytest tests/integration/test_ingest_scheduler_active_standby_failover.py -q` -> passed; `pytest tests/integration/test_ingest_scheduler_dual_active_partitioned.py -q` -> passed; `pytest tests/integration/test_ingest_scheduler_cluster_assignment.py -q` -> passed | 已有双节点接管、分区互斥和 cluster owner/fencing 证据，但网络分区、长时一致性和管理面干预路径仍未覆盖 | 补 fault injection、管理面接管路径与长时一致性测试 | 2026-05-27 |
| I-AR-005 | P-SCR-001 | 配置包与隔离区边界 | AR | 高 | ingest_bundle | L2 | 测试通过 | `src/whale/ingest/bundle/service.py`; `src/whale/ingest/bundle/redaction.py`; `src/whale/shared/persistence/orm/ingest_runtime.py` | `pytest tests/unit/test_ingest_bundle_redaction.py -q` -> 2 passed; `pytest tests/integration/test_ingest_bundle_import_export.py -q` -> passed; `pytest tests/integration/test_ingest_bundle_offline_one_way_flow.py -q` -> passed | 已验证 raw/redacted bundle、rollback 和离线单向导入边界；外部签名校验和长期归档策略仍待补充 | 补签名校验与长期归档策略 | 2026-05-27 |
| I-SCR-001 | P-SCR-001 | 电力监控系统安全分区 | SCR | 高 | ingest | L3 | 测试通过 | `config/ingest/security_partition.example.yaml`; `config/ingest/access_policy.external.example.yaml`; `src/whale/ingest/adapters/security/external_access_policy.py`; `src/whale/ingest/adapters/audit/http_audit_sink.py`; `ai_shared/reports/ingest_security_partition_deployment_topology.md`; `ai_shared/reports/ingest_access_policy_integration_contract.md`; `ai_shared/reports/ingest_external_audit_sink_contract.md`; `scripts/run_ingest_bundle_one_way_flow_smoke.sh` | `pytest tests/unit/test_ingest_security_partition_config.py -q` -> 1 passed; `pytest tests/integration/test_ingest_security_partition_smoke.py -q` -> 1 passed; `pytest tests/integration/test_ingest_security_partition_bundle_flow.py -q` -> 5 passed; `pytest tests/integration/test_ingest_external_access_policy_contract.py -q` -> 5 passed; `pytest tests/integration/test_ingest_external_audit_sink_contract.py -q` -> 5 passed; `bash scripts/run_ingest_bundle_one_way_flow_smoke.sh` -> 0 failures | 新增安全分区部署拓扑（4区模型/通信矩阵/禁止流）、单向bundle闭环、外部授权适配器（fail_closed/fail_open/cache/redact）、外部审计sink（batch/retry/redact/no-throw）；仍缺真实IAM/SIEM集成 | 真实IAM/SIEM集成待平台团队实施 | 2026-05-28 |
| I-SCR-002 | P-SCR-001 | 隔离区配置流转与单向链路约束 | SCR | 高 | ingest_bundle | L1 | 测试通过 | `src/whale/ingest/bundle/checksum.py`; `src/whale/ingest/bundle/redaction.py`; `src/whale/ingest/bundle/service.py` | `pytest tests/unit/test_ingest_bundle_checksum.py -q` -> 3 passed; `pytest tests/integration/test_ingest_bundle_import_export.py -q` -> passed; `pytest tests/integration/test_ingest_bundle_offline_one_way_flow.py -q` -> passed | 已验证 checksum、validate、rollback、redacted deny 和离线 raw bundle 导入；受控介质流程与签名扩展仍待补充 | 补受控介质流程说明与签名扩展验证 | 2026-05-27 |
| I-SCR-003 | P-SCR-001 | 写入控制安全边界 | SCR | 高 | ingest_write_runtime | L2 | 部分实现 | `src/whale/ingest/usecases/source_command_use_case.py`; `src/whale/ingest/runtime/write_lease.py`; `src/whale/ingest/ports/command/source_command_audit_port.py`; `src/whale/ingest/domain/write_security_profile.py`; `src/whale/ingest/decorators/source_write.py`; `src/whale/ingest/adapters/security/file_access_policy.py`; `src/whale/ingest/composition.py` | `pytest tests/unit/test_source_command_use_case.py tests/unit/test_source_command_audit.py -q` -> 11 passed; `pytest tests/unit/test_ingest_write_lease_fencing.py -q` -> passed; `pytest tests/integration/test_ingest_write_lease_fencing_e2e.py -q` -> passed; `pytest tests/unit/test_ingest_write_security_profile.py tests/unit/test_source_command_authorization_guard.py -q` -> 15 passed; `pytest tests/integration/test_ingest_prodlike_access_policy.py -q` -> 7 passed（含 write deny） | 新增 File/AllowAll/DenyAll AccessPolicy baseline，同一 policy 对象可同时用于 API CRUD 与 write/control；deny 已纳入审计验证，真实 write/control 仍默认关闭 | 补真实写控制接口接入与协议级 readback E2E | 2026-05-28 |
| I-TEST-001 | P-NFR-001/P-NFR-004 | 分层测试与协议准入测试 | TEST | 高 | ingest | L3 | 测试通过 | `tests/unit/`; `tests/integration/test_ingest_source_cache_message_e2e.py`; `tests/integration/test_ingest_source_cache_message_kafka_e2e.py`; `tests/integration/test_ingest_lightweight_load_gate.py`; security/observability smoke; `docker-compose.ingest-prodlike.yaml`; `scripts/run_ingest_prodlike_dependency_smoke.sh`; `tests/integration/test_ingest_prodlike_postgres_fault_injection.py`; `tests/integration/test_ingest_prodlike_redis_fault_injection.py`; `tests/integration/test_ingest_prodlike_kafka_fault_injection.py`; `tests/integration/test_ingest_prodlike_audit_metrics_resilience.py`; `tests/integration/test_ingest_prodlike_worker_failover.py`; `tests/integration/test_ingest_prodlike_scheduler_backpressure.py` | `pytest tests/unit/ -q` -> 355 passed; `pytest tests/unit/ tests/integration/test_ingest_prodlike_worker_failover.py tests/integration/test_ingest_prodlike_scheduler_backpressure.py -q` -> 364 passed; `pytest tests/integration/test_ingest_prodlike_postgres_fault_injection.py -q` -> 4 passed; `pytest tests/integration/test_ingest_prodlike_redis_fault_injection.py -q` -> 4 passed; `pytest tests/integration/test_ingest_prodlike_kafka_fault_injection.py -q` -> 4 passed; `pytest tests/integration/test_ingest_prodlike_audit_metrics_resilience.py -q` -> 4 passed; `bash scripts/run_ingest_prodlike_endurance_smoke.sh --duration-seconds 300` -> 300s passed | Round 2 故障注入回归全部通过：PG/Redis/Kafka/audit 共 20 Docker tests、worker failover 5 tests、backpressure 4 tests、endurance 300s 通过 | 补 performance/stress 压测与长稳验证 | 2026-05-28 |
| I-TEST-002 | P-NFR-004/P-NFR-005 | runtime / scheduler / CRUD / bundle / multi-node E2E | TEST | 高 | ingest_runtime | L3 | 测试通过 | `tests/integration/test_ingest_runtime_entrypoint_smoke.py`; `tests/integration/test_ingest_api_acquisition_task_crud.py`; `tests/integration/test_ingest_api_runtime_config_crud.py`; `tests/integration/test_ingest_api_audit.py`; `tests/integration/test_ingest_api_runtime_config_audit.py`; `tests/integration/test_ingest_runtime_db_init.py`; `tests/integration/test_ingest_runtime_alembic_migration.py`; `tests/integration/test_ingest_scheduler_active_standby_failover.py`; `tests/integration/test_ingest_scheduler_dual_active_partitioned.py`; `tests/integration/test_ingest_scheduler_cluster_assignment.py`; `tests/integration/test_ingest_bundle_import_export.py`; `tests/integration/test_ingest_bundle_offline_one_way_flow.py`; `tests/integration/test_ingest_write_lease_fencing_e2e.py`; `scripts/run_ingest_runtime_compose_smoke.sh`; `tests/integration/test_ingest_scheduler_apscheduler_runtime.py`; `tests/integration/test_ingest_scheduler_missed_tick_and_stagger.py`; `tests/integration/test_ingest_scheduler_graceful_shutdown.py`; `tests/integration/test_ingest_runtime_alembic_sqlite_matrix.py`; `tests/integration/test_ingest_runtime_migrate_entrypoint.py`; `tests/integration/test_ingest_api_scheduler_job_crud.py`; `tests/integration/test_ingest_api_security_partition_crud.py`; `tests/integration/test_ingest_api_bundle_metadata_crud.py`; `tests/integration/test_ingest_api_node_lease_audit_query.py`; `tests/integration/test_ingest_api_full_audit_matrix.py`; `tests/integration/test_ingest_audit_matrix_api_bundle_scheduler_write.py`; `tests/integration/test_ingest_audit_db_jsonl_consistency.py`; `scripts/ci_ingest_runtime_gate.sh`; `docker-compose.ingest-prodlike.yaml`; `scripts/run_ingest_prodlike_dependency_smoke.sh`; `tests/integration/test_ingest_security_partition_bundle_flow.py`; `tests/integration/test_ingest_external_access_policy_contract.py`; `tests/integration/test_ingest_external_audit_sink_contract.py`; `tests/integration/test_ingest_prodlike_performance_profile.py`; `scripts/run_ingest_bundle_one_way_flow_smoke.sh`; `scripts/run_ingest_prodlike_performance_profile.sh` | `pytest tests/integration -q` -> 237 passed; `pytest tests/unit tests/integration -q` -> 592 passed, 0 failed; `bash scripts/run_ingest_runtime_compose_smoke.sh` -> 全部通过; `bash scripts/run_ingest_prodlike_dependency_smoke.sh` -> 24/24 passed; `bash scripts/run_ingest_bundle_one_way_flow_smoke.sh` -> 0 failures; `bash scripts/run_ingest_prodlike_performance_profile.sh` -> 0 failures | Round 3 新增 24 integration tests，全局 integration 237 + unit 355 = 592 passed；安全分区、外部授权、外部审计、性能基线、部署/回滚手册全部完成 | 真实worker `_do_execute`、fault injection、performance/stress压测和真实硬件验证待后续补充 | 2026-05-28 |
