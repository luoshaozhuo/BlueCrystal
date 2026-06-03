# Whale Speed Layer 现场部署说明

## 职责

Speed Layer 从 message_pipeline 消费消息，写入各存储层：
- RawArchiveWriter: 消费消息 → 写入 raw_archive 压缩文件。
- RawIndexWriter: 消费消息 → 写入 raw_index 时序索引。
- StandardizedWriter: 消费消息 → 写入 standardized 标准时序层。
- ServingCacheUpdater: 消费消息 → 更新 serving cache。

## 部署拓扑

```
┌─────────────────────────────────────────────────┐
│  PipelineRunner (asyncio / Flink)               │
│  ┌───────────────────────────────────────────┐  │
│  │ RawArchiveWriter   → raw_archive (HDFS/S3)│  │
│  │ RawIndexWriter     → raw_index (TDengine)  │  │
│  │ StandardizedWriter → standardized (TDengine)│ │
│  │ ServingCacheUpdater → serving_cache (Redis) │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │ MetricsCollector (checkpoint/lag/latency)  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## 运行时模式

| 模式 | 适用场景 | 运行器 |
|---|---|---|
| dev | 开发测试 | LocalPipelineRunner (asyncio) |
| compose | 单机 docker compose | LocalPipelineRunner |
| prodlike | 生产模拟 | LocalPipelineRunner multi-process |
| field | 现场生产 | FlinkPipelineAdapter / Kubernetes operator |

Flink 模式标记为 environment-pending，需部署 Flink 集群和 PyFlink 依赖后启用。

## 配置模板

参考 `config/whale/speed_layer.writers.example.yaml`。

## 关键配置项

| 配置 | 说明 | 默认值 |
|---|---|---|
| writer_count | 每类 writer 实例数 | 1 |
| batch_size | 归档批量大小 | 100 |
| checkpoint_interval_ms | checkpoint 间隔 | 60000 |
| consumer_group_prefix | consumer group 前缀 | whale-speed-layer |
| max_concurrent_writers | 最大并发 writer 数 | 4 |

## 启动命令

```bash
# 本地开发模式 (asyncio runner)
whale speed-layer run --mode dev --config config/whale/speed_layer.writers.example.yaml

# 检查健康状态
curl -f http://localhost:8000/speed-layer/healthz
```

## 监控指标

- consumer lag (per writer/topic/partition)
- checkpoint position
- sink success/failure count
- latency histogram

## 故障恢复

参考 `tests/integration/test_whale_writer_failure_recovery.py` 中的故障恢复验证。
