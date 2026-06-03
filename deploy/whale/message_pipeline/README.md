# Whale Message Pipeline 现场部署说明

## 职责

Message Pipeline 是 ingest 与 speed_layer 之间的异步解耦边界，提供统一的消息
Envelope、Topic/Partition 配置、Source/Sink 端口、DLQ 回放和 Schema Registry 抽象。

## 消息流

```
ingest → Kafka/Pulsar topic → speed_layer writers → storage layers
                                  │
                                  └── DLQ (失败重试上限后写入)
```

## Kafka 部署

### 前置依赖

- Kafka broker (>= 2.8，推荐 3.x)
- SASL/SSL 证书（如启用）
- topic 已创建或启用 auto-create

### 配置模板

参考 `config/whale/message_pipeline.kafka.example.yaml`。

### 关键配置项

| 配置 | 说明 | 默认值 |
|---|---|---|
| bootstrap_servers | Kafka broker 地址列表 | localhost:9092 |
| topic_prefix | topic 名称前缀 | whale |
| consumer_group | consumer group 命名规范 | whale-speed-layer |
| acks | 生产者确认级别 | all |
| retries | 发布重试次数 | 3 |
| enable_auto_commit | 自动 offset 提交 | false（手动管理） |
| auto_offset_reset | 无 committed offset 时的策略 | earliest |

### topic 命名规范

```text
whale.ingest.state          — 采集状态消息（ingest → pipeline）
whale.ingest.state.dlq      — 采集状态 DLQ
whale.speed.raw_archive      — 归档消费 group
whale.speed.raw_index        — 索引消费 group
whale.speed.standardized     — 标准层消费 group
whale.speed.serving_cache    — serving cache 消费 group
```

## Pulsar 部署（MISSING_ENVIRONMENT）

Pulsar 支持标记为 MISSING_ENVIRONMENT，仅在 Pulsar 集群部署并安装 pulsar-client
Python 库后可用。

### 配置模板

参考 `config/whale/message_pipeline.pulsar.example.yaml`。

## 健康检查

```bash
# 检查 Kafka broker 连通性
kafka-topics.sh --bootstrap-server <servers> --list

# 检查 consumer group lag
kafka-consumer-groups.sh \
    --bootstrap-server <servers> \
    --group whale-speed-layer \
    --describe

# 检查 topic 消息积压
kafka-run-class.sh kafka.tools.GetOffsetShell \
    --broker-list <servers> \
    --topic whale.ingest.state
```

## 切换步骤

参考 `scripts/run_whale_writer_switchover.sh` 中的无缝切换流程。
