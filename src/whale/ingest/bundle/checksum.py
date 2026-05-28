"""Checksum helpers for ingest bundle payloads."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize_bundle_payload(payload: dict[str, Any]) -> bytes:
    """Return one canonical JSON encoding used for checksums."""

    cloned = dict(payload)
    cloned.pop("checksum", None)
    return json.dumps(
        cloned,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    ).encode("utf-8")


def compute_bundle_checksum(payload: dict[str, Any]) -> str:
    """Compute one SHA256 checksum for a bundle payload."""

    return hashlib.sha256(canonicalize_bundle_payload(payload)).hexdigest()
