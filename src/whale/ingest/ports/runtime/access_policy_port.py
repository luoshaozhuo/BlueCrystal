"""ingest 运行时 access policy port。

负责 相关功能，包含并发模型、租约、fencing token、
异常传播和资源释放语义。
"""

from __future__ import annotations

from typing import Protocol

from starlette.requests import Request


class AccessPolicyPort(Protocol):
    """评估请求是否被授权对给定资源和操作执行访问。返回 AccessDecision 对象。"""

    def authorize(
        self,
        request: Request,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
    ) -> bool:
        """如果请求允许返回 True，否则返回 False。"""
