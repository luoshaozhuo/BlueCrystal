"""speed layer 预处理 Operator / Strategy Registry。

提供固定 10 阶段 pipeline 的 operator 注册、选择和降级机制。
Registry 只管理阶段到 operator 的映射关系，不编排阶段顺序。
阶段顺序由 PreprocessingPipeline 固定。

选择条件支持：
- payload_type: JSON / BINARY / SCALAR / PROTOBUF
- protocol: OPC_UA / MODBUS / IEC104 / IEC101 / IEC61850 / MQTT / HTTP_REST / BECKHOFF_ADS
- vendor: STANDARD / VendorA / VendorB / 等
- signal_profile_item: 按 descriptor_key 匹配描述符
- default: 最低优先级兜底

选择策略：按条件匹配得分，得分最高者胜出。同分时按注册顺序（先注册优先）。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from whale.speed_layer.preprocessing.models import PipelineContext

logger = logging.getLogger(__name__)


class StageOperator(Protocol):
    """Stage operator 协议。

    每个 pipeline 阶段的可替换 operator 必须实现此协议。
    operator 从 PipelineContext 读取输入，处理后写回 context。

    Raises:
        实现方应在内部捕获异常并写入 context.errors，不向上层抛出。
    """

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """执行阶段处理逻辑。

        Args:
            ctx: 当前 pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文。
        """
        ...


@dataclass
class RegistryCondition:
    """operator 注册时的匹配条件。

    所有条件均为可选，设 None 表示不参与该维度匹配。
    多个条件同时设置时，每条命中增加对应权重。

    Attributes:
        payload_type: 载荷类型条件。
        protocol: 协议条件。
        vendor: 厂家条件。
        descriptor_key: 描述符键条件（精确匹配）。
    """

    payload_type: str | None = None
    """载荷类型。"""
    protocol: str | None = None
    """协议。"""
    vendor: str | None = None
    """厂家。"""
    descriptor_key: str | None = None
    """描述符键（精确匹配）。"""

    def is_default(self) -> bool:
        """判断是否为默认兜底条件（所有字段均为 None）。

        Returns:
            True 表示无任何条件限制，作为 fallback 使用。
        """
        return (
            self.payload_type is None
            and self.protocol is None
            and self.vendor is None
            and self.descriptor_key is None
        )


class OperatorRegistry:
    """Operator 注册表。

    按 pipeline 阶段（1-10）组织 operator 注册条目，支持按 conditions 匹配
    选择最适合的 operator。每个阶段可注册多个 operator，运行时按 condition
    score 降序选择。

    匹配规则（按优先级/权重）：
    - descriptor_key 精确匹配：权重 30（最高优先级，点位级定制）。
    - protocol 匹配：权重 20。
    - payload_type 匹配：权重 10。
    - vendor 匹配：权重 5。
    - default（无条件）：权重 0（兜底）。

    Attributes:
        _entries: 阶段号到 operator 注册条目列表的映射。
           每条条目为 (operator, condition, score)。
    """

    def __init__(self) -> None:
        """初始化空的 operator 注册表。"""
        self._entries: dict[int, list[tuple[StageOperator, RegistryCondition]]] = {}
        """阶段号到注册条目列表的映射。"""

    def register(
        self,
        stage: int,
        operator: StageOperator,
        *,
        payload_type: str | None = None,
        protocol: str | None = None,
        vendor: str | None = None,
        descriptor_key: str | None = None,
    ) -> None:
        """在指定阶段注册一个 operator。

        按条件注册，支持多维度匹配。默认 operator 应最后注册（最低优先级）。
        同一阶段允许注册多个 operator，运行时按条件得分选择。

        Args:
            stage: pipeline 阶段序号（1-10）。
            operator: 阶段 operator 实例。
            payload_type: 载荷类型条件。
            protocol: 协议条件。
            vendor: 厂家条件。
            descriptor_key: 描述符键条件。
        """
        condition = RegistryCondition(
            payload_type=payload_type,
            protocol=protocol,
            vendor=vendor,
            descriptor_key=descriptor_key,
        )
        if stage not in self._entries:
            self._entries[stage] = []
        self._entries[stage].append((operator, condition))
        logger.debug(
            "operator 已注册: stage=%d payload_type=%s protocol=%s vendor=%s key=%s",
            stage, payload_type, protocol, vendor, descriptor_key,
        )

    def select(self, stage: int, ctx: PipelineContext) -> StageOperator:
        """根据上下文选择最适合当前阶段和数据的 operator。

        按条件得分降序选择：descriptor_key 精确匹配 > protocol > payload_type >
        vendor > default。同分时按注册顺序优先。

        Args:
            stage: pipeline 阶段序号（1-10）。
            ctx: 当前 pipeline 上下文（用于条件匹配）。

        Returns:
            选中的 operator 实例。

        Raises:
            KeyError: 指定阶段无任何注册 operator。
        """
        entries = self._entries.get(stage)
        if not entries:
            raise KeyError(
                f"阶段 {stage} 无已注册 operator，请先注册至少一个 operator"
            )

        best_score = -1
        best_operator: StageOperator | None = None

        for operator, condition in entries:
            score = self._compute_score(condition, ctx)
            if score > best_score:
                best_score = score
                best_operator = operator

        if best_operator is None:
            raise KeyError(
                f"阶段 {stage} 无法选择 operator（内部错误，best_operator 为 None）"
            )

        logger.debug(
            "operator 已选择: stage=%d payload_type=%s protocol=%s vendor=%s score=%d",
            stage, ctx.payload_type, ctx.protocol, ctx.vendor, best_score,
        )
        return best_operator

    @staticmethod
    def _compute_score(
        condition: RegistryCondition, ctx: PipelineContext
    ) -> int:
        """计算条件与上下文的匹配得分。

        权重设计：
        - descriptor_key 精确匹配：30（点位级定制最高优先级）
        - protocol 匹配：20
        - payload_type 匹配：10
        - vendor 匹配：5
        - default：0

        Args:
            condition: 注册条件。
            ctx: pipeline 上下文。

        Returns:
            匹配得分，0 表示 default fallback。
        """
        score = 0

        # descriptor_key 精确匹配：最高优先级
        if condition.descriptor_key is not None:
            ctx_descriptor = ctx.descriptor
            if ctx_descriptor is not None:
                if condition.descriptor_key == ctx_descriptor.descriptor_key:
                    score += 30
                else:
                    # 描述符不匹配时返回 -1，完全不匹配
                    return -1

        # protocol 匹配
        if condition.protocol is not None:
            if condition.protocol == (ctx.protocol or ""):
                score += 20

        # payload_type 匹配
        if condition.payload_type is not None:
            if condition.payload_type == (ctx.payload_type or ""):
                score += 10

        # vendor 匹配
        if condition.vendor is not None:
            if condition.vendor == (ctx.vendor or ""):
                score += 5

        return score

    def get_registered_stages(self) -> list[int]:
        """返回已注册 operator 的阶段列表。

        Returns:
            已注册的阶段序号列表（升序）。
        """
        return sorted(self._entries.keys())

    def clear(self) -> None:
        """清空所有注册条目（测试辅助）。"""
        self._entries.clear()
