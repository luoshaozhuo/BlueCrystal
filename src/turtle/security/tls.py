"""TLS 配置模型。

Turtle 全局 TLS 配置模型，供各协议适配器使用。
"""

from __future__ import annotations

from dataclasses import dataclass

from turtle.security.model import CertificateRef


@dataclass(frozen=True, slots=True)
class TlsConfig:
    """单条出站连接的 TLS 或 mTLS 配置。

    Attributes:
        enabled: 是否启用 TLS。
        require_mutual_tls: 是否要求双向 TLS。
        ca_certificate: CA 证书引用（可选）。
        client_certificate: 客户端证书引用（可选）。
        private_key: 私钥引用（可选）。
        verify_hostname: 是否校验主机名。
    """

    enabled: bool = False
    require_mutual_tls: bool = False
    ca_certificate: CertificateRef | None = None
    client_certificate: CertificateRef | None = None
    private_key: CertificateRef | None = None
    verify_hostname: bool = True

