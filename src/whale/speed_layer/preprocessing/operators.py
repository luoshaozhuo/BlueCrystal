"""speed layer 预处理 Operator 实现。

实现固定 10 阶段 pipeline 的所有基础 operator，每个 operator 返回更新后的
PipelineContext，不抛异常到 pipeline 编排层。错误记录在 ctx.errors 中。

Operator 清单（对应 10 阶段）：
1. PayloadClassifierAdapter: 分类并适配载荷。
2. JsonScalarDecoder / BinaryDecoderStub: 解码载荷。
3. SignalResolver: 解析信号到描述符。
4. TimestampNormalizer: 标准化时间戳。
5. ValueNormalizer: 标准化值。
6. QualityEvaluator: 评估质量。
7. DeduplicateOrderGuard: 去重与乱序保护。
8. LightDerivation: 轻量派生。
9. StandardizedWriterOperator: 写入标准化层。
10. StateViewUpdater: 更新状态视图。
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import struct
from datetime import datetime, timedelta, timezone
from typing import Any, TypeVar

from whale.speed_layer.light_processor import MessageDeduplicator, OutOfOrderGuard
from whale.speed_layer.preprocessing.models import (
    DecodedSignal,
    PipelineContext,
    ResolvedSignal,
    SignalProfileItemDescriptor,
    StandardizedPointValue,
)
from whale.storage.serving_cache import ServingCachePort
from whale.storage.standardized import StandardizedTimeSeriesSinkPort

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


def _run_async(coro: Any) -> Any:
    """在同步和异步上下文中安全运行 async 协程。

    pipeline operator 的 execute() 方法是同步的，但 sink（如
    StandardizedTimeSeriesSinkPort、ServingCachePort）的方法是异步的。
    此函数桥接两种调用模式：
    - 无运行中的 event loop 时：使用 asyncio.run()。
    - 有运行中的 event loop 时（如 pytest-asyncio 上下文）：
      在新线程的独立 event loop 中运行。

    注意：此桥接模式仅用于轻量内存 sink。生产环境中的外部 I/O sink
    （TDengine、Redis）应在 pipeline 的异步 runner 中通过原生 async/await
    调用，不使用此函数。

    Args:
        coro: 要运行的协程。

    Returns:
        协程的返回值。
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # 无运行中的 loop，直接使用 asyncio.run()
        return asyncio.run(coro)

    # 有运行中的 loop，在新线程中创建独立 event loop 运行协程
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


# ── 辅助转换工具 ──────────────────────────────────────────────────────────────


def _safe_float(value: Any, default: float = 1.0) -> float:
    """安全地将值转换为 float。

    Args:
        value: 待转换的值。
        default: 转换失败时的默认值。

    Returns:
        float 值。
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    """安全地将值转换为 int。

    Args:
        value: 待转换的值。
        default: 转换失败时的默认值。

    Returns:
        int 值。
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_iso_timestamp(value: Any) -> str:
    """安全地将值转换为 UTC ISO 时间戳字符串。

    支持 datetime 对象和 ISO 格式字符串输入。转换失败返回当前 UTC 时间。

    Args:
        value: datetime 对象或 ISO 字符串。

    Returns:
        UTC ISO 格式时间戳字符串。
    """
    if value is None:
        return datetime.now(tz=timezone.utc).isoformat()
    if isinstance(value, datetime):
        dt: datetime = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except (ValueError, TypeError):
            pass
    return datetime.now(tz=timezone.utc).isoformat()


# ── 阶段 1: PayloadClassifierAdapter ──────────────────────────────────────────


class PayloadClassifierAdapter:
    """Payload 分类与适配 operator（阶段 1）。

    根据载荷内容判断 payload_type、protocol、vendor 并填充到 PipelineContext。
    支持 dict payload（通用 JSON state item）和 bytes payload（二进制协议）。

    分类规则：
    - bytes 类型载荷 → payload_type="BINARY"，protocol 从 ctx 已有字段获取。
    - dict 类型载荷 → payload_type="JSON"，protocol 从 item 字段推断。
    - 无法分类 → payload_type="UNKNOWN"，记录错误。

    不负责：
    - 载荷本身的结构化解析（由阶段 2 decoder 负责）。
    """

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """对载荷进行分类和适配。

        分析 ctx.original_payload 类型，设置 payload_type、protocol、vendor。
        如果 ctx 已有 protocol 和 vendor，则保留已有值。

        Args:
            ctx: pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文。
        """
        try:
            payload = ctx.original_payload

            if isinstance(payload, bytes):
                ctx.payload_type = ctx.payload_type or "BINARY"
            elif isinstance(payload, dict):
                ctx.payload_type = ctx.payload_type or "JSON"
                # 从载荷字典中推断协议
                if not ctx.protocol:
                    ctx.protocol = payload.get("protocol") or payload.get(
                        "_protocol"
                    )
                if not ctx.vendor:
                    ctx.vendor = payload.get("vendor") or payload.get("_vendor")
            elif isinstance(payload, (int, float, str, bool)):
                ctx.payload_type = ctx.payload_type or "SCALAR"
            else:
                ctx.payload_type = "UNKNOWN"
                ctx.errors.append(
                    f"无法分类的载荷类型: {type(payload).__name__}"
                )

            # 确保 items 填充
            if isinstance(payload, dict) and not ctx.items:
                items = payload.get("items", [])
                if isinstance(items, list):
                    ctx.items = items

            ctx.stage_results["1_classify"] = {
                "status": "OK",
                "payload_type": ctx.payload_type,
                "protocol": ctx.protocol,
            }
        except Exception as exc:
            ctx.errors.append(f"Payload 分类失败: {exc}")
            ctx.payload_type = "ERROR"
            ctx.stage_results["1_classify"] = {"status": "ERROR", "error": str(exc)}

        return ctx


# ── 阶段 2: JsonScalarDecoder ─────────────────────────────────────────────────


class JsonScalarDecoder:
    """JSON / Scalar 解码 operator（阶段 2）。

    从 dict payload 的 items 中逐条提取 DecodedSignal。
    每条 item 提取 variable_key、value（含 quality_code 和 source_observed_at）。
    适用于 JSON 格式的 state item。

    解码失败不抛异常，记录 decode_status=DECODE_ERROR。
    """

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """将 dict items 解码为 DecodedSignal 列表。

        遍历 ctx.items，将每条 item 的 variable_key、value、source_observed_at、
        quality_code 提取为 DecodedSignal。

        Args:
            ctx: pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文（ctx.decoded_signals 已填充）。
        """
        try:
            decoded: list[DecodedSignal] = []
            for item in ctx.items:
                if not isinstance(item, dict):
                    continue

                variable_key = str(item.get("variable_key", ""))
                descriptor_key = item.get(
                    "_descriptor_key"
                ) or item.get(
                    "descriptor_key"
                ) or variable_key

                signal = DecodedSignal(
                    descriptor_key=str(descriptor_key),
                    variable_key=variable_key,
                    raw_value=item.get("value"),
                    source_timestamp=(
                        item.get("source_observed_at")
                        or item.get("observed_at")
                    ),
                    quality_code=str(
                        item.get("quality_code", "0")
                    ),
                    decode_status="SUCCESS",
                )
                decoded.append(signal)

            ctx.decoded_signals = decoded
            ctx.stage_results["2_decode"] = {
                "status": "OK",
                "decoded_count": len(decoded),
                "decoder": "JsonScalarDecoder",
            }
        except Exception as exc:
            ctx.errors.append(f"JSON 解码失败: {exc}")
            ctx.stage_results["2_decode"] = {"status": "ERROR", "error": str(exc)}

        return ctx


# ── 阶段 2: BinaryDecoderStub ─────────────────────────────────────────────────


class BinaryDecoderStub:
    """二进制解码 stub operator（阶段 2）。

    根据 SignalProfileItemDescriptor 的 byte_length / data_type / endian /
    scale / offset 从 bytes payload 解码一个或多个 DecodedSignal。

    Round A 只做开发期验证，不接文件系统 watcher。支持的基础类型：
    - INT16 (2 bytes, struct 'h' / 'H')
    - INT32 (4 bytes, struct 'i' / 'I')
    - FLOAT32 (4 bytes, struct 'f')
    - FLOAT64 (8 bytes, struct 'd')
    - BOOLEAN (1 byte, struct '?')

    解码失败时标记 decode_status=DECODE_ERROR 并记录 decode_error。
    """

    # 数据类型到 struct format 和字节数映射
    _TYPE_MAP: dict[str, tuple[str, int, bool]] = {
        # (format_char, byte_length, is_signed)
        "INT16": ("h", 2, True),
        "UINT16": ("H", 2, False),
        "INT32": ("i", 4, True),
        "UINT32": ("I", 4, False),
        "INT64": ("q", 8, True),
        "UINT64": ("Q", 8, False),
        "FLOAT32": ("f", 4, False),
        "FLOAT64": ("d", 8, False),
        "BOOLEAN": ("?", 1, False),
        "INT8": ("b", 1, True),
        "UINT8": ("B", 1, False),
        "INT16_BE": ("h", 2, True),
        "UINT16_BE": ("H", 2, False),
        "INT32_BE": ("i", 4, True),
        "UINT32_BE": ("I", 4, False),
        "FLOAT32_BE": ("f", 4, False),
        "FLOAT64_BE": ("d", 8, False),
    }

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """从 bytes payload 解码二进制信号。

        根据 ctx.descriptor 的 byte_length / data_type / endian 解析 bytes。
        如果 descriptor 为 None，尝试从 ctx.items 中每条 item 的 item-level
        描述信息解码。

        Args:
            ctx: pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文（ctx.decoded_signals 已填充）。
        """
        try:
            payload = ctx.original_payload
            if not isinstance(payload, bytes):
                ctx.errors.append(
                    "BinaryDecoderStub 要求 bytes payload，"
                    f"实际类型为 {type(payload).__name__}"
                )
                ctx.stage_results["2_decode"] = {
                    "status": "ERROR",
                    "error": "非 bytes 载荷",
                }
                return ctx

            decoded: list[DecodedSignal] = []

            desc = ctx.descriptor
            if desc is not None:
                signal = self._decode_single(payload, desc)
                decoded.append(signal)
            else:
                # 无 descriptor 时尝试解析整段 bytes 为单个信号
                signal = self._decode_raw_bytes(
                    payload,
                    variable_key="raw",
                    descriptor_key="raw",
                )
                decoded.append(signal)
                if signal.decode_status == "DECODE_ERROR":
                    ctx.errors.append(
                        f"二进制解码失败（无描述符）: {signal.decode_error}"
                    )

            ctx.decoded_signals = decoded
            ctx.stage_results["2_decode"] = {
                "status": "OK" if all(
                    s.decode_status == "SUCCESS" for s in decoded
                ) else "PARTIAL",
                "decoded_count": len(decoded),
                "error_count": sum(
                    1 for s in decoded if s.decode_status == "DECODE_ERROR"
                ),
                "decoder": "BinaryDecoderStub",
            }
        except Exception as exc:
            ctx.errors.append(f"二进制解码异常: {exc}")
            ctx.stage_results["2_decode"] = {"status": "ERROR", "error": str(exc)}

        return ctx

    def _decode_single(
        self, data: bytes, desc: SignalProfileItemDescriptor
    ) -> DecodedSignal:
        """根据描述符从 bytes 中解码单个信号。

        支持指定 byte_length / data_type / endian 解析，应用 scale 和 offset。

        Args:
            data: 原始 bytes 载荷。
            desc: 点位描述符。

        Returns:
            解码后的信号。
        """
        byte_length = desc.byte_length or len(data)
        endian = desc.endian or "BIG_ENDIAN"
        data_type = desc.data_type.upper()

        # 检查数据长度
        if len(data) < byte_length:
            return DecodedSignal(
                descriptor_key=desc.descriptor_key,
                variable_key=desc.variable_key,
                decode_status="DECODE_ERROR",
                decode_error=(
                    f"数据长度不足: need {byte_length} bytes, "
                    f"got {len(data)} bytes"
                ),
            )

        slice_data = data[:byte_length]

        # 确定字节序前缀
        prefix = ">" if endian.upper() == "BIG_ENDIAN" else "<"

        # 解析值
        try:
            raw_value: Any = None
            decoded_status = "SUCCESS"
            decoded_error: str | None = None

            if data_type in ("FLOAT32", "FLOAT64", "FLOAT32_BE", "FLOAT64_BE"):
                # 浮点类型
                fmt_char, _, _ = self._TYPE_MAP.get(data_type, ("d", 8, False))
                fmt = f"{prefix}{fmt_char}"
                raw_value = struct.unpack(fmt, slice_data)[0]
            elif data_type == "BOOLEAN":
                raw_value = bool(slice_data[0])
            elif data_type == "STRING":
                # 字符串：直接按 bytes 解码
                try:
                    raw_value = slice_data.decode("utf-8").rstrip("\x00")
                except UnicodeDecodeError:
                    raw_value = slice_data.hex()
                    decoded_status = "DECODE_ERROR"
                    decoded_error = "UTF-8 解码失败，已转为 hex"
            elif data_type in self._TYPE_MAP:
                fmt_char, _, _ = self._TYPE_MAP[data_type]
                fmt = f"{prefix}{fmt_char}"
                raw_value = struct.unpack(fmt, slice_data)[0]
            else:
                # 未知类型：按原始 bytes 处理
                raw_value = list(slice_data)
                decoded_status = "DECODE_ERROR"
                decoded_error = f"未知数据类型: {data_type}"

            # 应用 scale 和 offset
            if isinstance(raw_value, (int, float)) and decoded_status == "SUCCESS":
                scale = desc.default_scale or 1.0
                offset = desc.default_offset or 0.0
                raw_value = raw_value * scale + offset

            return DecodedSignal(
                descriptor_key=desc.descriptor_key,
                variable_key=desc.variable_key,
                raw_value=raw_value,
                decode_status=decoded_status,
                decode_error=decoded_error,
            )
        except (struct.error, ValueError, TypeError) as exc:
            return DecodedSignal(
                descriptor_key=desc.descriptor_key,
                variable_key=desc.variable_key,
                decode_status="DECODE_ERROR",
                decode_error=f"struct 解包失败: {exc}",
            )

    def _decode_raw_bytes(
        self,
        data: bytes,
        variable_key: str,
        descriptor_key: str,
    ) -> DecodedSignal:
        """无描述符时的原始 bytes 解码（兜底路径）。

        尝试按 bytes 的十六进制表示解码，标记为 MISSING 状态。

        Args:
            data: 原始 bytes 载荷。
            variable_key: 变量标识。
            descriptor_key: 描述符键。

        Returns:
            解码后的信号。
        """
        return DecodedSignal(
            descriptor_key=descriptor_key,
            variable_key=variable_key,
            raw_value=data.hex(),
            decode_status="MISSING",
            decode_error="无描述符可用，按 hex 存储",
        )


# ── 阶段 3: SignalResolver ────────────────────────────────────────────────────


class SignalResolver:
    """信号解析 operator（阶段 3）。

    将 DecodedSignal 按 descriptor_key / variable_key / relative_path /
    profile_item_id 映射到 SignalProfileItemDescriptor，生成 ResolvedSignal。

    解析策略：
    - 按 descriptor_key 精确匹配（优先级最高）。
    - 按 variable_key 匹配。
    - 匹配失败标记 UNRESOLVED，不中断管道。

    依赖 descriptor_registry（外部注入的映射表）：
        {descriptor_key: SignalProfileItemDescriptor}

    不负责：
    - 方案描述符本身的管理（由持久化层负责）。
    """

    def __init__(
        self,
        descriptor_registry: dict[str, SignalProfileItemDescriptor] | None = None,
    ) -> None:
        """初始化信号解析器。

        Args:
            descriptor_registry: 描述符键到描述符对象的映射表。
                None 表示使用空的 registry（解析全部为 UNRESOLVED）。
        """
        self._registry: dict[str, SignalProfileItemDescriptor] = (
            descriptor_registry or {}
        )

    def set_registry(
        self, registry: dict[str, SignalProfileItemDescriptor]
    ) -> None:
        """设置或更新描述符注册表。

        Args:
            registry: 描述符键到描述符对象的映射表。
        """
        self._registry = registry

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """将 DecodedSignal 解析为 ResolvedSignal。

        按 descriptor_key → variable_key → 失败 的顺序尝试匹配。

        Args:
            ctx: pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文（ctx.resolved_signals 已填充）。
        """
        try:
            resolved: list[ResolvedSignal] = []
            for signal in ctx.decoded_signals:
                desc = self._resolve_descriptor(signal)
                if desc is not None:
                    resolved.append(
                        ResolvedSignal(
                            descriptor=desc,
                            decoded=signal,
                            resolve_status="RESOLVED",
                        )
                    )
                else:
                    resolved.append(
                        ResolvedSignal(
                            descriptor=None,
                            decoded=signal,
                            resolve_status="UNRESOLVED",
                        )
                    )

            ctx.resolved_signals = resolved
            resolved_count = sum(
                1 for r in resolved if r.resolve_status == "RESOLVED"
            )
            ctx.stage_results["3_resolve"] = {
                "status": "OK",
                "total": len(resolved),
                "resolved": resolved_count,
                "unresolved": len(resolved) - resolved_count,
            }
        except Exception as exc:
            ctx.errors.append(f"信号解析失败: {exc}")
            ctx.stage_results["3_resolve"] = {"status": "ERROR", "error": str(exc)}

        return ctx

    def _resolve_descriptor(
        self, signal: DecodedSignal
    ) -> SignalProfileItemDescriptor | None:
        """按优先级查找描述符。

        1. descriptor_key 精确匹配。
        2. variable_key 匹配（遍历 registry 查找 variable_key 相同的描述符）。
        3. 全部失败返回 None。

        Args:
            signal: 解码后的信号。

        Returns:
            匹配的描述符，未匹配返回 None。
        """
        # 按 descriptor_key 精确匹配
        desc = self._registry.get(signal.descriptor_key)
        if desc is not None:
            return desc

        # 按 variable_key 匹配
        for candidate in self._registry.values():
            if candidate.variable_key == signal.variable_key:
                return candidate

        return None


# ── 阶段 4: TimestampNormalizer ───────────────────────────────────────────────


class TimestampNormalizer:
    """时间戳标准化 operator（阶段 4）。

    将源端时间戳标准化为 UTC ISO 格式。优先级：
    1. source_observed_at（源端观测时间）。
    2. observed_at（通用观测时间）。
    3. published_at（消息发布时间）。
    4. received_at（消息接收时间，兜底）。

    所有输出时间戳统一为 UTC 时区 ISO 格式字符串。

    不负责：
    - 时间戳的语义校验和业务逻辑（如未来时间、过期时间判定）。
    """

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """标准化所有已解码信号的时间戳。

        遍历 ctx.decoded_signals，为每条信号附加标准化后的时间戳。
        同时设置 ctx 的 published_at 和 received_at。

        Args:
            ctx: pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文。
        """
        try:
            # 确保 received_at 有值
            if not ctx.received_at:
                ctx.received_at = datetime.now(tz=timezone.utc).isoformat()

            # 标准化 published_at
            if ctx.published_at:
                ctx.published_at = _safe_iso_timestamp(ctx.published_at)

            # 为每条 decoded signal 标准化时间戳
            for signal in ctx.decoded_signals:
                # 按优先级选择时间戳来源
                ts = (
                    signal.source_timestamp
                    or ctx.published_at
                    or ctx.received_at
                )
                signal.source_timestamp = _safe_iso_timestamp(ts)

            ctx.stage_results["4_normalize_ts"] = {
                "status": "OK",
                "received_at": ctx.received_at,
                "published_at": ctx.published_at,
            }
        except Exception as exc:
            ctx.errors.append(f"时间戳标准化失败: {exc}")
            ctx.stage_results["4_normalize_ts"] = {
                "status": "ERROR", "error": str(exc)
            }

        return ctx


# ── 阶段 5: ValueNormalizer ───────────────────────────────────────────────────


class ValueNormalizer:
    """值标准化 operator（阶段 5）。

    对每个 ResolvedSignal 执行基础类型转换、scale、offset 和最小可扩展的
    单位转换。

    支持的类型转换：
    - bool: "true"/"1"/1 → True, "false"/"0"/0 → False
    - int: 按 int() 转换，带 scale/offset
    - float: 按 float() 转换，带 scale/offset
    - string: 按 str() 保留

    转换后的值写入 ctx.standardized_values（StandardizedPointValue 列表）。

    不负责：
    - 复杂数值校验（范围、死区、变化率等）。
    - 多步单位换算（Round A 仅支持单步 scale+offset）。
    """

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """对解析后的信号执行值标准化。

        将每个 ResolvedSignal 的 decoded.raw_value 按描述符要求的类型、
        scale、offset 转换为标准化值。

        Args:
            ctx: pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文（ctx.standardized_values 已填充）。
        """
        try:
            standardized: list[StandardizedPointValue] = []
            for resolved in ctx.resolved_signals:
                desc = resolved.descriptor
                signal = resolved.decoded
                raw_value = signal.raw_value

                # 确定目标类型
                target_type = desc.data_type if desc else "STRING"

                # 类型转换
                normalized_value = self._convert_value(raw_value, target_type)

                # 应用 scale / offset（仅对数值类型生效）
                if isinstance(normalized_value, (int, float)):
                    scale = _safe_float(
                        desc.default_scale if desc else None, 1.0
                    )
                    offset = _safe_float(
                        desc.default_offset if desc else None, 0.0
                    )
                    if scale != 1.0 or offset != 0.0:
                        normalized_value = normalized_value * scale + offset

                # 精度处理
                if desc and desc.default_precision is not None:
                    try:
                        normalized_value = round(
                            float(normalized_value), desc.default_precision
                        )
                    except (ValueError, TypeError):
                        pass

                # 构造 StandardizedPointValue
                spv = StandardizedPointValue(
                    node_key=ctx.source_id,
                    variable_key=signal.variable_key,
                    value=normalized_value,
                    value_type=target_type,
                    quality_code=signal.quality_code or "0",
                    observed_at=signal.source_timestamp or ctx.received_at,
                    received_at=ctx.received_at,
                    source_id=ctx.source_id,
                    message_id=ctx.message_id,
                    schema_version=ctx.schema_version,
                )
                standardized.append(spv)

            ctx.standardized_values = standardized
            ctx.stage_results["5_normalize_value"] = {
                "status": "OK",
                "count": len(standardized),
            }
        except Exception as exc:
            ctx.errors.append(f"值标准化失败: {exc}")
            ctx.stage_results["5_normalize_value"] = {
                "status": "ERROR", "error": str(exc)
            }

        return ctx

    @staticmethod
    def _convert_value(value: Any, target_type: str) -> Any:
        """按目标类型转换值。

        支持 BOOLEAN / INT32 / INT64 / FLOAT32 / FLOAT64 / STRING。

        Args:
            value: 原始值。
            target_type: 目标类型名称。

        Returns:
            转换后的值，转换失败返回原始值。
        """
        if value is None:
            return None

        target = target_type.upper()

        try:
            if target in ("BOOLEAN", "BOOL"):
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes")
                if isinstance(value, (int, float)):
                    return bool(value)
                return False

            if target in ("INT32", "INT64", "INT", "INT16", "INT8",
                          "UINT32", "UINT64", "UINT16", "UINT8"):
                if isinstance(value, bool):
                    return int(value)
                return int(float(str(value)))

            if target in ("FLOAT32", "FLOAT64", "FLOAT", "REAL", "LREAL"):
                return float(str(value))

            if target == "STRING":
                return str(value)

            # 未知类型，保留原值
            return value
        except (ValueError, TypeError):
            return value


# ── 阶段 6: QualityEvaluator ──────────────────────────────────────────────────


class QualityEvaluator:
    """质量评估 operator（阶段 6）。

    对每个标准化值评估质量码。评估规则简单可配置：
    - GOOD (0): 解码成功、解析成功、值非空。
    - MISSING_VALUE (1): 值为 None。
    - DECODE_ERROR (2): 解码阶段失败。
    - STALE (3): 时间戳过期（observed_at 早于 cutoff）。
    - OUT_OF_ORDER (4): 乱序检测标记（由阶段 7 设置，此处仅预留）。

    Round A 不做复杂质量规则（如范围检查、梯度异常等）。

    Attributes:
        stale_seconds: stale 判定阈值（秒），observed_at 早于当前时间
            超过此值时标记 STALE。None 表示不启用 stale 检测。
    """

    def __init__(self, *, stale_seconds: int | None = 300) -> None:
        """初始化质量评估器。

        Args:
            stale_seconds: stale 判定阈值（秒）。None 表示不启用 stale 检测。
        """
        self._stale_seconds = stale_seconds

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """评估每个标准化值的质量码。

        更新每个 StandardizedPointValue 的 quality_code。

        Args:
            ctx: pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文。
        """
        try:
            now = datetime.now(tz=timezone.utc)
            cutoff = now - timedelta(seconds=self._stale_seconds) if (
                self._stale_seconds is not None
            ) else None

            for i, spv in enumerate(ctx.standardized_values):
                # 检查对应 decoded signal 的解码状态
                if i < len(ctx.decoded_signals):
                    ds = ctx.decoded_signals[i]
                    if ds.decode_status == "DECODE_ERROR":
                        spv.quality_code = "2"  # DECODE_ERROR
                        continue

                # 检查值是否为空
                if spv.value is None:
                    spv.quality_code = "1"  # MISSING_VALUE
                    continue

                # 检查时间戳是否 stale
                if cutoff is not None:
                    try:
                        obs_dt = datetime.fromisoformat(spv.observed_at)
                        if obs_dt.tzinfo is None:
                            obs_dt = obs_dt.replace(tzinfo=timezone.utc)
                        if obs_dt < cutoff:
                            spv.quality_code = "3"  # STALE
                            continue
                    except (ValueError, TypeError):
                        pass

                # 默认 GOOD
                spv.quality_code = "0"

            # 聚合质量码
            quality_codes = [sv.quality_code for sv in ctx.standardized_values]
            if quality_codes:
                # 最差质量码作为全局质量码
                ctx.quality_code = max(quality_codes, key=lambda x: int(x))

            ctx.stage_results["6_quality"] = {
                "status": "OK",
                "quality_code_distribution": {
                    qc: quality_codes.count(qc) for qc in set(quality_codes)
                },
            }
        except Exception as exc:
            ctx.errors.append(f"质量评估失败: {exc}")
            ctx.stage_results["6_quality"] = {"status": "ERROR", "error": str(exc)}

        return ctx


# ── 阶段 7: DeduplicateOrderGuard ─────────────────────────────────────────────


class DeduplicateOrderGuard:
    """去重与乱序保护 operator（阶段 7）。

    复用 light_processor 中的 MessageDeduplicator 和 OutOfOrderGuard 语义：
    - message_id 去重：基于 LRU 缓存，重复消息标记 is_duplicate。
    - observed_at 乱序保护：按 (node_key, variable_key) 维护最大时间戳，
      乱序数据标记 is_out_of_order 和 should_dlq。

    与 light_processor 的去重器共享相同的 LRU 和乱序容忍策略。

    Attributes:
        deduplicator: message_id 去重器。
        order_guard: observed_at 乱序保护器。
    """

    def __init__(
        self,
        *,
        dedup_size: int = 10000,
        tolerance_seconds: int = 60,
    ) -> None:
        """初始化去重与乱序保护 composite operator。

        Args:
            dedup_size: 去重 LRU 容量。
            tolerance_seconds: 乱序容忍秒数。
        """
        self.deduplicator = MessageDeduplicator(max_size=dedup_size)
        self.order_guard = OutOfOrderGuard(
            tolerance_seconds=tolerance_seconds,
        )

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """执行去重检查和乱序保护。

        1. 检查 message_id 是否重复 → 设置 ctx.is_duplicate。
        2. 对每个标准化值检查 observed_at 是否乱序 → 设置 quality_code。

        Args:
            ctx: pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文。
        """
        try:
            # message_id 去重
            if ctx.message_id and self.deduplicator.is_duplicate(ctx.message_id):
                ctx.is_duplicate = True
                ctx.should_dlq = False  # 重复消息跳过即可，无需 DLQ
                ctx.errors.append(f"重复消息: message_id={ctx.message_id}")
                ctx.stage_results["7_dedup_order"] = {
                    "status": "OK",
                    "is_duplicate": True,
                }
                return ctx

            # 乱序保护：对每个标准化值检查 observed_at
            any_out_of_order = False
            any_should_dlq = False
            for spv in ctx.standardized_values:
                node_key = spv.node_key or ctx.source_id
                variable_key = spv.variable_key
                observed_at = spv.observed_at

                is_ooo, should_dlq = self.order_guard.check(
                    node_key, variable_key, observed_at,
                )
                if is_ooo:
                    any_out_of_order = True
                    if should_dlq:
                        any_should_dlq = True
                        spv.quality_code = "4"  # OUT_OF_ORDER

            ctx.is_out_of_order = any_out_of_order
            ctx.should_dlq = any_should_dlq

            ctx.stage_results["7_dedup_order"] = {
                "status": "OK",
                "is_duplicate": ctx.is_duplicate,
                "is_out_of_order": ctx.is_out_of_order,
                "should_dlq": ctx.should_dlq,
            }
        except Exception as exc:
            ctx.errors.append(f"去重或乱序保护失败: {exc}")
            ctx.stage_results["7_dedup_order"] = {
                "status": "ERROR", "error": str(exc)
            }

        return ctx

    def reset(self) -> None:
        """重置内部状态（测试辅助）。

        仅重置乱序保护器状态，不去重重置去重器（保持跨批次幂等）。
        去重器只在 pipeline 级别管理。
        """
        self.order_guard.reset()


# ── 阶段 8: LightDerivation ───────────────────────────────────────────────────


class LightDerivation:
    """轻量派生 operator（阶段 8）。

    根据当前消息和标准化值的状态，计算简单的派生状态：
    - source_alive: 接收到任何有效（非 DECODE_ERROR）信号时为 True。
    - communication_state: 基于消息新鲜度的通信状态评估。
    - processed_item_count: 处理的信号数量。

    派生结果写入 ctx.derived_states 字典。可配置关闭。

    Attributes:
        enabled: 是否启用派生（默认 True）。
        stale_threshold_seconds: 通信状态判定阈值（秒）。消息的 published_at
            早于此阈值时判定通信异常。
    """

    def __init__(
        self,
        *,
        enabled: bool = True,
        stale_threshold_seconds: int = 300,
    ) -> None:
        """初始化轻量派生 operator。

        Args:
            enabled: 是否启用派生。
            stale_threshold_seconds: 通信状态 stale 判定阈值。
        """
        self.enabled = enabled
        self._stale_threshold = stale_threshold_seconds

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """计算派生状态。

        Args:
            ctx: pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文（ctx.derived_states 已填充）。
        """
        if not self.enabled:
            ctx.stage_results["8_derivation"] = {
                "status": "OK", "enabled": False
            }
            return ctx

        try:
            derived: dict[str, Any] = {}

            # source_alive: 至少有一个有效信号
            valid_count = sum(
                1 for sv in ctx.standardized_values
                if sv.quality_code not in ("2",)  # 非 DECODE_ERROR
            )
            derived["source_alive"] = valid_count > 0

            # communication_state: 基于消息时间戳判断
            if ctx.published_at:
                try:
                    pub_dt = datetime.fromisoformat(ctx.published_at)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                    now = datetime.now(tz=timezone.utc)
                    age_seconds = (now - pub_dt).total_seconds()
                    if age_seconds > self._stale_threshold:
                        derived["communication_state"] = "STALE"
                    else:
                        derived["communication_state"] = "ACTIVE"
                except (ValueError, TypeError):
                    derived["communication_state"] = "UNKNOWN"
            else:
                derived["communication_state"] = "UNKNOWN"

            # 处理统计
            derived["processed_item_count"] = len(ctx.standardized_values)
            derived["error_count"] = len(ctx.errors)
            derived["is_duplicate"] = ctx.is_duplicate
            derived["is_out_of_order"] = ctx.is_out_of_order

            ctx.derived_states = derived
            ctx.stage_results["8_derivation"] = {
                "status": "OK",
                "derived": derived,
            }
        except Exception as exc:
            ctx.errors.append(f"派生状态计算失败: {exc}")
            ctx.stage_results["8_derivation"] = {
                "status": "ERROR", "error": str(exc)
            }

        return ctx


# ── 阶段 9: StandardizedWriterOperator ────────────────────────────────────────


class StandardizedWriterOperator:
    """标准化层写入 operator（阶段 9）。

    将 PipelineContext 中的 StandardizedPointValue 列表写入
    StandardizedTimeSeriesSinkPort（MemoryStandardizedSink 或
    TdengineStandardizedSink）。

    写入失败时记录错误但不抛异常。重复消息和 DLQ 标记的消息跳过写入。

    Attributes:
        _sink: 标准化时序数据 sink 端口。
    """

    def __init__(self, sink: StandardizedTimeSeriesSinkPort) -> None:
        """初始化标准化写入 operator。

        Args:
            sink: 标准化时序数据写入端口。
        """
        self._sink = sink

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """将标准化值写入存储层。

        跳过重复消息。写入失败时记录到 ctx.errors。

        Args:
            ctx: pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文。
        """
        if ctx.is_duplicate:
            ctx.stage_results["9_write_std"] = {
                "status": "SKIPPED",
                "reason": "duplicate",
            }
            return ctx

        try:
            # 将 StandardizedPointValue 转换为 node_states dict 格式
            node_states: list[dict[str, Any]] = []
            for spv in ctx.standardized_values:
                if ctx.should_dlq:
                    # DLQ 标记的消息仍写入（DLQ 由 pipeline 协调处理）
                    pass
                state = {
                    "source_id": spv.source_id,
                    "node_key": spv.node_key,
                    "variable_key": spv.variable_key,
                    "value": spv.value,
                    "value_type": spv.value_type,
                    "quality_code": spv.quality_code,
                    "observed_at": spv.observed_at,
                    "received_at": spv.received_at,
                    "message_id": spv.message_id,
                    "schema_version": spv.schema_version,
                }
                node_states.append(state)

            # 写入 sink（使用桥接辅助函数处理 async sink）
            written = _run_async(self._sink.write(node_states))
            ctx.derived_states["_written_count"] = written
            ctx.stage_results["9_write_std"] = {
                "status": "OK",
                "written": written,
            }

        except Exception as exc:
            ctx.errors.append(f"标准化写入失败: {exc}")
            ctx.stage_results["9_write_std"] = {
                "status": "ERROR",
                "error": str(exc),
            }

        return ctx


# ── 阶段 10: StateViewUpdater ─────────────────────────────────────────────────


class StateViewUpdater:
    """Redis 状态视图更新 operator（阶段 10）。

    将标准化值写入 ServingCachePort（InMemoryServingCache 或
    RedisServingCache），供业务侧近实时查询。

    每条标准化值按 "source_id:device_id:variable_key" 格式构造缓存键。
    写入包含乱序时间戳保护（由 ServingCachePort.set() 内部实现）。

    Attributes:
        _cache: serving cache 写入端口。
        _default_ttl: 默认 TTL 秒数。
    """

    def __init__(
        self,
        cache: ServingCachePort,
        *,
        default_ttl: int = 60,
    ) -> None:
        """初始化状态视图更新 operator。

        Args:
            cache: serving cache 写入端口。
            default_ttl: 默认 TTL 秒数。
        """
        self._cache = cache
        self._default_ttl = default_ttl

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """将标准化值更新到状态视图缓存。

        跳过重复消息。为每个标准化值构造 StateViewRecord 并写入缓存。

        Args:
            ctx: pipeline 上下文。

        Returns:
            更新后的 pipeline 上下文。
        """
        if ctx.is_duplicate:
            ctx.stage_results["10_update_cache"] = {
                "status": "SKIPPED",
                "reason": "duplicate",
            }
            return ctx

        try:
            updated = 0
            for spv in ctx.standardized_values:
                cache_key = (
                    f"{spv.source_id}:{spv.node_key}:{spv.variable_key}"
                )
                cache_value = {
                    "source_id": spv.source_id,
                    "observed_at": spv.observed_at,
                    "value": spv.value,
                    "quality_code": spv.quality_code,
                    "variable_key": spv.variable_key,
                    "message_type": ctx.message_type,
                }
                accepted = _run_async(
                    self._cache.set(
                        cache_key, cache_value, ttl_seconds=self._default_ttl,
                    )
                )
                if accepted:
                    updated += 1

            ctx.derived_states["_cache_updated_count"] = updated
            ctx.stage_results["10_update_cache"] = {
                "status": "OK",
                "updated": updated,
                "total": len(ctx.standardized_values),
            }

        except Exception as exc:
            ctx.errors.append(f"状态视图更新失败: {exc}")
            ctx.stage_results["10_update_cache"] = {
                "status": "ERROR",
                "error": str(exc),
            }

        return ctx
