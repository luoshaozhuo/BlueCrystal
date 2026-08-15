"""HTTP REST shared source 模块。

对外暴露 HTTP REST 客户端 backend 和响应/结果模型。
当前为 python_lightweight_runner 级别实现，
基于 asyncio 标准库构建 HTTP 客户端。
"""
from pacific.whale.shared.source.http_rest.client import (
    HttpReadResult,
    HttpRestClientBackend,
    HttpResponseData,
)

__all__ = [
    "HttpReadResult",
    "HttpRestClientBackend",
    "HttpResponseData",
]
