"""Secret provider boundary used by modules that need external secret storage."""

from __future__ import annotations

from typing import Protocol

from whale.shared.crosscutting.security.model import SecretRef


class SecretProviderPort(Protocol):
    """Resolve secret references without coupling callers to one backend."""

    def resolve_secret(self, ref: SecretRef) -> str:
        """Return the secret value for the provided reference."""

