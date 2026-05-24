# ADR-20260524-005-cache-to-message-queue-publish-use-case

## Status

Accepted

## Keywords

- state snapshot publish
- cache to message queue
- use case boundary
- full snapshot
- port-adapter
- composition

## Context

Whale 项目已完成 OPC UA 和 Modbus TCP 两种协议的采集（acquisition）与写入（write）能力接入。Round 3 建立了协议生产准入与 capability registry 治理门禁。当前逐步进入"采集结果 → 消息队列"的管道建设阶段。

在架构设计过程中出现以下需要固化的问题：

1. **现有 use case 职责已满**：`SourceAcquisitionUseCase` 负责采集和缓存写入，`SourceCommandUseCase` 负责设备写入。新增"缓存读取 → 消息发布"不应混入两者。

2. **端口可复用**：`SourceStateSnapshotReaderPort` 已由 `RedisSourceStateCache` 实现，`MessagePublisherPort` 已由 `KafkaMessagePublisher` / `RedisStreamsMessagePublisher` 实现。新 use case 可直接依赖这两个端口，无需新增 port。

3. **字段映射缺口**：`CachedSourceState` 不包含 `station_id`、`device_code`、`model_id` 等业务字段。`StateSnapshotItem` 需要这些字段。需要通过构造参数和 attributes 字段建立 fallback 策略。

4. **增量 vs 全量**：首版只需要全量快照，不需要增量变更事件。增量需要 base snapshot + change tracking。

5. **Composition 注入策略**：现有 composition.py 中采集 compositon 提供默认实现，write composition 也是。但消息发布的 publisher 后端由环境变量决定，composition 不应替调用者决定。因此 publisher 必须显式注入。

这些决策需要在 ADR 中固化。

## Decision

### 1. 独立 publish use case

新增 `StateSnapshotPublishUseCase`，职责：

- 依赖 `SourceStateSnapshotReaderPort` 读取最新状态快照。
- 依赖 `MessagePublisherPort` 发布已组装的消息。
- 不依赖 `SourceAcquisitionUseCase`、`SourceCommandUseCase`、`source_lab`、`source` adapter。
- 支持按 `source_id` / `ld_name` 过滤。
- 支持 `dry_run` 模式（只读缓存不发布）。
- 支持 `max_items_per_message` 拆分（大快照拆为多条消息）。
- 不做增量变更检测。

### 2. 全量快照语义

`StateSnapshotPublishUseCase` 只发布"调用瞬间的快照"。不跟踪变更，不记录上一次发布状态。每次 `execute()` 读取完整缓存、组装、发布。

后续如需增量，应新增独立 use case 或模式（如 CDC），不修改现有全量语义。

### 3. 字段映射 fallback 策略

`CachedSourceState` → `StateSnapshotItem` 映射规则：

| `StateSnapshotItem` 字段 | 数据来源 | fallback |
|---|---|---|
| `station_id` | request 参数或 use_case 构造参数 | "unknown-station" |
| `device_id` | `CachedSourceState.ld_name` | `source_id` |
| `device_code` | `CachedSourceState.source_id` | `ld_name` |
| `model_id` | `attributes["model_id"]` | `device_code` |
| `variable_key` | `CachedNodeValue.node_key` | 无 |
| `value_type` | `attributes["value_type"]` | None |
| `received_at` | `CachedSourceState.client_received_at` | `CachedNodeValue.server_timestamp` |

### 4. Composition 要求 publisher 显式注入

`build_state_snapshot_publish_composition()` 不允许默认创建 publisher。调用者必须传入实现了 `MessagePublisherPort` 的对象。原因：publisher 后端（Kafka、Redis Streams、Relational Outbox）由外部环境配置决定，不在 composition 的职责范围内。

### 5. 拆分消息的 id 策略

当 `max_items_per_message > 0` 且实际 item 数超过阈值时，拆为多条消息：

- 首条消息 `message_id == snapshot_id`。
- 后续消息 `message_id = "{snapshot_id}-{seq:04d}"`。
- 所有拆分消息共享同一 `snapshot_id`。

## Consequences

### 收益

- `StateSnapshotPublishUseCase` 与采集/写入 use case 解耦，各自独立演进。
- 端口复用降低了新 use case 的接入成本。
- fallback 策略保证在缺少部分字段时仍能发布有效消息。
- 显式注入 publisher 让测试可以注入 FakePublisher 而无需模拟 Kafka。
- dry_run 模式允许在正式发布前验证数据。
- 拆分机制避免单条消息过大。

### 代价

- fallback 策略可能导致下游消费者收到不完全准确的设备标识。
- 全量快照每次读取全部缓存，大站（数千变量）时迭代成本高。
- 多消息拆分当前无顺序保证语义。
- 增量检测缺失意味着下游消费者需要自己实现去重或状态跟踪。

### 约束

- `StateSnapshotPublishUseCase` 不得 import `source_lab` 或 protocol adapter。
- 不得通过 `source_lab` 的 task facade 作为 production client 证据。
- 不得为通过测试而降低断言或跳过门禁。
- field mapping 的 fallback 逻辑必须记录在代码中。

## Rejected Options

### 方案一：扩展现有 `SourceAcquisitionUseCase` 加入消息发布

拒绝。原因：

- `SourceAcquisitionUseCase` 职责已明确：采集 + 缓存写入。加入发布违反单一职责。
- 现有 tests 需要大量修改。
- 发布策略（全量/增量/定时）与采集策略（轮询/订阅）正交。

### 方案二：在 scheduler 层面直接调用 reader + publisher

拒绝。原因：

- 绕过 use case 层意味着没有统一的错误处理、过滤、dry_run、指标收集。
- 测试时只能测试 scheduler 集成，不能单独测试业务逻辑。
- 违反 clean architecture 分层原则。

### 方案三：使用 service locator 模式，不通过 composition 注入 publisher

拒绝。原因：

- 隐式依赖难以测试。
- publisher 后端切换时 composition 无法感知。
- 与服务定位器反模式带来的所有问题一致。

### 方案四：支持增量变更事件（CDC 模式）

推迟。原因：

- 增量需要 base snapshot、change tracking、event dedup 等基础设施。
- 当前阶段全量快照已满足需求。
- 后续可新增独立 use case 实现增量而不修改现有代码。

## Related Files

- `src/whale/ingest/usecases/state_snapshot_publish_use_case.py`
- `src/whale/ingest/usecases/dtos/state_publish_request.py`
- `src/whale/ingest/usecases/dtos/state_publish_result.py`
- `src/whale/ingest/composition.py`
- `src/whale/ingest/ports/state/source_state_snapshot_reader_port.py`
- `src/whale/ingest/ports/message/message_publisher_port.py`
- `tests/unit/test_state_snapshot_publish_use_case.py`
- `tests/integration/test_ingest_cache_to_kafka_pipeline.py`
- `ai_shared/reports/cache_to_message_queue_use_case_round4_report.md`

## Supersedes / Superseded By

None.
