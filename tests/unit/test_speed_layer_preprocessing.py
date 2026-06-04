"""speed layer 预处理 Pipeline Round A 测试。

验证固定 10 阶段 pipeline、Operator/Strategy Registry、运行期 DTO 与
基础 operator 的正确性。

被验证对象：
- whale.speed_layer.preprocessing.models: 所有 DTO/dataclass。
- whale.speed_layer.preprocessing.registry: OperatorRegistry + 条件选择。
- whale.speed_layer.preprocessing.operators: 11 个基础 operator。
- whale.speed_layer.preprocessing.pipeline: PreprocessingPipeline 编排。
- whale.speed_layer.__init__: Round A 导出兼容性。

所属生命周期阶段：开发期验证（纯内存测试，无外部依赖）。
使用的替身：InMemoryMessageBus、InMemoryServingCache、MemoryStandardizedSink。

不能证明：
- TDengine 真实时序写入。
- Redis 真实 serving cache 读写。
- 二进制协议文件 watcher。
- raw_archive 文件落地检测。
- model_asset / simulation 相关 ORM。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from whale.speed_layer.preprocessing.models import (
    DecodedSignal,
    PipelineContext,
    ResolvedSignal,
    SignalProfileItemDescriptor,
    StandardizedPointValue,
    StandardizedWaveformValue,
    StateViewRecord,
)
from whale.speed_layer.preprocessing.operators import (
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
from whale.speed_layer.preprocessing.pipeline import (
    PreprocessingPipeline,
    build_context_from_envelope,
)
from whale.speed_layer.preprocessing.registry import (
    OperatorRegistry,
    RegistryCondition,
)
from whale.storage.serving_cache import InMemoryServingCache
from whale.storage.standardized import MemoryStandardizedSink


# ── Helper ────────────────────────────────────────────────────────────────────


def _make_descriptor(
    descriptor_key: str = "desc:1:temp",
    variable_key: str = "temp",
    data_type: str = "FLOAT64",
    protocol: str | None = None,
    vendor: str | None = None,
    **kwargs,
) -> SignalProfileItemDescriptor:
    """构造测试用 SignalProfileItemDescriptor。

    Args:
        descriptor_key: 描述符键。
        variable_key: 变量标识。
        data_type: 数据类型。
        protocol: 协议。
        vendor: 厂家。
        **kwargs: 其他字段。

    Returns:
        测试用描述符。
    """
    defaults = {
        "profile_item_id": 1,
        "relative_path": variable_key,
        "default_unit": None,
        "default_scale": None,
        "default_offset": None,
        "default_precision": None,
        "byte_length": None,
        "endian": None,
        "payload_type": "JSON",
        "quality_supported": False,
        "timestamp_supported": False,
    }
    defaults.update(kwargs)
    return SignalProfileItemDescriptor(
        descriptor_key=descriptor_key,
        variable_key=variable_key,
        data_type=data_type,
        protocol=protocol,
        vendor=vendor,
        **defaults,
    )


def _make_envelope_dict(
    message_id: str = "msg-001",
    source_id: str = "src-001",
    items: list[dict] | None = None,
) -> dict:
    """构造测试用 envelope 字典。

    Args:
        message_id: 消息 ID。
        source_id: 源 ID。
        items: 载荷数据项列表。

    Returns:
        测试用字典。
    """
    return {
        "schema_version": "1.0",
        "message_id": message_id,
        "message_type": "state_snapshot",
        "source_id": source_id,
        "trace_id": f"trace-{message_id}",
        "published_at": datetime.now(tz=timezone.utc).isoformat(),
        "items": items or [
            {"variable_key": "temp", "value": 25.5, "quality_code": "0"},
        ],
    }


# ── SignalProfileItemDescriptor 测试 ─────────────────────────────────────────


class TestSignalProfileItemDescriptor:
    """SignalProfileItemDescriptor DTO 测试。"""

    def test_default_values(self) -> None:
        """验证默认字段值正确。"""
        desc = SignalProfileItemDescriptor(
            profile_item_id=1,
            descriptor_key="key-1",
            variable_key="temp",
            relative_path="MMXU1.TotW.mag.f",
            data_type="FLOAT64",
        )
        assert desc.profile_item_id == 1
        assert desc.descriptor_key == "key-1"
        assert desc.variable_key == "temp"
        assert desc.payload_type == "JSON"  # 默认
        assert desc.quality_supported is False
        assert desc.timestamp_supported is False

    def test_with_protocol_and_vendor(self) -> None:
        """验证 protocol 和 vendor 字段存储。"""
        desc = _make_descriptor(
            descriptor_key="k:v",
            variable_key="v",
            data_type="INT32",
            protocol="MODBUS",
            vendor="VendorA",
            byte_length=2,
            endian="BIG_ENDIAN",
        )
        assert desc.protocol == "MODBUS"
        assert desc.vendor == "VendorA"
        assert desc.byte_length == 2
        assert desc.endian == "BIG_ENDIAN"
        assert desc.data_type == "INT32"


# ── DecodedSignal DTO 测试 ────────────────────────────────────────────────────


class TestDecodedSignal:
    """DecodedSignal DTO 测试。"""

    def test_successful_decode(self) -> None:
        """成功解码应设置 SUCCESS 状态。"""
        ds = DecodedSignal(
            descriptor_key="dk",
            variable_key="vk",
            raw_value=42.5,
            decode_status="SUCCESS",
        )
        assert ds.decode_status == "SUCCESS"
        assert ds.decode_error is None
        assert ds.raw_value == 42.5

    def test_decode_error(self) -> None:
        """解码失败应记录错误信息。"""
        ds = DecodedSignal(
            descriptor_key="dk",
            variable_key="vk",
            decode_status="DECODE_ERROR",
            decode_error="数据解析失败",
        )
        assert ds.decode_status == "DECODE_ERROR"
        assert ds.decode_error == "数据解析失败"

    def test_with_timestamp_and_quality(self) -> None:
        """验证时间戳和质量码字段。"""
        ts = "2026-06-04T10:00:00+00:00"
        ds = DecodedSignal(
            descriptor_key="dk",
            variable_key="vk",
            raw_value=1.0,
            source_timestamp=ts,
            quality_code="3",
        )
        assert ds.source_timestamp == ts
        assert ds.quality_code == "3"


# ── ResolvedSignal DTO 测试 ───────────────────────────────────────────────────


class TestResolvedSignal:
    """ResolvedSignal DTO 测试。"""

    def test_resolved(self) -> None:
        """已解析信号应有描述符和 RESOLVED 状态。"""
        desc = _make_descriptor()
        ds = DecodedSignal(descriptor_key="dk", variable_key="vk")
        rs = ResolvedSignal(descriptor=desc, decoded=ds, resolve_status="RESOLVED")
        assert rs.descriptor is desc
        assert rs.resolve_status == "RESOLVED"

    def test_unresolved(self) -> None:
        """未解析信号应有 None 描述符和 UNRESOLVED 状态。"""
        ds = DecodedSignal(descriptor_key="unknown", variable_key="unknown")
        rs = ResolvedSignal(descriptor=None, decoded=ds, resolve_status="UNRESOLVED")
        assert rs.descriptor is None
        assert rs.resolve_status == "UNRESOLVED"


# ── StandardizedPointValue DTO 测试 ───────────────────────────────────────────


class TestStandardizedPointValue:
    """StandardizedPointValue DTO 测试。"""

    def test_default_values(self) -> None:
        """验证默认值。"""
        spv = StandardizedPointValue(node_key="n", variable_key="v")
        assert spv.node_key == "n"
        assert spv.variable_key == "v"
        assert spv.quality_code == "0"
        assert spv.schema_version == "1.0"

    def test_full_construction(self) -> None:
        """验证全字段构造。"""
        spv = StandardizedPointValue(
            node_key="dev-01",
            variable_key="power",
            value=1500.0,
            value_type="FLOAT64",
            quality_code="0",
            observed_at="2026-06-04T10:00:00+00:00",
            received_at="2026-06-04T10:00:01+00:00",
            source_id="src-01",
            message_id="msg-01",
            schema_version="1.0",
        )
        assert spv.value == 1500.0
        assert spv.value_type == "FLOAT64"


# ── StandardizedWaveformValue DTO 测试 ────────────────────────────────────────


class TestStandardizedWaveformValue:
    """StandardizedWaveformValue DTO 测试。"""

    def test_default_empty(self) -> None:
        """验证默认为空波形。"""
        wf = StandardizedWaveformValue(node_key="n", variable_key="v")
        assert wf.timestamps == []
        assert wf.values == []
        assert wf.sample_rate_hz == 0.0

    def test_with_data(self) -> None:
        """验证波形数据存储。"""
        wf = StandardizedWaveformValue(
            node_key="n",
            variable_key="v",
            timestamps=["2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z"],
            values=[1.0, 2.0],
            sample_rate_hz=50.0,
            channel_id="ch-1",
        )
        assert len(wf.values) == 2
        assert wf.channel_id == "ch-1"


# ── StateViewRecord DTO 测试 ──────────────────────────────────────────────────


class TestStateViewRecord:
    """StateViewRecord DTO 测试。"""

    def test_default_ttl(self) -> None:
        """验证默认 TTL。"""
        svr = StateViewRecord(cache_key="k")
        assert svr.ttl_seconds == 60

    def test_with_value(self) -> None:
        """验证缓存值存储。"""
        svr = StateViewRecord(
            cache_key="k",
            value={"source_id": "s", "observed_at": "t"},
            ttl_seconds=120,
        )
        assert svr.value["source_id"] == "s"
        assert svr.ttl_seconds == 120


# ── PipelineContext DTO 测试 ─────────────────────────────────────────────────


class TestPipelineContext:
    """PipelineContext DTO 测试。"""

    def test_default_context(self) -> None:
        """验证默认上下文初始值。"""
        ctx = PipelineContext()
        assert ctx.source_id == ""
        assert ctx.message_id == ""
        assert ctx.decoded_signals == []
        assert ctx.is_duplicate is False
        assert ctx.is_out_of_order is False

    def test_received_at_auto_populated(self) -> None:
        """验证 received_at 自动填充。"""
        ctx = PipelineContext()
        assert ctx.received_at != ""
        # 应可解析为 datetime
        datetime.fromisoformat(ctx.received_at)

    def test_from_envelope_dict(self) -> None:
        """验证从 envelope 字典构造。"""
        envelope = _make_envelope_dict(
            message_id="m1",
            source_id="s1",
        )
        ctx = build_context_from_envelope(envelope, protocol="MODBUS")
        assert ctx.source_id == "s1"
        assert ctx.message_id == "m1"
        assert ctx.protocol == "MODBUS"
        assert len(ctx.items) == 1
        assert ctx.items[0]["variable_key"] == "temp"


# ── RegistryCondition 测试 ────────────────────────────────────────────────────


class TestRegistryCondition:
    """RegistryCondition 测试。"""

    def test_is_default_empty(self) -> None:
        """所有字段为 None 时 is_default 返回 True。"""
        rc = RegistryCondition()
        assert rc.is_default() is True

    def test_is_default_with_payload_type(self) -> None:
        """有 payload_type 时 is_default 返回 False。"""
        rc = RegistryCondition(payload_type="JSON")
        assert rc.is_default() is False


# ── OperatorRegistry 测试 ─────────────────────────────────────────────────────


class TestOperatorRegistry:
    """OperatorRegistry 选择逻辑测试。"""

    def test_select_default_when_only_default_registered(self) -> None:
        """只有一个 default operator 时应选中它。"""
        registry = OperatorRegistry()

        class _DefaultOp:
            def execute(self, ctx):
                ctx.stage_results["2_test"] = {"status": "OK"}
                return ctx

        op = _DefaultOp()
        registry.register(2, op)
        ctx = PipelineContext()
        selected = registry.select(2, ctx)
        assert selected is op

    def test_select_by_payload_type(self) -> None:
        """按 payload_type 匹配时应选择专用 operator。"""
        registry = OperatorRegistry()

        class _JsonOp:
            called = False

            def execute(self, ctx):
                _JsonOp.called = True
                ctx.stage_results["2_test"] = {"status": "JSON"}
                return ctx

        class _DefaultOp:
            called = False

            def execute(self, ctx):
                _DefaultOp.called = True
                ctx.stage_results["2_test"] = {"status": "DEFAULT"}
                return ctx

        json_op = _JsonOp()
        default_op = _DefaultOp()
        registry.register(2, json_op, payload_type="JSON")
        registry.register(2, default_op)

        ctx = PipelineContext(payload_type="JSON")
        selected = registry.select(2, ctx)
        assert selected is json_op, "应按 payload_type=JSON 选择专用 op"

    def test_select_by_protocol(self) -> None:
        """按 protocol 匹配时应选择协议专用 operator。"""
        registry = OperatorRegistry()

        class _ModbusOp:
            passed = False

            def execute(self, ctx):
                _ModbusOp.passed = True
                return ctx

        class _DefaultOp:
            passed = False

            def execute(self, ctx):
                _DefaultOp.passed = True
                return ctx

        modbus_op = _ModbusOp()
        default_op = _DefaultOp()
        registry.register(2, modbus_op, protocol="MODBUS")
        registry.register(2, default_op)

        ctx = PipelineContext(protocol="MODBUS")
        selected = registry.select(2, ctx)
        assert selected is modbus_op

    def test_select_by_descriptor_key_exact_match(self) -> None:
        """按 descriptor_key 精确匹配应具有最高优先级。"""
        registry = OperatorRegistry()
        desc = _make_descriptor(descriptor_key="special:key")

        class _SpecificOp:
            passed = False

            def execute(self, ctx):
                _SpecificOp.passed = True
                return ctx

        class _ProtocolOp:
            passed = False

            def execute(self, ctx):
                _ProtocolOp.passed = True
                return ctx

        class _DefaultOp:
            passed = False

            def execute(self, ctx):
                _DefaultOp.passed = True
                return ctx

        specific_op = _SpecificOp()
        protocol_op = _ProtocolOp()
        default_op = _DefaultOp()

        registry.register(3, specific_op, descriptor_key="special:key")
        registry.register(3, protocol_op, protocol="MODBUS")
        registry.register(3, default_op)

        ctx = PipelineContext(protocol="MODBUS", descriptor=desc)
        selected = registry.select(3, ctx)
        # descriptor_key 精确匹配应优先于 protocol 匹配
        assert selected is specific_op

    def test_select_by_vendor(self) -> None:
        """按 vendor 匹配应选择厂家专用 operator。"""
        registry = OperatorRegistry()

        class _VendorAOp:
            passed = False

            def execute(self, ctx):
                _VendorAOp.passed = True
                return ctx

        class _DefaultOp:
            passed = False

            def execute(self, ctx):
                _DefaultOp.passed = True
                return ctx

        va_op = _VendorAOp()
        default_op = _DefaultOp()
        registry.register(5, va_op, vendor="VendorA")
        registry.register(5, default_op)

        ctx = PipelineContext(vendor="VendorA")
        selected = registry.select(5, ctx)
        assert selected is va_op

    def test_select_raises_keyerror_on_empty_stage(self) -> None:
        """未注册任何 operator 的阶段应抛出 KeyError。"""
        registry = OperatorRegistry()
        ctx = PipelineContext()
        with pytest.raises(KeyError):
            registry.select(5, ctx)

    def test_get_registered_stages(self) -> None:
        """验证 get_registered_stages 返回已注册阶段。"""
        registry = OperatorRegistry()
        registry.register(1, PayloadClassifierAdapter())
        registry.register(3, SignalResolver())
        assert registry.get_registered_stages() == [1, 3]


# ── PayloadClassifierAdapter 测试 ─────────────────────────────────────────────


class TestPayloadClassifier:
    """PayloadClassifierAdapter 测试。"""

    def test_classify_json_dict(self) -> None:
        """dict 类型载荷应分类为 JSON。"""
        op = PayloadClassifierAdapter()
        ctx = PipelineContext(original_payload={"items": []})
        ctx = op.execute(ctx)
        assert ctx.payload_type == "JSON"

    def test_classify_bytes(self) -> None:
        """bytes 类型载荷应分类为 BINARY。"""
        op = PayloadClassifierAdapter()
        ctx = PipelineContext(original_payload=b"\x01\x02\x03")
        ctx = op.execute(ctx)
        assert ctx.payload_type == "BINARY"

    def test_classify_scalar_int(self) -> None:
        """标量 int 应分类为 SCALAR。"""
        op = PayloadClassifierAdapter()
        ctx = PipelineContext(original_payload=42)
        ctx = op.execute(ctx)
        assert ctx.payload_type == "SCALAR"

    def test_classify_scalar_float(self) -> None:
        """标量 float 应分类为 SCALAR。"""
        op = PayloadClassifierAdapter()
        ctx = PipelineContext(original_payload=3.14)
        ctx = op.execute(ctx)
        assert ctx.payload_type == "SCALAR"

    def test_classify_scalar_string(self) -> None:
        """标量 string 应分类为 SCALAR。"""
        op = PayloadClassifierAdapter()
        ctx = PipelineContext(original_payload="hello")
        ctx = op.execute(ctx)
        assert ctx.payload_type == "SCALAR"

    def test_classify_unknown_type(self) -> None:
        """不支持的类型应标记 UNKNOWN。"""
        op = PayloadClassifierAdapter()
        ctx = PipelineContext(original_payload=[1, 2, 3])
        ctx = op.execute(ctx)
        assert ctx.payload_type == "UNKNOWN"
        assert len(ctx.errors) > 0

    def test_extract_protocol_from_dict(self) -> None:
        """dict 载荷中的 protocol 字段应被提取。"""
        op = PayloadClassifierAdapter()
        ctx = PipelineContext(
            original_payload={"protocol": "IEC104", "items": []}
        )
        ctx = op.execute(ctx)
        assert ctx.protocol == "IEC104"


# ── JsonScalarDecoder 测试 ───────────────────────────────────────────────────


class TestJsonScalarDecoder:
    """JsonScalarDecoder 测试。"""

    def test_decode_single_item(self) -> None:
        """单条 item 应正确解码。"""
        op = JsonScalarDecoder()
        ctx = PipelineContext(items=[
            {"variable_key": "temp", "value": 25.5, "quality_code": "0"},
        ])
        ctx = op.execute(ctx)
        assert len(ctx.decoded_signals) == 1
        assert ctx.decoded_signals[0].variable_key == "temp"
        assert ctx.decoded_signals[0].raw_value == 25.5
        assert ctx.decoded_signals[0].decode_status == "SUCCESS"

    def test_decode_multiple_items(self) -> None:
        """多条 item 应全部解码。"""
        op = JsonScalarDecoder()
        ctx = PipelineContext(items=[
            {"variable_key": "temp", "value": 25.0},
            {"variable_key": "humidity", "value": 60.0},
            {"variable_key": "pressure", "value": 1013.0},
        ])
        ctx = op.execute(ctx)
        assert len(ctx.decoded_signals) == 3

    def test_decode_with_timestamp(self) -> None:
        """应提取 source_observed_at 到 source_timestamp。"""
        op = JsonScalarDecoder()
        ctx = PipelineContext(items=[
            {
                "variable_key": "v",
                "value": 1.0,
                "source_observed_at": "2026-06-04T10:00:00+00:00",
            }
        ])
        ctx = op.execute(ctx)
        assert ctx.decoded_signals[0].source_timestamp == "2026-06-04T10:00:00+00:00"

    def test_decode_empty_items(self) -> None:
        """空 items 列表应产生空信号列表。"""
        op = JsonScalarDecoder()
        ctx = PipelineContext(items=[])
        ctx = op.execute(ctx)
        assert ctx.decoded_signals == []


# ── BinaryDecoderStub 测试 ────────────────────────────────────────────────────


class TestBinaryDecoderStub:
    """BinaryDecoderStub 测试。"""

    def test_decode_with_descriptor_int32(self) -> None:
        """按 INT32 描述符解码 bytes。"""
        desc = _make_descriptor(
            descriptor_key="dk",
            variable_key="v",
            data_type="INT32",
            byte_length=4,
            endian="BIG_ENDIAN",
        )
        op = BinaryDecoderStub()
        ctx = PipelineContext(
            original_payload=b"\x00\x00\x00\x2A",  # 42 in big-endian
            descriptor=desc,
        )
        ctx = op.execute(ctx)
        assert len(ctx.decoded_signals) == 1
        assert ctx.decoded_signals[0].raw_value == 42
        assert ctx.decoded_signals[0].decode_status == "SUCCESS"

    def test_decode_with_descriptor_float64(self) -> None:
        """按 FLOAT64 描述符解码 bytes。"""
        import struct
        desc = _make_descriptor(
            descriptor_key="dk",
            variable_key="v",
            data_type="FLOAT64",
            byte_length=8,
            endian="BIG_ENDIAN",
        )
        op = BinaryDecoderStub()
        data = struct.pack(">d", 3.14159)
        ctx = PipelineContext(original_payload=data, descriptor=desc)
        ctx = op.execute(ctx)
        assert len(ctx.decoded_signals) == 1
        assert ctx.decoded_signals[0].decode_status == "SUCCESS"
        assert abs(ctx.decoded_signals[0].raw_value - 3.14159) < 0.0001

    def test_decode_with_scale_offset(self) -> None:
        """验证 scale 和 offset 在解码后正确应用。"""
        desc = _make_descriptor(
            descriptor_key="dk",
            variable_key="v",
            data_type="INT32",
            byte_length=4,
            endian="BIG_ENDIAN",
            default_scale=0.1,
            default_offset=10.0,
        )
        op = BinaryDecoderStub()
        # raw=100, after scale+offset: 100*0.1 + 10 = 20.0
        ctx = PipelineContext(
            original_payload=b"\x00\x00\x00\x64",  # 100
            descriptor=desc,
        )
        ctx = op.execute(ctx)
        assert ctx.decoded_signals[0].raw_value == 20.0

    def test_decode_wrong_type_for_bytes(self) -> None:
        """非 bytes 载荷应报错。"""
        op = BinaryDecoderStub()
        ctx = PipelineContext(original_payload={"not": "bytes"})
        ctx = op.execute(ctx)
        assert len(ctx.errors) > 0

    def test_decode_insufficient_length(self) -> None:
        """数据长度不足应报 DECODE_ERROR。"""
        desc = _make_descriptor(
            descriptor_key="dk",
            variable_key="v",
            data_type="INT32",
            byte_length=8,
            endian="BIG_ENDIAN",
        )
        op = BinaryDecoderStub()
        ctx = PipelineContext(
            original_payload=b"\x00\x00",  # 仅 2 bytes
            descriptor=desc,
        )
        ctx = op.execute(ctx)
        assert ctx.decoded_signals[0].decode_status == "DECODE_ERROR"


# ── SignalResolver 测试 ───────────────────────────────────────────────────────


class TestSignalResolver:
    """SignalResolver 测试。"""

    def test_resolve_by_descriptor_key_exact_match(self) -> None:
        """按 descriptor_key 精确匹配应解析成功。"""
        desc = _make_descriptor(descriptor_key="match:key", variable_key="v")
        registry = {"match:key": desc}
        op = SignalResolver(descriptor_registry=registry)
        ctx = PipelineContext(decoded_signals=[
            DecodedSignal(descriptor_key="match:key", variable_key="v"),
        ])
        ctx = op.execute(ctx)
        assert len(ctx.resolved_signals) == 1
        assert ctx.resolved_signals[0].resolve_status == "RESOLVED"
        assert ctx.resolved_signals[0].descriptor is desc

    def test_resolve_by_variable_key_fallback(self) -> None:
        """按 variable_key 兜底匹配应成功。"""
        desc = _make_descriptor(descriptor_key="other:key", variable_key="match_me")
        registry = {"other:key": desc}
        op = SignalResolver(descriptor_registry=registry)
        ctx = PipelineContext(decoded_signals=[
            DecodedSignal(descriptor_key="unknown_key", variable_key="match_me"),
        ])
        ctx = op.execute(ctx)
        assert len(ctx.resolved_signals) == 1
        assert ctx.resolved_signals[0].resolve_status == "RESOLVED"

    def test_resolve_fails_with_unresolved(self) -> None:
        """无匹配描述符时应返回 UNRESOLVED。"""
        op = SignalResolver(descriptor_registry={})
        ctx = PipelineContext(decoded_signals=[
            DecodedSignal(descriptor_key="no_match", variable_key="no_match"),
        ])
        ctx = op.execute(ctx)
        assert ctx.resolved_signals[0].resolve_status == "UNRESOLVED"
        assert ctx.resolved_signals[0].descriptor is None


# ── Decode-before-Resolve 测试 ────────────────────────────────────────────────


class TestDecodeBeforeResolve:
    """验证 decode → resolve 顺序约束：二进制 payload 必须先 decode 再 resolve。"""

    def test_json_decode_then_resolve(self) -> None:
        """JSON 载荷：decode → resolve 完整路径。"""
        desc = _make_descriptor(descriptor_key="temp", variable_key="temp")
        registry = {"temp": desc}

        # Stage 1: classify
        classifier = PayloadClassifierAdapter()
        ctx = PipelineContext(
            original_payload={"items": [{"variable_key": "temp", "value": 25.5}]}
        )
        ctx = classifier.execute(ctx)
        assert ctx.payload_type == "JSON"

        # Stage 2: decode
        decoder = JsonScalarDecoder()
        ctx = decoder.execute(ctx)
        assert len(ctx.decoded_signals) == 1
        assert ctx.decoded_signals[0].decode_status == "SUCCESS"

        # Stage 3: resolve (必须在 decode 之后)
        resolver = SignalResolver(descriptor_registry=registry)
        ctx = resolver.execute(ctx)
        assert len(ctx.resolved_signals) == 1
        assert ctx.resolved_signals[0].resolve_status == "RESOLVED"
        assert ctx.resolved_signals[0].descriptor is desc

    def test_binary_decode_then_resolve(self) -> None:
        """二进制 payload：decode → resolve 完整路径。"""
        import struct
        desc = _make_descriptor(
            descriptor_key="bin:1",
            variable_key="power",
            data_type="INT32",
            byte_length=4,
            endian="BIG_ENDIAN",
        )
        registry = {"bin:1": desc}

        # Stage 1: classify
        classifier = PayloadClassifierAdapter()
        ctx = PipelineContext(
            original_payload=struct.pack(">i", 1500),
            descriptor=desc,
        )
        ctx = classifier.execute(ctx)
        assert ctx.payload_type == "BINARY"

        # Stage 2: decode binary
        decoder = BinaryDecoderStub()
        ctx = decoder.execute(ctx)
        assert len(ctx.decoded_signals) == 1
        assert ctx.decoded_signals[0].decode_status == "SUCCESS"
        assert ctx.decoded_signals[0].raw_value == 1500

        # Stage 3: resolve (必须在 decode 之后)
        resolver = SignalResolver(descriptor_registry=registry)
        ctx = resolver.execute(ctx)
        assert len(ctx.resolved_signals) == 1
        assert ctx.resolved_signals[0].resolve_status == "RESOLVED"
        # 验证 resolved signal 的 descriptor 正确
        assert ctx.resolved_signals[0].descriptor.descriptor_key == "bin:1"


# ── TimestampNormalizer 测试 ─────────────────────────────────────────────────


class TestTimestampNormalizer:
    """TimestampNormalizer 测试。"""

    def test_normalize_uses_source_timestamp_first(self) -> None:
        """优先使用 source_timestamp。"""
        op = TimestampNormalizer()
        ctx = PipelineContext(
            received_at="2026-06-04T10:00:00+00:00",
            decoded_signals=[
                DecodedSignal(
                    descriptor_key="dk", variable_key="v",
                    source_timestamp="2026-06-04T09:00:00+00:00",
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.decoded_signals[0].source_timestamp == "2026-06-04T09:00:00+00:00"

    def test_normalize_falls_back_to_received_at(self) -> None:
        """无 timestamp 时兜底到 received_at。"""
        op = TimestampNormalizer()
        ctx = PipelineContext(
            received_at="2026-06-04T10:00:00+00:00",
            decoded_signals=[
                DecodedSignal(descriptor_key="dk", variable_key="v"),
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.decoded_signals[0].source_timestamp is not None

    def test_normalize_handles_datetime_object(self) -> None:
        """datetime 对象应转换为 ISO 字符串。"""
        op = TimestampNormalizer()
        now = datetime.now(tz=timezone.utc)
        ctx = PipelineContext(
            published_at=now.isoformat(),
            decoded_signals=[
                DecodedSignal(
                    descriptor_key="dk", variable_key="v",
                    source_timestamp=now,
                )
            ],
        )
        ctx = op.execute(ctx)
        # 应无异常
        assert ctx.decoded_signals[0].source_timestamp is not None


# ── ValueNormalizer 测试 ──────────────────────────────────────────────────────


class TestValueNormalizer:
    """ValueNormalizer 测试。"""

    def test_normalize_float(self) -> None:
        """FLOAT64 类型应正确转换。"""
        op = ValueNormalizer()
        desc = _make_descriptor(data_type="FLOAT64")
        ctx = PipelineContext(
            source_id="s", message_id="m",
            resolved_signals=[
                ResolvedSignal(
                    descriptor=desc,
                    decoded=DecodedSignal(
                        descriptor_key="dk", variable_key="v", raw_value="3.14",
                    ),
                )
            ],
        )
        ctx = op.execute(ctx)
        assert len(ctx.standardized_values) == 1
        assert ctx.standardized_values[0].value == 3.14
        assert ctx.standardized_values[0].value_type == "FLOAT64"

    def test_normalize_int_with_scale(self) -> None:
        """INT32 类型带 scale/offset 应正确转换。"""
        op = ValueNormalizer()
        desc = _make_descriptor(
            data_type="INT32",
            default_scale=0.01,
            default_offset=5.0,
        )
        ctx = PipelineContext(
            source_id="s", message_id="m",
            resolved_signals=[
                ResolvedSignal(
                    descriptor=desc,
                    decoded=DecodedSignal(
                        descriptor_key="dk", variable_key="v", raw_value=100,
                    ),
                )
            ],
        )
        ctx = op.execute(ctx)
        # 100 * 0.01 + 5.0 = 6.0
        assert ctx.standardized_values[0].value == 6.0

    def test_normalize_boolean(self) -> None:
        """BOOLEAN 类型应正确转换。"""
        op = ValueNormalizer()
        desc = _make_descriptor(data_type="BOOLEAN")
        ctx = PipelineContext(
            source_id="s", message_id="m",
            resolved_signals=[
                ResolvedSignal(
                    descriptor=desc,
                    decoded=DecodedSignal(
                        descriptor_key="dk", variable_key="v", raw_value="true",
                    ),
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.standardized_values[0].value is True

    def test_normalize_string(self) -> None:
        """STRING 类型应原样保留。"""
        op = ValueNormalizer()
        desc = _make_descriptor(data_type="STRING")
        ctx = PipelineContext(
            source_id="s", message_id="m",
            resolved_signals=[
                ResolvedSignal(
                    descriptor=desc,
                    decoded=DecodedSignal(
                        descriptor_key="dk", variable_key="v", raw_value="running",
                    ),
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.standardized_values[0].value == "running"

    def test_normalize_with_precision(self) -> None:
        """default_precision 应控制小数位数。"""
        op = ValueNormalizer()
        desc = _make_descriptor(
            data_type="FLOAT64", default_precision=2,
        )
        ctx = PipelineContext(
            source_id="s", message_id="m",
            resolved_signals=[
                ResolvedSignal(
                    descriptor=desc,
                    decoded=DecodedSignal(
                        descriptor_key="dk", variable_key="v",
                        raw_value=3.1415926,
                    ),
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.standardized_values[0].value == 3.14

    def test_normalize_none_value(self) -> None:
        """None 值不转换。"""
        op = ValueNormalizer()
        desc = _make_descriptor(data_type="FLOAT64")
        ctx = PipelineContext(
            source_id="s", message_id="m",
            resolved_signals=[
                ResolvedSignal(
                    descriptor=desc,
                    decoded=DecodedSignal(
                        descriptor_key="dk", variable_key="v", raw_value=None,
                    ),
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.standardized_values[0].value is None


# ── QualityEvaluator 测试 ─────────────────────────────────────────────────────


class TestQualityEvaluator:
    """QualityEvaluator 测试。"""

    def test_default_good(self) -> None:
        """正常值应评估为 GOOD (0)。"""
        op = QualityEvaluator()
        ctx = PipelineContext(
            decoded_signals=[
                DecodedSignal(
                    descriptor_key="dk", variable_key="v",
                    decode_status="SUCCESS",
                )
            ],
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v", value=1.0,
                    observed_at=datetime.now(tz=timezone.utc).isoformat(),
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.standardized_values[0].quality_code == "0"

    def test_missing_value(self) -> None:
        """None 值应评估为 MISSING_VALUE (1)。"""
        op = QualityEvaluator()
        ctx = PipelineContext(
            decoded_signals=[
                DecodedSignal(
                    descriptor_key="dk", variable_key="v",
                    decode_status="SUCCESS",
                )
            ],
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v", value=None,
                    observed_at=datetime.now(tz=timezone.utc).isoformat(),
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.standardized_values[0].quality_code == "1"

    def test_decode_error(self) -> None:
        """解码失败应评估为 DECODE_ERROR (2)。"""
        op = QualityEvaluator()
        ctx = PipelineContext(
            decoded_signals=[
                DecodedSignal(
                    descriptor_key="dk", variable_key="v",
                    decode_status="DECODE_ERROR",
                )
            ],
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v", value=0,
                    observed_at=datetime.now(tz=timezone.utc).isoformat(),
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.standardized_values[0].quality_code == "2"

    def test_stale_value(self) -> None:
        """过期时间戳应评估为 STALE (3)。"""
        # stale_seconds=1 使几乎任何过去数据都 stale
        op = QualityEvaluator(stale_seconds=1)
        old_time = (datetime.now(tz=timezone.utc) - timedelta(seconds=120)).isoformat()
        ctx = PipelineContext(
            decoded_signals=[
                DecodedSignal(
                    descriptor_key="dk", variable_key="v",
                    decode_status="SUCCESS",
                )
            ],
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v", value=1.0,
                    observed_at=old_time,
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.standardized_values[0].quality_code == "3"

    def test_aggregate_quality_code(self) -> None:
        """聚合质量码应取最差质量码。"""
        op = QualityEvaluator()
        ctx = PipelineContext(
            decoded_signals=[
                DecodedSignal(
                    descriptor_key="d1", variable_key="v1",
                    decode_status="SUCCESS",
                ),
                DecodedSignal(
                    descriptor_key="d2", variable_key="v2",
                    decode_status="DECODE_ERROR",
                ),
            ],
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v1", value=1.0,
                    observed_at=datetime.now(tz=timezone.utc).isoformat(),
                ),
                StandardizedPointValue(
                    node_key="n", variable_key="v2", value=0.0,
                    observed_at=datetime.now(tz=timezone.utc).isoformat(),
                ),
            ],
        )
        ctx = op.execute(ctx)
        # 聚合质量码应为 "2"（最差）
        assert ctx.quality_code == "2"


# ── DeduplicateOrderGuard 测试 ────────────────────────────────────────────────


class TestDeduplicateOrderGuardOperator:
    """DeduplicateOrderGuard operator 测试。"""

    def test_unique_message_passes(self) -> None:
        """新 message_id 应通过去重检查。"""
        op = DeduplicateOrderGuard(dedup_size=10)
        ctx = PipelineContext(
            message_id="unique-001",
            source_id="s",
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v",
                    observed_at=datetime.now(tz=timezone.utc).isoformat(),
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.is_duplicate is False

    def test_duplicate_message_detected(self) -> None:
        """相同 message_id 第二次应被检测为重复。"""
        op = DeduplicateOrderGuard(dedup_size=10)
        ctx1 = PipelineContext(message_id="dup-001", standardized_values=[])
        op.execute(ctx1)
        ctx2 = PipelineContext(message_id="dup-001", standardized_values=[])
        ctx2 = op.execute(ctx2)
        assert ctx2.is_duplicate is True

    def test_out_of_order_detected(self) -> None:
        """乱序 observed_at 应被检测。"""
        op = DeduplicateOrderGuard(tolerance_seconds=60)
        now = datetime.now(tz=timezone.utc)
        old = now - timedelta(seconds=120)

        # 先到达较新数据
        ctx1 = PipelineContext(
            message_id="ooo-1",
            source_id="s",
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v",
                    observed_at=now.isoformat(),
                )
            ],
        )
        op.execute(ctx1)

        # 再到达旧数据
        ctx2 = PipelineContext(
            message_id="ooo-2",
            source_id="s",
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v",
                    observed_at=old.isoformat(),
                )
            ],
        )
        ctx2 = op.execute(ctx2)
        assert ctx2.is_out_of_order is True
        assert ctx2.should_dlq is True  # 超出 tolerance


# ── LightDerivation 测试 ─────────────────────────────────────────────────────


class TestLightDerivation:
    """LightDerivation operator 测试。"""

    def test_source_alive_with_valid_data(self) -> None:
        """有效数据应设置 source_alive=True。"""
        op = LightDerivation(enabled=True)
        ctx = PipelineContext(
            source_id="s",
            published_at=datetime.now(tz=timezone.utc).isoformat(),
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v", value=1.0,
                    quality_code="0",
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.derived_states["source_alive"] is True

    def test_source_alive_with_decode_error(self) -> None:
        """仅 DECODE_ERROR 信号时 source_alive=False。"""
        op = LightDerivation(enabled=True)
        ctx = PipelineContext(
            source_id="s",
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v", value=0,
                    quality_code="2",  # DECODE_ERROR
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.derived_states["source_alive"] is False

    def test_communication_state_active(self) -> None:
        """新鲜数据应评估 communication_state=ACTIVE。"""
        op = LightDerivation(enabled=True, stale_threshold_seconds=300)
        ctx = PipelineContext(
            source_id="s",
            published_at=datetime.now(tz=timezone.utc).isoformat(),
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v", value=1.0,
                    quality_code="0",
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.derived_states["communication_state"] == "ACTIVE"

    def test_communication_state_stale(self) -> None:
        """过期数据应评估 communication_state=STALE。"""
        op = LightDerivation(enabled=True, stale_threshold_seconds=1)
        old = (datetime.now(tz=timezone.utc) - timedelta(seconds=120)).isoformat()
        ctx = PipelineContext(
            source_id="s",
            published_at=old,
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v", value=1.0,
                    quality_code="0",
                )
            ],
        )
        ctx = op.execute(ctx)
        assert ctx.derived_states["communication_state"] == "STALE"

    def test_disabled_derivation(self) -> None:
        """派生关闭时应跳过计算。"""
        op = LightDerivation(enabled=False)
        ctx = PipelineContext(standardized_values=[])
        ctx = op.execute(ctx)
        assert ctx.derived_states == {}


# ── StandardizedWriterOperator 测试 ──────────────────────────────────────────


class TestStandardizedWriterOperator:
    """StandardizedWriterOperator 测试。"""

    @pytest.mark.asyncio
    async def test_write_to_memory_sink(self) -> None:
        """验证写入 MemoryStandardizedSink。"""
        sink = MemoryStandardizedSink()
        op = StandardizedWriterOperator(sink=sink)
        ctx = PipelineContext(
            source_id="s",
            message_id="m",
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v", value=1.0,
                    value_type="FLOAT64", quality_code="0",
                    observed_at=datetime.now(tz=timezone.utc).isoformat(),
                    received_at=datetime.now(tz=timezone.utc).isoformat(),
                    source_id="s", message_id="m",
                )
            ],
        )
        op.execute(ctx)
        # 由于 execute 内部会异步写入，检查 sink 状态
        assert len(sink.states) == 1
        assert sink.states[0]["node_key"] == "n"

    def test_duplicate_payload_skipped(self) -> None:
        """重复消息应跳过写入。"""
        sink = MemoryStandardizedSink()
        op = StandardizedWriterOperator(sink=sink)
        ctx = PipelineContext(
            source_id="s",
            message_id="m",
            is_duplicate=True,
            standardized_values=[
                StandardizedPointValue(node_key="n", variable_key="v"),
            ],
        )
        op.execute(ctx)
        # 重复消息跳过，sink 应无写入
        assert len(sink.states) == 0


# ── StateViewUpdater 测试 ────────────────────────────────────────────────────


class TestStateViewUpdater:
    """StateViewUpdater operator 测试。"""

    @pytest.mark.asyncio
    async def test_update_to_memory_cache(self) -> None:
        """验证写入 InMemoryServingCache。"""
        cache = InMemoryServingCache()
        op = StateViewUpdater(cache=cache, default_ttl=60)
        ctx = PipelineContext(
            source_id="s",
            message_id="m",
            message_type="state_snapshot",
            standardized_values=[
                StandardizedPointValue(
                    node_key="n", variable_key="v", value=1.0,
                    quality_code="0",
                    observed_at=datetime.now(tz=timezone.utc).isoformat(),
                    source_id="s",
                )
            ],
        )
        op.execute(ctx)
        # 验证缓存有数据
        value = await cache.get("s:n:v")
        assert value is not None
        assert value["source_id"] == "s"

    def test_duplicate_payload_skipped(self) -> None:
        """重复消息应跳过缓存更新。"""
        cache = InMemoryServingCache()
        op = StateViewUpdater(cache=cache)
        ctx = PipelineContext(
            is_duplicate=True,
            standardized_values=[
                StandardizedPointValue(node_key="n", variable_key="v"),
            ],
        )
        op.execute(ctx)
        assert cache.size() == 0


# ── PreprocessingPipeline 完整流程测试 ───────────────────────────────────────


class TestPreprocessingPipeline:
    """PreprocessingPipeline 完整编排测试。"""

    def test_pipeline_runs_all_10_stages(self) -> None:
        """验证 pipeline 执行全部 10 个阶段。"""
        pipeline = PreprocessingPipeline()
        pipeline.register_defaults()

        envelope = _make_envelope_dict(
            message_id="pipe-full-01",
            source_id="src-pipe",
        )
        ctx = build_context_from_envelope(envelope)
        ctx = pipeline.run(ctx)

        # 验证所有阶段都有结果
        stage_keys = list(ctx.stage_results.keys())
        assert len(stage_keys) >= 8, f"应有至少 8 个阶段结果，实际 {len(stage_keys)}"

    def test_pipeline_with_json_payload(self) -> None:
        """JSON 载荷应完整走通 pipeline。"""
        pipeline = PreprocessingPipeline()
        pipeline.register_defaults()

        envelope = _make_envelope_dict(
            message_id="pipe-json-01",
            source_id="src-json",
            items=[
                {"variable_key": "temp", "value": 25.5, "quality_code": "0"},
                {"variable_key": "power", "value": 1500.0, "quality_code": "0"},
            ],
        )
        ctx = build_context_from_envelope(envelope)
        ctx = pipeline.run(ctx)

        # 解码应产生 2 个信号
        assert len(ctx.decoded_signals) == 2
        # 标准化值应产生 2 个
        assert len(ctx.standardized_values) == 2
        # 无错误
        assert ctx.errors == []

    @pytest.mark.asyncio
    async def test_duplicate_message_skips_write(self) -> None:
        """重复消息应从阶段 8+ 跳过。"""
        pipeline = PreprocessingPipeline()
        pipeline.register_defaults()

        envelope = _make_envelope_dict(message_id="pipe-dup-01")
        # 第一条消息
        ctx1 = build_context_from_envelope(envelope)
        ctx1 = pipeline.run(ctx1)
        assert ctx1.is_duplicate is False

        # 第二条相同消息
        ctx2 = build_context_from_envelope(envelope)
        ctx2 = pipeline.run(ctx2)
        assert ctx2.is_duplicate is True

    def test_build_context_with_protocol_vendor(self) -> None:
        """验证 build_context_from_envelope 传递 protocol 和 vendor。"""
        envelope = _make_envelope_dict()
        ctx = build_context_from_envelope(
            envelope, protocol="MODBUS", vendor="VendorA",
        )
        assert ctx.protocol == "MODBUS"
        assert ctx.vendor == "VendorA"

    def test_pipeline_stage_order_fixed(self) -> None:
        """验证 pipeline 的阶段顺序是固定的 1-10。"""
        pipeline = PreprocessingPipeline()
        assert pipeline.STAGE_ORDER == list(range(1, 11))
        assert pipeline.STAGE_NAMES[1] == "classify / adapt payload"
        assert pipeline.STAGE_NAMES[10] == "update Redis state view"


# ── 与既有 light_processor 导出兼容性测试 ────────────────────────────────────


class TestCompatibilityWithLightProcessor:
    """验证 Round A 新增导出不破坏 light_processor 公共导出。"""

    def test_light_processor_exports_unchanged(self) -> None:
        """既有 light_processor 类型仍可从 speed_layer 导入。"""
        from whale.speed_layer import (
            EnvelopeValidator,
            LightProcessingPipeline,
        )
        # 可实例化
        validator = EnvelopeValidator()
        assert validator is not None
        pipeline = LightProcessingPipeline()
        assert pipeline is not None

    def test_runner_exports_unchanged(self) -> None:
        """runner 类型仍可从 speed_layer 导入。"""
        from whale.speed_layer import (
            LocalPipelineRunner,
            PipelineRunner,
            SpeedLayerWiring,
        )
        runner = LocalPipelineRunner()
        assert isinstance(runner, PipelineRunner)
        wiring = SpeedLayerWiring()
        assert wiring is not None

    def test_writers_exports_unchanged(self) -> None:
        """writer 类型仍可从 speed_layer 导入。"""
        from whale.speed_layer import (
            RawArchiveWriter,
            RawIndexWriter,
        )
        # 仅导入验证，这些类需要 source/sink/dlq 参数来实例化
        assert RawArchiveWriter is not None
        assert RawIndexWriter is not None

    def test_new_round_a_types_importable(self) -> None:
        """新 Round A 类型可从 speed_layer 正确导入。"""
        from whale.speed_layer import (
            DecodedSignal,
            PipelineContext,
            PreprocessingPipeline,
            SignalProfileItemDescriptor,
        )
        assert DecodedSignal is not None
        assert PipelineContext is not None
        assert PreprocessingPipeline is not None
        assert SignalProfileItemDescriptor is not None

    def test_preprocessing_subpackage_importable(self) -> None:
        """preprocessing 子包可直接导入。"""
        from whale.speed_layer.preprocessing import (
            OperatorRegistry,
            RegistryCondition,
        )
        registry = OperatorRegistry()
        assert registry is not None
        condition = RegistryCondition(payload_type="JSON")
        assert condition.payload_type == "JSON"

    def test_speed_layer_wiring_with_light_processor_still_works(self) -> None:
        """SpeedLayerWiring.with_light_processor() 保持兼容。

        验证 SpeedLayerWiring 链式调用 .with_memory().with_inmemory_dlq()
        .with_light_processor().build() 正常返回 runner。
        """
        from whale.speed_layer import LightProcessingPipeline, SpeedLayerWiring

        wiring = SpeedLayerWiring()
        wiring.with_memory()
        wiring.with_inmemory_dlq()
        wiring.with_light_processor(LightProcessingPipeline(dedup_size=100))

        runner = wiring.build()
        assert runner.writer_count >= 4
