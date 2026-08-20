"""错误 Trace 去重指纹生成。"""

from __future__ import annotations

import hashlib
import re
import traceback


_NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")
_ADDR = re.compile(r"0x[0-9a-fA-F]+")


def make_error_fingerprint(
    exc: BaseException,
    *,
    operation: str,
) -> str:
    """从异常类型、操作、消息和末端栈帧生成稳定指纹。"""
    frames = traceback.extract_tb(exc.__traceback__)
    stable_frames = tuple(
        (frame.name, frame.filename.rsplit("/", 1)[-1])
        for frame in frames[-4:]
    )
    message = _NUMBER.sub(
        "<n>",
        _ADDR.sub("<addr>", str(exc)),
    )[:512]
    raw = repr(
        (
            type(exc).__module__,
            type(exc).__qualname__,
            operation,
            message,
            stable_frames,
        )
    )
    return hashlib.sha256(raw.encode()).hexdigest()
