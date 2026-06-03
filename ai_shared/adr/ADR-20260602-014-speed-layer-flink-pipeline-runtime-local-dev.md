# ADR-20260602-014-speed-layer-flink-pipeline-runtime-local-dev

## Status

Accepted

## Keywords

- speed_layer, Flink, pipeline runner, local runner, raw_archive, raw_index, standardized, serving_cache, metrics

## Context

Whale 的速度层负责消费 message_pipeline 中的实时消息，写入 raw storage（raw_archive/raw_index/standardized），并更新 serving cache。生产环境需支撑高吞吐、低延迟的流处理。

Flink 是成熟的分布式流处理框架，而开发测试阶段需要本地轻量 runner 避免依赖完整的 Flink 集群。

## Decision

1. `src/whale/speed_layer/` 定位为速度层消费和运行时编排。
2. runner.py 提供统一的 PipelineRunner 抽象和两种实现：
   - LocalPipelineRunner：用于开发测试，内存中消费消息并同步写入 storage。
   - FlinkPipelineAdapter：生产运行时适配 Flink pipeline（当前 environment-pending）。
3. writers.py 封装写入逻辑：RawArchiveWriter、RawIndexWriter、StandardizedWriter、ServingCacheUpdater，各自通过对应的 storage port 写入。
4. metrics.py 提供 MetricsCollectorPort 和 InMemoryMetricsCollector，用于收集消费延迟、写入延迟、错误计数等指标。
5. Flink/TDengine/Pulsar 真实环境当前标注 environment-pending；Ingest pipeline runner 已通过 InMemory mode 验证端到端可控。

## Consequences

- 本地开发无需部署 Flink/TDengine/Pulsar 集群，使用 InMemory 模式即可验证 pipeline 逻辑。
- 生产切换到 Flink 时只需替换 runner 适配器，writer 和 port 接口不变。
- serving_cache 更新通过 InMemoryServingCache 验证，真实 Redis/内存缓存待后续补齐。

## Rejected Options

- 直接在 speed_layer 中硬编码 Flink DataStream API：无法在开发环境独立验证 pipeline 逻辑。
- 用 Python 自建流处理框架：开发和运维成本高，不如适配成熟的 Flink。

## Related Files

- `src/whale/speed_layer/runner.py`
- `src/whale/speed_layer/writers.py`
- `src/whale/speed_layer/metrics.py`
- `tests/unit/test_speed_layer_pipeline_runner.py`
- `tests/integration/test_speed_layer_dlq_replay.py`
- `tests/integration/test_speed_layer_index_standardized_pipeline.py`
- `tests/integration/test_speed_layer_raw_archive_pipeline.py`
