"""安全策略适配器。

实现访问控制和安全分区策略。
"""

from whale.ingest.adapters.security.file_access_policy import (
    AllowAllAccessPolicy,
    DenyAllAccessPolicy,
    FileAccessPolicy,
)
from whale.ingest.adapters.security.external_access_policy import ExternalAccessPolicy

__all__ = [
    "AllowAllAccessPolicy",
    "DenyAllAccessPolicy",
    "ExternalAccessPolicy",
    "FileAccessPolicy",
]
