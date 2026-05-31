"""安全策略适配器。

实现访问控制和安全分区策略。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from starlette.requests import Request

from whale.ingest.ports.runtime.access_policy_port import AccessPolicyPort as RuntimeAccessPolicyPort
from whale.shared.crosscutting.auth import (
    AccessDecision,
    AccessPolicyPort,
    Permission,
    Principal,
)


class FileAccessPolicy(AccessPolicyPort, RuntimeAccessPolicyPort):
    """基于 YAML 文件白名单的访问策略，默认拒绝。"""

    def __init__(self, path: str | Path) -> None:
        """初始化 FileAccessPolicy 实例。"""
        self._path = Path(path)
        self._rules = self._load(self._path)

    def evaluate(self, principal: Principal, permission: Permission) -> AccessDecision:
        """初始化基于文件的访问策略。Args: path: YAML 策略文件路径。"""
        """评估访问权限，返回 AccessDecision。"""
        if self._match(principal, permission):
            return AccessDecision(allowed=True)
        return AccessDecision(
            allowed=False,
            reason=(
                f"No policy rule allows {principal.principal_id} "
                f"to {permission.action} {permission.resource_type}"
            ),
        )

    def authorize(
        self,
        request: Request,
        
        action: str,
        resource_type: str,
        resource_id: str | None = None,
    ) -> bool:
        """检查请求是否对给定操作和资源授权。返回布尔值表示允许或拒绝。"""
        decision = self.evaluate(
            _principal_from_request(request),
            Permission(
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
            ),
        )
        return decision.allowed

    def _match(self, principal: Principal, permission: Permission) -> bool:
        for rule in self._rules:
            if not self._actor_matches(principal, rule):
                continue
            if not self._field_matches(permission.action, rule.get("action", "")):
                continue
            if not self._field_matches(permission.resource_type, rule.get("resource_type", "")):
                continue
            if not self._field_matches(permission.resource_id or "", rule.get("resource_id", "")):
                continue
            return True
        return False

    @staticmethod
    def _actor_matches(principal: Principal, rule: dict[str, Any]) -> bool:
        actors: list[str] = rule.get("actors", [])
        for actor in actors:
            if actor.startswith("role:") and actor[5:] in principal.roles:
                return True
            if actor == principal.principal_id:
                return True
        return False

    @staticmethod
    def _field_matches(value: str, pattern: str) -> bool:
        return pattern == "*" or value == pattern

    @staticmethod
    def _load(path: Path) -> list[dict[str, Any]]:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return raw.get("policies", []) if isinstance(raw, dict) else []


class AllowAllAccessPolicy(AccessPolicyPort, RuntimeAccessPolicyPort):
    """开发/测试默认的 allow-all 策略。"""

    def evaluate(self, principal: Principal, permission: Permission) -> AccessDecision:
        """评估访问权限。返回 AccessDecision 含允许/拒绝决定。"""
        
        del principal, permission
        return AccessDecision(allowed=True)

    def authorize(
        self,
        request: Request,
        
        action: str,
        resource_type: str,
        resource_id: str | None = None,
    ) -> bool:
        """评估主体的访问权限。返回 AccessDecision 包含允许/拒绝决定和拒绝原因。"""
        """检查请求是否对给定操作和资源授权。返回布尔值表示允许或拒绝。"""
        del request, action, resource_type, resource_id
        return True


class DenyAllAccessPolicy(AccessPolicyPort, RuntimeAccessPolicyPort):
    
    """安全测试和锁定模式使用的 deny-all 策略。"""

    def evaluate(self, principal: Principal, permission: Permission) -> AccessDecision:
        """评估访问权限。返回 AccessDecision 含允许/拒绝决定。"""
        del principal, permission
        return AccessDecision(
            allowed=False,
            reason="Deny-all policy",
        )

    def authorize(
        self,
        request: Request,
        
        action: str,
        resource_type: str,
        resource_id: str | None = None,
    ) -> bool:
        """评估主体的访问权限。返回 AccessDecision 包含允许/拒绝决定和拒绝原因。"""
        """检查请求是否对给定操作和资源授权。返回布尔值表示允许或拒绝。"""
        del request, action, resource_type, resource_id
        return False


def _principal_from_request(request: Request) -> Principal:
    """从请求头构造共享授权主体。"""

    actor = (request.headers.get("x-actor") or "anonymous").strip() or "anonymous"
    raw_roles = request.headers.get("x-roles", "")
    roles = tuple(role.strip() for role in raw_roles.split(",") if role.strip())
    return Principal(
        principal_id=actor,
        principal_type="request",
        roles=roles,
    )
