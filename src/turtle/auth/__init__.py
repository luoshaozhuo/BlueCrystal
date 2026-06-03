"""Turtle 认证授权基础能力。

提供跨模块的 identity、principal、permission、access policy 端口和决策模型。
"""

from turtle.auth.authorizer import AccessDecision
from turtle.auth.credential import CredentialRef
from turtle.auth.identity import Principal
from turtle.auth.policy import AccessPolicyPort, Permission

__all__ = [
    "AccessDecision",
    "AccessPolicyPort",
    "CredentialRef",
    "Permission",
    "Principal",
]

