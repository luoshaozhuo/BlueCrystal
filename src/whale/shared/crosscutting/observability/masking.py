"""Helpers for masking sensitive values before they reach logs or traces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SensitiveDataMasker:
    """Mask values whose keys suggest secrets, tokens, or private material."""

    sensitive_keys: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "password",
                "token",
                "secret",
                "authorization",
                "credential",
                "private_key",
                "certificate",
            }
        )
    )
    replacement: str = "***"

    def mask_mapping(self, values: Mapping[str, object]) -> dict[str, object]:
        """Return a copy with sensitive keys redacted."""

        masked: dict[str, object] = {}
        for key, value in values.items():
            masked[key] = self.replacement if self._is_sensitive_key(key) else value
        return masked

    def mask_text(self, key: str, value: object) -> object:
        """Mask one scalar when its key is sensitive."""

        return self.replacement if self._is_sensitive_key(key) else value

    def _is_sensitive_key(self, key: str) -> bool:
        normalized = key.strip().lower()
        return any(candidate in normalized for candidate in self.sensitive_keys)
