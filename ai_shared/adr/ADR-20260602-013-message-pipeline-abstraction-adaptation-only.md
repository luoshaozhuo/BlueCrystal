# ADR-20260602-013-message-pipeline-abstraction-adaptation-only

## Status

Accepted

## Keywords

- message_pipeline, Kafka, Pulsar, envelope, schema, DLQ, replay, port-adapter

## Context

Whale 需要将 ingest 采集的数据异步发布给下游 speed layer/downstream consumers。核心需求是统一的消息模型（Envelope、TopicSpec、PartitionKey）、端口抽象（SourceSink port、SchemaRegistry、DLQ、Replay）和多 broker 适配（Kafka/Pulsar）。

关键约束：Kafka 和 Pulsar 是成熟的生产级 broker，message_pipeline 只应做统一的抽象和适配，不应重造 Kafka/Pulsar 的消息存储、分区、消费组、offset 管理能力。

## Decision

1. `src/whale/message_pipeline/` 定位为消息管道抽象与适配层，不重造 Kafka/Pulsar。
2. model.py 定义统一消息模型：Envelope（schema_version, message_id, message_type, trace_id, source_id, published_at, items）、TopicSpec、PartitionKey、MessageOffset、ReplayRequest。
3. ports.py 定义端口接口：MessageSourcePort、MessageSinkPort、SchemaRegistryPort、DeadLetterSinkPort、ReplayPort。
4. adapters/ 提供三类适配器：
   - in_memory.py：InMemoryMessageBus 用于开发测试（L1/L2 级验证）。
   - kafka.py：KafkaSourceAdapter/KafkaSinkAdapter，提供 contract + real 两种模式。
   - pulsar.py：PulsarSourceAdapter/PulsarSinkAdapter，当前 contract-only（real 标记 environment-pending）。
5. Kafka/Pulsar 的 topic 创建、partition 管理、consumer group 协调和 broker 运维职责不属于 message_pipeline，由部署运维侧负责。

## Consequences

- 各 consumer（speed_layer 等）通过 MessageSourcePort 消费消息，不直接依赖 Kafka/Pulsar SDK。
- Kafka/Pulsar 真实环境验证需要实际 broker 部署，当前标注 environment-pending。
- InMemory 实现可支撑 pipeline E2E 的开发和 CI 验证，无需外部 broker。

## Rejected Options

- 直接在 ingest 中硬编码 Kafka SDK：违反端口-适配器模式，无法替换 broker。
- 自建消息存储/offset 管理：重造轮子，引入运维复杂度且不可靠。

## Related Files

- `src/whale/message_pipeline/model.py`
- `src/whale/message_pipeline/ports.py`
- `src/whale/message_pipeline/adapters/in_memory.py`
- `src/whale/message_pipeline/adapters/kafka.py`
- `src/whale/message_pipeline/adapters/pulsar.py`
- `tests/unit/test_message_pipeline_envelope.py`
- `tests/unit/test_message_pipeline_ports.py`
- `tests/unit/test_message_pipeline_adapters.py`
- `tests/unit/test_message_pipeline_kafka_adapter.py`
- `tests/integration/test_message_pipeline_inmemory_e2e.py`
- `tests/integration/test_message_pipeline_kafka_e2e.py`
