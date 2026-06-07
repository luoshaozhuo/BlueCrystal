"""seahorse 端口层。

定义外部可替代的策略接口，包括生成策略和导出器端口。
本轮仅定义 GenerationStrategy，后续可扩展导出器等抽象。
"""
from __future__ import annotations

from seahorse.ports.generation_strategy import GenerationStrategy

__all__ = ["GenerationStrategy"]
