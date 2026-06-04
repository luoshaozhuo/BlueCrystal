"""Ingest 模块入口。

注册 ingest 的依赖注入容器、API 路由和应用启动逻辑。
负责将 ingest 挂载到主 FastAPI 应用和 scheduler。

子模块：
- message_pipeline: 消息管道（Kafka/InMemory）。
- file_ingest: 文件接入最小闭环。
- bundle: 配置 bundle 管理。
"""

from whale.ingest.message_pipeline import IngestMessagePipeline, InMemoryIngestMessagePipeline

__all__ = [
    "InMemoryIngestMessagePipeline",
    "IngestMessagePipeline",
]
