"""speed layer 实时轻处理管线（SP-FR-004）。

speed layer 在消费消息后、写入存储层前，执行最小实时轻处理：
- schema/envelope 校验：验证 schema_version、message_type、items 非空。
- message_id 去重：基于 message_id 的幂等消费（内存 LRU）。
- 质量码透传：quality_code 原样透传，不做额外质量判断。
- observed_at 乱序保护：迟到/乱序数据写入 DLQ 或标记，不阻塞正常流。
- 格式转换：必要时执行最小格式转换（不包含复杂清洗/标准化）。

保持复杂清洗、历史重算和全量标准化归 batch_layer.processing 负责，
speed layer 仅做实时链路中必不可少的轻量校验。

本文件包含：
- EnvelopeValidator: schema/envelope 校验器。
- MessageDeduplicator: message_id 幂等去重器（内存 LRU + 可选 Redis-backed）。
- QualityCodePassThrough: 质量码透传器。
- OutOfOrderGuard: observed_at 乱序保护器。
- LightProcessingPipeline: 轻处理管线编排器（组合上述四个处理器）。
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class EnvelopeValidator:
    """Envelope schema 校验器。

    验证入站 envelope 的 schema_version、message_type、items 基本结构和
    必要字段完整性。不通过校验的消息应直接 DLQ。

    校验规则：
    - schema_version 必须存在且格式正确（类似 MAJOR.MINOR）。
    - message_type 必须为非空字符串。
    - items 必须为非空列表。
    - source_id 必须为非空字符串。

    Attributes:
        _max_errors: 单批次最大错误计数，超过后停止校验。
        _allowed_types: 允许的 message_type 白名单（None 表示不限制）。
    """

    def __init__(
        self,
        *,
        max_errors: int = 100,
        allowed_types: list[str] | None = None,
    ) -> None:
        """初始化 envelope 校验器。

        Args:
            max_errors: 单批次最大错误计数。
            allowed_types: 允许的 message_type 白名单，None 表示不限制。
        """
        self._max_errors = max_errors
        self._allowed_types = allowed_types
        self._error_count = 0

    def validate(self, envelope: dict[str, Any]) -> tuple[bool, str | None]:
        """验证单条 envelope 的 schema 合规性。

        检查 schema_version、message_type、items、source_id 的必要性。
        不通过的 envelope 应被路由到 DLQ。

        Args:
            envelope: 消息信封的序列化字典。

        Returns:
            (是否通过, 失败原因)。通过时失败原因为 None。
        """
        errors: list[str] = []

        # schema_version 校验
        schema_version = envelope.get("schema_version", "")
        if not schema_version or not isinstance(schema_version, str):
            errors.append("schema_version 缺失或非字符串")
        elif "." not in str(schema_version):
            errors.append(f"schema_version 格式无效: {schema_version}")

        # message_type 校验
        message_type = envelope.get("message_type", "")
        if not message_type or not isinstance(message_type, str):
            errors.append("message_type 缺失或非字符串")

        # message_type 白名单
        if self._allowed_types is not None:
            if message_type not in self._allowed_types:
                errors.append(
                    f"message_type={message_type} 不在白名单中"
                )

        # source_id 校验
        source_id = envelope.get("source_id", "")
        if not source_id or not isinstance(source_id, str):
            errors.append("source_id 缺失或非字符串")

        # items 校验
        items = envelope.get("items", [])
        if not items or not isinstance(items, list):
            errors.append("items 缺失或非列表")
        elif len(items) == 0:
            errors.append("items 为空列表")

        if errors:
            self._error_count += 1
            reason = "; ".join(errors)
            if self._error_count >= self._max_errors:
                logger.error(
                    "EnvelopeValidator 达到最大错误阈值 %d", self._max_errors
                )
            return False, reason

        return True, None

    def reset(self) -> None:
        """重置错误计数器，用于新批次开始。"""
        self._error_count = 0

    @property
    def error_count(self) -> int:
        """当前累计错误数。"""
        return self._error_count


class MessageDeduplicator:
    """message_id 幂等去重器。

    基于 message_id 的 LRU 缓存实现幂等消费。已消费的 message_id 在
    保留窗口内不会被重复处理。窗口外的 message_id 视为新消息。

    支持两种后端：
    - memory: 内存 OrderedDict LRU（默认，适用于单进程）。
    - redis-backed: Redis SET 实现（适用于多进程/多机场景，暂未实现）。

    去重窗口基于消息数量而非时间，避免时间漂移导致的误去重。

    Attributes:
        _seen: LRU 有序字典，记录已消费的 message_id。
        _max_size: LRU 最大容量（最近 N 条消息的去重窗口）。
    """

    def __init__(self, *, max_size: int = 10000) -> None:
        """初始化去重器。

        Args:
            max_size: LRU 最大容量，超过后淘汰最早的记录。
        """
        self._seen: OrderedDict[str, bool] = OrderedDict()
        """LRU 有序字典：message_id → True。"""
        self._max_size = max_size
        self._duplicate_count = 0
        self._total_checked = 0

    def is_duplicate(self, message_id: str) -> bool:
        """检查 message_id 是否已消费。

        如果是新消息，记录到 LRU。如果已存在，返回 True。
        LRU 容量超过 max_size 时，淘汰最旧的记录。

        Args:
            message_id: 消息唯一标识。

        Returns:
            True 表示消息已消费（应跳过），False 表示新消息（可处理）。
        """
        self._total_checked += 1
        if message_id in self._seen:
            self._duplicate_count += 1
            # 将已有记录移至末尾（LRU 策略）
            self._seen.move_to_end(message_id)
            return True

        # 新消息：添加到 LRU
        self._seen[message_id] = True
        # 超出容量时淘汰最旧记录
        if len(self._seen) > self._max_size:
            self._seen.popitem(last=False)
        return False

    def reset(self) -> None:
        """清空 LRU 缓存和计数器。"""
        self._seen.clear()
        self._duplicate_count = 0
        self._total_checked = 0

    @property
    def duplicate_count(self) -> int:
        """已拦截的重复消息数。"""
        return self._duplicate_count

    @property
    def total_checked(self) -> int:
        """已检查的消息总数（含重复）。"""
        return self._total_checked

    @property
    def cache_size(self) -> int:
        """当前 LRU 缓存中的 message_id 数量。"""
        return len(self._seen)


class QualityCodePassThrough:
    """质量码透传器。

    将 source 上报的 quality_code 原样透传到标准化层和 serving cache。
    不做质量判断或转换，不做异常分类。质量码的解释和判断由下游消费方
    或 batch layer 的质量处理阶段完成。

    透传规则：
    - quality_code 为 None 或缺失时，透传默认值 "0"（正常）。
    - 仅验证 quality_code 是否为合法字符串，不做语义解释。

    Attributes:
        _default_quality: 默认质量码（当 source 未上报时使用）。
    """

    def __init__(self, *, default_quality: str = "0") -> None:
        """初始化质量码透传器。

        Args:
            default_quality: 当 item 中无 quality_code 时的默认值。
                "0" 表示正常，"1"-"9" 可供现场自定义。
        """
        self._default_quality = default_quality

    def pass_through(self, item: dict[str, Any]) -> str:
        """从 item 中提取并透传 quality_code。

        如果 item 中无 quality_code 字段或值为空，使用默认值。
        不做任何质量判断或转换。

        Args:
            item: 消息载荷中的一个数据项。

        Returns:
            原样 quality_code 字符串。
        """
        quality = item.get("quality_code")
        if quality is None or quality == "":
            return self._default_quality
        return str(quality)


class OutOfOrderGuard:
    """observed_at 乱序保护器。

    检测 state 数据项的 observed_at 时间戳是否早于已知的最大时间戳。
    如果数据乱序到达（新 observed_at < 已记录的最大值），标记为乱序。
    乱序数据不丢弃，而是附加标记后继续透传，由下游决定处理策略。

    保护策略：
    - 按 (node_key, variable_key) 维护最大 observed_at。
    - 新 observed_at >= 最大值 → 正常通过，更新最大值。
    - 新 observed_at < 最大值 → 标记乱序，仍透传（不丢弃）。

    乱序数据不阻塞正常流。如果数据长时间乱序（超出 tolerance_seconds），
    可配置写入 DLQ。

    Attributes:
        _max_timestamps: (node_key, variable_key) → max observed_at 映射。
        _tolerance: 乱序容忍秒数，超出后写入 DLQ。
        _out_of_order_count: 乱序数据计数。
        _total_count: 处理总数。
    """

    def __init__(self, *, tolerance_seconds: int = 60) -> None:
        """初始化乱序保护器。

        Args:
            tolerance_seconds: 乱序容忍秒数。新数据早于最大值但差异在
                此范围内时，视为可容忍的轻微乱序（网络重传），不做 DLQ。
                超出范围时标记为严重乱序，应写入 DLQ。
        """
        self._max_timestamps: dict[tuple[str, str], datetime] = {}
        """已记录的最大 observed_at 时间戳映射。"""
        self._tolerance = tolerance_seconds
        self._out_of_order_count = 0
        self._total_count = 0

    def check(
        self,
        node_key: str,
        variable_key: str,
        observed_at: datetime | str | None,
    ) -> tuple[bool, bool]:
        """检查 observed_at 是否乱序。

        如果 observed_at 为 None，视为正常通过（不维护无时间戳数据的状态）。
        如果新 observed_at 早于已记录最大值，标记乱序。
        如果差异超出 tolerance，标记应写入 DLQ。

        Args:
            node_key: 节点标识。
            variable_key: 变量标识。
            observed_at: 数据观测时间，None 表示无时间戳（直接放行）。

        Returns:
            (is_out_of_order, should_dlq):
                is_out_of_order: True 表示乱序到达。
                should_dlq: True 表示严重乱序，建议写入 DLQ。
        """
        self._total_count += 1

        if observed_at is None:
            return False, False

        # 解析时间戳
        if isinstance(observed_at, str):
            try:
                obs_dt = datetime.fromisoformat(observed_at)
            except (ValueError, TypeError):
                logger.warning(
                    "observed_at 解析失败: node=%s var=%s val=%s",
                    node_key, variable_key, observed_at,
                )
                return False, False
        elif isinstance(observed_at, datetime):
            obs_dt = observed_at
        else:
            return False, False

        # 确保时区一致性
        if obs_dt.tzinfo is None:
            obs_dt = obs_dt.replace(tzinfo=timezone.utc)

        cache_key = (node_key, variable_key)
        max_obs = self._max_timestamps.get(cache_key)

        if max_obs is None:
            # 首次出现：记录最大值
            self._max_timestamps[cache_key] = obs_dt
            return False, False

        # 比较时间戳
        if obs_dt >= max_obs:
            self._max_timestamps[cache_key] = obs_dt
            return False, False

        # 乱序到达
        self._out_of_order_count += 1
        diff_seconds = (max_obs - obs_dt).total_seconds()

        if diff_seconds > self._tolerance:
            logger.warning(
                "严重乱序: node=%s var=%s observed_at=%s max=%s diff=%.1fs",
                node_key, variable_key,
                obs_dt.isoformat(), max_obs.isoformat(), diff_seconds,
            )
            return True, True  # 乱序 + 建议 DLQ
        else:
            logger.debug(
                "轻微乱序: node=%s var=%s observed_at=%s max=%s diff=%.1fs",
                node_key, variable_key,
                obs_dt.isoformat(), max_obs.isoformat(), diff_seconds,
            )
            return True, False  # 乱序但可容忍

    def reset(self) -> None:
        """清空状态和计数器。"""
        self._max_timestamps.clear()
        self._out_of_order_count = 0
        self._total_count = 0

    @property
    def out_of_order_count(self) -> int:
        """乱序数据计数。"""
        return self._out_of_order_count

    @property
    def total_count(self) -> int:
        """处理总数（含乱序）。"""
        return self._total_count


class LightProcessingPipeline:
    """实时轻处理管线编排器。

    将 EnvelopeValidator、MessageDeduplicator、QualityCodePassThrough、
    OutOfOrderGuard 组合为一个完整的轻处理流程。

    处理流程：
    1. Envelope 校验 → 失败直接 DLQ。
    2. message_id 去重 → 重复跳过。
    3. 对每个 item 执行质量码透传和乱序保护。
    4. 标记严重乱序的 item 供上游决定是否 DLQ。

    保持复杂清洗和标准化归 batch_layer.processing 负责。

    Attributes:
        _validator: envelope 校验器。
        _deduplicator: 消息去重器。
        _quality: 质量码透传器。
        _out_of_order: 乱序保护器。
    """

    def __init__(
        self,
        *,
        dedup_size: int = 10000,
        ooo_tolerance_seconds: int = 60,
        allowed_message_types: list[str] | None = None,
    ) -> None:
        """初始化轻处理管线。

        Args:
            dedup_size: 去重 LRU 容量。
            ooo_tolerance_seconds: 乱序容忍秒数。
            allowed_message_types: 允许的消息类型白名单（用于校验器）。
        """
        self._validator = EnvelopeValidator(
            allowed_types=allowed_message_types,
        )
        self._deduplicator = MessageDeduplicator(max_size=dedup_size)
        self._quality = QualityCodePassThrough()
        self._out_of_order = OutOfOrderGuard(
            tolerance_seconds=ooo_tolerance_seconds,
        )

    def process(self, envelope: dict[str, Any]) -> dict[str, Any]:
        """对单条 envelope 执行完整轻处理流程。

        处理结果通过返回值中的标记字段表达：
        - "validated": bool — 是否通过 schema 校验。
        - "duplicate": bool — 是否为重复消息。
        - "items_enhanced": list[dict] — 增强后的 items（含透传的质量码）。
        - "out_of_order_items": list[dict] — 检测到乱序的 item 列表。
        - "dlq_items": list[dict] — 应写入 DLQ 的 item（严重乱序）。
        - "skipped": bool — 是否应跳过后续处理（校验失败或重复）。

        Args:
            envelope: 消息信封的序列化字典。

        Returns:
            处理结果字典，包含所有标记字段。
        """
        result: dict[str, Any] = {
            "validated": False,
            "duplicate": False,
            "items_enhanced": [],
            "out_of_order_items": [],
            "dlq_items": [],
            "skipped": True,
            "envelope": envelope,
        }

        # 1. Schema 校验
        passed, error = self._validator.validate(envelope)
        if not passed:
            result["validation_error"] = error
            return result
        result["validated"] = True

        # 2. message_id 去重
        message_id = str(envelope.get("message_id", ""))
        if self._deduplicator.is_duplicate(message_id):
            result["duplicate"] = True
            return result

        result["duplicate"] = False
        result["skipped"] = False

        # 3. 处理每个 item：质量码透传 + 乱序保护
        items = envelope.get("items", [])
        enhanced_items: list[dict[str, Any]] = []
        out_of_order_items: list[dict[str, Any]] = []
        dlq_items: list[dict[str, Any]] = []

        source_id = str(envelope.get("source_id", ""))

        for item in items:
            if not isinstance(item, dict):
                continue

            enhanced = dict(item)

            # 质量码透传
            enhanced["quality_code"] = self._quality.pass_through(item)

            # 乱序保护
            node_key = str(
                item.get("node_key")
                or item.get("device_id")
                or item.get("device_code")
                or source_id
            )
            variable_key = str(item.get("variable_key", ""))
            observed_at = item.get("source_observed_at")

            is_ooo, should_dlq = self._out_of_order.check(
                node_key, variable_key, observed_at,
            )
            if is_ooo:
                enhanced["_out_of_order"] = True
                out_of_order_items.append(enhanced)
                if should_dlq:
                    enhanced["_should_dlq"] = True
                    dlq_items.append(enhanced)

            enhanced_items.append(enhanced)

        result["items_enhanced"] = enhanced_items
        result["out_of_order_items"] = out_of_order_items
        result["dlq_items"] = dlq_items

        return result

    def reset(self) -> None:
        """重置所有处理器的内部状态。

        用于批次开始时清除计数器，便于按批次统计。
        注意：MessageDeduplicator 不重置（跨批次去重）。
        """
        self._validator.reset()
        self._out_of_order.reset()

    @property
    def validator(self) -> EnvelopeValidator:
        """返回校验器实例，用于外部读取统计。"""
        return self._validator

    @property
    def deduplicator(self) -> MessageDeduplicator:
        """返回去重器实例，用于外部读取统计。"""
        return self._deduplicator

    @property
    def out_of_order_guard(self) -> OutOfOrderGuard:
        """返回乱序保护器实例，用于外部读取统计。"""
        return self._out_of_order
