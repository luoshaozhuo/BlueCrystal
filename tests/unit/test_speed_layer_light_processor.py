"""speed layer 轻处理管线单元测试（SP-FR-004）。

验证实时轻处理管线的四个核心处理器：
- EnvelopeValidator: schema/envelope 结构校验。
- MessageDeduplicator: message_id 幂等去重（内存 LRU）。
- QualityCodePassThrough: 质量码透传。
- OutOfOrderGuard: observed_at 乱序保护。
- LightProcessingPipeline: 轻处理管线编排。

被验证对象：
- whale.speed_layer.light_processor: EnvelopeValidator, MessageDeduplicator,
  QualityCodePassThrough, OutOfOrderGuard, LightProcessingPipeline

证据等级：L1 unit/mock（纯内存测试，无外部依赖）。
不能证明：Redis-backed 去重器的分布式去重能力（memory LRU 仅证明单进程）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from whale.speed_layer.light_processor import (
    EnvelopeValidator,
    LightProcessingPipeline,
    MessageDeduplicator,
    OutOfOrderGuard,
    QualityCodePassThrough,
)


# ── EnvelopeValidator 测试 ──────────────────────────────────────────────────


class TestEnvelopeValidator:
    """EnvelopeValidator 单元测试。"""

    def test_valid_envelope_passes(self) -> None:
        """合法 envelope 应通过校验。"""
        validator = EnvelopeValidator()
        passed, error = validator.validate({
            "schema_version": "1.0",
            "message_type": "state_snapshot",
            "source_id": "src-001",
            "message_id": "msg-001",
            "items": [{"key": "val"}],
        })
        assert passed is True
        assert error is None

    def test_missing_schema_version_fails(self) -> None:
        """缺少 schema_version 应校验失败。"""
        validator = EnvelopeValidator()
        passed, error = validator.validate({
            "message_type": "state_snapshot",
            "source_id": "src-001",
            "message_id": "msg-001",
            "items": [{"key": "val"}],
        })
        assert passed is False
        assert "schema_version" in (error or "")

    def test_empty_message_type_fails(self) -> None:
        """空 message_type 应校验失败。"""
        validator = EnvelopeValidator()
        passed, error = validator.validate({
            "schema_version": "1.0",
            "message_type": "",
            "source_id": "src-001",
            "message_id": "msg-001",
            "items": [{"key": "val"}],
        })
        assert passed is False
        assert "message_type" in (error or "")

    def test_empty_items_fails(self) -> None:
        """空 items 列表应校验失败。"""
        validator = EnvelopeValidator()
        passed, error = validator.validate({
            "schema_version": "1.0",
            "message_type": "state_snapshot",
            "source_id": "src-001",
            "message_id": "msg-001",
            "items": [],
        })
        assert passed is False
        assert "items" in (error or "")

    def test_allowed_types_whitelist(self) -> None:
        """白名单模式：不在白名单中的 message_type 应失败。"""
        validator = EnvelopeValidator(
            allowed_types=["state_snapshot", "alarm_event"],
        )
        passed, _ = validator.validate({
            "schema_version": "1.0",
            "message_type": "state_snapshot",
            "source_id": "src-001",
            "message_id": "msg-001",
            "items": [{"key": "val"}],
        })
        assert passed is True

        passed2, err2 = validator.validate({
            "schema_version": "1.0",
            "message_type": "unknown_type",
            "source_id": "src-001",
            "message_id": "msg-001",
            "items": [{"key": "val"}],
        })
        assert passed2 is False
        assert "白名单" in (err2 or "")

    def test_reset_error_count(self) -> None:
        """reset 应清除错误计数。"""
        validator = EnvelopeValidator()
        validator.validate({"items": []})  # 应失败
        assert validator.error_count == 1
        validator.reset()
        assert validator.error_count == 0


# ── MessageDeduplicator 测试 ────────────────────────────────────────────────


class TestMessageDeduplicator:
    """MessageDeduplicator 单元测试。"""

    def test_new_message_not_duplicate(self) -> None:
        """新 message_id 不应判定为重复。"""
        dedup = MessageDeduplicator(max_size=100)
        assert dedup.is_duplicate("msg-new") is False
        assert dedup.total_checked == 1
        assert dedup.duplicate_count == 0

    def test_duplicate_message_detected(self) -> None:
        """相同 message_id 第二次出现应判定为重复。"""
        dedup = MessageDeduplicator(max_size=100)
        assert dedup.is_duplicate("msg-001") is False
        assert dedup.is_duplicate("msg-001") is True
        assert dedup.duplicate_count == 1
        assert dedup.total_checked == 2

    def test_lru_eviction(self) -> None:
        """LRU 策略：超出 max_size 时淘汰最早记录。"""
        dedup = MessageDeduplicator(max_size=3)
        # 加入 3 条
        dedup.is_duplicate("msg-1")
        dedup.is_duplicate("msg-2")
        dedup.is_duplicate("msg-3")
        assert dedup.cache_size == 3
        # msg-1 应被 evict
        dedup.is_duplicate("msg-4")
        assert dedup.cache_size == 3
        # msg-1 再出现应视为新消息
        assert dedup.is_duplicate("msg-1") is False

    def test_reset(self) -> None:
        """reset 应清除所有记录和计数。"""
        dedup = MessageDeduplicator()
        dedup.is_duplicate("msg-1")
        dedup.is_duplicate("msg-2")
        dedup.is_duplicate("msg-1")  # 重复
        dedup.reset()
        assert dedup.cache_size == 0
        assert dedup.duplicate_count == 0
        assert dedup.total_checked == 0


# ── QualityCodePassThrough 测试 ─────────────────────────────────────────────


class TestQualityCodePassThrough:
    """QualityCodePassThrough 单元测试。"""

    def test_passthrough_normal(self) -> None:
        """正常 quality_code 应原样透传。"""
        qc = QualityCodePassThrough()
        assert qc.pass_through({"quality_code": "0"}) == "0"
        assert qc.pass_through({"quality_code": "1"}) == "1"
        assert qc.pass_through({"quality_code": "3"}) == "3"

    def test_default_for_missing(self) -> None:
        """缺失 quality_code 时应返回默认值 "0"。"""
        qc = QualityCodePassThrough()
        assert qc.pass_through({}) == "0"
        assert qc.pass_through({"other": "data"}) == "0"

    def test_default_for_empty(self) -> None:
        """空 quality_code 时应返回默认值。"""
        qc = QualityCodePassThrough()
        assert qc.pass_through({"quality_code": ""}) == "0"
        assert qc.pass_through({"quality_code": None}) == "0"

    def test_custom_default(self) -> None:
        """可自定义默认质量码。"""
        qc = QualityCodePassThrough(default_quality="9")
        assert qc.pass_through({}) == "9"


# ── OutOfOrderGuard 测试 ───────────────────────────────────────────────────


class TestOutOfOrderGuard:
    """OutOfOrderGuard 单元测试。"""

    def test_first_record_not_out_of_order(self) -> None:
        """首次出现的 (node_key, var_key) 不为乱序。"""
        guard = OutOfOrderGuard(tolerance_seconds=60)
        ts = datetime.now(tz=timezone.utc)
        is_ooo, should_dlq = guard.check("node-1", "var-1", ts)
        assert is_ooo is False
        assert should_dlq is False
        assert guard.total_count == 1
        assert guard.out_of_order_count == 0

    def test_ordered_data_normal(self) -> None:
        """按时间升序到达的数据不标记乱序。"""
        guard = OutOfOrderGuard()
        t1 = datetime.now(tz=timezone.utc)
        t2 = t1 + timedelta(seconds=10)
        assert guard.check("n", "v", t1) == (False, False)
        assert guard.check("n", "v", t2) == (False, False)

    def test_out_of_order_detected_within_tolerance(self) -> None:
        """乱序但在容忍范围内：标记乱序但不建议 DLQ。"""
        guard = OutOfOrderGuard(tolerance_seconds=60)
        t1 = datetime.now(tz=timezone.utc)
        t0 = t1 - timedelta(seconds=30)  # 30秒前的数据
        guard.check("n", "v", t1)
        is_ooo, should_dlq = guard.check("n", "v", t0)
        assert is_ooo is True  # 乱序
        assert should_dlq is False  # 在容忍范围内

    def test_out_of_order_beyond_tolerance_dlq(self) -> None:
        """乱序超出容忍范围：标记乱序且建议 DLQ。"""
        guard = OutOfOrderGuard(tolerance_seconds=60)
        t1 = datetime.now(tz=timezone.utc)
        t_old = t1 - timedelta(seconds=120)  # 2分钟前的数据
        guard.check("n", "v", t1)
        is_ooo, should_dlq = guard.check("n", "v", t_old)
        assert is_ooo is True
        assert should_dlq is True  # 超出容忍

    def test_none_timestamp_passes(self) -> None:
        """无时间戳时直接放行。"""
        guard = OutOfOrderGuard()
        assert guard.check("n", "v", None) == (False, False)

    def test_reset(self) -> None:
        """reset 清除内部状态。"""
        guard = OutOfOrderGuard()
        guard.check("n", "v", datetime.now(tz=timezone.utc))
        guard.reset()
        assert guard.total_count == 0
        assert guard.out_of_order_count == 0

    def test_different_keys_independent(self) -> None:
        """不同 node_key 或 variable_key 的时间戳独立维护。"""
        guard = OutOfOrderGuard()
        t1 = datetime.now(tz=timezone.utc)
        t_old = t1 - timedelta(seconds=100)
        guard.check("node-a", "var-1", t1)
        # 不同 node 的旧数据不应被 node-a 的最大时间戳影响
        is_ooo, _ = guard.check("node-b", "var-1", t_old)
        assert is_ooo is False  # node-b 首次出现


# ── LightProcessingPipeline 测试 ───────────────────────────────────────────


class TestLightProcessingPipeline:
    """LightProcessingPipeline 集成测试。"""

    def test_valid_envelope_full_pipeline(self) -> None:
        """合法 envelope 应通过完整轻处理流程。"""
        pipeline = LightProcessingPipeline(
            dedup_size=10,
            ooo_tolerance_seconds=60,
        )
        envelope = {
            "schema_version": "1.0",
            "message_type": "state_snapshot",
            "source_id": "src-001",
            "message_id": "msg-pipe-001",
            "items": [
                {
                    "device_id": "dev-01",
                    "variable_key": "temp",
                    "value": 25.5,
                    "quality_code": "0",
                    "source_observed_at": datetime.now(tz=timezone.utc).isoformat(),
                }
            ],
        }

        result = pipeline.process(envelope)
        assert result["validated"] is True
        assert result["duplicate"] is False
        assert result["skipped"] is False
        assert len(result["items_enhanced"]) == 1
        # 质量码透传
        assert result["items_enhanced"][0]["quality_code"] == "0"
        # 不乱序
        assert result["out_of_order_items"] == []

    def test_validation_failure_skips_processing(self) -> None:
        """校验失败的 envelope 应 skip 且不进入去重。"""
        pipeline = LightProcessingPipeline()
        envelope = {
            "message_type": "",
            "source_id": "src-001",
            "items": [],
        }
        result = pipeline.process(envelope)
        assert result["validated"] is False
        assert result["skipped"] is True
        assert "validation_error" in result

    def test_duplicate_message_skips_processing(self) -> None:
        """重复消息应被去重并 skip。"""
        pipeline = LightProcessingPipeline()
        envelope = {
            "schema_version": "1.0",
            "message_type": "state_snapshot",
            "source_id": "src-001",
            "message_id": "dup-001",
            "items": [{"variable_key": "temp", "value": 25.5}],
        }
        r1 = pipeline.process(envelope)
        assert r1["duplicate"] is False
        assert r1["skipped"] is False

        r2 = pipeline.process(envelope)
        assert r2["duplicate"] is True
        assert r2["skipped"] is True

    def test_out_of_order_detection_in_pipeline(self) -> None:
        """包含乱序数据的 envelope 应被检测。"""
        pipeline = LightProcessingPipeline(ooo_tolerance_seconds=60)
        t1 = datetime.now(tz=timezone.utc)
        t_old = t1 - timedelta(seconds=120)

        # 先处理一条正常数据
        envelope1 = {
            "schema_version": "1.0",
            "message_type": "state_snapshot",
            "source_id": "src-001",
            "message_id": "msg-ooo-1",
            "items": [
                {
                    "device_id": "dev-01",
                    "variable_key": "power",
                    "value": 1500.0,
                    "source_observed_at": t1.isoformat(),
                }
            ],
        }
        pipeline.process(envelope1)

        # 再处理乱序数据
        envelope2 = {
            "schema_version": "1.0",
            "message_type": "state_snapshot",
            "source_id": "src-001",
            "message_id": "msg-ooo-2",
            "items": [
                {
                    "device_id": "dev-01",
                    "variable_key": "power",
                    "value": 1400.0,
                    "source_observed_at": t_old.isoformat(),
                }
            ],
        }
        result = pipeline.process(envelope2)
        assert result["validated"] is True
        assert result["skipped"] is False
        assert len(result["out_of_order_items"]) == 1
        # 超出 tolerance，建议 DLQ
        assert len(result["dlq_items"]) == 1

    def test_reset_pipeline(self) -> None:
        """pipeline reset 应重置校验器和乱序保护器（去重器不重置）。"""
        pipeline = LightProcessingPipeline()
        envelope = {
            "schema_version": "1.0",
            "message_type": "state_snapshot",
            "source_id": "src-001",
            "message_id": "msg-reset-01",
            "items": [{"variable_key": "temp", "value": 25.5}],
        }
        pipeline.process(envelope)
        assert pipeline.validator.error_count == 0
        assert pipeline.out_of_order_guard.total_count == 1
        pipeline.reset()
        assert pipeline.out_of_order_guard.total_count == 0
        # 去重器不重置，已处理的 message_id 仍然记录
        assert pipeline.deduplicator.cache_size == 1
