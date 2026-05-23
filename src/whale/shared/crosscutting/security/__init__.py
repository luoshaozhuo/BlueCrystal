"""Security-oriented crosscutting models and ports."""

from whale.shared.crosscutting.security.model import CertificateRef, CredentialRef, SecretRef
from whale.shared.crosscutting.security.secret_provider import SecretProviderPort
from whale.shared.crosscutting.security.tls import TlsConfig

__all__ = [
    "CertificateRef",
    "CredentialRef",
    "SecretProviderPort",
    "SecretRef",
    "TlsConfig",
]

