"""Ingest 模块入口。

注册 ingest 的依赖注入容器、API 路由和应用启动逻辑。
负责将 ingest 挂载到主 FastAPI 应用和 scheduler。
"""

from whale.ingest.message_pipeline import IngestMessagePipeline, InMemoryIngestMessagePipeline

__all__ = [
    "InMemoryIngestMessagePipeline",
    "IngestMessagePipeline",
]
