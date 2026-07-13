"""DB view adapter 错误边界。"""

from __future__ import annotations


class DbViewLoadError(ValueError):
    """从 Whale DB view 加载 Starfish server definition 失败。"""


__all__ = ["DbViewLoadError"]
