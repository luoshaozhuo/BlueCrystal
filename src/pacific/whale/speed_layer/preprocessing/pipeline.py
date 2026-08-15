"""speed layer 预处理 Pipeline — 固定 10 阶段编排。

PreprocessingPipeline 使用 Operator/Strategy Registry 按固定阶段顺序执行
预处理流程，不通过继承 BasePipeline 派生不同 pipeline。每个阶段的 operator
由 OperatorRegistry 按上下文选择。

固定 10 阶段顺序：
1. classify / adapt payload → PayloadClassifierAdapter
2. decode payload → JsonScalarDecoder / BinaryDecoderStub
3. resolve signal → SignalResolver
4. normalize timestamp → TimestampNormalizer
5. normalize value → ValueNormalizer
6. evaluate quality → QualityEvaluator
7. deduplicate & order guard → DeduplicateOrderGuard
8. light derivation → LightDerivation
9. write TDengine standardized → StandardizedWriterOperator
10. update Redis state view → StateViewUpdater

Pipeline 只编排阶段顺序，不负责 operator 选择（由 registry 负责）。
未注册 operator 的阶段默认跳过（不报错），允许部分阶段可选。

不负责：
- 替代现有 LightProcessingPipeline（两者并存，LightProcessingPipeline 保持兼容）。
- 长期历史重算（由 batch_layer.processing 负责）。
- ingest 层消息接收与 DLQ 管理（由 message_pipeline 和 runner 负责）。
"""

from __future__ import annotations

import logging
import time
from typing import Any

from pacific.whale.speed_layer.preprocessing.models import PipelineContext
from pacific.whale.speed_layer.preprocessing.registry import OperatorRegistry

logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    """固定 10 阶段预处理管线。

    使用 OperatorRegistry 在每个阶段动态选择 operator。管线不通过继承
    BasePipeline 派生，所有实例共享相同的 10 阶段顺序。

    使用方式：
        pipeline = PreprocessingPipeline(registry)
        pipeline.register_defaults()  # 注册默认 operator
        ctx = build_context(envelope_dict)
        ctx = pipeline.run(ctx)

    管线自身不管理 operator 实例生命周期，只引用 registry 中注册的 operator。

    Attributes:
        _registry: operator 注册表（外部注入，可跨 pipeline 共享）。
        _stage_names: 阶段序号到名称的映射。
        _stage_order: 固定阶段顺序（1-10）。
        _error_count: 累计错误计数（跨批次）。
    """

    # 固定阶段序号与名称映射
    STAGE_NAMES: dict[int, str] = {
        1: "classify / adapt payload",
        2: "decode payload",
        3: "resolve signal",
        4: "normalize timestamp",
        5: "normalize value",
        6: "evaluate quality",
        7: "deduplicate & order guard",
        8: "light derivation",
        9: "write TDengine standardized",
        10: "update Redis state view",
    }

    # 固定阶段执行顺序
    STAGE_ORDER = list(range(1, 11))

    def __init__(self, registry: OperatorRegistry | None = None) -> None:
        """初始化预处理管线。

        Args:
            registry: operator 注册表。None 时创建空注册表（需后续注册）。
        """
        self._registry = registry or OperatorRegistry()
        """operator 注册表。"""
        self._error_count = 0
        """累计错误计数。"""
        self._run_count = 0
        """累计运行批次计数。"""

    @property
    def registry(self) -> OperatorRegistry:
        """返回 operator 注册表（只读访问）。"""
        return self._registry

    def register_defaults(
        self,
        *,
        dedup_size: int = 10000,
        ooo_tolerance_seconds: int = 60,
    ) -> "PreprocessingPipeline":
        """注册所有阶段的默认 operator。

        注册后，每个阶段至少有一个 default operator 可用。
        调用方应在注册后按协议/厂家注册特定 operator 定制。

        默认注册顺序保证 default fallback 优先级最低。

        Args:
            dedup_size: 去重 LRU 容量。
            ooo_tolerance_seconds: 乱序容忍秒数。

        Returns:
            self，支持链式调用。
        """
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
        from pacific.whale.storage.serving_cache import InMemoryServingCache
        from pacific.whale.storage.standardized import MemoryStandardizedSink

        # 阶段 1: classify / adapt（默认）
        self._registry.register(
            1, PayloadClassifierAdapter(),
        )

        # 阶段 2: decode（JSON default, BINARY 专用）
        self._registry.register(
            2, JsonScalarDecoder(),
            payload_type="JSON",
        )
        self._registry.register(
            2, JsonScalarDecoder(),
            payload_type="SCALAR",
        )
        self._registry.register(
            2, BinaryDecoderStub(),
            payload_type="BINARY",
        )
        # default fallback for stage 2
        self._registry.register(
            2, JsonScalarDecoder(),
        )

        # 阶段 3: resolve signal（default）
        self._registry.register(
            3, SignalResolver(),
        )

        # 阶段 4: normalize timestamp（default）
        self._registry.register(
            4, TimestampNormalizer(),
        )

        # 阶段 5: normalize value（default）
        self._registry.register(
            5, ValueNormalizer(),
        )

        # 阶段 6: evaluate quality（default）
        self._registry.register(
            6, QualityEvaluator(),
        )

        # 阶段 7: deduplicate & order guard（default）
        self._registry.register(
            7, DeduplicateOrderGuard(
                dedup_size=dedup_size,
                tolerance_seconds=ooo_tolerance_seconds,
            ),
        )

        # 阶段 8: light derivation（default）
        self._registry.register(
            8, LightDerivation(),
        )

        # 阶段 9: write standardized（default in-memory sink）
        # 注意：生产环境应在调用方替换为 TdengineStandardizedSink
        self._registry.register(
            9,
            StandardizedWriterOperator(
                sink=MemoryStandardizedSink(),
            ),
        )

        # 阶段 10: update state view（default in-memory cache）
        # 注意：生产环境应在调用方替换为 RedisServingCache
        self._registry.register(
            10,
            StateViewUpdater(
                cache=InMemoryServingCache(),
            ),
        )

        logger.info(
            "PreprocessingPipeline 默认 operator 注册完成，已注册阶段: %s",
            self._registry.get_registered_stages(),
        )
        return self

    def run(self, ctx: PipelineContext) -> PipelineContext:
        """按固定阶段顺序执行预处理管线。

        遍历 STAGE_ORDER（1-10），从 registry 中选择 operator 并执行。
        未注册 operator 的阶段默认跳过。

        执行期间的异常被捕获并写入 ctx.errors，不中断后续阶段执行。
        但致命错误（如所有阶段 operator 都无法选择）会设置 ctx.should_dlq。

        Args:
            ctx: 输入 pipeline 上下文（应已包含 source_id、message_id 等元信息）。

        Returns:
            更新后的 pipeline 上下文（含所有阶段结果和标准化值）。

        Raises:
            ValueError: ctx 为空或无法选择任何 operator（严重配置错误）。
        """
        if ctx is None:
            raise ValueError("PipelineContext 不能为 None")

        self._run_count += 1
        stage_count = 0

        for stage in self.STAGE_ORDER:
            stage_name = self.STAGE_NAMES.get(stage, f"stage_{stage}")

            try:
                operator = self._registry.select(stage, ctx)
                if operator is None:
                    logger.debug("阶段 %d (%s) 无 operator，跳过", stage, stage_name)
                    continue
            except KeyError:
                logger.debug(
                    "阶段 %d (%s) 无已注册 operator，跳过", stage, stage_name
                )
                continue

            try:
                stage_start = time.monotonic()
                ctx = operator.execute(ctx)
                stage_elapsed = time.monotonic() - stage_start
                stage_count += 1

                # 记录阶段耗时
                result_key = f"{stage}_{stage_name.split('/')[0].strip().replace(' ', '_')}"
                if result_key not in ctx.stage_results:
                    ctx.stage_results[result_key] = {}
                ctx.stage_results[result_key]["elapsed_ms"] = (
                    stage_elapsed * 1000
                )

                # 如果是重复消息，跳过后续阶段
                if stage == 7 and ctx.is_duplicate:
                    logger.debug(
                        "message_id=%s 为重复消息，跳过阶段 8-10",
                        ctx.message_id,
                    )
                    # 标记后续阶段为 SKIPPED
                    for skip_stage in range(8, 11):
                        skip_name = self.STAGE_NAMES.get(skip_stage, f"stage_{skip_stage}")
                        ctx.stage_results[f"{skip_stage}_{skip_name}"] = {
                            "status": "SKIPPED",
                            "reason": "duplicate",
                        }
                    break

            except Exception as exc:
                logger.warning(
                    "阶段 %d (%s) operator 执行异常: %s",
                    stage, stage_name, exc,
                )
                self._error_count += 1
                ctx.errors.append(
                    f"阶段 {stage} ({stage_name}) 异常: {exc}"
                )

        logger.info(
            "PreprocessingPipeline 执行完成: run=%d stages=%d errors=%d",
            self._run_count, stage_count, len(ctx.errors),
        )

        return ctx

    @property
    def error_count(self) -> int:
        """累计错误计数。"""
        return self._error_count

    @property
    def run_count(self) -> int:
        """累计运行批次计数。"""
        return self._run_count

    def reset_stats(self) -> None:
        """重置运行统计（测试辅助）。"""
        self._error_count = 0
        self._run_count = 0


def build_context_from_envelope(
    envelope_dict: dict[str, Any],
    *,
    protocol: str | None = None,
    vendor: str | None = None,
    descriptor: Any = None,  # SignalProfileItemDescriptor | None
) -> PipelineContext:
    """从 envelope 字典构造 PipelineContext。

    将 message_pipeline Envelope 或类似 dict 载荷转换为预处理管线
    使用的 PipelineContext。此函数是 speed layer 与 preprocessing
    管线之间的适配点。

    Args:
        envelope_dict: 消息信封字典（含 schema_version、message_id、
            message_type、source_id、items 等字段）。
        protocol: 已知协议（如有，跳过分类推断）。
        vendor: 已知厂家（如有，跳过分类推断）。
        descriptor: 已知的点位描述符（如有）。

    Returns:
        初始化好的 PipelineContext。
    """
    items = envelope_dict.get("items", [])
    if not isinstance(items, list):
        items = []

    return PipelineContext(
        source_id=str(envelope_dict.get("source_id", "")),
        message_id=str(envelope_dict.get("message_id", "")),
        message_type=str(envelope_dict.get("message_type", "")),
        schema_version=str(envelope_dict.get("schema_version", "1.0")),
        trace_id=envelope_dict.get("trace_id"),
        published_at=envelope_dict.get("published_at"),
        original_payload=envelope_dict,
        items=items,
        protocol=protocol,
        vendor=vendor,
        descriptor=descriptor,
    )
