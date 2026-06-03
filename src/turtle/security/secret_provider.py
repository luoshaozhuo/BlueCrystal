"""密钥提供方端口。

Turtle 全局密钥解析契约，各模块通过此端口解耦密钥后端。
"""

from __future__ import annotations

from typing import Protocol

from turtle.security.model import SecretRef


class SecretProviderPort(Protocol):
    """解析密钥引用，使调用方无需耦合到某一密钥后端。

    各模块可实现此协议接入 Vault、AWS Secrets Manager、K8s Secret 等。
    """

    def resolve_secret(self, ref: SecretRef) -> str:
        """返回指定引用对应的密钥值。

        Args:
            ref: 密钥引用。

        Returns:
            密钥明文字符串。

        Raises:
            实现可能因后端不可用或密钥不存在而抛出具体异常。
        """

