"""Reusable security reference models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SecretRef:
    """Reference to a secret stored outside the application process."""

    provider: str
    key: str
    version: str | None = None


@dataclass(frozen=True, slots=True)
class CredentialRef:
    """Reference to a credential bundle used by a protected integration."""

    credential_id: str
    username_secret: SecretRef | None = None
    password_secret: SecretRef | None = None
    token_secret: SecretRef | None = None


@dataclass(frozen=True, slots=True)
class CertificateRef:
    """Reference to one certificate or private-key material entry."""

    provider: str
    certificate_id: str
    version: str | None = None

