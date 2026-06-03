"""speed layer pipeline runner 单元测试。

验证 LocalPipelineRunner 的注册/启动/停止/健康检查生命周期，
以及 FlinkPipelineAdapter 的 contract 行为和 InMemoryMetricsCollector 的指标收集。

被验证对象：
- whale.speed_layer.runner: LocalPipelineRunner, FlinkPipelineAdapter
- whale.speed_layer.metrics: InMemoryMetricsCollector

所属生命周期阶段：开发期验证（纯内存测试，不连接任何外部系统）。
使用 mock/fake/in-memory 替身隔离依赖。
不能证明：真实 Flink 集群的 job 提交和运行行为。
"""

from __future__ import annotations

import asyncio

import pytest

from whale.speed_layer.metrics import (
    InMemoryMetricsCollector,
    MetricsCollectorPort,
)
from whale.speed_layer.runner import (
    FlinkPipelineAdapter,
    FlinkPipelineConfig,
    LocalPipelineRunner,
    PipelineRunner,
)


class TestLocalPipelineRunner:
    """LocalPipelineRunner 单元测试。"""

    def test_is_pipeline_runner(self) -> None:
        """验证 LocalPipelineRunner 实现 PipelineRunner。"""
        runner = LocalPipelineRunner()
        assert isinstance(runner, PipelineRunner)

    def test_initial_writer_count_zero(self) -> None:
        """验证初始 writer_count 为 0。"""
        runner = LocalPipelineRunner()
        assert runner.writer_count == 0

    def test_register_writer(self) -> None:
        """验证注册 writer 后 writer_count 增长。"""
        runner = LocalPipelineRunner()

        async def dummy_run() -> None:
            pass

        runner.register_writer("test-writer", dummy_run)
        assert runner.writer_count == 1

    @pytest.mark.asyncio
    async def test_start_and_stop(self) -> None:
        """验证 runner 可正常启动和停止。"""
        runner = LocalPipelineRunner()
        run_count = 0

        async def counting_run() -> None:
            nonlocal run_count
            run_count += 1

        runner.register_writer("counter", counting_run)
        await runner.start()
        await asyncio.sleep(0.2)
        await runner.stop()
        assert run_count > 0

    @pytest.mark.asyncio
    async def test_health_returns_status(self) -> None:
        """验证 health 返回 writer 状态映射。"""
        runner = LocalPipelineRunner()

        async def dummy_run() -> None:
            await asyncio.sleep(0.1)

        runner.register_writer("writer-a", dummy_run)
        await runner.start()
        await asyncio.sleep(0.05)
        health = await runner.health()
        assert "writer-a" in health
        await runner.stop()

    @pytest.mark.asyncio
    async def test_multiple_writers(self) -> None:
        """验证多个 writer 可并发运行。"""
        runner = LocalPipelineRunner()
        counts: dict[str, int] = {"a": 0, "b": 0}

        async def make_runner(name: str) -> None:
            async def _run() -> None:
                counts[name] += 1
            return _run

        runner.register_writer("a", await make_runner("a"))
        runner.register_writer("b", await make_runner("b"))
        await runner.start()
        await asyncio.sleep(0.2)
        await runner.stop()
        assert counts["a"] > 0
        assert counts["b"] > 0


class TestFlinkPipelineAdapter:
    """FlinkPipelineAdapter contract adapter 测试。"""

    def test_is_pipeline_runner(self) -> None:
        """验证 FlinkPipelineAdapter 实现 PipelineRunner。"""
        config = FlinkPipelineConfig(job_name="whale-speed-layer")
        adapter = FlinkPipelineAdapter(config)
        assert isinstance(adapter, PipelineRunner)

    @pytest.mark.asyncio
    async def test_start_stop_noop(self) -> None:
        """验证 contract mode 下 start/stop 为空操作不报错。"""
        config = FlinkPipelineConfig()
        adapter = FlinkPipelineAdapter(config)
        await adapter.start()
        await adapter.stop()
        # 不抛异常即为通过

    @pytest.mark.asyncio
    async def test_health_returns_empty(self) -> None:
        """验证 contract mode 下 health 返回空映射。"""
        config = FlinkPipelineConfig()
        adapter = FlinkPipelineAdapter(config)
        result = await adapter.health()
        assert result == {}


class TestFlinkPipelineConfig:
    """FlinkPipelineConfig 配置模型测试。"""

    def test_default_values(self) -> None:
        """验证 FlinkPipelineConfig 默认值正确。"""
        config = FlinkPipelineConfig()
        assert config.job_name == "whale-speed-layer"
        assert config.parallelism == 1
        assert config.checkpoint_interval_ms == 60000
        assert config.enable_checkpointing is True
        assert config.state_backend == "filesystem"

    def test_custom_values(self) -> None:
        """验证 FlinkPipelineConfig 自定义值。"""
        config = FlinkPipelineConfig(
            job_name="my-job",
            parallelism=4,
            state_backend="rocksdb",
        )
        assert config.job_name == "my-job"
        assert config.parallelism == 4
        assert config.state_backend == "rocksdb"


class TestInMemoryMetricsCollector:
    """InMemoryMetricsCollector 单元测试。"""

    def test_is_metrics_collector_port(self) -> None:
        """验证 InMemoryMetricsCollector 实现 MetricsCollectorPort。"""
        collector = InMemoryMetricsCollector()
        assert isinstance(collector, MetricsCollectorPort)

    @pytest.mark.asyncio
    async def test_record_checkpoint(self) -> None:
        """验证 checkpoint 记录正确。"""
        collector = InMemoryMetricsCollector()
        await collector.record_checkpoint("writer-1", "topic-a", 0, 100)
        ck = collector.checkpoints["writer-1"]["topic-a"]
        assert ck[0] == 100

    @pytest.mark.asyncio
    async def test_record_lag(self) -> None:
        """验证 lag 记录正确。"""
        collector = InMemoryMetricsCollector()
        await collector.record_lag("writer-1", "topic-a", 0, 50)
        assert collector.lags["writer-1"]["topic-a"][0] == 50

    @pytest.mark.asyncio
    async def test_record_latency(self) -> None:
        """验证延迟记录和平均延迟计算正确。"""
        collector = InMemoryMetricsCollector()
        await collector.record_latency("writer-1", 10.0)
        await collector.record_latency("writer-1", 20.0)
        avg = collector.get_avg_latency("writer-1")
        assert avg == 15.0

    @pytest.mark.asyncio
    async def test_record_sink_success_and_failure(self) -> None:
        """验证 sink 成功/失败计数正确。"""
        collector = InMemoryMetricsCollector()
        await collector.record_sink_success("writer-1")
        await collector.record_sink_success("writer-1")
        await collector.record_sink_failure("writer-1", "timeout")

        assert collector.get_success_count("writer-1") == 2
        assert collector.get_failure_count("writer-1") == 1

    @pytest.mark.asyncio
    async def test_get_avg_latency_empty(self) -> None:
        """验证无延迟数据时平均延迟返回 0.0。"""
        collector = InMemoryMetricsCollector()
        avg = collector.get_avg_latency("unknown")
        assert avg == 0.0

    @pytest.mark.asyncio
    async def test_dump_contains_all_metrics(self) -> None:
        """验证 dump 导出包含所有指标类型。"""
        collector = InMemoryMetricsCollector()
        await collector.record_sink_success("writer-1")
        dump = collector.dump()
        assert "checkpoints" in dump
        assert "lags" in dump
        assert "latencies" in dump
        assert "sink_success_count" in dump
        assert "sink_failure_count" in dump
        assert "snapshot_at" in dump


# ── SpeedLayerWiring + LightProcessingPipeline 集成测试 ──────────────────────


class TestSpeedLayerWiringWithLightProcessor:
    """SpeedLayerWiring.with_light_processor() 装配验证。

    验证 LightProcessingPipeline 集成到 SpeedLayerWiring 构建的管道中，
    _LightFilteredSource 正确过滤消息并路由到 writer 或 DLQ。

    所有测试使用 InMemory 适配器（InMemoryMessageBus + InMemoryDeadLetterSink +
    MemoryRawIndexSink / MemoryStandardizedSink / InMemoryServingCache），
    不依赖真实外部服务。测试阶段为跨模块联调期验证。
    """

    def test_with_light_processor_builds_registers_writers(self) -> None:
        """验证 with_light_processor() 后 build() 注册 >= 4 个 writer。"""
        from whale.speed_layer.light_processor import LightProcessingPipeline
        from whale.speed_layer.runner import SpeedLayerWiring

        wiring = SpeedLayerWiring()
        wiring.with_memory()
        wiring.with_inmemory_dlq()
        wiring.with_light_processor(LightProcessingPipeline(dedup_size=100))

        runner = wiring.build()
        # with_memory 注册 raw_archive、raw_index、standardized、serving_cache
        assert runner.writer_count >= 4
        # 验证 light_processor 已配置
        assert wiring._light_processor is not None

    @pytest.mark.asyncio
    async def test_light_processor_integrated_pipeline(self) -> None:
        """验证合法消息经 _LightFilteredSource → writer 的完整路径。

        发布一条合法 envelope，通过 SpeedLayerWiring + light_processor 管道，
        验证消息被 raw_index writer 索引。
        """
        from datetime import datetime, timezone

        from whale.message_pipeline.adapters.in_memory import (
            InMemoryDeadLetterSink,
            InMemoryMessageBus,
        )
        from whale.message_pipeline.model import Envelope
        from whale.speed_layer.light_processor import LightProcessingPipeline
        from whale.speed_layer.runner import _LightFilteredSource
        from whale.speed_layer.writers import RawIndexWriter
        from whale.storage.raw_index import MemoryRawIndexSink

        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()
        index_sink = MemoryRawIndexSink()
        processor = LightProcessingPipeline(dedup_size=100)

        filtered_source = _LightFilteredSource(
            source=bus, processor=processor, dlq=dlq,
        )
        writer = RawIndexWriter(
            source=filtered_source, index=index_sink, dlq=dlq,
        )

        # 发布合法消息
        envelope = Envelope(
            schema_version="1.0",
            message_id="integrated-001",
            message_type="state_snapshot",
            trace_id="trace-001",
            source_id="src-001",
            published_at=datetime.now(tz=timezone.utc),
            items=[{
                "device_id": "dev-01",
                "variable_key": "power",
                "value": 1500.0,
                "quality_code": "0",
                "source_observed_at": datetime.now(tz=timezone.utc).isoformat(),
            }],
        )
        await bus.publish(envelope)

        # 运行 writer 消费
        indexed = await writer.run("whale.state_snapshot", "l4-test-group")
        assert indexed >= 1, f"应索引至少 1 条，实际 {indexed}"
        assert len(index_sink.records) >= 1
        assert index_sink.records[0]["message_id"] == "integrated-001"

    @pytest.mark.asyncio
    async def test_duplicate_message_id_not_passed_to_writer(self) -> None:
        """验证重复 message_id 被 _LightFilteredSource 去重，不传给 writer。

        发布两条相同 message_id 的 envelope，只应输出一条，重复的被跳过。
        """
        from datetime import datetime, timezone

        from whale.message_pipeline.adapters.in_memory import (
            InMemoryDeadLetterSink,
            InMemoryMessageBus,
        )
        from whale.message_pipeline.model import Envelope
        from whale.speed_layer.light_processor import LightProcessingPipeline
        from whale.speed_layer.runner import _LightFilteredSource

        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()
        processor = LightProcessingPipeline(dedup_size=100)
        filtered_source = _LightFilteredSource(
            source=bus, processor=processor, dlq=dlq,
        )

        now = datetime.now(tz=timezone.utc)
        items = [{
            "device_id": "dev-dup",
            "variable_key": "temp",
            "value": 25.0,
            "quality_code": "0",
            "source_observed_at": now.isoformat(),
        }]

        # 发布两条相同 message_id 的消息
        env1 = Envelope(
            schema_version="1.0",
            message_id="dup-001",
            message_type="state_snapshot",
            trace_id="t1",
            source_id="src-dup",
            published_at=now,
            items=items,
        )
        env2 = Envelope(
            schema_version="1.0",
            message_id="dup-001",
            message_type="state_snapshot",
            trace_id="t2",
            source_id="src-dup",
            published_at=now,
            items=items,
        )
        await bus.publish(env1)
        await bus.publish(env2)

        # 消费验证：第一条应通过，第二条应被去重跳过
        consumed: list[Envelope] = []
        async for env in filtered_source.consume("whale.state_snapshot", "l4-dup-group"):
            consumed.append(env)
            if len(consumed) >= 2:
                break

        assert len(consumed) == 1, (
            f"重复消息应被过滤，期望 1 条，实际 {len(consumed)}"
        )
        assert consumed[0].message_id == "dup-001"
        # 验证去重器统计正确
        assert processor.deduplicator.total_checked == 2
        assert processor.deduplicator.duplicate_count == 1

    @pytest.mark.asyncio
    async def test_out_of_order_message_handled_by_policy(self) -> None:
        """验证乱序 observed_at 被 OutOfOrderGuard 检测并标记。

        先消费一条较新的数据，再消费一条旧数据（超出 tolerance），
        验证旧数据被检测到乱序且写入 DLQ。
        """
        from datetime import datetime, timedelta, timezone

        from whale.message_pipeline.adapters.in_memory import (
            InMemoryDeadLetterSink,
            InMemoryMessageBus,
        )
        from whale.message_pipeline.model import Envelope
        from whale.speed_layer.light_processor import LightProcessingPipeline
        from whale.speed_layer.runner import _LightFilteredSource

        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()
        # tolerance 设为 30 秒，乱序差异 120 秒应触发 DLQ
        processor = LightProcessingPipeline(
            dedup_size=100, ooo_tolerance_seconds=30,
        )
        filtered_source = _LightFilteredSource(
            source=bus, processor=processor, dlq=dlq,
        )

        now = datetime.now(tz=timezone.utc)
        old_time = now - timedelta(seconds=120)

        # 先发布较新数据
        env_new = Envelope(
            schema_version="1.0",
            message_id="ooo-001",
            message_type="state_snapshot",
            trace_id="t-new",
            source_id="src-ooo",
            published_at=now,
            items=[{
                "device_id": "dev-ooo",
                "variable_key": "power",
                "value": 1500.0,
                "quality_code": "0",
                "source_observed_at": now.isoformat(),
            }],
        )
        # 再发布 2 分钟前的旧数据
        env_old = Envelope(
            schema_version="1.0",
            message_id="ooo-002",
            message_type="state_snapshot",
            trace_id="t-old",
            source_id="src-ooo",
            published_at=old_time,
            items=[{
                "device_id": "dev-ooo",
                "variable_key": "power",
                "value": 1400.0,
                "quality_code": "0",
                "source_observed_at": old_time.isoformat(),
            }],
        )
        await bus.publish(env_new)
        await bus.publish(env_old)

        consumed: list[Envelope] = []
        async for env in filtered_source.consume("whale.state_snapshot", "l4-ooo-group"):
            consumed.append(env)
            if len(consumed) >= 2:
                break

        # 两条消息都应被消费（不一致消息仍透传，但乱序 item 进入 DLQ）
        assert len(consumed) >= 1
        # 验证乱序检测器工作
        assert processor.out_of_order_guard.out_of_order_count >= 1
        # 严重乱序的 item 应写入 DLQ
        assert len(dlq.dead_letters) >= 1, (
            f"严重乱序 item 应写入 DLQ，实际 DLQ 有 {len(dlq.dead_letters)} 条"
        )
        assert "out_of_order_beyond_tolerance" in str(dlq.dead_letters[0].get("error", ""))

    @pytest.mark.asyncio
    async def test_quality_code_passthrough_in_pipeline(self) -> None:
        """验证 quality_code 经轻处理管线原样透传到 writer。

        发布带 quality_code="3" 的消息，验证 items_enhanced 中 quality_code
        仍为 "3"，未被修改。
        """
        from datetime import datetime, timezone

        from whale.message_pipeline.adapters.in_memory import (
            InMemoryDeadLetterSink,
            InMemoryMessageBus,
        )
        from whale.message_pipeline.model import Envelope
        from whale.speed_layer.light_processor import LightProcessingPipeline
        from whale.speed_layer.runner import _LightFilteredSource

        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()
        processor = LightProcessingPipeline(dedup_size=100)
        filtered_source = _LightFilteredSource(
            source=bus, processor=processor, dlq=dlq,
        )

        envelope = Envelope(
            schema_version="1.0",
            message_id="qc-001",
            message_type="state_snapshot",
            trace_id="trace-qc",
            source_id="src-qc",
            published_at=datetime.now(tz=timezone.utc),
            items=[{
                "device_id": "dev-qc",
                "variable_key": "wind_speed",
                "value": 12.5,
                "quality_code": "3",  # 非 0 质量码
                "source_observed_at": datetime.now(tz=timezone.utc).isoformat(),
            }],
        )
        await bus.publish(envelope)

        consumed: list[Envelope] = []
        async for env in filtered_source.consume("whale.state_snapshot", "l4-qc-group"):
            consumed.append(env)
            if len(consumed) >= 1:
                break

        assert len(consumed) == 1
        # 验证 items_enhanced 中 quality_code 原样透传
        enhanced_items = consumed[0].items
        assert len(enhanced_items) == 1
        assert enhanced_items[0].get("quality_code") == "3", (
            f"quality_code 应为 '3'，实际 {enhanced_items[0].get('quality_code')}"
        )

    @pytest.mark.asyncio
    async def test_invalid_envelope_goes_to_dlq_or_error(self) -> None:
        """验证 schema 校验失败的 envelope 被写入 DLQ，不传给 writer。

        发布一条缺少必要字段的 envelope（空 message_type、空 items），
        验证其被 _LightFilteredSource 拦截并写入 DLQ。
        """
        from datetime import datetime, timezone

        from whale.message_pipeline.adapters.in_memory import (
            InMemoryDeadLetterSink,
            InMemoryMessageBus,
        )
        from whale.message_pipeline.model import Envelope
        from whale.speed_layer.light_processor import LightProcessingPipeline
        from whale.speed_layer.runner import _LightFilteredSource

        bus = InMemoryMessageBus()
        dlq = InMemoryDeadLetterSink()
        processor = LightProcessingPipeline(dedup_size=100)
        filtered_source = _LightFilteredSource(
            source=bus, processor=processor, dlq=dlq,
        )

        # 构造无效 envelope：空 source_id + 空 items
        # message_type 保持有效值以确保 topic 路由到 "whale.state_snapshot"
        invalid_envelope = Envelope(
            schema_version="1.0",
            message_id="invalid-001",
            message_type="state_snapshot",  # 有效值，确保 topic 路由正确
            trace_id="trace-inv",
            source_id="",  # 空 → 校验失败
            published_at=datetime.now(tz=timezone.utc),
            items=[],  # 空 → 校验失败
        )
        await bus.publish(invalid_envelope)

        consumed: list[Envelope] = []
        async for env in filtered_source.consume("whale.state_snapshot", "l4-inv-group"):
            consumed.append(env)
            if len(consumed) >= 1:
                break

        # 无效消息不应传递给 writer
        assert len(consumed) == 0, (
            f"无效 envelope 不应输出，实际输出 {len(consumed)} 条"
        )
        # 应写入 DLQ
        assert len(dlq.dead_letters) >= 1, (
            f"无效 envelope 应写入 DLQ，实际 DLQ 有 {len(dlq.dead_letters)} 条"
        )
        dlq_entry = dlq.dead_letters[0]
        error_msg = str(dlq_entry.get("error", ""))
        assert len(error_msg) > 0, "DLQ 错误信息不应为空"
        # 错误信息应包含 source_id 或 items 缺失相关描述
        assert "source_id" in error_msg or "items" in error_msg, (
            f"错误信息应包含校验失败字段，实际: {error_msg}"
        )
