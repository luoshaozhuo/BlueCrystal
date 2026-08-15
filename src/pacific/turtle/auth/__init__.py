"""Turtle 认证授权基础能力。

提供跨模块的 identity、principal、permission、access policy 端口和决策模型。
"""

from pacific.turtle.auth.authorizer import AccessDecision
from pacific.turtle.auth.credential import CredentialRef
from pacific.turtle.auth.identity import Principal
from pacific.turtle.auth.policy import AccessPolicyPort, Permission

__all__ = [
    "AccessDecision",
    "AccessPolicyPort",
    "CredentialRef",
    "Permission",
    "Principal",
]

