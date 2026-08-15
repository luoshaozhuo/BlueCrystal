"""安全引用模型。

Turtle 全局安全引用模型，提供密钥、凭证和证书的抽象引用，
使各模块无需耦合到具体密钥管理后端。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SecretRef:
    """对应用进程外存储的密钥的引用。

    Attributes:
        provider: 密钥提供方标识（如 vault、aws_secrets_manager）。
        key: 密钥路径或名称。
        version: 密钥版本（可选）。
    """

    provider: str
    key: str
    version: str | None = None


@dataclass(frozen=True, slots=True)
class CredentialRef:
    """对受保护集成使用的凭据包的引用。

    Attributes:
        credential_id: 凭据包唯一标识。
        username_secret: 用户名密钥引用（可选）。
        password_secret: 密码密钥引用（可选）。
        token_secret: Token 密钥引用（可选）。
    """

    credential_id: str
    username_secret: SecretRef | None = None
    password_secret: SecretRef | None = None
    token_secret: SecretRef | None = None


@dataclass(frozen=True, slots=True)
class CertificateRef:
    """对单个证书或私钥材料的引用。

    Attributes:
        provider: 证书提供方标识。
        certificate_id: 证书唯一标识。
        version: 证书版本（可选）。
    """

    provider: str
    certificate_id: str
    version: str | None = None

