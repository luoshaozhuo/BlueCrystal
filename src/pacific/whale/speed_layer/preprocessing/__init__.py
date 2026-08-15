"""speed layer 预处理 Pipeline — Round A。

实现固定 10 阶段预处理 pipeline 与 operator/strategy registry。
本包位于 speed_layer 内部，负责消息载荷的分类、解码、解析、标准化、
质量评估、去重乱序保护、轻量派生、标准层写入和状态视图更新。

不负责：
- ingest 层消息接收（由 message_pipeline 负责）。
- 长期历史数据重算（由 batch_layer.processing 负责）。
- 复杂清洗和 batch 标准化（由 batch layer 负责）。
"""

from __future__ import annotations

from pacific.whale.speed_layer.preprocessing.models import (
    DecodedSignal,
    PipelineContext,
    ResolvedSignal,
    SignalProfileItemDescriptor,
    StandardizedPointValue,
    StandardizedWaveformValue,
    StateViewRecord,
)
from pacific.whale.speed_layer.preprocessing.operators import (
    BinaryDecoderStub,
    DeduplicateOrderGuard,
    JsonScalarDecoder,
    LightDerivation,
    PayloadClassifierAdapter,
    QualityEvaluator,
    SignalResolver,
    StandardizedWriterOperator,
    StateViewUpdater,
    TimestampNormalizer,
    ValueNormalizer,
)
from pacific.whale.speed_layer.preprocessing.pipeline import (
    PreprocessingPipeline,
)
from pacific.whale.speed_layer.preprocessing.registry import (
    OperatorRegistry,
    RegistryCondition,
)

__all__ = [
    # models / DTO
    "DecodedSignal",
    "PipelineContext",
    "ResolvedSignal",
    "SignalProfileItemDescriptor",
    "StandardizedPointValue",
    "StandardizedWaveformValue",
    "StateViewRecord",
    # operators
    "BinaryDecoderStub",
    "DeduplicateOrderGuard",
    "JsonScalarDecoder",
    "LightDerivation",
    "PayloadClassifierAdapter",
    "QualityEvaluator",
    "SignalResolver",
    "StandardizedWriterOperator",
    "StateViewUpdater",
    "TimestampNormalizer",
    "ValueNormalizer",
    # pipeline
    "PreprocessingPipeline",
    # registry
    "OperatorRegistry",
    "RegistryCondition",
]
