"""Turtle 安全基础能力。

提供跨模块的密钥引用、凭证引用、证书引用、TLS 配置和密钥解析端口。
"""

from pacific.turtle.security.model import CertificateRef, CredentialRef, SecretRef
from pacific.turtle.security.secret_provider import SecretProviderPort
from pacific.turtle.security.tls import TlsConfig

__all__ = [
    "CertificateRef",
    "CredentialRef",
    "SecretProviderPort",
    "SecretRef",
    "TlsConfig",
]

