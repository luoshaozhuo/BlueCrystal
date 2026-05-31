"""Bundle 校验和。

计算和验证配置 bundle 的完整性校验和。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize_bundle_payload(payload: dict[str, Any]) -> bytes:
    """返回用于校验和的规范 JSON 编码。"""

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
    """计算 bundle payload 的 SHA256 校验和。"""

    return hashlib.sha256(canonicalize_bundle_payload(payload)).hexdigest()
