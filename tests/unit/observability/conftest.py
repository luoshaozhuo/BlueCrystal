"""为独立 ``abc/observability`` 包测试提供导入路径。

该 fixture 配置不改变生产路径；它只模拟该包独立安装后位于 sys.path 的状态。
"""

from __future__ import annotations

import sys
from pathlib import Path

OBSERVABILITY_ROOT = Path(__file__).parents[3] / "abc"
sys.path.insert(0, str(OBSERVABILITY_ROOT))
