# ADR-20260602-014-speed-layer-flink-pipeline-runtime-local-dev

## Status

Accepted

## Keywords

- speed_layer, Flink, pipeline runner, local runner, raw_archive, raw_index, standardized, serving_cache, metrics, preprocessing, operator registry, fixed 10-stage pipeline, decode-before-resolve

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

### Round A: 预处理 Pipeline 与 Operator Registry

2026-06-04 补充。本项目引入了位于 `speed_layer/preprocessing/` 的固定 10 阶段预处理 pipeline，与现有 `LightProcessingPipeline` 并行运行。

6. `src/whale/speed_layer/preprocessing/` 实现固定 10 阶段预处理流水线：
   - STAGE_ORDER = [1..10]：classify->decode->resolve->normalize timestamp->normalize value->evaluate quality->deduplicate & order guard->light derivation->write standardized->update state view。
   - Pipeline 阶段顺序固定，不通过继承 BasePipeline 派生不同 pipeline。
7. OperatorRegistry 按条件加权选择 operator：
   - 匹配维度：payload_type（JSON/BINARY/SCALAR）、protocol、vendor、descriptor_key、default fallback。
   - 权重：descriptor_key 精确匹配 30、protocol 20、payload_type 10、vendor 5、default 0。
   - 同分按注册顺序优先，default 最低优先级。
8. decode-before-resolve 模式：原始载荷先经 PayloadClassifierAdapter 分类，再经 JsonScalarDecoder/BinaryDecoderStub 解码为 DecodedSignal，最后由 SignalResolver 映射至 SignalProfileItemDescriptor。
9. 11 个基础 operator 覆盖全部 10 个阶段，每个 operator 从 PipelineContext 读取输入、写回结果，不抛异常到编排层。
10. 6 个运行期 DTO：SignalProfileItemDescriptor、DecodedSignal、ResolvedSignal、StandardizedPointValue、StandardizedWaveformValue、StateViewRecord + PipelineContext（共享上下文）。
11. 默认 sink 使用 InMemoryServingCache + MemoryStandardizedSink 实现纯内存闭环；生产环境可替换为 TdengineStandardizedSink + RedisServingCache。

## Consequences

- 本地开发无需部署 Flink/TDengine/Pulsar 集群，使用 InMemory 模式即可验证 pipeline 逻辑。
- 生产切换到 Flink 时只需替换 runner 适配器，writer 和 port 接口不变。
- serving_cache 更新通过 InMemoryServingCache 验证，真实 Redis/内存缓存待后续补齐。
- 预处理 pipeline 与 LightProcessingPipeline 并存：LightProcessingPipeline 负责任意轻处理（envelope 层校验/去重/乱序），PreprocessingPipeline 负责协议感知的载荷预处理（分类/解码/解析/标准化/视图更新）。两者职责互补，不相互替代。
- OperatorRegistry 支持协议和厂家级定制 operator 注册，允许同一阶段按数据特征选择不同处理路径，无需修改 pipeline 编排逻辑。

## Rejected Options

- 直接在 speed_layer 中硬编码 Flink DataStream API：无法在开发环境独立验证 pipeline 逻辑。
- 用 Python 自建流处理框架：开发和运维成本高，不如适配成熟的 Flink。

## Related Files

- `src/whale/speed_layer/runner.py`
- `src/whale/speed_layer/writers.py`
- `src/whale/speed_layer/metrics.py`
- `src/whale/speed_layer/light_processor.py`
- `src/whale/speed_layer/preprocessing/__init__.py`
- `src/whale/speed_layer/preprocessing/models.py`
- `src/whale/speed_layer/preprocessing/registry.py`
- `src/whale/speed_layer/preprocessing/operators.py`
- `src/whale/speed_layer/preprocessing/pipeline.py`
- `tests/unit/test_speed_layer_light_processor.py`
- `tests/unit/test_speed_layer_pipeline_runner.py`
- `tests/unit/test_speed_layer_preprocessing.py`
- `src/whale/storage/waveform.py` (StandardizedWaveformSinkPort，PreprocessingPipeline 阶段 9 StandardizedWaveformValue 的目标 sink)
- `src/whale/ingest/file_ingest/` (DecodedSignal 来源之一，见 ADR-20260604-016)
- `tests/integration/test_speed_layer_dlq_replay.py`
- `tests/integration/test_speed_layer_index_standardized_pipeline.py`
- `tests/integration/test_speed_layer_raw_archive_pipeline.py`
