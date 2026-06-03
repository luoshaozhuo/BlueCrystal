"""无策略的安全基础工具。

提供 masking、redaction、hash、checksum、digest 等纯技术安全原语。
不保存脱敏策略、不进行权限判断、不承载数据分类和合规规则。

数据分类、安全区、合规脱敏策略归 turtle。
"""

from platform_shared.security_primitives.masking import SensitiveDataMasker

__all__ = [
    "SensitiveDataMasker",
]
