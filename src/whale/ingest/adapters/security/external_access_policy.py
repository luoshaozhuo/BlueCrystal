"""基于外部 HTTP 的 ingest 运行时访问策略适配器。将权限决策委托给远程授权服务。"""

from __future__ import annotations

import json
import logging
import time

import urllib.request
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

from starlette.requests import Request

from whale.ingest.ports.runtime.access_policy_port import AccessPolicyPort as RuntimeAccessPolicyPort
from whale.shared.crosscutting.auth import (
    AccessDecision,
    AccessPolicyPort,
    Permission,
    Principal,
)

logger = logging.getLogger(__name__)


class ExternalAccessPolicy(AccessPolicyPort, RuntimeAccessPolicyPort):
    """基于外部 HTTP 授权服务的访问策略。将权限决策委托给远程端点，按 HTTP 响应码判断。"""

    def __init__(
        self,
        endpoint_url: str,
        *,
        timeout_seconds: float = 5.0,
        fail_closed: bool = True,
        cache_ttl_seconds: int = 0,
    ) -> None:
        """初始化外部 HTTP 授权策略。Args: endpoint_url: 授权服务 URL。timeout_seconds: 请求超时。"""
        self._endpoint_url = endpoint_url.rstrip("/") + "/authorize"
        self._timeout = timeout_seconds
        self._opener = build_opener(ProxyHandler({}))
        self._fail_closed = fail_closed
        self._cache_ttl = cache_ttl_seconds
        self._cache: dict[str, tuple[bool, float]] = {}
        self.last_error: Exception | None = None
        self.last_status_code: int | None = None

    def evaluate(self, principal: Principal, permission: Permission) -> AccessDecision:
        """委托给外部服务并将响应映射为 AccessDecision 对象。处理超时和连接失败。"""
        cache_key = f"{principal.principal_id}:{permission.action}:{permission.resource_type}:{permission.resource_id or ''}"
        now = time.monotonic()

        # Check cache
        if self._cache_ttl > 0:
            cached = self._cache.get(cache_key)
            if cached is not None and (now - cached[1]) < self._cache_ttl:
                return AccessDecision(allowed=cached[0])

        # Build request payload
        payload = {
            "principal_id": principal.principal_id,
            "roles": list(principal.roles),
            "action": permission.action,
            "resource_type": permission.resource_type,
            "resource_id": permission.resource_id,
        }
        body = json.dumps(payload).encode("utf-8")

        try:
            req = urllib.request.Request(
                self._endpoint_url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self._opener.open(req, timeout=self._timeout) as resp:
                self.last_status_code = resp.status
                data = json.loads(resp.read().decode("utf-8"))
                allowed = bool(data.get("allowed", False))
                reason = str(data.get("reason", "")) if not allowed else ""

            # Cache all decisions (both allow and deny)
            if self._cache_ttl > 0:
                self._cache[cache_key] = (allowed, now)

            self.last_error = None
            return AccessDecision(allowed=allowed, reason=reason)

        except (URLError, OSError, json.JSONDecodeError, ValueError) as exc:
            self.last_error = exc
            self.last_status_code = None

            if self._fail_closed:
                logger.warning("Access policy unreachable, denying: %s", exc)
                return AccessDecision(
                    allowed=False,
                    reason=f"external_policy_unreachable: {exc}",
                )
            logger.warning("Access policy unreachable, failing open: %s", exc)
            return AccessDecision(
                allowed=True,
                reason=f"external_policy_fail_open: {exc}",
            )

    def authorize(
        self,
        request: Request,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
    ) -> bool:
        """检查请求是否对指定操作和资源授权。返回布尔值。"""
        decision = self.evaluate(
            _principal_from_request(request),
            Permission(
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
            ),
        )
        return decision.allowed


def _principal_from_request(request: Request) -> Principal:
    """从请求头构造一个共享授权主体。提取 x-actor 和 x-roles 信息。"""
    actor = (request.headers.get("x-actor") or "anonymous").strip() or "anonymous"
    raw_roles = request.headers.get("x-roles", "")
    roles = tuple(role.strip() for role in raw_roles.split(",") if role.strip())
    return Principal(
        principal_id=actor,
        principal_type="request",
        roles=roles,
    )
