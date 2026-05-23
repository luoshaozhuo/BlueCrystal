"""Authorization and identity primitives shared across modules."""

from whale.shared.crosscutting.auth.authorizer import AccessDecision
from whale.shared.crosscutting.auth.identity import Principal
from whale.shared.crosscutting.auth.policy import AccessPolicyPort, Permission

__all__ = [
    "AccessDecision",
    "AccessPolicyPort",
    "Permission",
    "Principal",
]

