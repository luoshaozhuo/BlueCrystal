"""DB view outbound adapters。

本包按协议拆分 Whale 执行视图读取逻辑。adapter 负责把 DB rows 映射成
core definition，不创建真实 server，也不承担 Seahorse 的数据更新职责。
"""

from __future__ import annotations

from starfish.adapters.db_views.connections import ConnectionDbViewLoader
from starfish.adapters.db_views.errors import DbViewLoadError

__all__ = ["ConnectionDbViewLoader", "DbViewLoadError"]
