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
| I-FR-001 | P-FR-001/P-FR-002 | source -> cache 采集链路 | FR | 高 | ingest | L3 | 运行闭环通过 | `SourceAcquisitionUseCase`; `PollingAcquisitionRole`; `SubscriptionAcquisitionRole`; `RedisSourceStateCache`; `tests/integration/test_ingest_source_cache_message_e2e.py` | `pytest tests/unit/test_source_acquisition_use_case.py -q` -> 12 passed; `pytest tests/unit/test_subscription_acquisition_role.py -q tests/unit/test_polling_acquisition_role.py -q` -> 10 passed; `pytest tests/integration/test_ingest_source_cache_message_e2e.py -q` -> 2 passed | Report/runtime subscription 在长连接断线后的真实协议级恢复仍依赖 adapter/backend 能力 | 补更多协议级运行态恢复归档 | 2026-05-26 |
| I-FR-002 | P-FR-002 | cache -> message pipeline 发布链路 | FR | 高 | ingest | L3 | 运行闭环通过 | `StateSnapshotPublishUseCase`; `MessagePublisherPort`; `KafkaMessagePublisher`; `tests/integration/test_ingest_source_cache_message_e2e.py`; `tests/integration/test_ingest_source_cache_message_kafka_e2e.py` | `pytest tests/unit/test_state_snapshot_publish_use_case.py -q` -> 17 passed; `pytest tests/integration/test_ingest_cache_to_kafka_pipeline.py -q` -> 5 passed; `pytest tests/integration/test_ingest_source_cache_message_kafka_e2e.py -q` -> 1 passed | 发布 sink 仍是 Kafka adapter 级验证，非生产平台部署完成 | 补真实部署环境 topic/ACL/retention smoke | 2026-05-26 |
| I-FR-003 | P-FR-001/P-SCR-001 | 设备命令与写入控制 | FR | 高 | ingest | L2 | 部分实现 | `SourceCommandUseCase`; `SourceCommandAuditPort`; 协议 write adapters 与写入集成测试 | `pytest tests/unit/test_source_command_use_case.py tests/unit/test_source_command_audit.py -q` -> 12 passed; `pytest tests/integration/test_ingest_opcua_source_write.py -q` -> 3 passed | readback/确认仅覆盖已实现协议；生产审计 sink 未落地；多节点 write lease/fencing 未实现 | 补 write lease/fencing/audit/readback E2E | 2026-05-26 |
| I-FR-004 | P-FR-001 | 多协议 ingest adapter | FR | 高 | ingest | L2 | 部分实现 | `src/whale/ingest/adapters/source/`; static registries; adapter matrix; no-source-lab import gate | `pytest tests/unit/test_ingest_source_adapter_capability_matrix.py -q` -> 2 passed; `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed | IEC101/Modbus RTU/MQTT/HTTP REST/GOOSE/SV 未纳入 ingest production registry；GOOSE/SV 需单独安全论证 | 补 adapter capability matrix 与 unsupported 语义；另起 GOOSE/SV production boundary 决策 | 2026-05-26 |
| I-FR-005 | P-DGR-001 | 统一配置加载 | FR | 高 | ingest | L1 | 部分实现 | `SourceRuntimeConfigRepository`; `OpcUaSourceAcquisitionDefinitionRepository`; config DTO/ORM | `pytest tests/unit/test_source_runtime_config_repository.py -q` -> 2 passed | 未打通 source/connection/point/profile/protocol params 到 composition/use case/runtime/scheduler 的端到端装配 | 补配置模型、DB schema、composition 和 runtime E2E | 2026-05-26 |
| I-FR-006 | P-FR-002 | 端到端 ingest 管道 | FR | 高 | ingest | L3 | 运行闭环通过 | `tests/integration/test_ingest_source_cache_message_e2e.py`; `tests/integration/test_ingest_source_cache_message_kafka_e2e.py` | `pytest tests/integration/test_ingest_source_cache_message_e2e.py -q` -> 2 passed; `pytest tests/integration/test_ingest_source_cache_message_kafka_e2e.py -q` -> 1 passed | 当前闭环不等同生产部署 readiness | 补部署环境 smoke 与 topic/consumer policy 验证 | 2026-05-26 |
| I-FR-007 | P-NFR-003/P-AR-001 | 统一 ingest runtime image 与 entrypoint | FR | 高 | ingest_runtime | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 尚未发现唯一 runtime image 与 entrypoint 证据 | 新增 Dockerfile/entrypoint/Typer 命令与 smoke | 2026-05-26 |
| I-FR-008 | P-FR-005/P-NFR-005 | 采集任务 CRUD API | FR | 高 | ingest_api | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 尚未发现 FastAPI CRUD/API 审计实现 | 新增 API schema、service、audit middleware、E2E | 2026-05-26 |
| I-FR-009 | P-NFR-002 | 调度器与多节点任务分配 | FR | 高 | ingest_scheduler | 待核实 | 部分实现 | 现有 `src/whale/ingest/runtime/scheduler.py` 等需复核 | 待补充 | 现有 scheduler 是否支持 heartbeat/assignment/lease/fencing/multi-node 未核实，预计不足 | 补多节点 scheduler、lease、fencing 与 E2E | 2026-05-26 |
| I-FR-010 | P-DGR-001/P-NFR-002 | local runtime DB 与 migration | FR | 高 | ingest_runtime_db | 待核实 | 部分实现 | 现有 persistence/session/ORM/Alembic 状态待核实 | 待补充 | runtime DB 是否覆盖 node/job/lease/bundle/audit/fencing 未核实，预计不足 | 补 SQLAlchemy 2.x ORM、Alembic migration、DB tests | 2026-05-26 |
| I-FR-011 | P-DGR-001/P-SCR-001 | 配置包 import/export 与离线更新 | FR | 高 | ingest_bundle | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 未发现 bundle version/checksum/import/export/rollback 实现 | 补 bundle schema、CLI、checksum、rollback、审计 | 2026-05-26 |
| I-FR-012 | P-SCR-001/P-NFR-002 | 多节点 write/control lease 与 fencing | FR | 高 | ingest_write_runtime | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 未发现独立 write lease/fencing/token 实现 | 补 write lease port、DB schema、command guard、E2E | 2026-05-26 |
| I-FR-013 | P-NFR-004/P-NFR-005 | API 查询与操作全量审计 | FR | 高 | ingest_audit | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 当前仅写命令审计/metrics，未覆盖 CRUD/query/deny/conflict 全量审计 | 补 audit event schema、middleware、sink、E2E | 2026-05-26 |
| I-NFR-001 | P-NFR-001 | 性能与容量 | NFR | 高 | ingest | L2 | 部分实现 | `tests/integration/test_ingest_lightweight_load_gate.py`; `IngestMetricsPort` | `pytest tests/integration/test_ingest_lightweight_load_gate.py -q` -> 1 passed | 已完成 lightweight load gate，但未执行重型 performance/stress，不等同完整容量画像；scheduler metrics 未覆盖 | 补 performance/stress/scheduler load 归档 | 2026-05-26 |
| I-NFR-002 | P-NFR-002 | 稳定性与故障恢复 | NFR | 高 | ingest | L2 | 部分实现 | `SubscriptionAcquisitionRole` retry/backoff；reconnect tests | `pytest tests/unit/test_subscription_reconnect_baseline.py -q` -> 1 passed; `pytest tests/unit/test_subscription_reconnect_runtime.py -q` -> 2 passed | 多节点 failover、lease expiry、bundle rollback、DB 故障、worker crash 接管未覆盖 | 补 fault injection 与 multi-node recovery tests | 2026-05-26 |
| I-NFR-003 | P-NFR-004/P-NFR-005 | 可观测性、审计与安全 | NFR | 高 | ingest | L2 | 部分实现 | `SourceCommandAuditPort`; `IngestMetricsPort`; JSONL sink | `pytest tests/unit/test_ingest_metrics_events.py -q` -> 1 passed; `pytest tests/integration/test_ingest_observability_sink_smoke.py -q` -> 1 passed | 未覆盖 API/CRUD/bundle/scheduler/lease 全量审计；production observability/audit backend 未落地 | 补 middleware、scheduler metrics、真实 sink smoke | 2026-05-26 |
| I-NFR-004 | P-NFR-003 | 部署一致性与唯一 runtime image | NFR | 高 | ingest_deployment | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 未发现唯一 image + entrypoint smoke 证据 | 补 Dockerfile/compose/entrypoint CI smoke | 2026-05-26 |
| I-NFR-005 | P-NFR-002 | 多节点高可用与一致性 | NFR | 高 | ingest_scheduler | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 未发现 active_standby/dual_active_partitioned/cluster 的 assignment/lease/fencing 实现 | 补 HA scheduler 与 multi-node E2E | 2026-05-26 |
| I-NFR-006 | P-NFR-005/P-NFR-004 | CRUD/API 全量审计与合规 | NFR | 高 | ingest_audit | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 未覆盖 query success/failure、deny、validation、conflict 的全量审计 | 补审计 schema、middleware、sink 与安全 smoke | 2026-05-26 |
| I-AR-001 | P-AR-001 | use case / role / port / adapter 边界 | AR | 高 | ingest | L2 | 测试通过 | `SourceAcquisitionUseCase`; `SourceCommandUseCase`; `StateSnapshotPublishUseCase`; `composition.py` | `pytest tests/unit/test_source_acquisition_use_case.py -q` -> 12 passed; `pytest tests/unit/test_state_snapshot_publish_use_case.py -q` -> 17 passed | runtime/scheduler/API 边界尚未完整落地 | 新增 runtime/API/worker/scheduler 边界测试 | 2026-05-26 |
| I-AR-002 | P-AR-002 | source_lab 隔离 | AR | 高 | ingest | L2 | 测试通过 | `tests/unit/test_ingest_no_source_lab_imports.py` | `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed | 测试侧可使用 source_lab simulator；生产路径需持续禁止 import | 保持 import gate | 2026-05-26 |
| I-AR-003 | P-AR-001 | runtime / API / worker / scheduler 边界 | AR | 高 | ingest_runtime | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 尚未形成 API/worker/scheduler/bundle/migrate 清晰边界 | 补模块结构、composition、边界测试 | 2026-05-26 |
| I-AR-004 | P-NFR-002 | 多节点调度一致性边界 | AR | 高 | ingest_scheduler | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 尚未发现 DB-backed assignment/lease/fencing 一致性边界 | 补 DB-backed scheduler 设计与 E2E | 2026-05-26 |
| I-AR-005 | P-SCR-001 | 配置包与隔离区边界 | AR | 高 | ingest_bundle | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 尚未发现离线 bundle 流转边界实现 | 补 bundle import/export 与 security partition tests | 2026-05-26 |
| I-SCR-001 | P-SCR-001 | 电力监控系统安全分区 | SCR | 高 | ingest | L2 | 部分实现 | `ingest_security_partition_boundary.md`; `config/ingest/security_partition.example.yaml`; security smoke | `pytest tests/unit/test_ingest_security_partition_config.py -q` -> 1 passed; `pytest tests/integration/test_ingest_security_partition_smoke.py -q` -> 1 passed | 仅有 example config，无 production security profile；bundle/runtime DB/write control 分区未完整覆盖 | 补 production profile、bundle 流向、write control 安全 smoke | 2026-05-26 |
| I-SCR-002 | P-SCR-001 | 隔离区配置流转与单向链路约束 | SCR | 高 | ingest_bundle | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 未发现单向链路 bundle 更新机制 | 补 offline bundle E2E 与审计 | 2026-05-26 |
| I-SCR-003 | P-SCR-001 | 写入控制安全边界 | SCR | 高 | ingest_write_runtime | 待核实 | 部分实现 | `SourceCommandUseCase`; write audit tests | `pytest tests/unit/test_source_command_use_case.py tests/unit/test_source_command_audit.py -q` -> 12 passed | 默认 disabled/dry_run 已有部分证据；write lease/fencing/authorization/readback 多节点安全闭环未完成 | 补 write security profile、lease/fencing、readback E2E | 2026-05-26 |
| I-TEST-001 | P-NFR-001/P-NFR-004 | 分层测试与协议准入测试 | TEST | 高 | ingest | L2 | 部分实现 | `tests/unit/`; `tests/integration/`; Kafka true E2E; load gate; security smoke | `pytest tests/unit -q` -> 318 passed; `pytest tests/integration -q` -> 41 passed | performance/fault/security/runtime/scheduler/multi-node 未形成完整矩阵 | 补 runtime/scheduler/bundle/multi-node 测试 | 2026-05-26 |
| I-TEST-002 | P-NFR-004/P-NFR-005 | runtime / scheduler / CRUD / bundle / multi-node E2E | TEST | 高 | ingest_runtime | 待核实 | 未实现 | 当前需求新增，待读源码确认 | 待补充 | 未发现对应 E2E 矩阵 | 补 image/entrypoint/API/scheduler/bundle/lease/fencing E2E | 2026-05-26 |
