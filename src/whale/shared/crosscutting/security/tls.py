"""TLS configuration models shared across protocol adapters."""

from __future__ import annotations

from dataclasses import dataclass

from whale.shared.crosscutting.security.model import CertificateRef


@dataclass(frozen=True, slots=True)
class TlsConfig:
    """TLS or mTLS configuration for one outbound connection."""

    enabled: bool = False
    require_mutual_tls: bool = False
    ca_certificate: CertificateRef | None = None
    client_certificate: CertificateRef | None = None
    private_key: CertificateRef | None = None
    verify_hostname: bool = True

