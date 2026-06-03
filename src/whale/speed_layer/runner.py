"""speed layer pipeline runner。

协调多个 writer 的启动、停止和健康检查，提供本地 asyncio runner 和
Flink runtime adapter contract。

本文件包含：
- PipelineRunner: 管道运行器抽象端口。
- LocalPipelineRunner: 本地 asyncio 实现（测试和单机部署）。
- SpeedLayerWiring: speed layer 装配入口，组装 source → light_processor → writers 管道。
- _LightFilteredSource: 内部过滤消息源，将 LightProcessingPipeline 透明插入消费链路。
- FlinkPipelineAdapter: Flink runtime adapter contract（environment-pending）。
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from whale.message_pipeline.model import Envelope, MessageOffset, TopicSpec
from whale.message_pipeline.ports import (
    DeadLetterSinkPort,
    MessageSourcePort,
)
from whale.speed_layer.light_processor import LightProcessingPipeline
from whale.speed_layer.writers import (
    RawArchiveWriter,
    RawIndexWriter,
    ServingCacheUpdater,
    StandardizedWriter,
)
from whale.storage.raw_archive import LocalCompressedArchiveSink

logger = logging.getLogger(__name__)


class PipelineRunner(ABC):
    """管道运行器抽象端口。

    定义 speed layer pipeline 的运行时生命周期：启动、停止和健康检查。

    实现方责任：
    - 管理 writer 实例的生命周期。
    - 协调多个 writer 的并发运行。
    - 提供健康检查和 metrics 收集。

    不负责：
    - writer 内部的具体消费和写入逻辑。
    """

    @abstractmethod
    async def start(self) -> None:
        """启动所有 writer。

        异步启动，不阻塞调用方。

        Raises:
            RuntimeError: 启动失败。
        """
        ...

    @abstractmethod
    async def stop(self) -> None:
        """停止所有 writer 并等待完成。

        优雅关闭，先停止消费，再等待正在处理的消息完成。

        Raises:
            RuntimeError: 停止过程中出现错误。
        """
        ...

    @abstractmethod
    async def health(self) -> dict[str, bool]:
        """返回各 writer 的健康状态。

        Returns:
            writer 名称到健康状态（True=健康）的映射。
        """
        ...


class LocalPipelineRunner(PipelineRunner):
    """本地 asyncio pipeline runner 实现。

    在单个 asyncio 事件循环中协调多个 writer 的并发运行。
    每个 writer 作为独立 task 运行，支持启动/停止/健康检查。

    本 runner 用于开发、测试和单机部署。生产环境多进程/多机部署推荐使用
    FlinkPipelineAdapter 或 Kubernetes operator。

    Attributes:
        _writers: 已注册的 writer 任务工厂列表。
        _tasks: 运行中的 asyncio Task 列表。
        _running: 是否正在运行。
    """

    def __init__(
        self,
        *,
        light_processor: LightProcessingPipeline | None = None,
    ) -> None:
        """初始化 pipeline runner。

        Args:
            light_processor: 可选的轻处理管线实例。如果提供，SpeedLayerWiring
                在装配时会使用它构建过滤消息源。直接使用 LocalPipelineRunner
                的场景中，调用方应自行在 writer 注册时插入处理逻辑。
        """
        self._writers: list[
            tuple[str, Callable[[], Awaitable[None]]]
        ] = []
        """writer 注册列表：(name, coroutine_factory)。"""
        self._tasks: list[asyncio.Task[Any]] = []
        """运行中的 asyncio Task。"""
        self._running = False
        self._light_processor = light_processor
        """可选的轻处理管线引用。"""

    def register_writer(
        self,
        name: str,
        run_fn: Callable[[], Awaitable[None]],
    ) -> None:
        """注册一个 writer 到 runner。

        Args:
            name: writer 名称（用于健康检查和日志）。
            run_fn: 无参数异步函数，执行 writer 的 run 循环。
        """
        self._writers.append((name, run_fn))

    async def start(self) -> None:
        """启动所有已注册的 writer。

        每个 writer 创建独立的 asyncio Task，并发运行。
        如果任何 writer 抛出未捕获异常，记录日志但不停止其他 writer。
        """
        if self._running:
            return
        self._running = True
        for name, run_fn in self._writers:
            task = asyncio.create_task(
                self._run_writer(name, run_fn),
                name=f"writer-{name}",
            )
            self._tasks.append(task)
        logger.info("pipeline runner 已启动，writer 数量=%d", len(self._tasks))

    async def stop(self) -> None:
        """停止所有并发 writer。

        先取消所有 task，再等待它们完成。设置超时避免永久阻塞。
        """
        if not self._running:
            return
        self._running = False
        for task in self._tasks:
            if not task.done():
                task.cancel()
        if self._tasks:
            await asyncio.wait(self._tasks, timeout=10.0)
        self._tasks.clear()
        logger.info("pipeline runner 已停止")

    async def health(self) -> dict[str, bool]:
        """返回各 writer 的健康状态。

        Health 规则：task 未完成且未被取消 = 健康。

        Returns:
            writer 名称到健康状态的映射。
        """
        result: dict[str, bool] = {}
        for (name, _), task in zip(self._writers, self._tasks):
            result[name] = not task.done() if task else False
        return result

    async def _run_writer(
        self,
        name: str,
        run_fn: Callable[[], Awaitable[None]],
    ) -> None:
        """包装 writer 执行，捕获未处理异常。

        记录异常但不重新抛出，避免影响其他 writer。

        Args:
            name: writer 名称。
            run_fn: writer 执行函数。
        """
        try:
            while self._running:
                await run_fn()
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            logger.info("writer %s 被取消", name)
        except Exception:
            logger.exception("writer %s 发生未处理异常", name)

    @property
    def writer_count(self) -> int:
        """已注册的 writer 数量。"""
        return len(self._writers)


class _LightFilteredSource(MessageSourcePort):
    """轻处理过滤消息源。

    包装原始 MessageSourcePort，在消息消费时先经过 LightProcessingPipeline 处理，
    再输出给下游 writer。schema 校验失败的消息写入 DLQ，重复消息跳过，
    超出 tolerance 的乱序 items 写入 DLQ。

    本类是 SpeedLayerWiring 内部实现细节，不对外暴露。被包装的 source 的
    commit() 和 seek() 直接委托给原始 source。
    """

    def __init__(
        self,
        source: MessageSourcePort,
        processor: LightProcessingPipeline,
        dlq: DeadLetterSinkPort,
    ) -> None:
        """初始化轻处理过滤源。

        Args:
            source: 被包装的原始消息源。
            processor: 轻处理管线实例。
            dlq: 死信队列 sink，用于接收校验失败和严重乱序的消息。
        """
        self._source = source
        self._processor = processor
        self._dlq = dlq

    async def consume(
        self, topic: str, group_id: str
    ) -> AsyncIterator[Envelope]:
        """从原始 source 消费消息，经轻处理管线过滤后输出。

        处理流程：
        1. 从原始 source 获取 envelope。
        2. 转换为 dict 后送入 LightProcessingPipeline。
        3. 校验失败 → 写入 DLQ，跳过。
        4. 重复消息 → 跳过。
        5. 正常消息 → 用增强后的 items 构建新的 Envelope，yield。
        6. 严重乱序 items → 单独写入 DLQ。

        Args:
            topic: 消费 topic 名称。
            group_id: consumer group ID。

        Yields:
            经轻处理增强后的 Envelope（items 已添加 quality_code 透传和
            乱序标记）。
        """
        async for envelope in self._source.consume(topic, group_id):
            # 转换为 dict 供轻处理管线处理
            envelope_dict: dict[str, Any] = {
                "schema_version": envelope.schema_version,
                "message_id": envelope.message_id,
                "message_type": envelope.message_type,
                "trace_id": envelope.trace_id,
                "source_id": envelope.source_id,
                "published_at": envelope.published_at.isoformat(),
                "items": envelope.items,
            }
            result = self._processor.process(envelope_dict)

            if result["skipped"]:
                # 校验失败：原始 envelope 写入 DLQ
                if not result["validated"]:
                    error = result.get(
                        "validation_error",
                        "light_processor schema 校验失败",
                    )
                    await self._dlq.send(envelope, str(error), retry_count=0)
                # 重复消息：静默跳过
                continue

            # 严重乱序 items 单独写入 DLQ
            dlq_items = result.get("dlq_items", [])
            if dlq_items:
                dlq_envelope = Envelope(
                    schema_version=envelope.schema_version,
                    message_id=f"{envelope.message_id}-dlq",
                    message_type=envelope.message_type,
                    trace_id=envelope.trace_id,
                    source_id=envelope.source_id,
                    published_at=envelope.published_at,
                    items=dlq_items,
                )
                await self._dlq.send(
                    dlq_envelope,
                    "out_of_order_beyond_tolerance",
                    retry_count=0,
                )

            # 构建增强后的 envelope（items 已含透传 quality_code 和乱序标记）
            enhanced = Envelope(
                schema_version=envelope.schema_version,
                message_id=envelope.message_id,
                message_type=envelope.message_type,
                trace_id=envelope.trace_id,
                source_id=envelope.source_id,
                published_at=envelope.published_at,
                items=result["items_enhanced"],
            )
            yield enhanced

    async def commit(self, offsets: list[MessageOffset]) -> None:
        """委托 commit 到原始 source。"""
        await self._source.commit(offsets)

    async def seek(self, offsets: list[MessageOffset]) -> None:
        """委托 seek 到原始 source。"""
        await self._source.seek(offsets)


class SpeedLayerWiring:
    """speed layer 装配入口。

    提供从配置组装完整 pipeline 的工厂方法，将 message_pipeline source、
    storage sink、DLQ 组装为可运行的 writer 并注册到 runner。

    支持以下装配模式：
    - memory: 纯内存实现，用于测试和 smoke。
    - local: 本地文件 + 内存 sink，用于单机开发。
    - prod: 真实 Kafka + S3 + TDengine + Redis，用于生产部署。

    Attributes:
        runner: 已装配的 LocalPipelineRunner 实例。
    """

    def __init__(self) -> None:
        """初始化空的装配器。"""
        self.runner = LocalPipelineRunner()
        self._source: MessageSourcePort | None = None
        self._archive: Any = None
        self._manifest: Any = None
        self._index: Any = None
        self._standardized_sink: Any = None
        self._cache: Any = None
        self._dlq: Any = None
        self._light_processor: LightProcessingPipeline | None = None
        """实时轻处理管线，None 表示不经轻处理直接消费。"""

    def with_memory(self) -> "SpeedLayerWiring":
        """装配纯内存链路（Ingest → InMemory → InMemory sinks）。

        所有组件使用 InMemory 实现，适用于单元测试和 smoke。

        Returns:
            self，支持链式调用。
        """
        from whale.message_pipeline.adapters.in_memory import (
            InMemoryDeadLetterSink,
            InMemoryMessageBus,
        )
        from whale.storage.raw_archive import InMemoryManifestRepository
        from whale.storage.raw_index import MemoryRawIndexSink
        from whale.storage.serving_cache import InMemoryServingCache
        from whale.storage.standardized import MemoryStandardizedSink

        self._source = InMemoryMessageBus()
        self._archive = LocalCompressedArchiveSink("/tmp/whale_raw_archive")
        self._manifest = InMemoryManifestRepository()
        self._index = MemoryRawIndexSink()
        self._standardized_sink = MemoryStandardizedSink()
        self._cache = InMemoryServingCache()
        self._dlq = InMemoryDeadLetterSink()
        return self

    def with_kafka_source(
        self, bootstrap_servers: list[str], group_id_prefix: str
    ) -> "SpeedLayerWiring":
        """使用 Kafka consumer 作为消息源。

        Args:
            bootstrap_servers: Kafka broker 地址列表。
            group_id_prefix: consumer group ID 前缀。

        Returns:
            self，支持链式调用。
        """
        from whale.message_pipeline.adapters.kafka import KafkaSourceAdapter

        self._source = KafkaSourceAdapter(
            bootstrap_servers=bootstrap_servers,
            group_id=f"{group_id_prefix}-main",
            topic_specs=[TopicSpec(name="whale.ingest.state")],
        )
        return self

    def with_s3_archive(
        self, endpoint_url: str, bucket: str, **kwargs: Any
    ) -> "SpeedLayerWiring":
        """使用 S3/MinIO 作为 raw_archive 后端。

        Args:
            endpoint_url: S3/MinIO endpoint URL。
            bucket: S3 bucket 名称。
            **kwargs: 传递给 S3RawArchiveSink 的额外参数。

        Returns:
            self，支持链式调用。
        """
        from whale.storage.raw_archive import S3RawArchiveSink, S3ManifestRepository

        self._archive = S3RawArchiveSink(
            endpoint_url=endpoint_url, bucket=bucket, **kwargs
        )
        # 从 S3RawArchiveSink 获取内部 client 创建 manifest repo
        # 此处使用独立 S3ManifestRepository（需独立的 boto3 client）
        import boto3  # type: ignore[import-untyped]

        s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=kwargs.get("region_name", "us-east-1"),
            use_ssl=kwargs.get("use_ssl", False),
            aws_access_key_id=kwargs.get("access_key", ""),
            aws_secret_access_key=kwargs.get("secret_key", ""),
        )
        self._manifest = S3ManifestRepository(
            s3_client=s3_client,
            bucket=bucket,
            prefix=kwargs.get("prefix", "raw_archive/"),
        )
        return self

    def with_tdengine_index(
        self, dsn: str, **kwargs: Any
    ) -> "SpeedLayerWiring":
        """使用 TDengine 作为 raw_index 后端。

        Args:
            dsn: TDengine 连接字符串。
            **kwargs: 传递给 TdengineRawIndexSink 的额外参数。

        Returns:
            self，支持链式调用。
        """
        from whale.storage.raw_index import TdengineRawIndexSink

        self._index = TdengineRawIndexSink(dsn=dsn, **kwargs)
        return self

    def with_tdengine_standardized(
        self, dsn: str, **kwargs: Any
    ) -> "SpeedLayerWiring":
        """使用 TDengine 作为 standardized 后端。

        Args:
            dsn: TDengine 连接字符串。
            **kwargs: 传递给 TdengineStandardizedSink 的额外参数。

        Returns:
            self，支持链式调用。
        """
        from whale.storage.standardized import TdengineStandardizedSink

        self._standardized_sink = TdengineStandardizedSink(dsn=dsn, **kwargs)
        return self

    def with_redis_cache(
        self, redis_url: str, **kwargs: Any
    ) -> "SpeedLayerWiring":
        """使用 Redis 作为 serving cache 后端。

        Args:
            redis_url: Redis 连接 URL。
            **kwargs: 传递给 RedisServingCache 的额外参数。

        Returns:
            self，支持链式调用。
        """
        from whale.storage.serving_cache import RedisServingCache

        self._cache = RedisServingCache(redis_url=redis_url, **kwargs)
        return self

    def with_inmemory_dlq(self) -> "SpeedLayerWiring":
        """使用内存 DLQ sink。

        Returns:
            self，支持链式调用。
        """
        from whale.message_pipeline.adapters.in_memory import InMemoryDeadLetterSink

        self._dlq = InMemoryDeadLetterSink()
        return self

    def with_light_processor(
        self, processor: LightProcessingPipeline
    ) -> "SpeedLayerWiring":
        """配置实时轻处理管线。

        在消费链路中插入 LightProcessingPipeline，每条消息在进入 writer 前
        先经过 schema 校验、message_id 去重、质量码透传和乱序保护。

        向后兼容：如果不调用此方法，行为与原有逻辑一致，消息不经轻处理
        直接进入 writer。

        Args:
            processor: 已初始化的 LightProcessingPipeline 实例。

        Returns:
            self，支持链式调用。
        """
        self._light_processor = processor
        return self

    def build(
        self,
        topic: str = "whale.ingest.state",
        raw_archive_group: str = "whale-speed-layer-raw-archive",
        raw_index_group: str = "whale-speed-layer-raw-index",
        standardized_group: str = "whale-speed-layer-standardized",
        serving_cache_group: str = "whale-speed-layer-serving-cache",
    ) -> LocalPipelineRunner:
        """将已配置的组件组装为可运行的 pipeline。

        将所有配置的 source、sink、DLQ 组合为 writer 并注册到 runner。
        每个 writer 分配独立的 consumer group ID。

        Args:
            topic: 消费 topic 名称。
            raw_archive_group: raw_archive writer 的 consumer group。
            raw_index_group: raw_index writer 的 consumer group。
            standardized_group: standardized writer 的 consumer group。
            serving_cache_group: serving_cache writer 的 consumer group。

        Returns:
            已装配完成的 LocalPipelineRunner 实例。

        Raises:
            RuntimeError: 未配置 source。
        """
        if self._source is None:
            raise RuntimeError(
                "未配置 message source（调用 with_memory() 或 with_kafka_source()）"
            )
        if self._dlq is None:
            raise RuntimeError(
                "未配置 DLQ sink（调用 with_inmemory_dlq()）"
            )

        # 如果配置了轻处理管线，创建过滤源包装原始 source
        effective_source: MessageSourcePort = self._source
        if self._light_processor is not None:
            effective_source = _LightFilteredSource(
                source=self._source,
                processor=self._light_processor,
                dlq=self._dlq,
            )
            logger.info("SpeedLayerWiring 已启用 light_processor 过滤")

        # raw_archive writer
        if self._archive and self._manifest:
            archive_runner = RawArchiveWriter(
                source=effective_source,
                archive=self._archive,
                manifest=self._manifest,
                dlq=self._dlq,
            )

            async def run_archive() -> None:
                await archive_runner.run(topic, raw_archive_group)

            self.runner.register_writer("raw_archive", run_archive)

        # raw_index writer
        if self._index:
            index_runner = RawIndexWriter(
                source=effective_source,
                index=self._index,
                dlq=self._dlq,
            )

            async def run_index() -> None:
                await index_runner.run(topic, raw_index_group)

            self.runner.register_writer("raw_index", run_index)

        # standardized writer
        if self._standardized_sink:
            standardized_runner = StandardizedWriter(
                source=effective_source,
                sink=self._standardized_sink,
                dlq=self._dlq,
            )

            async def run_standardized() -> None:
                await standardized_runner.run(topic, standardized_group)

            self.runner.register_writer("standardized", run_standardized)

        # serving cache updater
        if self._cache:
            cache_runner = ServingCacheUpdater(
                source=effective_source,
                cache=self._cache,
                dlq=self._dlq,
            )

            async def run_cache() -> None:
                await cache_runner.run(topic, serving_cache_group)

            self.runner.register_writer("serving_cache", run_cache)

        logger.info(
            "SpeedLayerWiring 装配完成，writer 数量=%d", self.runner.writer_count
        )
        return self.runner


@dataclass
class FlinkPipelineConfig:
    """Flink pipeline 运行时配置。

    定义 Flink job 的基础参数。仅用于 contract adapter 的配置校验。

    Attributes:
        job_name: Flink job 名称。
        parallelism: 默认并行度。
        checkpoint_interval_ms: checkpoint 间隔（毫秒）。
        enable_checkpointing: 是否启用 checkpoint。
        state_backend: 状态后端类型（filesystem / rocksdb）。
    """
    job_name: str = "whale-speed-layer"
    parallelism: int = 1
    checkpoint_interval_ms: int = 60000
    enable_checkpointing: bool = True
    state_backend: str = "filesystem"

class FlinkPipelineAdapter(PipelineRunner):
    """Flink runtime pipeline adapter（contract adapter）。

    environment-pending: 需要 Flink 集群环境和 PyFlink 依赖。
    当前为 contract adapter，仅提供配置校验和接口骨架。

    不建议在本轮提交生产 Flink job jar。

    Attributes:
        _config: Flink pipeline 配置。
        _config_valid: 配置是否有效。
    """

    def __init__(self, config: FlinkPipelineConfig) -> None:
        """初始化 Flink pipeline adapter。

        Args:
            config: Flink pipeline 配置。
        """
        self._config = config
        self._config_valid = bool(config.job_name)
        # environment-pending: Flink 集群环境依赖

    async def start(self) -> None:
        """提交 Flink job（contract-only 模式）。

        environment-pending: 空操作。真实环境下通过 PyFlink 提交 job。
        """
        pass

    async def stop(self) -> None:
        """停止 Flink job（contract-only 模式）。

        environment-pending: 空操作。
        """
        pass

    async def health(self) -> dict[str, bool]:
        """返回 Flink job 健康状态（contract-only 模式）。

        environment-pending: 返回空映射。
        """
        return {}
