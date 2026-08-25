"""为 observability 模块内单元测试提供独立包导入路径。"""

from __future__ import annotations

import sys
from pathlib import Path


OBSERVABILITY_SOURCE_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(OBSERVABILITY_SOURCE_ROOT))
