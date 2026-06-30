"""Seahorse CLI 薄入口。

包根只负责把 ``python -m seahorse`` 转发到 controller adapter；
argparse 子命令和文件 I/O 行为保留在
``seahorse.adapters.controllers.cli_controller``。
"""
from __future__ import annotations

import sys

from seahorse.adapters.controllers.cli_controller import main


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["main"]
