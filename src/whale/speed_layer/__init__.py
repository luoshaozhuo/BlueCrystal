"""speed layer 模块。

消费 message_pipeline 的实时消息，写入 raw storage，更新 serving cache。
提供本地 asyncio pipeline runner、Flink runtime adapter contract、
实时轻处理管线（SP-FR-004）和 Round A 预处理 Pipeline。

本模块包含：
- writers: 消息消费者与写入者（RawArchiveWriter / RawIndexWriter /
  StandardizedWriter / ServingCacheUpdater）。
- runner: 管道运行器（PipelineRunner / LocalPipelineRunner / FlinkPipelineAdapter）。
- metrics: 指标收集（MetricsCollectorPort / InMemoryMetricsCollector）。
- light_processor: 实时轻处理管线（EnvelopeValidator / MessageDeduplicator /
  QualityCodePassThrough / OutOfOrderGuard / LightProcessingPipeline）。
- preprocessing: Round A 预处理 Pipeline（固定 10 阶段 + Operator/Strategy Registry）。
"""

from __future__ import annotations

from whale.speed_layer.light_processor import (
    EnvelopeValidator,
    LightProcessingPipeline,
    MessageDeduplicator,
    OutOfOrderGuard,
    QualityCodePassThrough,
)
from whale.speed_layer.metrics import (
    InMemoryMetricsCollector,
    MetricsCollectorPort,
)
from whale.speed_layer.preprocessing import (
    BinaryDecoderStub,
    DecodedSignal,
    DeduplicateOrderGuard,
    JsonScalarDecoder,
    LightDerivation,
    OperatorRegistry,
    PayloadClassifierAdapter,
    PipelineContext,
    PreprocessingPipeline,
    QualityEvaluator,
    RegistryCondition,
    ResolvedSignal,
    SignalProfileItemDescriptor,
    SignalResolver,
    StandardizedPointValue,
    StandardizedWaveformValue,
    StandardizedWriterOperator,
    StateViewRecord,
    StateViewUpdater,
    TimestampNormalizer,
    ValueNormalizer,
)
from whale.speed_layer.runner import (
    FlinkPipelineAdapter,
    FlinkPipelineConfig,
    LocalPipelineRunner,
    PipelineRunner,
    SpeedLayerWiring,
)
from whale.speed_layer.writers import (
    RawArchiveWriter,
    RawIndexWriter,
    ServingCacheUpdater,
    StandardizedWriter,
)

__all__ = [
    # runner
    "FlinkPipelineAdapter",
    "FlinkPipelineConfig",
    "LocalPipelineRunner",
    "PipelineRunner",
    "SpeedLayerWiring",
    # writers
    "RawArchiveWriter",
    "RawIndexWriter",
    "ServingCacheUpdater",
    "StandardizedWriter",
    # metrics
    "InMemoryMetricsCollector",
    "MetricsCollectorPort",
    # light_processor (SP-FR-004)
    "EnvelopeValidator",
    "LightProcessingPipeline",
    "MessageDeduplicator",
    "OutOfOrderGuard",
    "QualityCodePassThrough",
    # preprocessing (Round A)
    "BinaryDecoderStub",
    "DecodedSignal",
    "DeduplicateOrderGuard",
    "JsonScalarDecoder",
    "LightDerivation",
    "OperatorRegistry",
    "PayloadClassifierAdapter",
    "PipelineContext",
    "PreprocessingPipeline",
    "QualityEvaluator",
    "RegistryCondition",
    "ResolvedSignal",
    "SignalProfileItemDescriptor",
    "SignalResolver",
    "StandardizedPointValue",
    "StandardizedWaveformValue",
    "StandardizedWriterOperator",
    "StateViewRecord",
    "StateViewUpdater",
    "TimestampNormalizer",
    "ValueNormalizer",
]
